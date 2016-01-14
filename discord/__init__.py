# -*- coding: utf-8 -*-

"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015 Rapptz
:license: MIT, see LICENSE for more details.

"""

__title__ = 'discord'
__author__ = 'Rapptz'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Rapptz'
__version__ = '0.9.2'
__build__ = 0x009020

from .client import Client
from .user import User
from .game import Game
from .channel import Channel, PrivateChannel
from .server import Server
from .member import Member
from .message import Message
from .errors import *
from .permissions import Permissions
from .role import Role
from .colour import Color, Colour
from .invite import Invite
from .object import Object
from . import utils

import logging
import warnings

_warning_message = """
The next major version of discord.py (v0.10.0) will have major breaking changes
that will require updating/changing your code.
Please check the migrating guide to alleviate yourself of unexpected issues.
http://discordpy.readthedocs.org/en/latest/migrating.html
It is strongly recommended to make the switch as soon as possible.
"""

warnings.warn(_warning_message, UserWarning)

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
