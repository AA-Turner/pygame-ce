import sys, os
sys.path.append(os.path.abspath('.'))
extensions = [
    'sphinx.ext.autodoc',
    'ext.indexer',
    'ext.headers',
    'ext.boilerplate',
]
templates_path = ['_templates']
# Format strings for the version directives
add_module_names = True
modindex_common_prefix = ['pygame']
boilerplate_skip_transform = ['index']
html_use_modindex = False
html_show_sphinx = False
smartquotes = False
