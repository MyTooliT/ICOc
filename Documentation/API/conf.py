# -- Project information -----------------------------------------------------

project = "ICOc"
copyright = "2024, Clemens Burgstaller, René Schwaiger"
author = "Clemens Burgstaller, René Schwaiger"
release = "1.11.0"

# -- General configuration ---------------------------------------------------


extensions = [
    "sphinx.ext.autodoc",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
