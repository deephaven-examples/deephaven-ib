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
from pathlib import Path

new_python_path = Path(os.path.realpath(__file__)).parents[2].joinpath("src")
sys.path.append(str(new_python_path))

# import jpy
#
# jpy.create_jvm(['-Xmx512M'])

# from deephaven.start_jvm import start_jvm
# start_jvm()

# adapted from deephaven2/_utils/bootstrap.py

from deephaven.start_jvm import start_jvm
import jpy

DEFAULT_DEVROOT = os.environ.get('DEEPHAVEN_DEVROOT', "/tmp/pyintegration")
DEFAULT_WORKSPACE = os.environ.get('DEEPHAVEN_WORKSPACE', "/tmp")
DEFAULT_PROPFILE = os.environ.get('DEEPHAVEN_PROPFILE', 'dh-defaults.prop')
DEFAULT_CLASSPATH = os.environ.get('DEEPHAVEN_CLASSPATH', "/opt/deephaven/server/lib/*")


def build_py_session():
    if not jpy.has_jvm():
        os.environ['JAVA_VERSION'] = '11'

        # we will try to initialize the jvm
        kwargs = {
            'workspace': DEFAULT_WORKSPACE,
            'devroot': DEFAULT_DEVROOT,
            'verbose': False,
            'propfile': DEFAULT_PROPFILE,
            'java_home': os.environ.get('JDK_HOME', None),
            'jvm_properties': {'PyObject.cleanup_on_thread': 'false'},
            'jvm_options': {'-Djava.awt.headless=true',
                            # '-Xms1g',
                            # '-Xmn512m',
                            '-XX:+UseG1GC',
                            '-XX:MaxGCPauseMillis=100',
                            '-XX:+UseStringDeduplication',
                            '-XX:InitialRAMPercentage=25.0',
                            '-XX:MinRAMPercentage=70.0',
                            '-XX:MaxRAMPercentage=80.0',
                            # '-XshowSettings:vm',
                            # '-verbose:gc', '-XX:+PrintGCDetails',
                            },
            # 'jvm_maxmem': '1g',
            'jvm_classpath': DEFAULT_CLASSPATH,
            'skip_default_classpath': True
        }
        # initialize the jvm
        start_jvm(**kwargs)


build_py_session()


import deephaven_ib

docs_title = "deephaven_ib python modules."
package_roots = [deephaven_ib]
package_excludes = ['._']

import dh_sphinx

dh_sphinx.gen_sphinx_modules(docs_title, package_roots, package_excludes)
