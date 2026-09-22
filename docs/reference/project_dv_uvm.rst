``project.dv.uvm``
==================

The UVM project archetype: the :doc:`project.dv <project_dv>` interface plus
the UVM building blocks in scope.

.. code-block:: yaml

   package:
     name: my-project
     uses: project.dv.uvm
     imports:
     - project.dv.uvm

     tasks:
     - override: src-rtl
       needs: [rtl]
     - override: tests
       needs: [uvm-tests]

**This package declares no tasks of its own.** What it contributes is a
pairing, and the pairing is the point: inherit one name and both halves
arrive, already wired to the same knobs.

Inherited from ``project.dv``
  The project interface (``src-rtl``, ``src-spl``, ``lint-rtl``), the
  ``tests``/``tests-info`` entrypoints, the ``--sim``/``--build`` knobs, the
  ``flags-<stage>-<variant>`` holders those knobs select, and the
  ``sv-module``/``sv-package`` FileSet conveniences. All of it is documented
  on :doc:`project_dv`, and all of it is the inheriting project's own --
  ``my-project.tests``, not ``my-project.dv.tests``.

Imported from ``project.dv.uvm.utils``
  The UVM compounds -- ``lib``, ``env-base``, ``tb-img``, ``tb-base``,
  ``run``. Imported rather than inherited, so a project that inherits this
  package can instantiate them by name without importing them itself. See
  :doc:`project_dv_uvm_utils`.

Having no tasks here is the intended shape rather than an unfinished one.
``project.dv`` is methodology-neutral so that a cocotb or formal archetype can
sit beside this one on the same project interface; the UVM specifics are
compounds a project instantiates, not tasks it inherits.
:doc:`../guide/archetypes` makes the argument in full.
