from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment.adapters.indexentries import IndexEntries
from sphinx.writers.html5 import HTML5Translator

class DPYHTML5Translator(HTML5Translator):
    def visit_section(self, node):
        self.section_level += 1
        self.body.append(
            self.starttag(node, 'section'))

    def depart_section(self, node):
        self.section_level -= 1
        self.body.append('</section>\n')

    def visit_table(self, node):
        self.body.append('<div class="table-wrapper">')
        super().visit_table(node)

    def depart_table(self, node):
        super().depart_table(node)
        self.body.append('</div>')

class DPYStandaloneHTMLBuilder(StandaloneHTMLBuilder):
    # This is mostly copy pasted from Sphinx.
    def write_genindex(self) -> None:
        # the total count of lines for each index letter, used to distribute
        # the entries into two columns
        genindex = IndexEntries(self.env).create_index(self, group_entries=False)
        indexcounts = []
        for _k, entries in genindex:
            indexcounts.append(sum(1 + len(subitems)
                                   for _, (_, subitems, _) in entries))

        genindexcontext = {
            'genindexentries': genindex,
            'genindexcounts': indexcounts,
            'split_index': self.config.html_split_index,
        }

        if self.config.html_split_index:
            self.handle_page('genindex', genindexcontext,
                             'genindex-split.html')
            self.handle_page('genindex-all', genindexcontext,
                             'genindex.html')
            for (key, entries), count in zip(genindex, indexcounts):
                ctx = {'key': key, 'entries': entries, 'count': count,
                       'genindexentries': genindex}
                self.handle_page('genindex-' + key, ctx,
                                 'genindex-single.html')
        else:
            self.handle_page('genindex', genindexcontext, 'genindex.html')


def add_custom_jinja2(app):
    env = app.builder.templates.environment
    env.tests['prefixedwith'] = str.startswith
    env.tests['suffixedwith'] = str.endswith

def add_builders(app):
    """This is necessary because RTD injects their own for some reason."""
    app.set_translator('html', DPYHTML5Translator, override=True)
    app.add_builder(DPYStandaloneHTMLBuilder, override=True)

    try:
        original = app.registry.builders['readthedocs']
    except KeyError:
        pass
    else:
        injected_mro = tuple(base if base is not StandaloneHTMLBuilder else DPYStandaloneHTMLBuilder
                             for base in original.mro()[1:])
        new_builder = type(original.__name__, injected_mro, {'name': 'readthedocs'})
        app.set_translator('readthedocs', DPYHTML5Translator, override=True)
        app.add_builder(new_builder, override=True)

def setup(app):
    add_builders(app)
    app.connect('builder-inited', add_custom_jinja2)
