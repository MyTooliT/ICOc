# -- Imports ------------------------------------------------------------------

import maisie_sphinx_theme


# -- Project information ------------------------------------------------------

project = "ICOc"
copyright = "2024, Clemens Burgstaller, René Schwaiger"
author = "Clemens Burgstaller, René Schwaiger"
release = "1.11.0"

# -- General configuration ----------------------------------------------------


extensions = [
    "sphinx.ext.autodoc",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output --------------------------------------------------

html_theme_path = maisie_sphinx_theme.html_theme_path()
html_theme = "maisie_sphinx_theme"
# Register the theme as an extension to generate a sitemap.xml
extensions.append("maisie_sphinx_theme")
