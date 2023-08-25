import sys, os
sys.path.append(os.path.abspath('.'))
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'ext.indexer',
    'ext.headers',
    'ext.boilerplate',
]
templates_path = ['_templates']
project = 'pygame-ce'
copyright = '2000-2022, pygame developers, 2023 pygame-ce developers'
version = release = '2.4.0'
# Format strings for the version directives
add_module_names = True
modindex_common_prefix = ['pygame']
boilerplate_skip_transform = ['index']
html_theme = 'classic'
html_theme_options = {'home_uri': 'https://pyga.me/docs'}
html_theme_path = ['themes']
html_static_path = ['_static']
html_extra_path = ['../LGPL.txt']
html_use_modindex = False
html_show_sphinx = False
smartquotes = False
