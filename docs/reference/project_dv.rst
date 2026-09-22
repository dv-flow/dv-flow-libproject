``project.dv``
==============

Methodology-neutral DV project archetype: the ``src-*``/``lint-*`` interface,
the project-wide ``sim``/``build`` knobs, and the flag holders those knobs
select.

.. code-block:: yaml

   package:
     name: my-project
     uses: project.dv
     imports:
     - project.dv

Both lines are required: ``uses:`` names the base to inherit from, the import
is what puts it in scope to be found. A UVM project inherits
:doc:`project.dv.uvm <project_dv_uvm>` instead, which is this package plus the
UVM building blocks -- see :doc:`../guide/archetypes`.

The ``--sim`` and ``--build`` knobs are package variables rather than tasks
and do not appear below; :doc:`../guide/knobs` covers them.

The project interface
---------------------

The slots a project fills in with ``override:``, and the verbs it answers to
once it has. ``src-rtl``, ``src-spl`` and ``lint-rtl`` carry
``std.check.Implemented``, so a project that declares one of them and never
wires it fails with a hint instead of quietly reporting success --
:doc:`../guide/slots` explains why that is the interesting part.

.. dvf:autopackage::

Inherited building blocks
-------------------------

Package-internal tasks, which ``uses:`` inheritance nonetheless makes the
inheriting project's own. A project names these directly; other packages
cannot -- see :ref:`reference-visibility`.

The six flag holders are named by the ``build`` variable rather than by a
literal (``needs: ["flags-comp-${{ build }}"]``), which is what lets one knob
move the compiled library, the image and the run together;
:doc:`../guide/flags` covers the naming contract and what adding a build
variant requires.

.. dvf:autopackage::
   :internal:
   :members: flags-*, sv-module, sv-package
   :map: false
