#****************************************************************************
#* conf.py
#*
#* Sphinx configuration for the dv-flow-libproject documentation.
#****************************************************************************
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = os.path.join(_HERE, "..", "src", "dv_flow", "libproject")

project = "dv-flow-libproject"
copyright = "2023-2025, Matthew Ballance and Contributors"
author = "Matthew Ballance"

# `myst_parser` is listed because `dvflow_doc_format = "markdown"` below is
# inert without it -- having the module installed is not enough. With markdown
# selected and the parser unregistered, a fenced code block in a `doc:` string
# reaches docutils unparsed and the build reports `Unexpected indentation`
# rather than falling back to plain text.
extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx_dv_flow",
]

exclude_patterns = ["_build"]

# ---------------------------------------------------------------------------
# sphinx-dv-flow
# ---------------------------------------------------------------------------
# This distribution has no root flow.yaml: it registers three packages by
# entry point, each a flow.yaml in its own directory. So there is no single
# project root to point at. The default below covers `project.dv`; the two
# nested packages carry `:root:` on their own directives.
dvflow_root = os.path.abspath(os.path.join(_LIB, "dv"))

# The `desc:`/`doc:` strings in these flow files are Markdown because the same
# strings are read by `dfm show`, `dfm llms` and editor hovers, none of which
# render reStructuredText. The docs build follows what is written rather than
# asking the flow files to be written twice.
dvflow_doc_format = "markdown"

# `std.FileSet`, `hdlsim.SuiteResult` and friends are types this library uses
# and another distribution owns. Naming them here says "documented elsewhere"
# instead of suppressing the nitpick; when dv-flow-mgr and dv-flow-libhdlsim
# publish inventories, an `intersphinx_mapping` entry turns these into links
# with nothing else to change.
dvflow_intersphinx_packages = ["std", "hdlsim"]

# Reported (dvflow-coverage.txt), not enforced. The gate is a separate
# `dvflow-doc coverage --strict` run -- see docs/contributing.rst -- because an
# undocumented parameter is a finding about the flow file, not a broken
# document, and folding it into `-W` is how the report ends up switched off.
dvflow_coverage = True

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
nitpicky = True

html_theme = "furo"
html_title = "dv-flow-libproject"

# No `html_static_path`/`templates_path` until there is an asset to put in
# them: an entry naming an empty directory works in the tree that created it
# and fails under -W on every clean checkout.
