# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('../../../'))
sys.path.insert(0, os.path.abspath('../../../osc_cr_converter/'))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'commonroad-openscenario-converter'
copyright = '2023, Technical University of Munich, Cyber-Physical Systems Group'
author = 'Yuanfei Lin, Michael Ratzel, Matthias Althoff'
release = 'v0.0.4'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc",
              "sphinx.ext.viewcode",
              "sphinx.ext.napoleon",
              'sphinx.ext.inheritance_diagram',
              "sphinx.ext.todo",
              'sphinx_autodoc_typehints',
              "m2r2"
              ]

# order of displaying the members in an automodule/autoclass
autodoc_member_order = "bysource"

# show todo items
todo_include_todos = True

autodoc_typehints = "both"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_logo = 'img/converter-logo.png'
