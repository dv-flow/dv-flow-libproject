The project interface
=====================

:doc:`project.dv <../reference/project_dv>` declares a small set of tasks a
project is expected to implement, and then holds the project to them. That is
the whole value of a shared archetype: the same command means the same thing
in every project built this way.

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Slot
     - What a project puts in it
   * - :dvf:task:`src-rtl`
     - The project's synthesizable Verilog RTL
   * - :dvf:task:`src-spl`
     - The project's sequential-process-level SystemVerilog sources
   * - :dvf:task:`lint-rtl`
     - The lint flow, wired downstream of ``src-rtl``
   * - :dvf:task:`tests`
     - The cases and suites the regression runs
   * - :dvf:task:`smoke`
     - A quick subset of those cases -- what CI runs on every commit
   * - :dvf:task:`tests-info`
     - Nothing -- it reads its inventory off ``tests``

A project fills a slot with ``override:``:

.. code-block:: yaml

   tasks:
   - override: src-rtl
     needs: [rtl]

An empty slot is worse than a missing one
-----------------------------------------

A task declared and never implemented **runs and reports success**. For a
shared interface that is the worst available outcome, because it makes
``dfm run src-rtl`` mean something in one project and nothing in the next, and
nothing about the failure is visible until something downstream is mysteriously
empty.

So the slots with no useful empty meaning carry a requirement:

.. code-block:: yaml

   requires:
   - std.check.Implemented:
       hint: |
         `src-rtl` must be wired to the task(s) providing this project's
         synthesizable RTL. Typically:

             - override: src-rtl
               needs: [rtl]

The check fails the run, and the hint tells the reader what to wire rather
than only that something is wrong. You do not have to run one to find out:
``dfm run`` marks what is still open.

.. code-block:: text

   my-project.lint-rtl   - Entrypoint for running lint on RTL sources  [unimplemented]
   my-project.tests      - Entrypoint for running tests defined by the project

   [unimplemented] run `dfm run <task>` for details on how to implement it.

Why ``Implemented`` and not a type check
----------------------------------------

The obvious alternative is ``Needs: {produces: std.FileSet}`` -- assert that
something upstream produces filesets. It does not work here.

``produces:`` matches what a task **declares**, and ``std.FileSet`` tasks emit
filesets at runtime without declaring anything. A produces-check on ``src-rtl``
would therefore fail a correctly wired project. Keyed checks suit a marker type
a producer declares deliberately; they do not suit a ubiquitous type nobody
annotates.

Declining a slot: ``std.NotProvided``
-------------------------------------

Not every project has a lint flow. A project that does not says so:

.. code-block:: yaml

   - override: lint-rtl
     uses: std.NotProvided

That takes ``lint-rtl`` out of ``dfm run`` entirely -- this project does not
offer that verb -- while ``dfm show task lint-rtl`` still reports that the slot
exists and was declined on purpose. Naming it anyway fails saying so:

.. code-block:: text

   $ dfm run lint-rtl
   error: my-project does not provide 'lint-rtl'

A project that has answered should not keep being asked, which is why the slot
leaves the listing rather than sitting there flagged.

.. warning::

   Do **not** reach for ``requires: [{std.check.Implemented: {severity: off}}]``
   here. That silences the check and leaves a task that reports success --
   which is the exact failure the check exists to prevent, now with the warning
   removed as well.

   ``severity: off`` is for declining a check you disagree with.
   ``std.NotProvided`` is for declaring a slot inapplicable. They look
   interchangeable and are opposites: one removes the diagnostic, the other
   records the decision.

The source slots carry the sources
----------------------------------

:dvf:task:`src-rtl` **is** the aggregated RTL source for the project, not a
marker pointing at it. A consumer wired the way the archetype's own
``lint-rtl`` is receives the filesets:

.. code-block:: yaml

   - name: lint
     uses: hdllint.Rtl
     needs: [src-rtl]          # gets the filesets, not an empty input set

This is what ``passthrough: all`` on the slot is for. Without it the slot
forwards nothing -- an ``export:`` task with no implementation passes through
none of its inputs by default -- and every consumer receives an empty input
set while the run still reports success. That is the same class of quiet
failure ``std.check.Implemented`` exists to prevent, one step further along,
and it is pinned by ``test_src_rtl_forwards_its_sources_to_consumers`` in the
library's own suite.

``tests`` is the gate
---------------------

:dvf:task:`tests` is not a wrapper around the suite; it **is** the suite, via
``hdlsim.SimSuiteReport``. Its status is the CI gate: nonzero if and only if a
case failed, errored, or nothing was selected -- that last one mattering more
than it looks, because a typo'd ``--tests`` filter that silently ran nothing
is otherwise a green build.

Command-line selection prunes the graph at build time, so a deselected case --
and any simulation image only it needed -- is never built.

:dvf:task:`tests-info` reports the inventory that selection draws from and
builds nothing. It reads that inventory off ``tests``'s own ``needs:`` at graph
build, so it cannot drift: a project that adds a suite gets it in
``tests-info`` for free, with nothing to keep in sync.

``smoke`` is the quick gate
---------------------------

:dvf:task:`smoke` is the same kind of task as ``tests`` -- a
``hdlsim.SimSuiteReport``, with the same gate and the same reports -- over a
small selection of the cases: the one to run before pushing, and the one CI
runs on every commit alongside ``lint-rtl``. A project names the suite and the
cases to take from it:

.. code-block:: yaml

   - override: smoke
     needs: [uvm-tests]
     with:
       tests: [sw_copy, pss_hello]

The selection prunes the graph exactly as ``--tests`` does, so the cases left
out -- and any image only they needed -- are never built. An unfilled
``smoke`` fails rather than passing, for the same reason an empty ``tests``
does: no test ran.

Both suite tasks write ``junit.xml`` and ``ctrf.json`` into their rundir. CTRF
is also what ``hdllint`` writes for lint, so a CI reporter such as
``ctrf-io/github-test-reporter`` shows a project's lint and its smoke tests
side by side.
