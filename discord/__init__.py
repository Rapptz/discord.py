"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord user API.

:copyright: (c) 2015-present Rapptz and 2021-present Dolfies
:license: MIT, see LICENSE for more details.
"""

__title__ = 'discord.py-self'
__author__ = 'Dolfies'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-present Rapptz and 2021-present Dolfies'
__version__ = '2.0.0'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import logging
from typing import Literal, NamedTuple

from . import abc as abc, opus as opus, utils as utils
from .activity import *
from .affinity import *
from .application import *
from .asset import *
from .audit_logs import *
from .automod import *
from .billing import *
from .calls import *
from .channel import *
from .client import *
from .colour import *
from .commands import *
from .components import *
from .connections import *
from .embeds import *
from .emoji import *
from .entitlements import *
from .enums import *
from .errors import *
from .file import *
from .flags import *
from .guild import *
from .guild_premium import *
from .handlers import *
from .integrations import *
from .interactions import *
from .invite import *
from .library import *
from .member import *
from .mentions import *
from .message import *
from .metadata import *
from .modal import *
from .object import *
from .partial_emoji import *
from .payments import *
from .permissions import *
from .player import *
from .profile import *
from .promotions import *
from .raw_models import *
from .reaction import *
from .relationship import *
from .role import *
from .scheduled_event import *
from .settings import *
from .stage_instance import *
from .sticker import *
from .store import *
from .subscriptions import *
from .team import *
from .template import *
from .threads import *
from .tracking import *
from .user import *
from .voice_client import *
from .webhook import *
from .welcome_screen import *
from .widget import *


class _VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal['alpha', 'beta', 'candidate', 'final']
    serial: int


version_info: _VersionInfo = _VersionInfo(major=2, minor=0, micro=0, releaselevel='final', serial=0)

logging.getLogger(__name__).addHandler(logging.NullHandler())


del logging, NamedTuple, Literal, _VersionInfo
