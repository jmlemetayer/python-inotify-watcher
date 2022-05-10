"""Configuration file for the Sphinx documentation builder.

Notes
-----
- `Sphinx configuration`_

.. _Sphinx configuration:
   https://www.sphinx-doc.org/en/master/usage/configuration.html
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

from inotify_watcher import __version__  # noqa: E402

project = "inotify_watcher"
copyright = "2021, Jean-Marie Lemetayer"
author = "Jean-Marie Lemetayer"

version = __version__
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]

html_theme = "sphinx_rtd_theme"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/devdocs/", None),
}
