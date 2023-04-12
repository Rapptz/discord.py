from __future__ import annotations
from typing import Dict, Any

from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes

import sphinx
from sphinx.application import Sphinx


class colour_input(nodes.General, nodes.Element):
    pass


def visit_colour_node(self, node):
    self.body.append(
        self.starttag(
            node,
            'input',
            empty=True,
            type='color',
            value=node.rawsource,
            disabled='',
            CLASS=node.attributes.get('class', ''),
        )
    )


def depart_colour_node(self, node):
    pass


class ColourDirective(SphinxDirective):
    required_arguments = 1
    has_content = False

    option_spec = {
        'class': directives.class_option,
    }

    def run(self):
        node = colour_input(self.arguments[0], **self.options)
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_node(colour_input, html=(visit_colour_node, depart_colour_node))
    app.add_directive('colour', ColourDirective)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
