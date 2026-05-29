"""Sphinx configuration for OME-IRIS docs."""

from __future__ import annotations

import pathlib
import sys

basedir = str(pathlib.Path(__file__).parent.parent.parent.resolve())
sys.path.insert(0, basedir)

project = "OME-IRIS"
copyright = "2026, OME-IRIS contributors"  # noqa: A001
author = "OME-IRIS contributors"

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "pydata_sphinx_theme",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "header_links_before_dropdown": 5,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/bioio-devs/OME-IRIS",
            "icon": "fa-brands fa-github",
        },
    ],
    "logo": {"text": "OME-IRIS"},
    "use_edit_page_button": False,
    "show_toc_level": 1,
    "navbar_align": "left",
    "navbar_center": ["navbar-nav"],
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
}

html_static_path = ["_static"]
html_css_files = ["custom.css"]

autodoc_preserve_defaults = True
myst_heading_anchors = 3
