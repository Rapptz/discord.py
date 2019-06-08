# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

from .asset import Asset
from .utils import parse_time, snowflake_time
from .mixins import Hashable
from .enums import ChannelType, VerificationLevel, try_enum
from collections import namedtuple

class PartialInviteChannel(namedtuple('PartialInviteChannel', 'id name type')):
    """Represents a "partial" invite channel.

    This model will be given when the user is not part of the
    guild the :class:`Invite` resolves to.

    .. container:: operations

        .. describe:: x == y

            Checks if two partial channels are the same.

        .. describe:: x != y

            Checks if two partial channels are not the same.

        .. describe:: hash(x)

            Return the partial channel's hash.

        .. describe:: str(x)

            Returns the partial channel's name.

    Attributes
    -----------
    name: :class:`str`
        The partial channel's name.
    id: :class:`int`
        The partial channel's ID.
    type: :class:`ChannelType`
        The partial channel's type.
    """

    __slots__ = ()

    def __str__(self):
        return self.name

    @property
    def mention(self):
        """:class:`str`: The string that allows you to mention the channel."""
        return '<#%s>' % self.id

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

class PartialInviteGuild:
    """Represents a "partial" invite guild.

    This model will be given when the user is not part of the
    guild the :class:`Invite` resolves to.

    .. container:: operations

        .. describe:: x == y

            Checks if two partial guilds are the same.

        .. describe:: x != y

            Checks if two partial guilds are not the same.

        .. describe:: hash(x)

            Return the partial guild's hash.

        .. describe:: str(x)

            Returns the partial guild's name.

    Attributes
    -----------
    name: :class:`str`
        The partial guild's name.
    id: :class:`int`
        The partial guild's ID.
    verification_level: :class:`VerificationLevel`
        The partial guild's verification level.
    features: List[:class:`str`]
        A list of features the guild has. See :attr:`Guild.features` for more information.
    icon: Optional[:class:`str`]
        The partial guild's icon.
    banner: Optional[:class:`str`]
        The partial guild's banner.
    splash: Optional[:class:`str`]
        The partial guild's invite splash.
    description: Optional[:class:`str`]
        The partial guild's description.
    """

    __slots__ = ('_state', 'features', 'icon', 'banner', 'id', 'name', 'splash',
                 'verification_level', 'description')

    def __init__(self, state, data, id):
        self._state = state
        self.id = id
        self.name = data['name']
        self.features = data.get('features', [])
        self.icon = data.get('icon')
        self.banner = data.get('banner')
        self.splash = data.get('splash')
        self.verification_level = try_enum(VerificationLevel, data.get('verification_level'))
        self.description = data.get('description')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name!r} features={0.features} ' \
               'description={0.description!r}>'.format(self)

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def icon_url(self):
        """:class:`Asset`: Returns the guild's icon asset."""
        return self.icon_url_as()

    def icon_url_as(self, *, format='webp', size=1024):
        """The same operation as :meth:`Guild.icon_url_as`."""
        return Asset._from_guild_image(self._state, self.id, self.icon, 'icons', format=format, size=size)

    @property
    def banner_url(self):
        """:class:`Asset`: Returns the guild's banner asset."""
        return self.banner_url_as()

    def banner_url_as(self, *, format='webp', size=2048):
        """The same operation as :meth:`Guild.banner_url_as`."""
        return Asset._from_guild_image(self._state, self.id, self.banner, 'banners', format=format, size=size)

    @property
    def splash_url(self):
        """:class:`Asset`: Returns the guild's invite splash asset."""
        return self.splash_url_as()

    def splash_url_as(self, *, format='webp', size=2048):
        """The same operation as :meth:`Guild.splash_url_as`."""
        return Asset._from_guild_image(self._state, self.id, self.splash, 'splashes', format=format, size=size)

class Invite(Hashable):
    r"""Represents a Discord :class:`Guild` or :class:`abc.GuildChannel` invite.

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

    The following table illustrates what methods will obtain the attributes:

    +------------------------------------+----------------------------------------------------------+
    |             Attribute              |                          Method                          |
    +====================================+==========================================================+
    | :attr:`max_age`                    | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`max_uses`                   | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`created_at`                 | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`temporary`                  | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`uses`                       | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites` |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`approximate_member_count`   | :meth:`Client.fetch_invite`                              |
    +------------------------------------+----------------------------------------------------------+
    | :attr:`approximate_presence_count` | :meth:`Client.fetch_invite`                              |
    +------------------------------------+----------------------------------------------------------+

    If it's not in the table above then it is available by all methods.

    Attributes
    -----------
    max_age: :class:`int`
        How long the before the invite expires in seconds. A value of 0 indicates that it doesn't expire.
    code: :class:`str`
        The URL fragment used for the invite.
    guild: Union[:class:`Guild`, :class:`PartialInviteGuild`]
        The guild the invite is for.
    revoked: :class:`bool`
        Indicates if the invite has been revoked.
    created_at: :class:`datetime.datetime`
        A datetime object denoting the time the invite was created.
    temporary: :class:`bool`
        Indicates that the invite grants temporary membership.
        If ``True``, members who joined via this invite will be kicked upon disconnect.
    uses: :class:`int`
        How many times the invite has been used.
    max_uses: :class:`int`
        How many times the invite can be used.
    inviter: :class:`User`
        The user who created the invite.
    approximate_member_count: Optional[:class:`int`]
        The approximate number of members in the guild.
    approximate_presence_count: Optional[:class:`int`]
        The approximate number of members currently active in the guild.
        This includes idle, dnd, online, and invisible members. Offline members are excluded.
    channel: Union[:class:`abc.GuildChannel`, :class:`PartialInviteChannel`]
        The channel the invite is for.
    """

    __slots__ = ('max_age', 'code', 'guild', 'revoked', 'created_at', 'uses',
                 'temporary', 'max_uses', 'inviter', 'channel', '_state',
                 'approximate_member_count', 'approximate_presence_count' )

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
        self.approximate_presence_count = data.get('approximate_presence_count')
        self.approximate_member_count = data.get('approximate_member_count')

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
            channel_data = data['channel']
            guild_data = data['guild']
            channel_type = try_enum(ChannelType, channel_data['type'])
            channel = PartialInviteChannel(id=channel_id, name=channel_data['name'], type=channel_type)
            guild = PartialInviteGuild(state, guild_data, guild_id)
        data['guild'] = guild
        data['channel'] = channel
        return cls(state=state, data=data)

    def __str__(self):
        return self.url

    def __repr__(self):
        return '<Invite code={0.code!r} guild={0.guild!r} ' \
                'online={0.approximate_presence_count} ' \
                'members={0.approximate_member_count}>'.format(self)

    def __hash__(self):
        return hash(self.code)

    @property
    def id(self):
        """:class:`str`: Returns the proper code portion of the invite."""
        return self.code

    @property
    def url(self):
        """:class:`str`: A property that retrieves the invite URL."""
        return 'http://discord.gg/' + self.code

    async def delete(self, *, reason=None):
        """|coro|

        Revokes the instant invite.

        You must have the :attr:`~Permissions.manage_channels` permission to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
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
