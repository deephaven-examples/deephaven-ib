# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------

project = 'deephaven_ib'
copyright = '2021, Deephaven Data Labs'
author = 'Deephaven Data Labs'

# The full version, including alpha/beta/rc tags
# release = '0.0.1'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.todo', 'sphinx.ext.viewcode',
              "sphinx_autodoc_typehints"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom CSS files
html_css_files = ['custom.css']

# Theme options
# see https://alabaster.readthedocs.io/en/latest/customization.html
# see https://github.com/bitprophet/alabaster/blob/master/alabaster/theme.conf
html_theme_options = {
    # 'logo' : 'deephaven.png',
    # 'logo_name' : 'Deephaven',
    'page_width': '80%',
    'sidebar_width': '35%',
}

# A boolean that decides whether module names are prepended to all object names (for object types where a “module” of some kind is defined), e.g. for py:function directives. Default is True.
add_module_names = False
# if we allow sphinx to generate type hints for signatures (default), it would make the generated doc cluttered and hard to read
autodoc_typehints = 'none'

#########################################################################################################################################################################

import os
import sys

github_workspace = os.environ.get("GITHUB_WORKSPACE")
new_path = os.path.join(github_workspace, "deephaven-ib", "src")
print(f"NEW PYTHON PATH: {new_path}")

print(f"DEBUG1: {github_workspace}")
print(f"DEBUG2: {os.listdir(github_workspace)}")
print(f"DEBUG3: {os.listdir(new_path)}")

from pathlib import Path

print(f"DEBUG X1: {Path(os.path.dirname(os.path.realpath(__file__)))}")
print(f"DEBUG X2: {Path(os.path.dirname(os.path.realpath(__file__))).parents[1]}")
print(f"DEBUG X3: {os.listdir(Path(os.path.dirname(os.path.realpath(__file__))).parents[1])}")

# # new_path = Path(os.path.dirname(os.path.realpath(__file__))).parents[1].joinpath("src")
# new_path = Path(os.path.realpath(__file__)).parents[1].joinpath("src")
# print(f"NEW PYTHON PATH: {new_path}")
#
# print(
#     f"DEBUG: {Path(os.path.realpath(__file__))} {Path(os.path.realpath(__file__)).parent} {Path(os.path.realpath(__file__)).parents[0]} {Path(os.path.realpath(__file__)).parents[1]}")

sys.path.append(new_path)

import deephaven_ib

docs_title = "deephaven_ib python modules."
package_roots = [deephaven_ib]
package_excludes = ['._']

import dh_sphinx

dh_sphinx.gen_sphinx_modules(docs_title, package_roots, package_excludes)
