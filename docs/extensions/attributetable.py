from sphinx.util.docutils import SphinxDirective
from sphinx.locale import _
from docutils import nodes
from sphinx import addnodes

from collections import OrderedDict
import importlib
import inspect
import os
import re

class attributetable(nodes.General, nodes.Element):
    pass

class attributetablecolumn(nodes.General, nodes.Element):
    pass

class attributetabletitle(nodes.TextElement):
    pass

class attributetableplaceholder(nodes.General, nodes.Element):
    pass

def visit_attributetable_node(self, node):
    self.body.append('<div class="py-attribute-table" data-move-to-id="%s">' % node['python-class'])

def visit_attributetablecolumn_node(self, node):
    self.body.append(self.starttag(node, 'div', CLASS='py-attribute-table-column'))

def visit_attributetabletitle_node(self, node):
    self.body.append(self.starttag(node, 'span'))

def depart_attributetable_node(self, node):
    self.body.append('</div>')

def depart_attributetablecolumn_node(self, node):
    self.body.append('</div>')

def depart_attributetabletitle_node(self, node):
    self.body.append('</span>')

_name_parser_regex = re.compile(r'(?P<module>[\w.]+\.)?(?P<name>\w+)')

class PyAttributeTable(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def parse_name(self, content):
        path, name = _name_parser_regex.match(content).groups()
        if path:
            modulename = path.rstrip('.')
        else:
            modulename = self.env.temp_data.get('autodoc:module')
            if not modulename:
                modulename = self.env.ref_context.get('py:module')
        if modulename is None:
            raise RuntimeError('modulename somehow None for %s in %s.' % (content, self.env.docname))

        return modulename, name

    def run(self):
        """If you're curious on the HTML this is meant to generate:

        <div class="py-attribute-table">
            <div class="py-attribute-table-column">
                <span>_('Attributes')</span>
                <ul>
                    <li><a href="..."></li>
                </ul>
            </div>
            <div class="py-attribute-table-column">
                <span>_('Coroutines')</span>
                <ul>
                    <li><a href="..."></li>
                </ul>
            </div>
            <div class="py-attribute-table-column">
                <span>_('Methods')</span>
                <ul>
                    <li><a href="..."></li>
                </ul>
            </div>
            ...
        </div>

        However, since this requires the tree to be complete
        and parsed, it'll need to be done at a different stage and then
        replaced.
        """
        content = self.arguments[0].strip()
        node = attributetableplaceholder('')
        modulename, name = self.parse_name(content)
        node['python-module'] = modulename
        node['python-class'] = name
        node['python-full-name'] = '%s.%s' % (modulename, name)
        return [node]

def build_lookup_table(env):
    # Given an environment, load up a lookup table of
    # full-class-name: objects
    result = {}
    domain = env.domains['py']

    ignored = {
        'data', 'exception', 'module', 'class',
    }

    for (fullname, _, objtype, docname, _, _) in domain.get_objects():
        if objtype in ignored:
            continue

        classname, _, child = fullname.rpartition('.')
        try:
            result[classname].append(child)
        except KeyError:
            result[classname] = [child]

    return result

def process_attributetable(app, doctree, fromdocname):
    env = app.builder.env

    lookup = build_lookup_table(env)
    for node in doctree.traverse(attributetableplaceholder):
        modulename, classname, fullname = node['python-module'], node['python-class'], node['python-full-name']
        groups = get_class_results(lookup, modulename, classname, fullname)
        table = attributetable('')
        for label, subitems in groups.items():
            if not subitems:
                continue
            table.append(class_results_to_node(label, sorted(subitems)))

        table['python-class'] = fullname

        if not table:
            node.replace_self([])
        else:
            node.replace_self([table])

def get_class_results(lookup, modulename, name, fullname):
    module = importlib.import_module(modulename)
    cls_dict = getattr(module, name).__dict__

    groups = OrderedDict([
        ('Attributes', []),
        ('Coroutines', []),
        ('Classmethods', []),
        ('Methods', []),
        ('Decorators', []),
    ])

    try:
        members = lookup[fullname]
    except KeyError:
        return groups

    for attr in members:
        attrlookup = '%s.%s' % (fullname, attr)
        key = 'Attributes'
        label = attr

        value = cls_dict.get(attr)
        if value is not None:
            doc = value.__doc__ or ''
            if inspect.iscoroutinefunction(value) or doc.startswith('|coro|'):
                key = 'Coroutines'
            elif isinstance(value, classmethod):
                key = 'Classmethods'
            elif inspect.isfunction(value):
                if doc.startswith(('A decorator', 'A shortcut decorator')):
                    # finicky but surprisingly consistent
                    key = 'Decorators'
                else:
                    key = 'Methods'

        groups[key].append((attrlookup, label))

    return groups

def class_results_to_node(key, elements):
    title = attributetabletitle(key, key)
    ul = nodes.bullet_list('')
    for fullname, label in elements:
        ref = nodes.reference('', '', internal=True,
                                      refuri='#' + fullname,
                                      anchorname='',
                                      *[nodes.Text(label)])
        para = addnodes.compact_paragraph('', '', ref)
        item = nodes.list_item('', para)
        ul.append(item)

    return attributetablecolumn('', title, ul)

def setup(app):
    app.add_directive('attributetable', PyAttributeTable)
    app.add_node(attributetable, html=(visit_attributetable_node, depart_attributetable_node))
    app.add_node(attributetablecolumn, html=(visit_attributetablecolumn_node, depart_attributetablecolumn_node))
    app.add_node(attributetabletitle, html=(visit_attributetabletitle_node, depart_attributetabletitle_node))
    app.add_node(attributetableplaceholder)
    app.connect('doctree-resolved', process_attributetable)
