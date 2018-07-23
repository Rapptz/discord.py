# -*- coding: utf-8 -*-

"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015-2016 Rapptz
:license: MIT, see LICENSE for more details.

"""

__title__ = 'discord'
__author__ = 'Rapptz'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-2016 Rapptz'
__version__ = '0.16.12'

from .client import Client, AppInfo, ChannelPermissions
from .user import User
from .game import Game
from .emoji import Emoji
from .channel import Channel, PrivateChannel
from .server import Server
from .member import Member, VoiceState
from .message import Message
from .errors import *
from .calls import CallMessage, GroupCall
from .permissions import Permissions, PermissionOverwrite
from .role import Role
from .colour import Color, Colour
from .invite import Invite
from .object import Object
from .reaction import Reaction
from . import utils, opus, compat
from .voice_client import VoiceClient
from .enums import ChannelType, ServerRegion, Status, MessageType, VerificationLevel
from collections import namedtuple
from .embeds import Embed

import logging

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=16, micro=12, releaselevel='final', serial=0)

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
