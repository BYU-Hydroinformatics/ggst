#Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'Grace Groundwater Subsetting Tool'
copyright = '2021, Dr. Norm L. Jones'
author = 'Dr. Norm Jones and Research Assistants'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.extlinks',
]



intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'

#Include the index in the content page

html_sidebars = {
    '**': ['globaltoc.html', 'localtoc.html', 'searchbox.html'],
    '**/index': ['globaltoc.html', 'localtoc.html', 'searchbox.html'],
}

#Changing screen width
def setup(app):
    app.add_css_file('screen_width.css')
    app.add_css_file('table_fixer.css')

html_static_path = ['_static']

#Adding a logo

#html_static_path = ['_static']
#html_logo = '_static/ggstlogo.png'

