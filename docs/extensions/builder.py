from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment.adapters.indexentries import IndexEntries

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

def get_builder(app):
    """This is necessary because RTD injects their own for some reason."""
    try:
        original = app.registry.builders['readthedocs']
    except KeyError:
        return DPYStandaloneHTMLBuilder
    else:
        injected_mro = tuple(base if base is not StandaloneHTMLBuilder else DPYStandaloneHTMLBuilder
                             for base in original.mro()[1:])
        return type(original.__name__, injected_mro, {'name': 'readthedocs'})

def setup(app):
    app.add_builder(get_builder(app), override=True)
