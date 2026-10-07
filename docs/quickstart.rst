Quickstart
==========

A UVM project from nothing, in the order the pieces have to arrive. Each step
leaves a flow file that loads, so ``dfm run`` is the check after every one.

This assumes the library is installed -- see :doc:`install`.

1. Inherit an archetype
-----------------------

.. code-block:: yaml

   # flow.yaml
   package:
     name: my-project
     uses: project.dv.uvm
     imports:
     - project.dv.uvm

Both lines are needed and they say different things. ``uses:`` names the
package to inherit from; ``imports:`` is what puts that name in scope to be
found. A ``uses:`` without the matching import fails at load with an
unresolved package.

That is already a working project:

.. code-block:: text

   $ dfm run
   my-project.lint-rtl   - Entrypoint for running lint on RTL sources  [unimplemented]
   my-project.tests      - Entrypoint for running tests defined by the project
   my-project.tests-info - Show the tests and DUT views this project offers

Note the names. The inherited tasks are **the project's own** --
``my-project.tests``, not ``my-project.dv.tests`` -- so a consumer of this
project never sees where the archetype came from.

2. Fill in the source slots
---------------------------

:dvf:task:`src-rtl` is the project's synthesizable RTL. It is a slot, and it
is not optional: declared-and-never-filled, it would run and report success,
so it carries a ``std.check.Implemented`` requirement that fails with a hint
instead.

.. code-block:: yaml

     tasks:
     - override: src-rtl
       needs: [rtl]

     - name: rtl
       uses: std.FileSet
       with:
         type: systemVerilogSource
         base: src/rtl
         include: ["*.sv"]

``src-rtl`` *is* the aggregated RTL, not a marker pointing at it: a consumer
wired ``needs: [src-rtl]`` receives the filesets. :doc:`guide/slots` covers
what the slot protocol guarantees and what to do about a slot this project
genuinely does not implement.

3. Build the env library
------------------------

The UVM compounds come from :doc:`project.dv.uvm.utils
<reference/project_dv_uvm_utils>`, in scope because the archetype imports it.
:dvf:task:`env-base` compiles ``env/`` and ``tests/`` under a base directory
into a simulation library:

.. code-block:: yaml

     - name: uvm-env
       uses: project.dv.uvm.utils.env-base
       needs:
       - rtl
       - "flags-comp-${{ build }}"

Everything in that ``needs:`` list is fed through the **compound boundary**:
the design sources the env packages import, and the project's compile-flag
holder. The compound names no flag holder itself, which is what keeps it
reusable -- see :doc:`guide/flags`.

4. Build the image
------------------

:dvf:task:`tb-img` compiles the testbench tops against that library:

.. code-block:: yaml

     - name: sim-img
       uses: project.dv.uvm.utils.tb-img
       needs: [uvm-env, flags-img]
       with:
         tb_include: [hdl_top.sv, hvl_top.sv]
         top: [hvl_top]

:dvf:task:`flags-img` bundles everything the project knobs contribute to an
image build: the compile and elaborate flags ``--build`` selects, and the
coverage level ``--cov`` selects. An image that needs the bundle picks up any
knob added to it later without its own ``needs:`` changing.

For a self-contained testbench with no separately shared env, use
:dvf:task:`tb-base` instead: it is ``env-base`` plus the tb tops and the image
in one compound.

5. Wire the suite into ``tests``
--------------------------------

:dvf:task:`tests` is the project's regression command and the CI gate --
nonzero if and only if a case failed, errored, or nothing was selected. A
project puts its cases in ``needs:``:

.. code-block:: yaml

     - override: tests
       needs: [uvm-tests]

.. code-block:: text

   $ dfm run tests                     # everything
   $ dfm run tests --tests arb,err     # a selection
   $ dfm run tests --views rtl         # one DUT view
   $ dfm run tests --build dbg         # -O0 and waveforms, end to end
   $ dfm run tests --sim mti           # a different simulator backend
   $ dfm run tests --cov func          # with coverage, per case in the report

Selection prunes the graph at build time, so a deselected case -- and any
simulation image only it needed -- is never built. :dvf:task:`tests-info`
reports the same inventory and builds nothing; because it reads the inventory
off ``tests``'s own ``needs:``, the two cannot drift apart.

6. Answer for ``lint-rtl``
--------------------------

The listing in step 1 still marks :dvf:task:`lint-rtl` as ``[unimplemented]``.
Either wire it:

.. code-block:: yaml

     - override: lint-rtl
       needs: [lint]

or, if this project has no lint flow, say so:

.. code-block:: yaml

     - override: lint-rtl
       uses: std.NotProvided

The second is a real answer, not a way of silencing the check: ``lint-rtl``
leaves ``dfm run`` entirely, while ``dfm show task lint-rtl`` still reports
that the slot exists and was declined on purpose. :doc:`guide/slots` explains
why ``severity: off`` is the wrong tool for this.

Where to go next
----------------

* :doc:`guide/archetypes` -- why ``project.dv.uvm`` has no tasks of its own,
  and when to inherit ``project.dv`` directly
* :doc:`guide/knobs` -- ``--sim``, ``--build`` and ``--cov``, and how a project changes
  a default or widens a value set
* :doc:`guide/flags` -- the ``flags-<stage>-<variant>`` contract, and what
  adding a build variant requires
* :doc:`reference/index` -- every task and parameter, generated from the flow
  files
