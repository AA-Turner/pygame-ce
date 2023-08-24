from ext.utils import get_sectionname, isections
from ext.indexer import tour_descinfo

import os


def setup(app):
    # This extension uses indexer collected tables.
    app.setup_extension("ext.indexer")

    # The target directory for the header files.
    app.add_config_value("headers_dest", ".", "html")

    # Create directory tree if missing?
    app.add_config_value("headers_mkdirs", False, "")

    # Suffix to tag onto file name before the '.h' extension
    app.add_config_value("headers_filename_sfx", "", "html")

    # Header template to use
    app.add_config_value("headers_template", "header.h", "html")

    # Write a header when its corresponding HTML page is written.
    app.connect("html-page-context", writer)


def writer(app, pagename, templatename, context, doctree):
    if doctree is None:
        return

    env = app.builder.env
    items = []
    for section in isections(doctree):
        tour_descinfo(items.append, section, env)
    if not items:
        return
    templates = app.builder.templates
    filename = f"{os.path.basename(pagename)}_doc.h"
    filepath = os.path.join('src_c', 'doc', filename)
    header = open(filepath, "w", encoding="utf-8")
    context["hdr_items"] = items
    try:
        header.write(templates.render('header.h', context))
    finally:
        header.close()
        del context["hdr_items"]
