from typing import Any, Dict, List, Tuple

from docutils import nodes, utils
from docutils.nodes import Node, system_message
from docutils.parsers.rst.states import Inliner

import sphinx
from sphinx.application import Sphinx
from sphinx.util.nodes import split_explicit_title
from sphinx.util.typing import RoleFunction

class strikethrough(nodes.Inline, nodes.TextElement):
    pass

class underline(nodes.Inline, nodes.TextElement):
    pass

def build_visitors(tag_name: str):
    def visit(self, node):
        self.body.append(self.starttag(node, tag_name, CLASS=node.attributes.get('class', '')))

    def depart(self, node):
        self.body.append(f'</{tag_name}>')

    return visit, depart

def setup(app: Sphinx):
    app.add_node(strikethrough, html=build_visitors('s'))
    app.add_node(underline, html=build_visitors('u'))
    app.add_generic_role('strike', strikethrough)
    app.add_generic_role('underline', underline)
