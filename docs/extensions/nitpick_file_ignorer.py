import logging

from sphinx.application import Sphinx
from sphinx.util import logging as sphinx_logging


class NitpickFileIgnorer(logging.Filter):
    
    def __init__(self, app: Sphinx) -> None:
        self.app = app
        super().__init__()

    def filter(self, record: sphinx_logging.SphinxLogRecord) -> bool:
        if getattr(record, 'type', None) == 'ref':
            return record.location.get('refdoc') not in self.app.config.nitpick_ignore_files
        return True


def setup(app: Sphinx):
    app.add_config_value('nitpick_ignore_files', [], '')
    f = NitpickFileIgnorer(app)
    sphinx_logging.getLogger('sphinx.transforms.post_transforms').logger.addFilter(f)
    return {'parallel_read_safe': True}
