#****************************************************************************
#* test_archetypes.py
#*
#* What a project gets by inheriting an archetype.
#*
#* These are contract tests, not coverage: each one pins something a project
#* built on this library depends on and would have no way to notice breaking
#* until a regression run. The archetypes are almost all declaration, so the
#* things that can break are the interface (which names exist, and where), the
#* knobs (which flags exist, and what they reach), and scope (which building
#* blocks a leaf can name).
#****************************************************************************
import subprocess
import sys
import textwrap

import pytest


# A project that inherits the UVM archetype and fills in its slots. `imports:`
# alongside `uses:` is required, not decoration: `uses:` says which package to
# inherit from, the import is what puts it in scope to be found.
LEAF = '''\
package:
    name: leaf
    uses: project.dv.uvm
    imports:
    - project.dv.uvm

    tasks:
    - override: src-rtl
      needs: [my-rtl]
    - override: lint-rtl
      uses: std.NotProvided

    - name: my-rtl
      uses: std.Message
      with: {msg: "rtl"}

    - root: show
      uses: std.Message
      with: {msg: "sim=${{ sim }} build=${{ build }}"}
'''


def _dfm(d, *args):
    return subprocess.run(
        [sys.executable, "-m", "dv_flow.mgr", "run"] + list(args),
        cwd=str(d), capture_output=True, text=True)


@pytest.fixture
def leaf(tmp_path):
    (tmp_path / "flow.yaml").write_text(textwrap.dedent(LEAF))
    return tmp_path


# ---------------------------------------------------------------------------
# The interface
# ---------------------------------------------------------------------------

def test_the_archetype_supplies_the_project_entrypoints(leaf):
    """`tests`, `tests-info` and `lint-rtl` are the verbs a project built on
    this library answers to. They are the whole point of a shared archetype: the
    same command means the same thing in every project that inherits it."""
    proc = _dfm(leaf)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for verb in ("leaf.tests", "leaf.tests-info"):
        assert verb in proc.stdout, proc.stdout
    # `lint-rtl` is inherited too, but the LEAF fixture declares it
    # not-provided -- see the not-provided tests below.


def test_inherited_tasks_are_named_for_the_inheriting_project(leaf):
    """`project.dv` is a DOTTED package name, and the leaf inherits it through
    `project.dv.uvm`. The inherited task is the leaf's own, under a plain short
    name -- not filed under a namespace made out of the base's name. Requires
    the fix in dv-flow-mgr 1.19."""
    proc = _dfm(leaf)
    assert "leaf.tests" in proc.stdout
    assert "leaf.dv.tests" not in proc.stdout
    assert "leaf.uvm.tests" not in proc.stdout


def test_an_unimplemented_slot_fails_rather_than_passing_quietly(tmp_path):
    """The reason the slots carry `std.check.Implemented`. A declared-and-never-
    filled task otherwise RUNS AND REPORTS SUCCESS, which is the worst outcome
    for a shared interface: `dfm run src-rtl` would mean something in one
    project and nothing in the next."""
    (tmp_path / "flow.yaml").write_text(textwrap.dedent('''\
    package:
        name: leaf
        uses: project.dv.uvm
        imports:
        - project.dv.uvm
        tasks:
        - root: use-rtl
          uses: std.Message
          needs: [src-rtl]
          with: {msg: hi}
    '''))
    proc = _dfm(tmp_path, "use-rtl")
    assert proc.returncode != 0
    out = proc.stdout + proc.stderr
    assert "src-rtl" in out
    # The hint tells the reader what to wire, rather than only that something
    # is wrong.
    assert "override: src-rtl" in out, out


# ---------------------------------------------------------------------------
# The knobs
# ---------------------------------------------------------------------------

def test_the_project_knobs_are_inherited_as_flags(leaf):
    """`--sim` and `--build` are declared once, in `project.dv`, with their
    value sets and per-value help. A leaf restates none of it."""
    proc = _dfm(leaf)
    assert "Project options" in proc.stdout
    assert "--sim" in proc.stdout
    assert "--build" in proc.stdout
    # The per-value documentation comes with them.
    assert "Verilator" in proc.stdout
    assert "waveform tracing" in proc.stdout


def test_the_knobs_are_readable_as_variables(leaf):
    """The flags and the variables have to arrive together: a leaf reads
    `${{ build }}` to name its flag holder, so inheriting the flag without the
    variable would leave the flag with nothing to set."""
    proc = _dfm(leaf, "show")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "sim=vlt build=opt" in proc.stdout


@pytest.mark.parametrize("args,expect", [
    (["--build", "dbg"], "sim=vlt build=dbg"),
    (["--sim", "mti"], "sim=mti build=opt"),
    (["-D", "build=dbg"], "sim=vlt build=dbg"),
])
def test_a_knob_can_be_set_from_the_command_line(leaf, args, expect):
    proc = _dfm(leaf, "show", *args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert expect in proc.stdout


def test_a_leaf_can_change_a_default_without_restating_the_declaration(tmp_path):
    """The value-only override. A project whose regressions should default to
    debug says so in one line and keeps the archetype's type, value set and
    help."""
    (tmp_path / "flow.yaml").write_text(textwrap.dedent('''\
    package:
        name: leaf
        uses: project.dv.uvm
        imports:
        - project.dv.uvm
        with:
          build: dbg
        tasks:
        - root: show
          uses: std.Message
          with: {msg: "build=${{ build }}"}
    '''))
    proc = _dfm(tmp_path, "show")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "build=dbg" in proc.stdout
    # ... and the declaration survived: the value set is still enforced.
    bad = _dfm(tmp_path, "show", "-D", "build=nosuch")
    assert bad.returncode != 0


def test_an_unknown_knob_value_is_rejected(leaf):
    proc = _dfm(leaf, "show", "--build", "nosuch")
    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr


# ---------------------------------------------------------------------------
# Flag holders
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("stage", ["comp", "elab", "run"])
@pytest.mark.parametrize("variant", ["opt", "dbg"])
def test_a_flag_holder_exists_for_every_stage_and_variant(leaf, stage, variant):
    """Consumers name a holder by the knob -- `needs: ["flags-comp-${{ build }}"]`
    -- so a missing (stage, variant) pair is not a missing convenience, it is an
    unresolvable reference in every project that selects that variant."""
    proc = _dfm(leaf, "flags-%s-%s" % (stage, variant))
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_a_flag_holder_resolves_its_simulator_backend(leaf):
    """The holders are abstract hdlsim tasks: an elaborator reads their `sim`
    parameter to pick the backend. Inherited two packages deep, that parameter
    has to survive the chain -- when it did not, the backend selector reported
    'no simulator selected' for a project that had chosen one. Requires the fix
    in dv-flow-mgr 1.19."""
    proc = _dfm(leaf, "flags-run-opt")
    assert "No simulator selected" not in (proc.stdout + proc.stderr)
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("compound", ["env-base", "tb-img", "tb-base", "run", "lib"])
def test_the_uvm_compounds_are_in_scope(leaf, compound):
    """`project.dv.uvm` imports `project.dv.uvm.utils` so that a project
    inheriting the archetype can instantiate the UVM blocks without importing
    them itself."""
    proc = subprocess.run(
        [sys.executable, "-m", "dv_flow.mgr", "show", "task",
         "project.dv.uvm.utils.%s" % compound],
        cwd=str(leaf), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert compound in proc.stdout


def test_the_filesets_are_inherited(leaf):
    proc = subprocess.run(
        [sys.executable, "-m", "dv_flow.mgr", "show", "task", "leaf.sv-package"],
        cwd=str(leaf), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_every_registered_package_resolves_to_a_file_that_declares_it():
    """The entry-point map is the only thing tying a dotted package name to a
    file. A name that points at the wrong file, or at a file declaring a
    different package, fails far from here."""
    import os
    import yaml
    from dv_flow.libproject.__ext__ import dvfm_packages

    for name, path in dvfm_packages().items():
        assert os.path.isfile(path), "%s -> missing %s" % (name, path)
        with open(path) as fp:
            declared = yaml.safe_load(fp)["package"]["name"]
        assert declared == name, \
            "%s is registered as '%s' but declares '%s'" % (path, name, declared)


def test_declaring_the_lint_slot_not_provided_removes_the_verb(leaf):
    """The LEAF fixture has no lint flow and says so. The slot then leaves the
    listing entirely rather than sitting there flagged: a project that has
    answered should not keep being asked."""
    proc = _dfm(leaf)
    assert "[unimplemented]" not in proc.stdout, proc.stdout
    assert "lint-rtl" not in proc.stdout, proc.stdout


def test_a_not_provided_slot_refuses_rather_than_passing(leaf):
    """What makes this a real answer rather than a way of silencing the check:
    typing the verb says the project does not provide it. Silencing the check
    instead would leave a task that reports success -- the failure the
    requirement exists to catch."""
    proc = _dfm(leaf, "lint-rtl")
    assert proc.returncode != 0
    assert "does not provide 'lint-rtl'" in proc.stdout + proc.stderr


def test_a_not_provided_slot_is_still_discoverable(leaf):
    proc = subprocess.run(
        [sys.executable, "-m", "dv_flow.mgr", "show", "task", "leaf.lint-rtl"],
        cwd=str(leaf), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "not provided by this project" in proc.stdout


# ---------------------------------------------------------------------------
# The source slots carry sources
# ---------------------------------------------------------------------------

SRC_LEAF = '''\
package:
    name: leaf
    uses: project.dv.uvm
    imports:
    - project.dv.uvm

    tasks:
    - override: src-rtl
      needs: [my-rtl]
    - override: lint-rtl
      uses: std.NotProvided

    - name: my-rtl
      uses: std.FileSet
      with:
        type: verilogSource
        base: rtl
        include: "*.v"

    - root: consume-rtl
      uses: std.Publish
      needs: [src-rtl]
'''


def test_src_rtl_forwards_its_sources_to_consumers(tmp_path):
    """`src-rtl` IS the aggregated RTL source for the package, not a marker
    pointing at it -- so a consumer wired the way the archetype's own
    `lint-rtl` is (`needs: [src-rtl]`) receives the filesets.

    This needs `passthrough: all` on the slot. Without it the slot forwards
    nothing (an `export:` task with no implementation defaults to passing
    through none of its inputs), and every consumer gets an empty input set
    while the run still reports success -- the same class of quiet failure
    that `std.check.Implemented` exists to prevent, one step further along.
    """
    (tmp_path / "flow.yaml").write_text(textwrap.dedent(SRC_LEAF))
    (tmp_path / "rtl").mkdir()
    (tmp_path / "rtl" / "dut.v").write_text("module dut; endmodule\n")

    proc = _dfm(tmp_path, "consume-rtl")
    assert proc.returncode == 0, proc.stdout + proc.stderr

    published = list((tmp_path / "rundir" / "out").rglob("dut.v"))
    assert published, (
        "src-rtl did not forward its fileset to the consumer\n"
        + proc.stdout + proc.stderr)
