Archetypes and capabilities
===========================

This library ships two kinds of package, and the difference decides how a
project reaches what is inside them.

An **archetype** is inherited with ``uses:``. Its tasks and variables become
the project's own, under the project's own name. :doc:`project.dv
<../reference/project_dv>` and :doc:`project.dv.uvm
<../reference/project_dv_uvm>` are archetypes.

A **capability** package is instantiated. Its compounds are building blocks a
project stamps out by name, with parameters it sets per instance.
:doc:`project.dv.uvm.utils <../reference/project_dv_uvm_utils>` is a
capability package.

.. code-block:: yaml

   package:
     name: my-project
     uses: project.dv.uvm        # archetype: inherited
     imports:
     - project.dv.uvm

     tasks:
     - name: uvm-env
       uses: project.dv.uvm.utils.env-base    # capability: instantiated

``uses:`` and ``imports:`` are both required
--------------------------------------------

They answer different questions. ``uses:`` says *which package to inherit
from*; the import is what *puts that name in scope to be found*. A ``uses:``
naming a package nothing has imported fails at load.

Inherited tasks are named for the inheriting project, not for the base: a
project that inherits ``project.dv.uvm`` gets ``my-project.tests``, never
``my-project.dv.tests``. That is what makes the archetype invisible from
outside -- a consumer of ``my-project`` sees a project with an interface, not
a project with a parent.

Why ``project.dv.uvm`` declares no tasks
----------------------------------------

Its :doc:`reference page <../reference/project_dv_uvm>` lists nothing of its
own, and that is the intended shape rather than an unfinished one.

:doc:`project.dv <../reference/project_dv>` is deliberately
methodology-neutral. It owns the questions every DV project answers -- which
simulator, which build variant, what ``dfm run tests`` means, where lint hangs
-- and nothing about how the tests are written. UVM is not in it anywhere.

``project.dv.uvm`` then contributes exactly one thing: a pairing. It ``uses:``
``project.dv`` and imports ``project.dv.uvm.utils``, so that inheriting one
name gets a project both the shared interface *and* the UVM blocks in scope,
already wired to the same knobs.

The payoff is that a cocotb or formal archetype can sit beside it on the same
interface. ``dfm run tests`` would mean the same thing, ``--build dbg`` would
still move the image and the run together, and a CI pipeline written against
the interface would not know the difference. Had the UVM specifics been tasks
in the base, that second archetype would have to inherit them and disown them.

When to inherit ``project.dv`` directly
---------------------------------------

Inherit ``project.dv`` when the project is not a UVM project: a design-only
RTL package with unit tests, a formal flow, or a cocotb bench. You get the
interface, the knobs and the flag holders, and nothing about UVM comes along.

Inherit ``project.dv.uvm`` for a UVM project. The only difference is scope:
``project.dv`` alone leaves the UVM compounds unimported, so a project would
have to import ``project.dv.uvm.utils`` itself.

Aliasing the long names
-----------------------

``project.dv.uvm.utils.env-base`` is unambiguous and long. Both are on
purpose, and a project that finds the length grating aliases the package
rather than shortening the library's names:

.. code-block:: yaml

   imports:
   - {name: project.dv.uvm.utils, as: uvm}

   tasks:
   - name: uvm-env
     uses: uvm.env-base
