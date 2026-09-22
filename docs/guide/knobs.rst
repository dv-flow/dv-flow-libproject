Project knobs: ``--sim`` and ``--build``
========================================

Every DV project answers two questions, and answers them project-wide: which
simulator, and which build variant. :doc:`project.dv
<../reference/project_dv>` asks them once, so that each project does not
invent its own spelling.

.. code-block:: text

   $ dfm run tests --sim mti
   $ dfm run tests --build dbg
   $ dfm run tests -D build=dbg      # same thing, the generic form

.. note::

   These are package **variables**, not tasks, so they have no entry in the
   :doc:`reference <../reference/index>` -- this page is where they are
   documented. ``dfm run --help`` in a project that inherits the archetype
   prints the authoritative value set with its per-value help, under
   *Project options*.

.. list-table::
   :header-rows: 1
   :widths: 14 12 74

   * - Variable
     - Default
     - Values
   * - ``sim``
     - ``vlt``
     - ``vlt`` (Verilator), ``mti`` (Questa/ModelSim), ``vcs``, ``xcm``
       (Xcelium), ``xsm`` (XSim), ``ivl`` (Icarus)
   * - ``build``
     - ``opt``
     - ``opt`` (optimized, the regression default), ``dbg`` (``-O0``, waveform
       tracing)

Both are declared with ``cli: true``, which is what turns them into flags. A
value outside the declared set is rejected at the command line rather than
somewhere downstream.

Reading them
------------

A project reads a knob by plain name:

.. code-block:: yaml

   - name: sim-img
     uses: project.dv.uvm.utils.tb-img
     needs: ["flags-comp-${{ build }}"]

Nothing in that project mentions ``opt`` or ``dbg``. The consumer names its
flag holder *by the variable*, so one knob moves the compiled library, the
simulation image and the run flags together -- see :doc:`flags`.

Changing a default
------------------

A project whose regressions should default to debug says so in one line:

.. code-block:: yaml

   package:
     name: my-project
     uses: project.dv.uvm
     with:
       build: dbg

That is a **value-only** override: the archetype's type, value set and
per-value help all survive, and ``-D build=nosuch`` is still rejected. To
widen the accepted set, restate the whole declaration in the project --
and declare the matching flag holders for the new value, which :doc:`flags`
covers.

.. note::

   Inheriting a package variable through ``uses:`` requires **dv-flow-mgr
   >= 1.19**. The flags and the variables have to arrive together: a project
   reads ``${{ build }}`` to name its flag holder, so inheriting the flag
   without the variable would leave the flag with nothing to set.

Why variables and not a package config
--------------------------------------

A package ``config`` would express the same choice, and for the simple case it
would be equivalent. The reason these are variables is what happens next.

A config is global and all-or-nothing. The moment a project grows a second DUT
view or a second image, *"the RTL image in debug, everything else optimized"*
is not expressible as a config -- it is two cells of an axis. As variables, it
is: the consumers that should follow the knob name their holder by
``${{ build }}``, and one that should not names a holder directly.

So this is a variable, and stays one.

Reaching ``project.dv.uvm.utils``
---------------------------------

The capability package declares its own ``sim`` variable rather than reading
``project.dv``'s, because it is not in that inheritance chain -- it is
instantiated, not inherited.

A project-wide ``--sim``/``-D sim=<name>`` reaches it all the same: an
unqualified package-variable override applies to every package declaring that
name. Nothing needs to be threaded through by hand.
