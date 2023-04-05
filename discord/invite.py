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
from .utils import parse_time, snowflake_time, _get_as_snowflake, MISSING
from .object import Object
from .mixins import Hashable
from .scheduled_event import ScheduledEvent
from .enums import ChannelType, VerificationLevel, InviteTarget, InviteType, NSFWLevel, try_enum
from .welcome_screen import WelcomeScreen

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
    from .abc import GuildChannel, Snowflake
    from .channel import DMChannel, GroupChannel
    from .user import User
    from .application import PartialApplication
    from .message import Message

    InviteGuildType = Union[Guild, 'PartialInviteGuild', Object]
    InviteChannelType = Union[GuildChannel, 'PartialInviteChannel', Object, DMChannel, GroupChannel]

    import datetime


class PartialInviteChannel:
    """Represents a "partial" invite channel.

    This model will be given when the user is not part of the
    guild or group channel the :class:`Invite` resolves to.

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
    name: Optional[:class:`str`]
        The partial channel's name.
    id: :class:`int`
        The partial channel's ID.
    type: :class:`ChannelType`
        The partial channel's type.
    recipients: Optional[List[:class:`str`]]
        The partial channel's recipient names. This is only applicable to group DMs.

        .. versionadded:: 2.0
    """

    __slots__ = ('_state', 'id', 'name', 'type', 'recipients', '_icon')

    def __new__(cls, data: Optional[InviteChannelPayload], *args, **kwargs):
        if data is None:
            return
        return super().__new__(cls)

    def __init__(self, data: Optional[InviteChannelPayload], state: ConnectionState):
        if data is None:
            return
        self._state = state
        self.id: int = int(data['id'])
        self.name: Optional[str] = data.get('name')
        self.type: ChannelType = try_enum(ChannelType, data['type'])
        self.recipients: Optional[List[str]] = (
            [user['username'] for user in data.get('recipients', [])]
            if self.type in (ChannelType.private, ChannelType.group)
            else None
        )
        self._icon: Optional[str] = data.get('icon')

    def __str__(self) -> str:
        if self.name:
            return self.name

        recipients = self.recipients or []
        if self.type == ChannelType.group:
            return ', '.join(recipients) if recipients else 'Unnamed'
        return f'Direct Message with {recipients[0] if recipients else "Unknown User"}'

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

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the channel's icon asset if available.

        Only applicable to channels of type :attr:`ChannelType.group`.

        .. versionadded:: 2.0
        """
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='channel')


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

    +------------------------------------+--------------------------------------------------------------+
    |             Attribute              |                          Method                              |
    +====================================+==============================================================+
    | :attr:`max_age`                    | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`     |
    +------------------------------------+--------------------------------------------------------------+
    | :attr:`max_uses`                   | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`     |
    +------------------------------------+--------------------------------------------------------------+
    | :attr:`created_at`                 | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`     |
    +------------------------------------+--------------------------------------------------------------+
    | :attr:`temporary`                  | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`     |
    +------------------------------------+--------------------------------------------------------------+
    | :attr:`uses`                       | :meth:`abc.GuildChannel.invites`\, :meth:`Guild.invites`     |
    +------------------------------------+--------------------------------------------------------------+
    | :attr:`approximate_member_count`   | :meth:`Client.fetch_invite` with ``with_counts`` enabled     |
    +------------------------------------+--------------------------------------------------------------+
    | :attr:`approximate_presence_count` | :meth:`Client.fetch_invite` with ``with_counts`` enabled     |
    +------------------------------------+--------------------------------------------------------------+

    If it's not in the table above then it is available by all methods.

    Attributes
    -----------
    max_age: Optional[:class:`int`]
        How long before the invite expires in seconds.
        A value of ``0`` indicates that it doesn't expire.
    code: :class:`str`
        The URL fragment used for the invite.
    type: :class:`InviteType`
        The type of invite.

        .. versionadded:: 2.0
    guild: Optional[Union[:class:`Guild`, :class:`Object`, :class:`PartialInviteGuild`]]
        The guild the invite is for. Can be ``None`` if not a guild invite.
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
        The expiration date of the invite. If the value is ``None`` (unless received through
        :meth:`Client.fetch_invite` with ``with_expiration`` disabled), the invite will never expire.

        .. versionadded:: 2.0
    channel: Optional[Union[:class:`abc.GuildChannel`, :class:`GroupChannel`, :class:`Object`, :class:`PartialInviteChannel`]]
        The channel the invite is for. Can be ``None`` if not a guild invite.
    target_type: :class:`InviteTarget`
        The type of target for the voice channel invite.

        .. versionadded:: 2.0
    target_user: Optional[:class:`User`]
        The user whose stream to display for this invite, if any.

        .. versionadded:: 2.0
    target_application: Optional[:class:`PartialApplication`]
        The embedded application the invite targets, if any.

        .. versionadded:: 2.0
    scheduled_event: Optional[:class:`ScheduledEvent`]
        The scheduled event associated with this invite, if any.

        .. versionadded:: 2.0
    scheduled_event_id: Optional[:class:`int`]
        The ID of the scheduled event associated with this invite, if any.

        .. versionadded:: 2.0
    welcome_screen: Optional[:class:`WelcomeScreen`]
        The guild's welcome screen, if available.

        .. versionadded:: 2.0
    new_member: :class:`bool`
        Whether the user was not previously a member of the guild.

        .. versionadded:: 2.0

        .. note::
            This is only possibly ``True`` in accepted invite objects
            (i.e. the objects received from :meth:`accept` and :meth:`use`).
    show_verification_form: :class:`bool`
        Whether the user should be shown the guild's member verification form.

        .. versionadded:: 2.0

        .. note::
            This is only possibly ``True`` in accepted invite objects
            (i.e. the objects received from :meth:`accept` and :meth:`use`).
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
        '_message',
        'welcome_screen',
        'type',
        'new_member',
        'show_verification_form',
    )

    BASE = 'https://discord.gg'

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: InvitePayload,
        guild: Optional[Union[PartialInviteGuild, Guild]] = None,
        channel: Optional[Union[PartialInviteChannel, GuildChannel, GroupChannel]] = None,
        welcome_screen: Optional[WelcomeScreen] = None,
    ):
        self._state: ConnectionState = state
        self.type: InviteType = try_enum(InviteType, data.get('type', 0))
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
        self._message: Optional[Message] = data.get('message')

        # We inject some missing data here since we can assume it
        if self.type in (InviteType.group_dm, InviteType.friend):
            self.temporary = False
            if self.max_uses is None and self.type is InviteType.group_dm:
                self.max_uses = 0

        expires_at = data.get('expires_at', None)
        self.expires_at: Optional[datetime.datetime] = parse_time(expires_at) if expires_at else None

        inviter_data = data.get('inviter')
        self.inviter: Optional[User] = None if inviter_data is None else self._state.create_user(inviter_data)

        self.channel: Optional[InviteChannelType] = self._resolve_channel(data.get('channel'), channel)

        target_user_data = data.get('target_user')
        self.target_user: Optional[User] = None if target_user_data is None else self._state.create_user(target_user_data)

        self.target_type: InviteTarget = try_enum(InviteTarget, data.get("target_type", 0))

        application = data.get('target_application')
        if application is not None:
            from .application import PartialApplication

            application = PartialApplication(data=application, state=state)
        self.target_application: Optional[PartialApplication] = application

        self.welcome_screen = welcome_screen

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

        # Only present on accepted invites
        self.new_member: bool = data.get('new_member', False)
        self.show_verification_form: bool = data.get('show_verification_form', False)

    @classmethod
    def from_incomplete(cls, *, state: ConnectionState, data: InvitePayload, message: Optional[Message] = None) -> Self:
        guild: Optional[Union[Guild, PartialInviteGuild]]
        try:
            guild_data = data['guild']
        except KeyError:
            # If we're here, then this is a group DM
            guild = None
            welcome_screen = None
        else:
            guild_id = int(guild_data['id'])
            guild = state._get_guild(guild_id)
            if guild is None:
                guild = PartialInviteGuild(state, guild_data, guild_id)

            welcome_screen = guild_data.get('welcome_screen')
            if welcome_screen is not None:
                welcome_screen = WelcomeScreen(data=welcome_screen, guild=guild)

        channel_data = data.get('channel')
        if channel_data and channel_data.get('type') == ChannelType.private.value:
            channel_data['recipients'] = [data['inviter']] if 'inviter' in data else []
        channel = PartialInviteChannel(channel_data, state)
        channel = state.get_channel(getattr(channel, 'id', None)) or channel

        if message is not None:
            data['message'] = message  # type: ignore # Not a real field

        return cls(state=state, data=data, guild=guild, channel=channel, welcome_screen=welcome_screen)  # type: ignore

    @classmethod
    def from_gateway(cls, *, state: ConnectionState, data: GatewayInvitePayload) -> Self:
        guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        guild: Optional[Union[Guild, Object]] = state._get_guild(guild_id)
        channel_id = _get_as_snowflake(data, 'channel_id')
        if guild is not None:
            channel = (guild.get_channel(channel_id) or Object(id=channel_id)) if channel_id is not None else None
        else:
            guild = state._get_or_create_unavailable_guild(guild_id) if guild_id is not None else None
            channel = Object(id=channel_id) if channel_id is not None else None

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
        channel: Optional[Union[PartialInviteChannel, GuildChannel, GroupChannel]] = None,
    ) -> Optional[InviteChannelType]:
        if channel is not None:
            return channel

        if data is None:
            return None

        return PartialInviteChannel(data, self._state)

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return (
            f'<Invite code={self.code!r} type={self.type!r} '
            f'guild={self.guild!r} '
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

    async def use(self) -> Invite:
        """|coro|

        Uses the invite.
        Either joins a guild, joins a group DM, or adds a friend.

        There is an alias for this called :func:`accept`.

        .. versionadded:: 1.9

        Raises
        ------
        HTTPException
            Using the invite failed.

        Returns
        -------
        :class:`Invite`
            The accepted invite.
        """
        state = self._state
        type = self.type
        if message := self._message:
            kwargs = {'message': message}
        else:
            kwargs = {
                'guild_id': getattr(self.guild, 'id', MISSING),
                'channel_id': getattr(self.channel, 'id', MISSING),
                'channel_type': getattr(self.channel, 'type', MISSING),
            }
        data = await state.http.accept_invite(self.code, type, **kwargs)
        return Invite.from_incomplete(state=state, data=data, message=message)

    async def accept(self) -> Invite:
        """|coro|

        Uses the invite.
        Either joins a guild, joins a group DM, or adds a friend.

        This is an alias of :func:`use`.

        .. versionadded:: 1.9

        Raises
        ------
        HTTPException
            Using the invite failed.

        Returns
        -------
        :class:`Invite`
            The accepted invite.
        """
        return await self.use()

    async def delete(self, *, reason: Optional[str] = None) -> Invite:
        """|coro|

        Revokes the instant invite.

        In a guild context, you must have :attr:`~Permissions.manage_channels` to do this.

        .. versionchanged:: 2.0

            The function now returns the deleted invite.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this invite. Shows up on the audit log.

            Only applicable to guild invites.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke invites.
        NotFound
            The invite is invalid or expired.
        HTTPException
            Revoking the invite failed.

        Returns
        --------
        :class:`Invite`
            The deleted invite.
        """
        state = self._state
        data = await state.http.delete_invite(self.code, reason=reason)
        return Invite.from_incomplete(state=state, data=data)
