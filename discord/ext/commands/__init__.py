# -*- coding: utf-8 -*-

"""
discord.ext.commands
~~~~~~~~~~~~~~~~~~~~~

An extension module to facilitate creation of bot commands.

:copyright: (c) 2015-2020 Rapptz
:license: MIT, see LICENSE for more details.
"""

from .bot import Bot, AutoShardedBot, when_mentioned, when_mentioned_or
from .context import Context
from .core import *
from .errors import *
from .help import *
from .converter import *
from .cooldowns import *
from .cog import *
