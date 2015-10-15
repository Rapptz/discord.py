# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from .user import User
from .permissions import Permissions
from .utils import parse_time

class Role(object):
    """Represents a Discord role in a :class:`Server`.

    Instance attributes:

    .. attribute:: id

        The ID for the role.
    .. attribute:: name

        The name of the role.
    .. attribute:: permissions

        A :class:`Permissions` that represents the role's permissions.
    .. attribute:: color
                   colour

        A tuple of (r, g, b) associated with the role colour.
    .. attribute:: hoist

        A boolean representing if the role will be displayed separately from other members.
    .. attribute:: position

        The position of the role.
    """

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.permissions = Permissions(kwargs.get('permissions', 0))
        self.position = kwargs.get('position', -1)
        self.colour = kwargs.get('color', 0)
        self.hoist = kwargs.get('hoist', False)
        self._colour_to_tuple()

    def _colour_to_tuple(self):
        # first we turn this into a hex string
        # the reason why we're using a hex string rather than just use bitwise
        # ops is because we don't want to care too much about endianness.
        hex_str = format(self.colour, '06x')
        red = int(hex_str[0] + hex_str[1], base=16)
        green = int(hex_str[2] + hex_str[3], base=16)
        blue = int(hex_str[4] + hex_str[5], base=16)
        self.colour = (red, green, blue)
        self.color = self.colour


class Member(User):
    """Represents a Discord member to a :class:`Server`.

    This is a subclass of :class:`User` that extends more functionality
    that server members have such as roles and permissions.

    Instance attributes:

    .. attribute:: deaf

        A boolean that specifies if the member is currently deafened by the server.
    .. attribute:: mute

        A boolean that specifies if the member is currently muted by the server.
    .. attribute:: self_mute

        A boolean that specifies if the member is currently muted by their own accord.
    .. attribute:: self_deaf

        A boolean that specifies if the member is currently deafened by their own accord.
    .. attribute:: is_afk

        A boolean that specifies if the member is currently in the AFK channel in the server.
    .. attribute:: voice_channel

        A voice :class:`Channel` that the member is currently connected to. None if the member
        is not currently in a voice channel.
    .. attribute:: roles

        An array of :class:`Role` that the member belongs to.
    .. attribute:: joined_at

        A datetime object that specifies the date and time in UTC that the member joined the server for
        the first time.
    .. attribute:: status

        A string that denotes the user's status. Can be 'online', 'offline' or 'idle'.
    .. attribute:: game_id

        The game ID that the user is currently playing. Could be None if no game is being played.
    .. attribute:: server

        The :class:`Server` that the member belongs to.
    """

    def __init__(self, deaf, joined_at, user, roles, mute, **kwargs):
        super(Member, self).__init__(**user)
        self.deaf = deaf
        self.mute = mute
        self.joined_at = parse_time(joined_at)
        self.roles = roles
        self.status = 'offline'
        self.game_id = kwargs.get('game_id', None)
        self.server = kwargs.get('server', None)
        self.update_voice_state(mute=mute, deaf=deaf)

    def update_voice_state(self, **kwargs):
        self.self_mute = kwargs.get('self_mute', False)
        self.self_deaf = kwargs.get('self_deaf', False)
        self.is_afk = kwargs.get('suppress', False)
        self.mute = kwargs.get('mute', False)
        self.deaf = kwargs.get('deaf', False)
        self.voice_channel = kwargs.get('voice_channel')

class Server(object):
    """Represents a Discord server.

    Instance attributes:

    .. attribute:: name

        The server name.
    .. attribute:: roles

        An array of :class:`Role` that the server has available.
    .. attribute:: region

        The region the server belongs on.
    .. attribute:: afk_timeout

        The timeout to get sent to the AFK channel.
    .. attribute:: afk_channel_id

        The channel ID for the AFK channel. None if it doesn't exist.
    .. attribute:: members

        An array of :class:`Member` that are currently on the server.
    .. attribute:: channels

        An array of :class:`Channel` that are currently on the server.
    .. attribute:: icon

        The server's icon.
    .. attribute:: id

        The server's ID.
    .. attribute:: owner

        The :class:`Member` who owns the server.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.roles = kwargs.get('roles')
        self.region = kwargs.get('region')
        self.afk_timeout = kwargs.get('afk_timeout')
        self.afk_channel_id = kwargs.get('afk_channel_id')
        self.members = kwargs.get('members')
        self.icon = kwargs.get('icon')
        self.id = kwargs.get('id')
        self.owner = kwargs.get('owner')

    def get_default_role(self):
        """Gets the @everyone role that all members have by default."""
        for role in self.roles:
            if role.name == '@everyone':
                return role
