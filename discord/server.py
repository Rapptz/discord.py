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

from . import utils
from .role import Role
from .member import Member
from .channel import Channel
from .enums import ServerRegion, Status

class Server:
    """Represents a Discord server.

    Attributes
    ----------
    name : str
        The server name.
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

    def __init__(self, **kwargs):
        self._from_data(kwargs)

    def _update_voice_state(self, data):
        user_id = data.get('user_id')
        member = utils.find(lambda m: m.id == user_id, self.members)
        if member is not None:
            ch_id = data.get('channel_id')
            channel = utils.find(lambda c: c.id == ch_id, self.channels)
            member.update_voice_state(voice_channel=channel, **data)
        return member

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
        self.roles = [Role(everyone=(self.id == r['id']), **r) for r in guild['roles']]
        default_role = self.get_default_role()

        self.members = []
        self.owner = guild['owner_id']

        for data in guild['members']:
            roles = [default_role]
            for role_id in data['roles']:
                role = utils.find(lambda r: r.id == role_id, self.roles)
                if role is not None:
                    roles.append(role)

            data['roles'] = roles
            member = Member(**data)
            member.server = self

            if member.id == self.owner:
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
                member.game_id = presence['game_id']

        self.channels = [Channel(server=self, **c) for c in guild['channels']]
        afk_id = guild.get('afk_channel_id')
        self.afk_channel = utils.find(lambda c: c.id == afk_id, self.channels)

        for obj in guild.get('voice_states', []):
            self._update_voice_state(obj)

    def get_default_role(self):
        """Gets the @everyone role that all members have by default."""
        return utils.find(lambda r: r.is_everyone(), self.roles)

    def get_default_channel(self):
        """Gets the default :class:`Channel` for the server."""
        return utils.find(lambda c: c.is_default_channel(), self.channels)

    def icon_url(self):
        """Returns the URL version of the server's icon. Returns an empty string if it has no icon."""
        if self.icon is None:
            return ''
        return 'https://cdn.discordapp.com/icons/{0.id}/{0.icon}.jpg'.format(self)

