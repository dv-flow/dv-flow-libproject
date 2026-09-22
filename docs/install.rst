Installation
============

The library is a Python distribution that registers its three flow packages
through a ``dv_flow.mgr`` entry point. Installing it is all that is needed --
there is no path to configure and nothing to import by filename.

.. code-block:: shell

   pip install dv-flow-libproject

or, with ivpm, as a dependency of the project that uses it:

.. code-block:: yaml

   # ivpm.yaml
   - name: dv-flow-libproject
     url: https://github.com/dv-flow/dv-flow-libproject.git
     deps: skip

``deps: skip`` fetches the sources without walking this package's own
manifest, whose dep-set is a *developer* environment. The runtime
requirements below are what a consuming project actually needs.

Requirements
------------

``dv-flow-mgr >= 1.19``
  Package ``uses:`` inheritance of **variables**. Without it a project
  inheriting ``project.dv`` gets the ``--sim``/``--build`` flags but not the
  variables they set, and the flag holders a project names by
  ``${{ build }}`` do not resolve.

``dv-flow-libhdlsim``
  The simulation tasks the archetypes are built on. ``project.dv``'s flag
  holders and test entrypoints, and every compound in
  ``project.dv.uvm.utils``, are hdlsim tasks.

``UVM_HOME``
  Only for the UVM packages. ``hdlsim.SimLibUVM`` locates the UVM library
  through it; with ivpm that is ``$IVPM_PACKAGES/uvm``.

Checking the installation
-------------------------

The packages are available by name from any flow project once the
distribution is installed:

.. code-block:: shell

   dfm show task project.dv.uvm.utils.env-base

A project that inherits an archetype sees the knobs in its own help:

.. code-block:: shell

   dfm run --help      # --sim and --build, under "Project options"
