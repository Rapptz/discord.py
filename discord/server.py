# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

from . import utils
from .role import Role
from .member import Member
from .game import Game
from .channel import Channel
from .enums import ServerRegion, Status
from .mixins import Hashable
import copy

class Server(Hashable):
    """Represents a Discord server.

    Supported Operations:

    +-----------+--------------------------------------+
    | Operation |             Description              |
    +===========+======================================+
    | x == y    | Checks if two servers are equal.     |
    +-----------+--------------------------------------+
    | x != y    | Checks if two servers are not equal. |
    +-----------+--------------------------------------+
    | hash(x)   | Returns the server's hash.           |
    +-----------+--------------------------------------+
    | str(x)    | Returns the server's name.           |
    +-----------+--------------------------------------+

    Attributes
    ----------
    name : str
        The server name.
    me : :class:`Member`
        Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
    roles
        A list of :class:`Role` that the server has available.
    region : :class:`ServerRegion`
        The region the server belongs on. There is a chance that the region
        will be a ``str`` if the value is not recognised by the enumerator.
    afk_timeout : int
        The timeout to get sent to the AFK channel.
    afk_channel : :class:`Channel`
        The channel that denotes the AFK channel. None if it doesn't exist.
    members
        A list of :class:`Member` that are currently on the server.
    channels
        A list of :class:`Channel` that are currently on the server.
    icon : str
        The server's icon.
    id : str
        The server's ID.
    owner : :class:`Member`
        The member who owns the server.
    unavailable : bool
        Indicates if the server is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :meth:`Server.id` is slim and they might
        all be None. It is best to not do anything with the server if it is unavailable.

        Check the :func:`on_server_unavailable` and :func:`on_server_available` events.
    """

    __slots__ = [ 'afk_timeout', 'afk_channel', 'members', 'channels', 'icon',
                  'name', 'id', 'owner', 'unavailable', 'name', 'me', 'region',
                  '_default_role', '_default_channel', 'roles' ]

    def __init__(self, **kwargs):
        self.channels = []
        self.owner = None
        self.members = []
        self._from_data(kwargs)

    def __str__(self):
        return self.name

    def _update_voice_state(self, data):
        user_id = data.get('user_id')
        member = utils.find(lambda m: m.id == user_id, self.members)
        before = copy.copy(member)
        if member is not None:
            ch_id = data.get('channel_id')
            channel = utils.find(lambda c: c.id == ch_id, self.channels)
            member.update_voice_state(voice_channel=channel, **data)
        return before, member

    def _from_data(self, guild):
        self.name = guild.get('name')
        self.region = guild.get('region')
        try:
            self.region = ServerRegion(self.region)
        except:
            pass

        self.afk_timeout = guild.get('afk_timeout')
        self.icon = guild.get('icon')
        self.unavailable = guild.get('unavailable', False)
        self.id = guild['id']
        self.roles = [Role(everyone=(self.id == r['id']), **r) for r in guild.get('roles', [])]

        owner_id = guild.get('owner_id')

        for data in guild.get('members', []):
            roles = [self.default_role]
            for role_id in data['roles']:
                role = utils.find(lambda r: r.id == role_id, self.roles)
                if role is not None:
                    roles.append(role)

            data['roles'] = roles
            member = Member(**data)
            member.server = self

            if member.id == owner_id:
                self.owner = member

            self.members.append(member)

        for presence in guild.get('presences', []):
            user_id = presence['user']['id']
            member = utils.find(lambda m: m.id == user_id, self.members)
            if member is not None:
                member.status = presence['status']
                try:
                    member.status = Status(member.status)
                except:
                    pass
                game = presence.get('game')
                member.game = game and Game(**game)

        if 'channels' in guild:
            channels = guild['channels']
            self.channels = [Channel(server=self, **c) for c in channels]

        afk_id = guild.get('afk_channel_id')
        self.afk_channel = utils.find(lambda c: c.id == afk_id, self.channels)

        for obj in guild.get('voice_states', []):
            self._update_voice_state(obj)

    @utils.cached_slot_property('_default_role')
    def default_role(self):
        """Gets the @everyone role that all members have by default."""
        return utils.find(lambda r: r.is_everyone, self.roles)

    @utils.cached_slot_property('_default_channel')
    def default_channel(self):
        """Gets the default :class:`Channel` for the server."""
        return utils.find(lambda c: c.is_default, self.channels)

    @property
    def icon_url(self):
        """Returns the URL version of the server's icon. Returns an empty string if it has no icon."""
        if self.icon is None:
            return ''
        return 'https://cdn.discordapp.com/icons/{0.id}/{0.icon}.jpg'.format(self)
