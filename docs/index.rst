dv-flow-libproject
==================

Project archetypes and methodology-specific template tasks for `dv-flow
<https://github.com/dv-flow/dv-flow-mgr>`_.

A verification project spends most of its flow file answering questions every
verification project answers: which simulator, which build variant, what does
``dfm run tests`` mean, where does lint hang. This library answers them once.
A project inherits an archetype and is left with only what is actually its own
-- its sources, its testbench wiring, its cases.

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

That project now answers to ``dfm run tests``, ``dfm run tests --tests arb``,
``dfm run tests-info``, ``dfm run tests --build dbg`` and ``dfm run tests
--sim mti``, and it is held to the interface it inherited:
:doc:`guide/slots` is about what happens when it is not.

The packages
------------

.. list-table::
   :header-rows: 1
   :widths: 24 22 54

   * - Package
     - Kind
     - What it is
   * - :doc:`project.dv <reference/project_dv>`
     - archetype (``uses:``)
     - Methodology-neutral DV project: the ``src-*``/``lint-*`` interface,
       ``tests``/``tests-info``, the ``--sim``/``--build``/``--cov`` knobs and
       the flag holders they select, ``sv-module``/``sv-package``
   * - :doc:`project.dv.uvm <reference/project_dv_uvm>`
     - archetype (``uses:``)
     - ``project.dv`` plus the UVM building blocks in scope
   * - :doc:`project.dv.uvm.utils <reference/project_dv_uvm_utils>`
     - capability (instantiate)
     - Reusable UVM compounds: ``env-base``, ``tb-img``, ``tb-base``, ``run``,
       ``lib``

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   guide/index
   reference/index
   install
   contributing
