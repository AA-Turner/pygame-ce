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
import sphinx.addnodes

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
            items.extend(tour_descinfo(section, app.builder.env))
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

    """Records the information for a document"""

    def unknown_visit(self, node):
        return

    def unknown_departure(self, node):
        return

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
        if node.children and node["ids"][0].startswith(MODULE_ID_PREFIX):
            self._add_descinfo(node, summary, sigs, child_descs)

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
        self._add_descinfo(node, summary, sigs, child_descs)
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
        refid = get_refid(node)
        self.env.pyg_descinfo_tbl[refid.removeprefix(MODULE_ID_PREFIX)] = {
            "fullname": fullname,
            "desctype": node.get("desctype", "module"),
            "summary": summary,
            "signatures": sigs,
            "children": list(map(get_refid, child_descs)),
            "refid": refid,
            "docname": self.env.docname,
        }


def tour_descinfo(node, env):
    refid = get_refid(node)
    try:
        descinfo = env.pyg_descinfo_tbl[refid.removeprefix(MODULE_ID_PREFIX)]
    except KeyError:
        return
    yield descinfo
    for refid in descinfo["children"]:
        yield env.pyg_descinfo_tbl[refid]  # A KeyError would mean a bug.


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
