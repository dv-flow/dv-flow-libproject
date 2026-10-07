Flags stay with the project
===========================

Compile, elaborate and run flags are a *project* decision -- they follow the
``build`` knob, which the project owns. Nothing in
:doc:`project.dv.uvm.utils <../reference/project_dv_uvm_utils>` names a flag
holder, and that is what makes those compounds reusable across projects whose
build variants differ.

This page is how the two halves meet.

The naming contract
-------------------

:doc:`project.dv <../reference/project_dv>` declares **one holder per (stage,
variant)**:

.. list-table::
   :header-rows: 1
   :widths: 16 42 42

   * - Stage
     - ``opt``
     - ``dbg``
   * - compile
     - :dvf:task:`flags-comp-opt`
     - :dvf:task:`flags-comp-dbg`
   * - elaborate
     - :dvf:task:`flags-elab-opt`
     - :dvf:task:`flags-elab-dbg`
   * - run
     - :dvf:task:`flags-run-opt`
     - :dvf:task:`flags-run-dbg`

A consumer picks its own by name, spelling the variant with the variable
rather than with a literal:

.. code-block:: yaml

   needs: ["flags-comp-${{ build }}"]

The names *are* the contract. ``flags-<stage>-<variant>`` is what a consumer
interpolates into, so a missing ``(stage, variant)`` pair is not a missing
convenience -- it is an unresolvable reference in every project that selects
that variant. The holders live in ``project.dv``, alongside the ``build``
variable that selects them, because a holder set that does not cover the
declared value set is a broken project rather than a style choice.

Coverage: one holder, not one per value
---------------------------------------

:dvf:task:`flags-cov` carries the coverage level the ``cov`` knob selects (see
:doc:`knobs`). There is one holder rather than one per value, because the
request is a simulator-neutral ``hdlsim.SimCovArgs`` item and the level is a
field of it. The knob is threaded into that field instead of choosing a name:

.. code-block:: yaml

   - { name: flags-cov, uses: hdlsim.SimCovArgs, with: { level: "${{ cov }}" } }

It belongs on **images** only. A run collects whatever its image was built
for, and a compiled library is not instrumented, so neither a run nor
``env-base`` needs it.

Leaving it off an image is how a project keeps that image uninstrumented
whatever ``--cov`` says. To pin one image to a fixed level, give it a holder
of its own (``uses: hdlsim.SimCovArgs`` with ``with: {level: full}``). An
image takes the highest level it is given.

The image bundle
----------------

:dvf:task:`flags-img` is everything the knobs contribute to an image build, in
one name:

.. code-block:: yaml

   - name: flags-img
     passthrough: all
     needs: ["flags-comp-${{ build }}", "flags-elab-${{ build }}", flags-cov]

An image that needs ``flags-img`` picks up a knob added to the bundle later
without its own ``needs:`` changing, which is the point: before the bundle,
each new knob meant editing every image in every project. The per-stage
holders are still there for a consumer that wants only one of them, and a
project that adds a build variant gets the bundle for free, because the
bundle names its holders by ``${{ build }}`` too.

.. note::

   The bundle resolves ``${{ build }}`` inside ``project.dv``, while that
   package loads. dv-flow-mgr 1.19.0 does not pass the ``--build`` flag to a
   registered base package during that load, so ``--build dbg`` gives the
   bundle the ``opt`` holders (``-D build=dbg`` works). The fix is in
   dv-flow-mgr after 1.19.0.

How a flag reaches the inside of a compound
-------------------------------------------

The compounds have no ``needs:`` on any holder. Instead each one has an
**injection slot**: a passthrough subtask that forwards whatever the
instantiation's ``needs:`` feeds it, down through the compound's body.

.. code-block:: yaml

   - name: uvm-env
     uses: project.dv.uvm.utils.env-base
     needs:
     - ral                          # generated RAL package
     - rtl                          # design sources
     - "flags-comp-${{ build }}"    # <- the project's compile flags

For :dvf:task:`env-base` the slot is ``pre-deps``, and the path is
``needs: -> pre-deps -> env-src -> ... -> env-lib``: the dependency files and
their incdirs arrive ahead of the env packages that import them, and the
compile-flag DataItem reaches the ``SimLib`` compile at the end. For
:dvf:task:`tb-img` the slot is ``tb-src``, which forwards the injected env
library and flags and adds the testbench tops on the way through.

The slots are load-bearing, but a project never writes their names -- it puts
things in the instantiation's ``needs:`` and the compound does the rest.

Wiring a whole project
----------------------

Three instantiations, one knob:

.. code-block:: yaml

   - name: uvm-env
     uses: project.dv.uvm.utils.env-base
     needs: [ral, rtl, "flags-comp-${{ build }}"]

   - name: sim-img
     uses: project.dv.uvm.utils.tb-img
     needs: [uvm-env, flags-img]
     with:
       tb_include: [hdl_top.sv, hvl_top.sv]
       top: [hvl_top]

   - name: run-arb
     uses: project.dv.uvm.utils.run
     needs: [sim-img, "flags-run-${{ build }}"]
     with:
       UVM_TESTNAME: arb_test

``--build dbg`` now moves the library, the image and the run together, and
nothing in the project mentions ``opt`` or ``dbg``. ``--cov code`` reaches the
image through the same bundle.

Adding a build variant
----------------------

A project that wants a third variant -- say ``prof`` -- does two things in its
own flow file:

1. Restate the ``build`` declaration to widen the accepted value set (see
   :doc:`knobs`).
2. Declare the matching three holders: ``flags-comp-prof``,
   ``flags-elab-prof``, ``flags-run-prof``.

Nothing else changes. Every ``needs: ["flags-<stage>-${{ build }}"]`` in the
project already resolves to the new holders when the knob selects them, which
is the return on naming the holder by the variable in the first place.

Leaving one out is the failure mode worth knowing about: the project loads
fine, ``--build prof`` is accepted, and the run fails on an unresolved
reference the first time something needs that stage.
