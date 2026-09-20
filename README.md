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
    needs: [uvm.uvm-tests]
```

That project now has:

```
dfm run tests                    # the regression -- nonzero iff a case failed
dfm run tests --tests arb,err    # a selection; unselected cases are never built
dfm run tests-info               # the inventory, building nothing
dfm run tests --build dbg        # -O0 and waveforms, end to end
dfm run tests --sim mti          # a different simulator backend
```

`--sim` and `--build` are package variables declared by `project.dv` with
`cli: true`. A project reads them by plain name (`${{ build }}`), changes a
default value-only (`with: {build: dbg}`), or restates the declaration to widen
the accepted set.

## Filling in the interface

`project.dv` declares slots a project is expected to implement. A slot declared
and never filled runs and reports success, which is the worst outcome for a
shared interface -- so the ones with no useful empty meaning carry a
`std.check.Implemented` requirement and fail with a hint instead.

You do not have to run one to find out. `dfm run` marks what is still open:

```
leaf.lint-rtl   - Entrypoint for running lint on RTL sources  [unimplemented]
leaf.tests      - Entrypoint for running tests defined by the project

[unimplemented] run `dfm run <task>` for details on how to implement it.
```

A project with no lint flow says so, rather than leaving the slot hanging:

```yaml
  - override: lint-rtl
    uses: std.NotProvided
```

That takes `lint-rtl` out of `dfm run` entirely -- this project does not offer
that verb -- while `dfm show task lint-rtl` still reports that the slot exists
and was declined on purpose. Naming it anyway fails saying so.

Do **not** reach for `requires: [{std.check.Implemented: {severity: off}}]`
here. That silences the check and leaves a task that reports success, which is
the exact failure the check exists to prevent. `severity: off` is for declining
a check you disagree with, not for declaring a slot inapplicable.

## Flags stay with the project

No task in `project.dv.uvm.utils` names a flag holder. Each compound has an
injection slot -- a passthrough subtask forwarding whatever the instantiation's
`needs:` feeds it -- so compile, elaborate and run flags arrive through the
compound boundary:

```yaml
  - name: uvm-env
    uses: project.dv.uvm.utils.env-base
    needs: [rtl, ral, "flags-comp-${{ build }}"]
```

`flags-comp-${{ build }}` names the holder by the variable rather than by a
literal, so `--build dbg` moves the library, the image and the run together and
nothing downstream mentions `opt` or `dbg`.

## Requirements

* `dv-flow-mgr >= 1.19` -- package `uses:` inheritance of *variables*
* `dv-flow-libhdlsim` -- the simulation tasks the archetypes are built on
* `UVM_HOME` -- for the UVM packages; `hdlsim.SimLibUVM` locates UVM through it
