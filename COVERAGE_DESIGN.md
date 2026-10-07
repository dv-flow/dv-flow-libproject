# Coverage in the project flow — Design

Status (2026-10-07): **implemented** on branch `coverage-knob`
(uncommitted): the knob, the holder, the bundle and the `coverage`
entrypoint. It depends on libhdlsim `1dfaf5d` (`SimCovMerge`, now synced into
`packages/`) and on two dv-flow-mgr fixes that are not released yet; see
[Implementation notes](#implementation-notes).

Builds on dv-flow-libhdlsim's `COVERAGE_DESIGN.md` (phase 1 implemented
2026-09-30, plus `SimCovMerge`). That design already sketched a libproject
knob, and its plan says Phase 7 (libproject) was done on a branch named
`coverage-knob`. That branch was never found: not in this repo, not in
`packages/dv-flow-libproject` under pss-registers-up (`packages/` and
`packages.1/`), and covsight has no libproject checkout. So this was redone
from `main`.

## What libhdlsim gives us

- **`hdlsim.SimCovArgs`**, a sim-neutral DataItem with one field, `level`:
  `none < func < code < full`. Each level includes the ones below it. The
  field defaults to the package variable `hdlsim.cov`.
- **`SimImage` consumes it.** The image is built at the highest level
  requested, and records that level in `cov.json`. **`SimRun` has no
  coverage parameter**: it reads `cov.json` and collects what the image was
  built for. So coverage has to be wired at the image, and only there.
  `SimLib` (and so `flags-comp-*` and `env-base`) is not involved.
- **Per-run results**: a `simCovDb` artifact with a `format=` attribute,
  `stats.cov_<kind>_{pct,covered,total}`, and `runinfo.cov`.
- **Per-suite results**: `SimSuiteReport` reports `cov_<kind>_pct_max` (the
  best single case, not merged coverage), and puts per-case coverage in
  `junit.xml`, `ctrf.json` and the printed summary. `tests` and `smoke` get
  all of this as soon as their images are built with coverage.
- **`hdlsim.SimCovMerge`** merges the databases from the runs, results or
  suites it `needs:`. It works on vlt, vcs and mti. It has no merge for xzm
  or xcm. It is an error if it finds no database to merge.

## Recommendation

Your guess is right: add a top-level knob, `cov`, next to `sim` and `build`.
It is a separate axis rather than more values of `build`, because a
regression wants `opt` with `code` and a triage run wants `dbg` with `none`.
Folding coverage into `build` would mean a holder for every combination
(`opt-code`, `dbg-func`, ...). The knob needs three supporting pieces:

1. **The `cov` knob** in `project.dv`.
2. **One holder, `flags-cov`**, which every image wires in.
3. **A `coverage` entrypoint** that merges the coverage from a `tests` run.

### 1. The knob

```yaml
cov:
  type: str
  value: none
  cli: true
  desc: Coverage collected by every image and run in this project
  values:
  - {value: none, desc: "no coverage -- the default"}
  - {value: func, desc: "covergroups and assertions"}
  - {value: code, desc: "functional plus line/branch/expression"}
  - {value: full, desc: "code plus toggle and FSM -- the expensive one"}
```

- The name `cov` matches `hdlsim.cov`. An unqualified `--cov code` /
  `-D cov=code` binds every package that declares `cov`, so it sets
  `hdlsim.cov` as well. That is harmless, and it means a bare
  `uses: hdlsim.SimCovArgs` anywhere in the project follows the same flag.
- The default stays `none`. Coverage slows the build and the run, and it
  rebuilds the images (see [Costs](#costs-and-caveats)), so it must be asked
  for.
- A leaf can change the default value-only (`with: {cov: func}`), the same
  way it changes `build`. A nightly-only project would not do this; it would
  pass `--cov` from CI instead.

### 2. The holder

One holder rather than one per value, because the level is a field of a
sim-neutral item and not a list of simulator flags:

```yaml
- { name: flags-cov, uses: hdlsim.SimCovArgs, with: { level: "${{ cov }}" } }
```

It goes in the image's `needs:`, next to the elab holder:

```yaml
- name: tb-img-rtl
  uses: project.dv.uvm.utils.tb-img
  needs: [uvm-env, "flags-comp-${{ build }}", "flags-elab-${{ build }}", flags-cov]
  with: { top: [hvl_top] }
```

`project.dv.uvm.utils` stays flag-agnostic: `tb-img`'s injection slot
(`tb-src`) forwards the item to `SimImage` as it does the other holders. The
`run` compound needs no change.

**Why wire it explicitly, rather than baking a bare `SimCovArgs` into
`tb-img`/`tb-base`?** Baking it in would make every existing project pick
up `--cov` with no edit. But it would break the rule that no compound names
flags, and it would take away the per-image choice. An RTL image with
coverage next to an SPL image without it is the same "two cells of an axis"
argument that made `build` a variable (`docs/guide/flags.rst`). With the
explicit holder, a leaf can:

- leave `flags-cov` off an image that should never be instrumented;
- pin one image to a fixed level with its own holder
  (`uses: hdlsim.SimCovArgs`, `with: {level: full}`). The image takes the
  highest level it is given.

#### Optional: a bundle so the next knob doesn't touch every leaf

`cov` is the second project-wide knob that has to reach every image, and
each one so far has meant editing every `tb-img` in every leaf. A passthrough
bundle would make `cov` the last knob that needs that edit:

```yaml
- name: flags-img                   # everything an image build needs
  passthrough: all
  needs: ["flags-comp-${{ build }}", "flags-elab-${{ build }}", flags-cov]
```

A leaf then writes `needs: [uvm-env, flags-img]`, and a future knob is one
line here. The per-stage holders stay, so nothing breaks. I'd do it in the
same change, but it is separable: see [Open questions](#open-questions).

### 3. The `coverage` entrypoint

`tests` already gives per-case percentages and the suite's best case. A
merged figure needs `SimCovMerge`, and that should be a named verb so every
project spells it the same way:

```yaml
- root: coverage
  uses: hdlsim.SimCovMerge
  desc: Merge the coverage of a `tests` run into one database and report it
  needs: [tests]
  with:
    sim: "${{ sim }}"
```

```
dfm run tests --cov code                    # per-case coverage in the suite report
dfm run coverage --cov code                 # the same run, plus the merged database and totals
dfm run coverage --cov code -D tests=a,b    # a selection, merged
dfm run tests --build dbg --cov func        # the knobs combine
```

- It hangs off `tests`, not `smoke`. Merged coverage is a regression
  question. A leaf that wants smoke coverage can add its own root.
- **Selection.** `--tests`/`--views` are flags of the root task, so they
  don't reach `tests` when you run `coverage`. `-D tests=...` does, because
  a bare `-D` binds any task with that parameter. That spelling works, but
  the asymmetry is a wart (see [Open questions](#open-questions)).
- **`--cov none`.** `SimCovMerge` fails with "no coverage database". That is
  the right outcome, but the message should say "run with `--cov func` or
  higher". This can be a hint in libhdlsim's error, or a `requires:` check
  here.
- **Unsupported simulators.** `--sim xzm|xcm|xsm|ivl` has no merge, so
  `coverage` fails there. `tests --cov ...` still works on xzm and xcm and
  gives per-case numbers. `std.NotProvided` doesn't fit, because it is a
  per-project choice and this is per-simulator. So the error from
  `SimCovMerge`'s backend selection is what users see, and it should name
  the simulators that do have a merge.

## Costs and caveats

- **Changing `cov` rebuilds every image it reaches.** That is correct,
  because the image is what's instrumented, but alternating `tests` and
  `tests --cov code` in one rundir rebuilds each time. CI should give the
  coverage job its own rundir.
- **On UVM benches, `code` and `full` mostly measure UVM.** libhdlsim has no
  exclusions yet, so the UVM library is instrumented with the design. In the
  libhdlsim measurement, xezim reported 0.67% statements and Verilator 22%
  line on a 6-statement DUT. Until selection lands, **`func` is the
  meaningful level for `project.dv.uvm` projects**, and code-coverage
  numbers are not comparable across simulators. The knob's `desc` should say
  so.
- **Verilator `get_coverage()` returns 0.** A testbench that prints
  covergroup coverage from `final` is wrong on vlt. The database and the
  `cov_*` stats are correct.

## Changes

As planned. Where the work diverged from this table, see
[Implementation notes](#implementation-notes).

| File | Change |
|---|---|
| `src/dv_flow/libproject/dv/flow.yaml` | `cov` knob; `flags-cov` holder; `coverage` root; optional `flags-img` bundle |
| `src/dv_flow/libproject/dv/uvm/utils/flow.yaml` | docs only: the `tb-img` example and the package doc show `flags-cov` (or `flags-img`) |
| `docs/guide/knobs.rst` | a `--cov` section: levels, orthogonal to `--build`, the UVM caveat, the rebuild cost |
| `docs/guide/flags.rst` | `flags-cov` in the contract (one holder, not per value); the bundle if adopted |
| `docs/guide/slots.rst` | the `coverage` entrypoint |
| `README.md` | the packages table and the `dfm run` examples |
| `tests/unit/test_archetypes.py` | `--cov code` resolves `flags-cov` to `SimCovArgs(level=code)`; the `cov` value set; the `coverage` root exists and needs `tests`; with the bundle, it forwards all three items |
| pss-registers-up (manual) | the libhdlsim plan's still-open 7.4: wire `flags-cov`, then `dfm run coverage --cov func` on vlt |

## Implementation notes

What was built, and what was found while building it.

**In `project.dv` now:** the `cov` knob, the `flags-cov` holder, the
`flags-img` bundle and the `coverage` root. Docs: `knobs.rst`, `flags.rst`,
`slots.rst`, `quickstart.rst`, `index.rst` and the README. Tests are in
`tests/unit/test_archetypes.py`: 43 pass against the fixed dv-flow-mgr, up
from 29. The Verilator tests skip if `verilator` is not on PATH:
- an image built through the bundle records `--cov code` in its `cov.json`;
- `coverage --cov code` merges both cases, and `coverage --cov func -D
  tests=a` merges one;
- `coverage` at `none` fails with a message about the coverage level.

**dv-flow-mgr bug, fixed on branch `fix-cli-reload-provider-cache` in
`../dv-flow-mgr` (uncommitted).** `--build dbg` gave `flags-img` the `opt`
holders, while `-D build=dbg` worked. `dfm run` loads the project, reads its
`cli:` flags, and reloads with their values. But a package registered by a
plugin (`project.dv`, `hdlsim`) is served by a process-wide `ExtRgy`
provider, and it handed the reload the package built in the first load,
without the flag. That breaks anything resolved while the base package
loads:

- `${{ build }}` in the `needs:` of an inherited task, which is what the
  bundle uses. A leaf's own `needs: ["flags-comp-${{ build }}"]` was never
  affected, because the leaf is always reloaded. That is why nobody hit this
  before.
- Package-variable defaults in non-root packages. So `--cov` didn't reach
  `hdlsim.cov`, and a bare `uses: hdlsim.SimCovArgs` ignored it.

`--sim` on the holders was never affected: a task parameter is evaluated at
graph build. The fix: a provider reuses its package only for a loader with
the same parameter overrides. It has a regression test
(`tests/unit/test_cli_flag_reload.py`; two of its cases fail without the
fix) and a ChangeLog entry. **Until a release has it, `flags-img` ignores
`--build`**, and `test_the_image_bundle_forwards_every_image_flag[dbg]` and
`test_the_cov_flag_reaches_a_bare_hdlsim_request` fail against dv-flow-mgr
`e50312c`, the latest. The README and `flags.rst` say so. (With the second
bug below, 5 of the 43 tests fail against `e50312c`.)

**Second dv-flow-mgr bug, found when the root went in (same branch, also
uncommitted).** After `ivpm sync` brought in libhdlsim `1dfaf5d`
(`SimCovMerge`) and `be8c790`, together with mgr `e50312c` (`rebindUses`),
`dfm run coverage` also ran `project.dv.tests`, the archetype's empty slot,
and failed with "no tests ran". `leaf.coverage` is the alias a leaf gets of
`project.dv.coverage`. Its `needs` are already re-resolved in the leaf
(`leaf.tests`), and it is marked `inherited` so needs gathering does not walk
into the base task as well. The mark was an ad-hoc attribute. `rebindUses`
copies with `dc.replace`, which copies only dataclass fields, so the rebound
alias lost the mark and gathered `project.dv.tests` too. A leaf-declared root
with the same `uses:` was never affected. The fix makes `Task.inherited` a
field. It has a regression test in `tests/unit/test_elab_rebind_chain.py`,
which fails without the fix, and a ChangeLog entry. The full mgr suite with
both fixes: 1962 passed, 10 skipped, 5 xfailed.

**The `coverage` root.** It was blocked while `SimCovMerge` existed only
uncommitted in `../dv-flow-libhdlsim`: committed libhdlsim `d651ae2` lacked
it, and a root that `uses:` a missing task makes the whole archetype fail to
load. libhdlsim `1dfaf5d` committed it, `ivpm sync` brought it into
`packages/`, and the root is now in `project.dv`. Before that, it was probed
against libhdlsim's working tree on a two-case Verilator project:

- `dfm run coverage --cov code`: both cases ran, the suite printed a
  coverage line, and the merge reported line 36.67%, branch 50%, expr
  45.45%, covergroup 75%, user 100%.
- `dfm run coverage --cov func -D tests=c0`: one case, one database merged,
  functional kinds only.
- `dfm run coverage` (at `none`): fails with "No format=vlt-dat coverage
  databases in the inputs. Were the runs' images built with a coverage
  level?". That is clear enough; no extra check is needed here.
- `dfm run coverage --tests c0`: refused, because `coverage` takes no
  arguments. That is the asymmetry noted under open question 2.

**Toolchain note.** `/tools/verilator` (5.041) comes first on PATH on this
machine. It ignores covergroups (`COVERIGN`), and its
`verilator_coverage` summary doesn't parse, so every `cov_*` stat comes
back empty. The 5.052 in `packages/verilator/bin` works. Coverage runs need
the packaged Verilator first on PATH.

## Open questions

1. ~~The `flags-img` bundle: now, later or never?~~ Done now. A matching
   `flags-run` bundle isn't needed yet: runs take only `flags-run-${{ build }}`.
2. **Selection on `coverage`.** Is `-D tests=a,b` acceptable, or should
   `coverage` accept `--tests`/`--views`? Two ways to get the flags:
   - a dfm feature that lets a root forward named parameters to a task it
     needs;
   - libhdlsim gives `SimSuiteReport` a merge option, so `tests --cov code`
     merges directly and no `coverage` root is needed. That is simpler for
     users, but it ties the suite report to the merge backends.
3. **Name of the root:** `coverage` or `tests-cov`? `tests-cov` sits next to
   `tests-info` in `dfm run` listings. `coverage` reads better on the command
   line.
4. **Should `coverage` default to a level** when `--cov` isn't given, so
   `dfm run coverage` alone just works? A root can't set a package variable,
   so this would need a second holder pinned to `func` that only the
   `coverage` graph uses. That means a second set of image instances, which
   is probably not worth it. I lean towards the clear error from the
   `--cov none` bullet.
