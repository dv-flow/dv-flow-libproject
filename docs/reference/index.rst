Package reference
=================

Generated from the flow files. Every task, parameter and contract on these
pages is extracted from ``src/dv_flow/libproject/**/flow.yaml`` at build time,
so a page that disagrees with the library is a bug in the library's ``desc:``
rather than in the page.

.. toctree::
   :maxdepth: 2

   project_dv
   project_dv_uvm
   project_dv_uvm_utils

.. _reference-visibility:

What appears on a page
----------------------

Which tasks a package's page lists depends on what kind of package it is,
because that decides what a reader is able to name.

**Archetype packages** -- :doc:`project.dv <project_dv>` and
:doc:`project.dv.uvm <project_dv_uvm>` -- are inherited with ``uses:``.
Inheritance copies every non-``local:`` task into the inheriting project's own
namespace, whatever its visibility, so an extending project can name more than
the package publishes. Their pages have two sections:

* **The project interface** -- the ``root:``/``export:`` tasks. Slots to fill
  and verbs to run. This is the contract, and it is what a project built on
  the archetype promises to anyone reading its flow file.
* **Inherited building blocks** -- the package-internal tasks an extending
  project still names or overrides. Useful, documented, and deliberately not
  part of the interface above.

**Capability packages** -- :doc:`project.dv.uvm.utils
<project_dv_uvm_utils>` -- are instantiated by name rather than inherited. A
project can name the compounds and nothing inside them, so the page lists the
compounds only. The subtasks each compound is built from are implementation:
where one of them is load-bearing, as the flag-injection slots are, the
compound's own description says so.
