"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from __future__ import annotations

from typing import List, Optional, Union, TYPE_CHECKING
from .asset import Asset
from .utils import parse_time, snowflake_time, _get_as_snowflake
from .object import Object
from .mixins import Hashable
from .enums import ChannelType, NSFWLevel, VerificationLevel, InviteTarget, try_enum
from .appinfo import PartialAppInfo
from .scheduled_event import ScheduledEvent

__all__ = (
    'PartialInviteChannel',
    'PartialInviteGuild',
    'Invite',
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.invite import (
        Invite as InvitePayload,
        InviteGuild as InviteGuildPayload,
        GatewayInvite as GatewayInvitePayload,
    )
    from .types.channel import (
        PartialChannel as InviteChannelPayload,
    )
    from .state import ConnectionState
    from .guild import Guild
    from .abc import GuildChannel
    from .user import User
    from .abc import Snowflake

    InviteGuildType = Union[Guild, 'PartialInviteGuild', Object]
    InviteChannelType = Union[GuildChannel, 'PartialInviteChannel', Object]

    import datetime


class PartialInviteChannel:
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

    __slots__ = ('id', 'name', 'type')

    def __init__(self, data: InviteChannelPayload):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.type: ChannelType = try_enum(ChannelType, data['type'])

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<PartialInviteChannel id={self.id} name={self.name} type={self.type!r}>'

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def created_at(self) -> datetime.datetime:
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
    description: Optional[:class:`str`]
        The partial guild's description.
    nsfw_level: :class:`NSFWLevel`
        The partial guild's NSFW level.

        .. versionadded:: 2.0
    vanity_url_code: Optional[:class:`str`]
        The partial guild's vanity URL code, if available.

        .. versionadded:: 2.0
    premium_subscription_count: :class:`int`
        The number of "boosts" the partial guild currently has.

        .. versionadded:: 2.0
    """

    __slots__ = (
        '_state',
        '_icon',
        '_banner',
        '_splash',
        'features',
        'id',
        'name',
        'verification_level',
        'description',
        'vanity_url_code',
        'nsfw_level',
        'premium_subscription_count',
    )

    def __init__(self, state: ConnectionState, data: InviteGuildPayload, id: int):
        self._state: ConnectionState = state
        self.id: int = id
        self.name: str = data['name']
        self.features: List[str] = data.get('features', [])
        self._icon: Optional[str] = data.get('icon')
        self._banner: Optional[str] = data.get('banner')
        self._splash: Optional[str] = data.get('splash')
        self.verification_level: VerificationLevel = try_enum(VerificationLevel, data.get('verification_level'))
        self.description: Optional[str] = data.get('description')
        self.vanity_url_code: Optional[str] = data.get('vanity_url_code')
        self.nsfw_level: NSFWLevel = try_enum(NSFWLevel, data.get('nsfw_level', 0))
        self.premium_subscription_count: int = data.get('premium_subscription_count') or 0

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} features={self.features} '
            f'description={self.description!r}>'
        )

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def vanity_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The Discord vanity invite URL for this partial guild, if available.

        .. versionadded:: 2.0
        """
        if self.vanity_url_code is None:
            return None
        return f'{Invite.BASE}/{self.vanity_url_code}'

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's icon asset, if available."""
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's banner asset, if available."""
        if self._banner is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._banner, path='banners')

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's invite splash asset, if available."""
        if self._splash is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._splash, path='splashes')


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

    +------------------------------------+------------------------------------------------------------+
    |             Attribute              |                          Method                            |
    +====================================+============================================================+
    | :attr:`max_age`                    | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`   |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`max_uses`                   | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`   |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`created_at`                 | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`   |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`temporary`                  | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`   |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`uses`                       | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`   |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`approximate_member_count`   | :meth:`Client.fetch_invite` with `with_counts` enabled     |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`approximate_presence_count` | :meth:`Client.fetch_invite` with `with_counts` enabled     |
    +------------------------------------+------------------------------------------------------------+
    | :attr:`expires_at`                 | :meth:`Client.fetch_invite` with `with_expiration` enabled |
    +------------------------------------+------------------------------------------------------------+

    If it's not in the table above then it is available by all methods.

    Attributes
    -----------
    max_age: Optional[:class:`int`]
        How long before the invite expires in seconds.
        A value of ``0`` indicates that it doesn't expire.
    code: :class:`str`
        The URL fragment used for the invite.
    guild: Optional[Union[:class:`Guild`, :class:`Object`, :class:`PartialInviteGuild`]]
        The guild the invite is for. Can be ``None`` if it's from a group direct message.
    revoked: Optional[:class:`bool`]
        Indicates if the invite has been revoked.
    created_at: Optional[:class:`datetime.datetime`]
        An aware UTC datetime object denoting the time the invite was created.
    temporary: Optional[:class:`bool`]
        Indicates that the invite grants temporary membership.
        If ``True``, members who joined via this invite will be kicked upon disconnect.
    uses: Optional[:class:`int`]
        How many times the invite has been used.
    max_uses: Optional[:class:`int`]
        How many times the invite can be used.
        A value of ``0`` indicates that it has unlimited uses.
    inviter: Optional[:class:`User`]
        The user who created the invite.
    approximate_member_count: Optional[:class:`int`]
        The approximate number of members in the guild.
    approximate_presence_count: Optional[:class:`int`]
        The approximate number of members currently active in the guild.
        This includes idle, dnd, online, and invisible members. Offline members are excluded.
    expires_at: Optional[:class:`datetime.datetime`]
        The expiration date of the invite. If the value is ``None`` when received through
        `Client.fetch_invite` with `with_expiration` enabled, the invite will never expire.

        .. versionadded:: 2.0

    channel: Optional[Union[:class:`abc.GuildChannel`, :class:`Object`, :class:`PartialInviteChannel`]]
        The channel the invite is for.
    target_type: :class:`InviteTarget`
        The type of target for the voice channel invite.

        .. versionadded:: 2.0

    target_user: Optional[:class:`User`]
        The user whose stream to display for this invite, if any.

        .. versionadded:: 2.0

    target_application: Optional[:class:`PartialAppInfo`]
        The embedded application the invite targets, if any.

        .. versionadded:: 2.0
    scheduled_event: Optional[:class:`ScheduledEvent`]
        The scheduled event associated with this invite, if any.

        .. versionadded:: 2.0
    scheduled_event_id: Optional[:class:`int`]
        The ID of the scheduled event associated with this invite, if any.

        .. versionadded:: 2.0
    """

    __slots__ = (
        'max_age',
        'code',
        'guild',
        'revoked',
        'created_at',
        'uses',
        'temporary',
        'max_uses',
        'inviter',
        'channel',
        'target_user',
        'target_type',
        '_state',
        'approximate_member_count',
        'approximate_presence_count',
        'target_application',
        'expires_at',
        'scheduled_event',
        'scheduled_event_id',
    )

    BASE = 'https://discord.gg'

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: InvitePayload,
        guild: Optional[Union[PartialInviteGuild, Guild]] = None,
        channel: Optional[Union[PartialInviteChannel, GuildChannel]] = None,
    ):
        self._state: ConnectionState = state
        self.max_age: Optional[int] = data.get('max_age')
        self.code: str = data['code']
        self.guild: Optional[InviteGuildType] = self._resolve_guild(data.get('guild'), guild)
        self.revoked: Optional[bool] = data.get('revoked')
        self.created_at: Optional[datetime.datetime] = parse_time(data.get('created_at'))
        self.temporary: Optional[bool] = data.get('temporary')
        self.uses: Optional[int] = data.get('uses')
        self.max_uses: Optional[int] = data.get('max_uses')
        self.approximate_presence_count: Optional[int] = data.get('approximate_presence_count')
        self.approximate_member_count: Optional[int] = data.get('approximate_member_count')

        expires_at = data.get('expires_at', None)
        self.expires_at: Optional[datetime.datetime] = parse_time(expires_at) if expires_at else None

        inviter_data = data.get('inviter')
        self.inviter: Optional[User] = None if inviter_data is None else self._state.create_user(inviter_data)

        self.channel: Optional[InviteChannelType] = self._resolve_channel(data.get('channel'), channel)

        target_user_data = data.get('target_user')
        self.target_user: Optional[User] = None if target_user_data is None else self._state.create_user(target_user_data)

        self.target_type: InviteTarget = try_enum(InviteTarget, data.get("target_type", 0))

        application = data.get('target_application')
        self.target_application: Optional[PartialAppInfo] = (
            PartialAppInfo(data=application, state=state) if application else None
        )

        scheduled_event = data.get('guild_scheduled_event')
        self.scheduled_event: Optional[ScheduledEvent] = (
            ScheduledEvent(
                state=self._state,
                data=scheduled_event,
            )
            if scheduled_event
            else None
        )
        self.scheduled_event_id: Optional[int] = self.scheduled_event.id if self.scheduled_event else None

    @classmethod
    def from_incomplete(cls, *, state: ConnectionState, data: InvitePayload) -> Self:
        guild: Optional[Union[Guild, PartialInviteGuild]]
        try:
            guild_data = data['guild']
        except KeyError:
            # If we're here, then this is a group DM
            guild = None
        else:
            guild_id = int(guild_data['id'])
            guild = state._get_guild(guild_id)
            if guild is None:
                # If it's not cached, then it has to be a partial guild
                guild = PartialInviteGuild(state, guild_data, guild_id)

        # As far as I know, invites always need a channel
        # So this should never raise.
        channel: Union[PartialInviteChannel, GuildChannel] = PartialInviteChannel(data['channel'])
        if guild is not None and not isinstance(guild, PartialInviteGuild):
            # Upgrade the partial data if applicable
            channel = guild.get_channel(channel.id) or channel

        return cls(state=state, data=data, guild=guild, channel=channel)

    @classmethod
    def from_gateway(cls, *, state: ConnectionState, data: GatewayInvitePayload) -> Self:
        guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        guild: Optional[Union[Guild, Object]] = state._get_guild(guild_id)
        channel_id = int(data['channel_id'])
        if guild is not None:
            channel = guild.get_channel(channel_id) or Object(id=channel_id)
        else:
            guild = state._get_or_create_unavailable_guild(guild_id) if guild_id is not None else None
            channel = Object(id=channel_id)

        return cls(state=state, data=data, guild=guild, channel=channel)  # type: ignore

    def _resolve_guild(
        self,
        data: Optional[InviteGuildPayload],
        guild: Optional[Union[Guild, PartialInviteGuild]] = None,
    ) -> Optional[InviteGuildType]:
        if guild is not None:
            return guild

        if data is None:
            return None

        guild_id = int(data['id'])
        return PartialInviteGuild(self._state, data, guild_id)

    def _resolve_channel(
        self,
        data: Optional[InviteChannelPayload],
        channel: Optional[Union[PartialInviteChannel, GuildChannel]] = None,
    ) -> Optional[InviteChannelType]:
        if channel is not None:
            return channel

        if data is None:
            return None

        return PartialInviteChannel(data)

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return (
            f'<Invite code={self.code!r} guild={self.guild!r} '
            f'online={self.approximate_presence_count} '
            f'members={self.approximate_member_count}>'
        )

    def __hash__(self) -> int:
        return hash(self.code)

    @property
    def id(self) -> str:
        """:class:`str`: Returns the proper code portion of the invite."""
        return self.code

    @property
    def url(self) -> str:
        """:class:`str`: A property that retrieves the invite URL."""
        url = self.BASE + '/' + self.code
        if self.scheduled_event_id is not None:
            url += '?event=' + str(self.scheduled_event_id)
        return url

    def set_scheduled_event(self, scheduled_event: Snowflake, /) -> Self:
        """Sets the scheduled event for this invite.

        .. versionadded:: 2.0

        Parameters
        ----------
        scheduled_event: :class:`~discord.abc.Snowflake`
            The ID of the scheduled event.

        Returns
        --------
        :class:`Invite`
            The invite with the new scheduled event.
        """
        self.scheduled_event_id = scheduled_event.id
        try:
            self.scheduled_event = self.guild.get_scheduled_event(scheduled_event.id)  # type: ignore # handled below
        except AttributeError:
            self.scheduled_event = None

        return self

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Revokes the instant invite.

        You must have :attr:`~Permissions.manage_channels` to do this.

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
