from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.gettext import MessageCatalogBuilder, I18nBuilder, timestamp, ltz, should_write, GettextRenderer
from sphinx.locale import __
from sphinx.util import status_iterator
from sphinx.util.osutil import ensuredir
from sphinx.environment.adapters.indexentries import IndexEntries
from sphinx.writers.html5 import HTML5Translator
import datetime
import os
import re


class DPYHTML5Translator(HTML5Translator):
    def visit_section(self, node):
        self.section_level += 1
        self.body.append(self.starttag(node, 'section'))

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
            indexcounts.append(sum(1 + len(subitems) for _, (_, subitems, _) in entries))

        genindexcontext = {
            'genindexentries': genindex,
            'genindexcounts': indexcounts,
            'split_index': self.config.html_split_index,
        }

        if self.config.html_split_index:
            self.handle_page('genindex', genindexcontext, 'genindex-split.html')
            self.handle_page('genindex-all', genindexcontext, 'genindex.html')
            for (key, entries), count in zip(genindex, indexcounts):
                ctx = {'key': key, 'entries': entries, 'count': count, 'genindexentries': genindex}
                self.handle_page('genindex-' + key, ctx, 'genindex-single.html')
        else:
            self.handle_page('genindex', genindexcontext, 'genindex.html')


class DPYMessageCatalogBuilder(MessageCatalogBuilder):
    _ADMONITION_REGEX = re.compile(r'\.\.\s*[a-zA-Z\_-]+::')

    def finish(self) -> None:
        # Bypass MessageCatalogBuilder.finish
        I18nBuilder.finish(self)

        # This is mostly copy pasted from Sphinx
        # However, this allows
        context = {
            'version': self.config.version,
            'copyright': self.config.copyright,
            'project': self.config.project,
            'last_translator': self.config.gettext_last_translator,
            'language_team': self.config.gettext_language_team,
            'ctime': datetime.datetime.fromtimestamp(timestamp, ltz).strftime('%Y-%m-%d %H:%M%z'),
            'display_location': self.config.gettext_location,
            'display_uuid': self.config.gettext_uuid,
        }

        REGEX = self._ADMONITION_REGEX
        for textdomain, catalog in status_iterator(
            self.catalogs.items(),
            __("writing message catalogs... "),
            "darkgreen",
            len(self.catalogs),
            self.app.verbosity,
            lambda textdomain__: textdomain__[0],
        ):
            # noop if config.gettext_compact is set
            ensuredir(os.path.join(self.outdir, os.path.dirname(textdomain)))

            # Due to a bug in Sphinx where messages contain admonitions, this code makes it
            # so they're suppressed from the output to prevent the output and CI from breaking
            # This is quite a bandaid fix but it seems to work ok
            # See https://github.com/sphinx-doc/sphinx/issues/10334
            context['messages'] = [msg for msg in catalog if REGEX.search(msg.text) is None]

            content = GettextRenderer(template_path='_templates/gettext', outdir=self.outdir).render(
                'message.pot_t', context
            )

            pofn = os.path.join(self.outdir, textdomain + '.pot')
            if should_write(pofn, content):
                with open(pofn, 'w', encoding='utf-8') as pofile:
                    pofile.write(content)


def add_custom_jinja2(app):
    env = app.builder.templates.environment
    env.tests['prefixedwith'] = str.startswith
    env.tests['suffixedwith'] = str.endswith


def add_builders(app):
    """This is necessary because RTD injects their own for some reason."""
    app.set_translator('html', DPYHTML5Translator, override=True)
    app.add_builder(DPYStandaloneHTMLBuilder, override=True)
    app.add_builder(DPYMessageCatalogBuilder, override=True)

    try:
        original = app.registry.builders['readthedocs']
    except KeyError:
        pass
    else:
        injected_mro = tuple(
            base if base is not StandaloneHTMLBuilder else DPYStandaloneHTMLBuilder for base in original.mro()[1:]
        )
        new_builder = type(original.__name__, injected_mro, {'name': 'readthedocs'})
        app.set_translator('readthedocs', DPYHTML5Translator, override=True)
        app.add_builder(new_builder, override=True)


def setup(app):
    add_builders(app)
    app.connect('builder-inited', add_custom_jinja2)
    return {'parallel_read_safe': True}
