Project knobs: ``--sim``, ``--build``, ``--cov`` and ``--prof``
================================================================

Every DV project answers four questions, and answers them project-wide: which
simulator, which build variant, how much coverage to collect, and whether to
profile. :doc:`project.dv
<../reference/project_dv>` asks them once, so that each project does not
invent its own spelling.

.. code-block:: text

   $ dfm run tests --sim mti
   $ dfm run tests --build dbg
   $ dfm run tests -D build=dbg      # same thing, the generic form
   $ dfm run tests --cov code
   $ dfm run tests --prof time

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
   * - ``cov``
     - ``none``
     - ``none``, ``func`` (covergroups and assertions), ``code`` (adds line,
       branch and expression), ``full`` (adds toggle and FSM)
   * - ``prof``
     - ``none``
     - ``none``, ``time`` (where the CPU time goes), ``mem`` (where the
       memory goes)

All four are declared with ``cli: true``, which is what turns them into flags. A
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

Coverage: ``--cov``
-------------------

``cov`` is a third axis rather than more values of ``build``. A regression
wants ``opt`` with coverage and a triage run wants ``dbg`` without, so folding
the two together would need a holder for every combination. The two combine
freely instead:

.. code-block:: text

   $ dfm run tests --cov code                 # the regression, with coverage
   $ dfm run tests --build dbg --cov func     # debug build, functional coverage

The levels are ordered, and each includes the ones below it. What each level
turns on for each simulator is in dv-flow-libhdlsim's coverage documentation.

The level reaches an image through the :dvf:task:`flags-cov` holder, usually
by way of the :dvf:task:`flags-img` bundle (see :doc:`flags`). Runs need
nothing: a run collects what its image was built for. With coverage on,
``tests`` reports per-case coverage, the best case per kind in the printed
summary, and the per-case figures in ``junit.xml`` and ``ctrf.json``.

Three things to know:

* **Changing the level rebuilds every image it reaches**, because the image is
  what is instrumented. Alternating ``tests`` and ``tests --cov code`` in one
  rundir rebuilds each time, so give a coverage CI job its own rundir.
* **On a UVM testbench, measure with ``func``.** No exclusions are applied
  yet, so ``code`` and ``full`` instrument the UVM library along with the
  design. Their line and branch figures then mostly measure UVM, and differ
  between simulators.
* **The suite figure is the best case, not merged coverage.** Merging the
  cases' databases is a separate step (``hdlsim.SimCovMerge``).

Profiling: ``--prof``
---------------------

``prof`` is a fourth axis, for the same reason as ``cov``: a profile is
normally of an ``opt`` build, and folding it into ``build`` would need a
holder per combination.

.. code-block:: text

   $ dfm run tests --prof time                # each case profiled
   $ dfm run profile --prof time              # ... and ranked across the run

The modes don't combine: the simulators say to profile time and memory in
separate runs, because each skews the other. vcs, xcm and mti profile both;
vlt profiles ``time`` only. On any other simulator, or vlt at ``mem``, the
image warns and builds without profiling. What each mode turns on for each
simulator is in dv-flow-libhdlsim's profiling documentation.

The mode reaches an image through the :dvf:task:`flags-prof` holder, usually
by way of the :dvf:task:`flags-img` bundle. Runs need nothing: a run profiles
what its image was built for. Each case's ``stats`` then carry the share of
its time per category (``prof_<category>_pct`` and ``_s``), so ``tests``
totals the seconds spent in, say, the constraint solver across the
regression. :dvf:task:`profile` ranks the cases and modules (see
:doc:`slots`).

* **Changing the mode rebuilds every image it reaches**, as with ``--cov``.
* **Profile with coverage off and ``--build opt``.** Coverage and debug
  access cost time, and the profile charges that cost to the design.

Each simulator's own deep profiler (Xcelium's xProf, say) has no knob,
because no two of them mean the same thing. A project that wants one adds
that simulator's request to its image, next to ``flags-img``:

.. code-block:: yaml

   - name: xprof
     uses: hdlsim.XcmProfArgs
     with: { xprof: true }
   - name: sim-img
     uses: hdlsim.SimImage
     needs: [src-rtl, flags-img, xprof]

Every image takes every simulator's request and acts only on its own, so the
holder stays in place on a project that also builds with ``--sim vcs``. The
profiler's output stays in each run, for the vendor's tools. With ``--prof
time`` as well, ``profile`` still ranks the run. dv-flow-libhdlsim's
profiling documentation lists the deep profilers and what each writes.

Reaching ``project.dv.uvm.utils``
---------------------------------

The capability package declares its own ``sim`` variable rather than reading
``project.dv``'s, because it is not in that inheritance chain -- it is
instantiated, not inherited.

A project-wide ``--sim``/``-D sim=<name>`` reaches it all the same: an
unqualified package-variable override applies to every package declaring that
name. Nothing needs to be threaded through by hand.

``cov`` and ``prof`` work the same way: ``--cov code`` also sets
``hdlsim.cov``, and ``--prof time`` sets ``hdlsim.prof``, so a bare
``uses: hdlsim.SimCovArgs`` or ``uses: hdlsim.SimProfArgs`` anywhere in the
project follows the flag too.
