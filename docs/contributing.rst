Working on the library
======================

Nearly all of this documentation is generated from the flow files. That is
deliberate, and it has a consequence: **a task's documentation is its
``desc:`` and ``doc:``**, not a page someone remembers to update.

The ``Defined in flow.yaml:NN`` line at the foot of every reference entry links
to a highlighted listing of that flow file, anchored at the declaration. Follow
it when a generated page looks wrong: the page is a rendering of the
declaration, so the two disagreeing means the ``desc:`` is what needs the
edit.

Building the docs
-----------------

.. code-block:: shell

   ivpm update -d default-dev
   ./packages/python/bin/sphinx-build -W -b html docs docs/_build/html

``-W`` is not optional. Because the extension loads the flow files through
the engine, a warning-free build is also a check that all three packages
still *load* -- and a load error is reported against ``flow.yaml:NN``, not
against the ``.rst`` that asked for it.

.. note::

   Name a dep-set explicitly. ``ivpm update -a`` with nothing selected exits
   zero having installed nothing, and the failure surfaces two steps later as
   ``sphinx-build: No such file or directory``.

Running the tests
-----------------

.. code-block:: shell

   ./packages/python/bin/pytest

``tests/unit/test_archetypes.py`` is a set of contract tests, not a coverage
exercise: each one pins something a project built on this library depends on
and would otherwise have no way to notice breaking until a regression run.
The archetypes are almost all declaration, so what can break is the interface
(which names exist, and where), the knobs (which flags exist, and what they
reach) and scope (which building blocks a leaf can name).

Documentation coverage
----------------------

The build writes ``docs/_build/html/dvflow-coverage.txt`` reporting every task
and parameter with no ``desc:``. The gate is a separate command, one per
package:

.. code-block:: shell

   P=src/dv_flow/libproject
   dvflow-doc coverage -r $P/dv --internal --strict
   dvflow-doc coverage -r $P/dv/uvm --internal --strict
   dvflow-doc coverage -r $P/dv/uvm/utils --internal --strict

Separate from the docs build, because an undocumented parameter is a finding
about the flow file rather than a broken document -- and because folding it
into ``-W`` is how a report ends up switched off entirely.

``--internal`` is deliberate. The compounds' inner subtasks are not published
and do not appear in the reference, but their parameters are read by anyone
changing the compound, and they are worth holding to the same standard.

Writing ``desc:`` and ``doc:``
------------------------------

``desc:``
  One line, no trailing period, reads as a menu entry. It is what ``dfm run``
  prints next to the task name, so it has to make sense with no surrounding
  context.

``doc:``
  The long form: what the task is for, what a caller has to supply, what the
  surprising part is. Markdown -- the same strings are read by ``dfm show``,
  ``dfm llms`` and editor hovers, none of which render reStructuredText, and
  ``conf.py`` sets ``dvflow_doc_format = "markdown"`` to follow that.

Two rules follow from how the strings are rendered, and both are the kind that
produce a wrong-looking page rather than a warning:

**Fence code blocks.** An indented block needs *four* spaces to be a code
block in Markdown. A two-space indent -- which reads perfectly well in the
YAML -- is a continuation of the preceding paragraph, and renders as the
commands run together into prose. Use a triple-backtick fence and the question
does not arise.

**A parameter's ``doc:`` is one paragraph.** The parameter table renders the
first paragraph and nothing after it, so a second paragraph is written, passes
coverage, and is never seen by anyone. Where a parameter needs more than a
paragraph, the surplus belongs in the **task's** ``doc:``, which is rendered
in full -- and usually belongs there anyway, since what does not fit is
generally about how the parameter interacts with the rest of the task.

A comment above a declaration documents nothing. ``sphinx-dv-flow`` extracts
what is *declared*, by design, so an explanation that belongs to a parameter
belongs in that parameter's ``desc:``/``doc:`` and not in a ``#`` line above
it. Comments that orient someone *editing the file* -- what the four compounds
are for, why a subtask exists -- are a different thing and stay as comments.

.. _doc-visibility-rules:

Which tasks a page documents
----------------------------

The rule differs by what kind of package it is, because that decides what a
reader can name. :ref:`reference-visibility` states it for readers; the
authoring side is:

**Archetype packages** (``project.dv``, ``project.dv.uvm``) get two sections.
A bare ``dvf:autopackage`` for the published interface, then a second one with
``:internal:`` and an explicit ``:members:`` list for the package-internal
tasks that ``uses:`` inheritance nonetheless hands to an extending project.

.. code-block:: rst

   .. dvf:autopackage::
      :internal:
      :members: flags-*, sv-module, sv-package
      :map: false

The ``:members:`` list is spelled out rather than relying on ``:internal:``
alone. ``:internal:`` means "everything not published", which is a property of
today's file; the list is a statement about what is *intended* for consumers,
so adding an internal task without deciding which side it falls on leaves it
out of the docs visibly rather than sweeping it in.

**Capability packages** (``project.dv.uvm.utils``) get one bare
``dvf:autopackage`` and no ``:internal:``. A project can name the compounds
and nothing inside them, so the subtasks are implementation. Where one is
load-bearing -- as the flag-injection slots are -- that belongs in the
compound's own ``doc:``, which is where a reader of the compound will be.

Adding a task
-------------

#. Decide its scope. ``root:``/``export:`` if it is part of the interface;
   ``name:`` if an extending project may name it but other packages should
   not; ``local:`` if it is a fragment-internal detail.
#. Give it a ``desc:``, and a ``doc:`` if there is anything surprising.
#. If it is package-internal in an archetype, decide whether it belongs in
   that package's ``:members:`` list.
#. If it changes what a project can name, add a contract test.
