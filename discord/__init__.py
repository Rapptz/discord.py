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
__version__ = '0.3.1'
__build__ = 0x003010

from client import Client
from user import User
from channel import Channel, PrivateChannel
from server import Server, Member, Permissions, Role
from message import Message
from errors import *
from permissions import Permissions
