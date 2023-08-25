"""Collect information on document sections and Pygame API objects

The following persistent Pygame specific environment structures are built:

pyg_sections: [{'docname': <docname>,
                'fullname': <fullname>,
                'refid': <ref>},
               ...]
    all Pygame api sections in the documents in order processed.
pyg_descinfo_tbl: {<id>: {'fullname': <fullname>,
                          'desctype': <type>,
                          'summary': <summary>,
                          'signatures': <sigs>,
                          'children': <toc>,
                          'refid': <ref>,
                          'docname': <docname>},
                   ...}
    object specific information, including a list of direct children, if any.

<docname>: (str) the simple document name without path or extension.
<fullname>: (str) a fully qualified object name. It is a unique identifier.
<ref>: (str) an id usable as local uri reference.
<id>: (str) unique desc id, the first entry in the ids attribute list.
<type>: (str) an object's type: the desctype attribute.
<summary>: (str) a summary line as identified by a :summaryline: role.
           This corresponds to the first line of a docstring.
<sigs>: (list of str) an object's signatures, in document order.
<toc>: (list of str) refids of an object's children, in document order.

"""

import docutils.nodes

MODULE_ID_PREFIX = "module-"


def setup(app):
    app.connect("doctree-read", collect_document_info)
    app.connect("html-page-context", writer)


def writer(app, pagename, _, context, doctree):
    if doctree is None:
        return

    items = []
    for section in doctree:
        if isinstance(section, docutils.nodes.section):
            refid = section["ids"][0]
            descinfo = app.builder.env.pyg_descinfo_tbl[refid.removeprefix(MODULE_ID_PREFIX)]
            items.append(descinfo)
            for refid in descinfo["children"]:
                items.append(app.builder.env.pyg_descinfo_tbl[refid])  # A KeyError would mean a bug.
    if not items:
        return
    print(pagename, len(items))
    context["hdr_items"] = items
    try:
        with open(fr'src_c\doc\{pagename}_doc.h', "w", encoding="utf-8") as header:
            header.write(app.builder.templates.render('header.h', context))
    finally:
        del context["hdr_items"]


def collect_document_info(app, doctree):
    doctree.walkabout(CollectInfo(app.builder.env, doctree))


class CollectInfo(docutils.nodes.SparseNodeVisitor):
    def unknown_visit(self, node): pass
    def unknown_departure(self, node): pass

    def __init__(self, env, document_node):
        super().__init__(document_node)
        self.env = env

        self.summary_stack = [""]
        self.sig_stack = [[]]
        self.desc_stack = [[]]
        try:
            self.env.pyg_descinfo_tbl
        except AttributeError:
            self.env.pyg_descinfo_tbl = {}

    def depart_section(self, node):
        """Record section info"""
        summary = self.summary_stack.pop()
        sigs = self.sig_stack.pop()
        child_descs = self.desc_stack.pop()
        refid = node["ids"][0]
        if node.children and node["ids"][0].startswith(MODULE_ID_PREFIX):
            self.env.pyg_descinfo_tbl[refid.removeprefix(MODULE_ID_PREFIX)] = {
                "fullname": node["names"][0],
                "desctype": node.get("desctype", "module"),
                "summary": summary,
                "signatures": sigs,
                "children": [desc[0]["ids"][0] for desc in child_descs],
                "refid": refid,
                "docname": self.env.docname,
            }

    def visit_desc(self, node):
        """Prepare to collect a summary and toc for this description"""
        self.summary_stack.append("")
        self.sig_stack.append([])
        self.desc_stack.append([])

    def depart_desc(self, node):
        """Record descinfo information and add descinfo to parent's toc"""

        summary = self.summary_stack.pop()
        sigs = self.sig_stack.pop()
        child_descs = self.desc_stack.pop()
        refid = node[0]["ids"][0]
        self.env.pyg_descinfo_tbl[refid.removeprefix(MODULE_ID_PREFIX)] = {
            "fullname": node[0]["ids"][0],
            "desctype": node.get("desctype", "module"),
            "summary": summary,
            "signatures": sigs,
            "children": [desc[0]["ids"][0] for desc in child_descs],
            "refid": refid,
            "docname": self.env.docname,
        }
        self.desc_stack[-1].append(node)

    def visit_inline(self, node):
        """Collect a summary or signature"""

        if "summaryline" in node["classes"]:
            self.summary_stack[-1] = node[0].astext()
        elif "signature" in node["classes"]:
            self.sig_stack[-1].append(node[0].astext())
        raise docutils.nodes.SkipDeparture()
