import sys, os
sys.path.append(os.path.abspath('.'))
extensions = [
    'ext.indexer',
    'ext.headers',
    'ext.boilerplate',
]
templates_path = ['_templates']
# Format strings for the version directives
boilerplate_skip_transform = ['index']
