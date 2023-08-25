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

import os
import os.path

import docutils.nodes
import sphinx.addnodes

MODULE_ID_PREFIX = "module-"


def setup(app):
    app.connect("env-purge-doc", prep_document_info)
    app.connect("doctree-read", collect_document_info)
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


def prep_document_info(app, env, docname):
    try:
        descinfo_tbl = env.pyg_descinfo_tbl
    except AttributeError:
        pass
    else:
        to_remove = [k for k, v in descinfo_tbl.items() if v["docname"] == docname]
        for k in to_remove:
            del descinfo_tbl[k]


def collect_document_info(app, doctree):
    doctree.walkabout(CollectInfo(app.builder.env, doctree))


class CollectInfo(docutils.nodes.SparseNodeVisitor):

    """Records the information for a document"""

    def unknown_visit(self, node):
        return

    def unknown_departure(self, node):
        return

    desctypes = {
        "data",
        "function",
        "exception",
        "class",
        "attribute",
        "method",
        "staticmethod",
        "classmethod",
    }

    def __init__(self, env, document_node):
        super().__init__(document_node)
        self.env = env
        self.summary_stack = []
        self.sig_stack = []
        self.desc_stack = []
        try:
            self.env.pyg_descinfo_tbl
        except AttributeError:
            self.env.pyg_descinfo_tbl = {}

    def visit_section(self, node):
        if not node["names"]:
            raise docutils.nodes.SkipNode()
        self._push()

    def depart_section(self, node):
        """Record section info"""

        summary, sigs, child_descs = self._pop()
        if not node.children:
            return
        if node["ids"][0].startswith(MODULE_ID_PREFIX):
            self._add_descinfo(node, summary, sigs, child_descs)
        elif child_descs:
            # No section level introduction: use the first toplevel directive
            # instead.
            desc_node = child_descs[0]
            self._add_descinfo_entry(node, get_descinfo_refid(get_refid(desc_node), self.env))

    def visit_desc(self, node):
        """Prepare to collect a summary and toc for this description"""

        if node.get("desctype", "") not in self.desctypes:
            raise docutils.nodes.SkipNode()
        self._push()

    def depart_desc(self, node):
        """Record descinfo information and add descinfo to parent's toc"""

        self._add_descinfo(node, *self._pop())
        self.desc_stack[-1].append(node)

    def visit_inline(self, node):
        """Collect a summary or signature"""

        if "summaryline" in node["classes"]:
            self.summary_stack[-1] = node[0].astext()
        elif "signature" in node["classes"]:
            self.sig_stack[-1].append(node[0].astext())
        raise docutils.nodes.SkipDeparture()

    def _add_descinfo(self, node, summary, sigs, child_descs):
        if isinstance(node, docutils.nodes.section):
            try:
                names = node["names"]
            except KeyError:
                raise GetError("No fullname: missing names attribute in section")
            try:
                fullname = names[0]
            except IndexError:
                raise GetError("No fullname: section has empty names list")
        elif isinstance(node, sphinx.addnodes.desc):
            try:
                sig = node[0]
            except IndexError:
                raise GetError("No fullname: missing children in desc")
            try:
                names = sig["ids"]
            except KeyError:
                raise GetError("No fullname: missing ids attribute in desc's child")
            try:
                fullname = names[0]
            except IndexError:
                raise GetError("No fullname: desc's child has empty names list")
        else:
            raise TypeError(f"Unrecognized node type '{node.__class__}'")
        entry = {
            "fullname": fullname,
            "desctype": node.get("desctype", "module"),
            "summary": summary,
            "signatures": sigs,
            "children": list(map(get_refid, child_descs)),
            "refid": get_refid(node),
            "docname": self.env.docname,
        }
        self._add_descinfo_entry(node, entry)

    def _add_descinfo_entry(self, node, entry):
        key = get_refid(node)
        if key.startswith(MODULE_ID_PREFIX):
            key = key[len(MODULE_ID_PREFIX) :]
        self.env.pyg_descinfo_tbl[key] = entry

    def _push(self):
        self.summary_stack.append("")
        self.sig_stack.append([])
        self.desc_stack.append([])

    def _pop(self):
        return (self.summary_stack.pop(), self.sig_stack.pop(), self.desc_stack.pop())


def tour_descinfo(fn, node, env):
    try:
        descinfo = get_descinfo_refid(get_refid(node), env)
    except GetError:
        return
    fn(descinfo)
    for refid in descinfo["children"]:
        tour_descinfo_refid(fn, refid, env)


def tour_descinfo_refid(fn, refid, env):
    descinfo = env.pyg_descinfo_tbl[refid]  # A KeyError would mean a bug.
    fn(descinfo)
    for refid in descinfo["children"]:
        tour_descinfo_refid(fn, refid, env)


def get_descinfo_refid(refid, env):
    if refid.startswith(MODULE_ID_PREFIX):
        refid = refid[len(MODULE_ID_PREFIX) :]
    try:
        return env.pyg_descinfo_tbl[refid]
    except KeyError:
        raise GetError("Not found")


class GetError(LookupError):
    pass


def get_refid(node):
    try:
        return get_ids(node)[0]
    except IndexError:
        raise GetError("Node has empty ids list")


def get_ids(node):
    if isinstance(node, docutils.nodes.section):
        try:
            return node["ids"]
        except KeyError:
            raise GetError("No ids: section missing ids attribute")
    if isinstance(node, sphinx.addnodes.desc):
        try:
            sig = node[0]
        except IndexError:
            raise GetError("No ids: missing desc children")
        try:
            return sig["ids"]
        except KeyError:
            raise GetError("No ids: desc's child missing ids attribute")
    raise TypeError(f"Unrecognized node type '{node.__class__}'")
