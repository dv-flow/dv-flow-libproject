# dv-flow-libproject

Project archetypes and methodology-specific template tasks for
[dv-flow](https://github.com/dv-flow/dv-flow-mgr).

A verification project spends most of its flow file answering questions every
verification project answers: which simulator, which build variant, what does
`dfm run tests` mean, where does lint hang. This library answers them once. A
project inherits an archetype and is left with only what is actually its own --
its sources, its testbench wiring, its cases.

## Packages

| Package | Kind | What it is |
| --- | --- | --- |
| `project.dv` | archetype (`uses:`) | Methodology-neutral DV project: the `src-*`/`lint-*` interface, `tests`/`tests-info`, the `--sim`/`--build` knobs and the flag holders they select, `sv-module`/`sv-package` |
| `project.dv.uvm` | archetype (`uses:`) | `project.dv` plus the UVM building blocks in scope |
| `project.dv.uvm.utils` | capability (instantiate) | Reusable UVM compounds: `env-base`, `tb-img`, `tb-base`, `run`, `lib` |

An **archetype** is inherited with `uses:`; its tasks and variables become the
project's own. A **capability** package is instantiated -- its compounds are
building blocks a project stamps out by name. The split is what lets a cocotb
or formal archetype sit beside `project.dv.uvm` on the same project interface.

## Using it

```yaml
package:
  name: my-project
  uses: project.dv.uvm
  imports:
  - project.dv.uvm      # `uses:` names the base; the import puts it in scope

  tasks:
  - override: src-rtl
    needs: [rtl]

  - override: tests
    needs: [uvm-tests]
```

That project now has:

```
dfm run tests                    # the regression -- nonzero iff a case failed
dfm run tests --tests arb,err    # a selection; unselected cases are never built
dfm run tests-info               # the inventory, building nothing
dfm run tests --build dbg        # -O0 and waveforms, end to end
dfm run tests --sim mti          # a different simulator backend
```

`project.dv` declares slots a project is expected to implement, and holds it
to them: a slot declared and never filled would otherwise run and report
success, so the ones with no useful empty meaning fail with a hint instead.
A project that has no lint flow says so -- `- override: lint-rtl` with
`uses: std.NotProvided` -- rather than leaving the slot hanging.

## Requirements

* `dv-flow-mgr >= 1.19` -- package `uses:` inheritance of *variables*
* `dv-flow-libhdlsim` -- the simulation tasks the archetypes are built on
* `UVM_HOME` -- for the UVM packages; `hdlsim.SimLibUVM` locates UVM through it

## Documentation

Full documentation is in [`docs/`](docs), including a generated reference for
every task and parameter in the three packages.

```shell
ivpm update -d default-dev
./packages/python/bin/sphinx-build -W -b html docs docs/_build/html
```

| Page | |
| --- | --- |
| `docs/quickstart.rst` | A UVM project from nothing, step by step |
| `docs/guide/archetypes.rst` | Archetype vs capability; why `project.dv.uvm` has no tasks |
| `docs/guide/slots.rst` | The project interface, `std.check.Implemented`, `std.NotProvided` |
| `docs/guide/knobs.rst` | `--sim` and `--build` |
| `docs/guide/flags.rst` | The `flags-<stage>-<variant>` contract |
| `docs/reference/` | Generated from the flow files |
| `docs/contributing.rst` | Docs build, coverage gate, and how tasks get documented |
