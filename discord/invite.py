# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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

from .utils import parse_time
from .mixins import Hashable
from .object import Object

class Invite(Hashable):
    """Represents a Discord :class:`Guild` or :class:`abc.GuildChannel` invite.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two invites are equal.

        .. describe:: x != y

            Checks if two invites are not equal.

        .. describe:: hash(x)

            Returns the invite hash.

        .. describe:: str(x)

            Returns the invite URL.

    Attributes
    -----------
    max_age: :class:`int`
        How long the before the invite expires in seconds. A value of 0 indicates that it doesn't expire.
    code: :class:`str`
        The URL fragment used for the invite.
    guild: :class:`Guild`
        The guild the invite is for.
    revoked: :class:`bool`
        Indicates if the invite has been revoked.
    created_at: `datetime.datetime`
        A datetime object denoting the time the invite was created.
    temporary: :class:`bool`
        Indicates that the invite grants temporary membership.
        If True, members who joined via this invite will be kicked upon disconnect.
    uses: :class:`int`
        How many times the invite has been used.
    max_uses: :class:`int`
        How many times the invite can be used.
    inviter: :class:`User`
        The user who created the invite.
    channel: :class:`abc.GuildChannel`
        The channel the invite is for.
    """


    __slots__ = ('max_age', 'code', 'guild', 'revoked', 'created_at', 'uses',
                 'temporary', 'max_uses', 'inviter', 'channel', '_state')

    def __init__(self, *, state, data):
        self._state = state
        self.max_age = data.get('max_age')
        self.code = data.get('code')
        self.guild = data.get('guild')
        self.revoked = data.get('revoked')
        self.created_at = parse_time(data.get('created_at'))
        self.temporary = data.get('temporary')
        self.uses = data.get('uses')
        self.max_uses = data.get('max_uses')

        inviter_data = data.get('inviter')
        self.inviter = None if inviter_data is None else self._state.store_user(inviter_data)
        self.channel = data.get('channel')

    @classmethod
    def from_incomplete(cls, *, state, data):
        guild_id = int(data['guild']['id'])
        channel_id = int(data['channel']['id'])
        guild = state._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
        else:
            guild = Object(id=guild_id)
            channel = Object(id=channel_id)
            guild.name = data['guild']['name']

            guild.splash = data['guild']['splash']
            guild.splash_url = ''
            if guild.splash:
                guild.splash_url = 'https://cdn.discordapp.com/splashes/{0.id}/{0.splash}.jpg?size=2048'.format(guild)

            channel.name = data['channel']['name']

        data['guild'] = guild
        data['channel'] = channel
        return cls(state=state, data=data)

    def __str__(self):
        return self.url

    def __repr__(self):
        return '<Invite code={0.code!r}>'.format(self)

    def __hash__(self):
        return hash(self.code)

    @property
    def id(self):
        """Returns the proper code portion of the invite."""
        return self.code

    @property
    def url(self):
        """A property that retrieves the invite URL."""
        return 'http://discord.gg/' + self.code

    async def delete(self, *, reason=None):
        """|coro|

        Revokes the instant invite.

        You must have the :attr:`~Permissions.manage_channels` permission to do this.

        Parameters
        -----------
        reason: Optional[str]
            The reason for deleting this invite. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke invites.
        NotFound
            The invite is invalid or expired.
        HTTPException
            Revoking the invite failed.
        """

        await self._state.http.delete_invite(self.code, reason=reason)
