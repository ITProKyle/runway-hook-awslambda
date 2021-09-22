# -*- coding: utf-8 -*-
# pylint: skip-file
# type: ignore
"""Configuration file for the Sphinx documentation builder.

This file only contain a selection of the most common options. For a
full list see the documentation: http://www.sphinx-doc.org/en/master/config

"""
import os
from pathlib import Path

from docs.pygment_styles import OneDark, pygments_patch_style

DOCS_DIR = Path(__file__).parent.parent.resolve()
ROOT_DIR = DOCS_DIR.parent
SRC_DIR = DOCS_DIR / "source"

pygments_patch_style("one_dark", OneDark)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "runway-hook-awslambda"
copyright = "2021, Kyle Finley"
author = "Kyle Finley"
version = "0.0.0"
release = "0.0.0"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
add_function_parentheses = True
add_module_names = True
default_role = None
exclude_patterns = []
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.apidoc",
]
highlight_language = "default"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),  # link to python docs
    "runway": (
        "https://docs.onica.com/projects/runway/en/stable/",
        None,
    ),
}
language = None
master_doc = "index"
needs_extensions = {}
needs_sphinx = "4.2"
nitpicky = False
primary_domain = "py"
pygments_style = "one_dark"
# TODO fix Dict in runway repo
rst_epilog = """
.. |Blueprint| replace::
  :class:`~runway.cfngin.blueprints.base.Blueprint`

.. |Dict| replace::
  :class:`~typing.Dict`

.. |Protocol| replace::
  :class:`~typing.Protocol`

.. |Stack| replace::
  :class:`~runway.cfngin.stack.Stack`

.. |cfngin_bucket| replace::
  :attr:`~cfngin.config.cfngin_bucket`

.. |class_path| replace::
  :attr:`~cfngin.stack.class_path`

.. |namespace| replace::
  :attr:`~cfngin.config.namespace`

.. |stack| replace::
  :class:`~cfngin.stack`

.. |template_path| replace::
  :attr:`~cfngin.stack.template_path`

"""
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "restructuredtext",
    ".md": "markdown",
}
templates_path = ["_templates"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_codeblock_linenos_style = "inline"
html_css_files = ["css/rtd_dark.css"]
html_favicon = None
html_logo = None
html_theme = "sphinx_rtd_theme"  # theme to use for HTML and HTML Help pages
html_theme_options = {
    "navigation_depth": -1,  # unlimited depth
}
html_short_title = f"{project} v{release}"
html_title = f"{project} v{release}"
html_show_copyright = True
html_show_sphinx = True
html_static_path = ["_static"]  # dir with static files relative to this dir


# -- Options for sphinx-apidoc -----------------------------------------------
# https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html#environment
os.environ["SPHINX_APIDOC_OPTIONS"] = "members"


# -- Options of sphinx.ext.autodoc -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autoclass_content = "class"  # TODO add to runway
autodoc_class_signature = "separated"  # TODO add to runway
autodoc_default_options = {
    "inherited-members": "dict",  # show all inherited members
    "member-order": "bysource",
    "members": True,
    "show-inheritance": True,
}
autodoc_type_aliases = {}
autodoc_typehints = "signature"


# -- Options for sphinx.ext.napoleon  ----------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
napoleon_google_docstring = True
napoleon_include_init_with_doc = False
napoleon_type_aliases = autodoc_type_aliases


# -- Options for sphinxcontrib.apidoc  ---------------------------------------
# https://github.com/sphinx-contrib/apidoc
apidoc_excluded_paths = []
apidoc_extra_args = [f"--templatedir={SRC_DIR / '_templates/apidocs'}"]
apidoc_module_dir = "../../awslambda"
apidoc_module_first = True
apidoc_output_dir = "apidocs"
apidoc_separate_modules = True
apidoc_toc_file = "index"
