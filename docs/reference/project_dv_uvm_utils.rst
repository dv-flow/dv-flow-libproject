``project.dv.uvm.utils``
========================

Reusable UVM building blocks: the env library, the testbench image, and the
test-run compound.

A methodology **capability** package, not a project archetype -- nothing here
is inherited with ``uses:``. A project instantiates these compounds by name,
and they are in scope for anything that inherits :doc:`project.dv.uvm
<project_dv_uvm>`:

.. code-block:: yaml

   - name: uvm-env
     uses: project.dv.uvm.utils.env-base
     needs: [rtl, "flags-comp-${{ build }}"]

Long names are the cost of an unambiguous one. Alias the package if they
grate:

.. code-block:: yaml

   imports:
   - {name: project.dv.uvm.utils, as: uvm}

   # ... then `uses: uvm.env-base`

Flag-agnostic by construction
-----------------------------

No task in this package names a flag holder. Each compound has an **injection
slot** -- a passthrough subtask that forwards whatever the instantiation's
``needs:`` feeds it -- so compile, elaborate and run flags arrive through the
compound boundary from the project that owns the opt-versus-debug choice.
That is what keeps these blocks reusable across projects whose build variants
differ; :doc:`../guide/flags` traces one all the way through.

The slots are load-bearing but not nameable: a project reaches them by putting
things in the instantiation's ``needs:``, never by writing ``pre-deps`` or
``tb-src``. So they do not appear below -- see :ref:`reference-visibility`.

.. note::

   These compounds require ``UVM_HOME`` to be set --
   ``hdlsim.SimLibUVM`` locates the UVM library through it. With ivpm, that is
   ``$IVPM_PACKAGES/uvm``.

Compounds
---------

.. dvf:autopackage::
   :root: ../src/dv_flow/libproject/dv/uvm/utils
