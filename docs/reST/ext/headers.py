import docutils.nodes
from ext.indexer import tour_descinfo

import os


def setup(app):
    app.connect("html-page-context", writer)


def writer(app, pagename, _, context, doctree):
    if doctree is None:
        return

    items = []
    for section in doctree:
        if isinstance(section, docutils.nodes.section):
            tour_descinfo(items.append, section, app.builder.env)
    if not items:
        return
    print(pagename, len(items))
    filename = f"{os.path.basename(pagename)}_doc.h"
    filepath = os.path.join('src_c', 'doc', filename)
    header = open(filepath, "w", encoding="utf-8")
    context["hdr_items"] = items
    try:
        header.write(app.builder.templates.render('header.h', context))
    finally:
        header.close()
        del context["hdr_items"]
