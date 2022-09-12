"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, overload

from .activity import create_settings_activity
from .enums import (
    FriendFlags,
    HighlightLevel,
    Locale,
    NotificationLevel,
    Status,
    StickerAnimationOptions,
    Theme,
    UserContentFilter,
    try_enum,
)
from .guild_folder import GuildFolder
from .object import Object
from .utils import MISSING, _get_as_snowflake, parse_time, utcnow, find

if TYPE_CHECKING:
    from .abc import GuildChannel, PrivateChannel
    from .activity import CustomActivity
    from .guild import Guild
    from .state import ConnectionState
    from .user import ClientUser

__all__ = (
    'ChannelSettings',
    'GuildSettings',
    'UserSettings',
    'TrackingSettings',
    'EmailSettings',
    'MuteConfig',
)


class UserSettings:
    """Represents the Discord client settings.

    .. versionadded:: 1.9

    Attributes
    ----------
    afk_timeout: :class:`int`
        How long (in seconds) the user needs to be AFK until Discord
        sends push notifications to your mobile device.
    allow_accessibility_detection: :class:`bool`
        Whether or not to allow Discord to track screen reader usage.
    animate_emojis: :class:`bool`
        Whether or not to animate emojis in the chat.
    contact_sync_enabled: :class:`bool`
        Whether or not to enable the contact sync on Discord mobile.
    convert_emoticons: :class:`bool`
        Whether or not to automatically convert emoticons into emojis.
        e.g. :-) -> 😃
    default_guilds_restricted: :class:`bool`
        Whether or not to automatically disable DMs between you and
        members of new guilds you join.
    detect_platform_accounts: :class:`bool`
        Whether or not to automatically detect accounts from services
        like Steam and Blizzard when you open the Discord client.
    developer_mode: :class:`bool`
        Whether or not to enable developer mode.
    disable_games_tab: :class:`bool`
        Whether or not to disable the showing of the Games tab.
    enable_tts_command: :class:`bool`
        Whether or not to allow tts messages to be played/sent.
    gif_auto_play: :class:`bool`
        Whether or not to automatically play gifs that are in the chat.
    inline_attachment_media: :class:`bool`
        Whether or not to display attachments when they are uploaded in chat.
    inline_embed_media: :class:`bool`
        Whether or not to display videos and images from links posted in chat.
    message_display_compact: :class:`bool`
        Whether or not to use the compact Discord display mode.
        native_phone_integration_enabled: :class:`bool`
        Whether or not to enable the new Discord mobile phone number friend
        requesting features.
    render_embeds: :class:`bool`
        Whether or not to render embeds that are sent in the chat.
    render_reactions: :class:`bool`
        Whether or not to render reactions that are added to messages.
    show_current_game: :class:`bool`
        Whether or not to display the game that you are currently playing.
    stream_notifications_enabled: :class:`bool`
        Whether stream notifications for friends will be received.
    timezone_offset: :class:`int`
        The timezone offset to use.
    view_nsfw_commands: :class:`bool`
        Whether or not to show NSFW application commands.

        .. versionadded:: 2.0
    view_nsfw_guilds: :class:`bool`
        Whether or not to show NSFW guilds on iOS.
    """

    if TYPE_CHECKING:  # Fuck me
        afk_timeout: int
        allow_accessibility_detection: bool
        animate_emojis: bool
        contact_sync_enabled: bool
        convert_emoticons: bool
        default_guilds_restricted: bool
        detect_platform_accounts: bool
        developer_mode: bool
        disable_games_tab: bool
        enable_tts_command: bool
        gif_auto_play: bool
        inline_attachment_media: bool
        inline_embed_media: bool
        message_display_compact: bool
        native_phone_integration_enabled: bool
        render_embeds: bool
        render_reactions: bool
        show_current_game: bool
        stream_notifications_enabled: bool
        timezone_offset: int
        view_nsfw_commands: bool
        view_nsfw_guilds: bool

    def __init__(self, *, data, state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return '<Settings>'

    def _get_guild(self, id: int) -> Guild:
        return self._state._get_guild(int(id)) or Object(id=int(id))  # type: ignore # Lying for better developer UX

    def _update(self, data: Dict[str, Any]) -> None:
        RAW_VALUES = {
            'afk_timeout',
            'allow_accessibility_detection',
            'animate_emojis',
            'contact_sync_enabled',
            'convert_emoticons',
            'default_guilds_restricted',
            'detect_platform_accounts',
            'developer_mode',
            'disable_games_tab',
            'enable_tts_command',
            'gif_auto_play',
            'inline_attachment_media',
            'inline_embed_media',
            'message_display_compact',
            'native_phone_integration_enabled',
            'render_embeds',
            'render_reactions',
            'show_current_game',
            'stream_notifications_enabled',
            'timezone_offset',
            'view_nsfw_commands',
            'view_nsfw_guilds',
        }

        for key, value in data.items():
            if key in RAW_VALUES:
                setattr(self, key, value)
            else:
                setattr(self, '_' + key, value)

    async def edit(self, **kwargs) -> UserSettings:
        """|coro|

        Edits the client user's settings.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited settings are returned.

        Parameters
        ----------
        activity_restricted_guilds: List[:class:`abc.Snowflake`]
            A list of guilds that your current activity will not be shown in.

            .. versionadded:: 2.0
        activity_joining_restricted_guilds: List[:class:`abc.Snowflake`]
            A list of guilds that will not be able to join your current activity.

            .. versionadded:: 2.0
        afk_timeout: :class:`int`
            How long (in seconds) the user needs to be AFK until Discord
            sends push notifications to your mobile device.
        allow_accessibility_detection: :class:`bool`
            Whether or not to allow Discord to track screen reader usage.
        animate_emojis: :class:`bool`
            Whether or not to animate emojis in the chat.
        animate_stickers: :class:`StickerAnimationOptions`
            Whether or not to animate stickers in the chat.
        contact_sync_enabled: :class:`bool`
            Whether or not to enable the contact sync on Discord mobile.
        convert_emoticons: :class:`bool`
            Whether or not to automatically convert emoticons into emojis.
            e.g. :-) -> 😃
        default_guilds_restricted: :class:`bool`
            Whether or not to automatically disable DMs between you and
            members of new guilds you join.
        detect_platform_accounts: :class:`bool`
            Whether or not to automatically detect accounts from services
            like Steam and Blizzard when you open the Discord client.
        developer_mode: :class:`bool`
            Whether or not to enable developer mode.
        disable_games_tab: :class:`bool`
            Whether or not to disable the showing of the Games tab.
        enable_tts_command: :class:`bool`
            Whether or not to allow tts messages to be played/sent.
        explicit_content_filter: :class:`UserContentFilter`
            The filter for explicit content in all messages.
        friend_source_flags: :class:`FriendFlags`
            Who can add you as a friend.
        gif_auto_play: :class:`bool`
            Whether or not to automatically play gifs that are in the chat.
        guild_positions: List[:class:`abc.Snowflake`]
            A list of guilds in order of the guild/guild icons that are on
            the left hand side of the UI.
        inline_attachment_media: :class:`bool`
            Whether or not to display attachments when they are uploaded in chat.
        inline_embed_media: :class:`bool`
            Whether or not to display videos and images from links posted in chat.
        locale: :class:`Locale`
            The :rfc:`3066` language identifier of the locale to use for the language
            of the Discord client.
        message_display_compact: :class:`bool`
            Whether or not to use the compact Discord display mode.
        native_phone_integration_enabled: :class:`bool`
            Whether or not to enable the new Discord mobile phone number friend
            requesting features.
        passwordless: :class:`bool`
            Whether the account is passwordless.
        render_embeds: :class:`bool`
            Whether or not to render embeds that are sent in the chat.
        render_reactions: :class:`bool`
            Whether or not to render reactions that are added to messages.
        restricted_guilds: List[:class:`abc.Snowflake`]
            A list of guilds that you will not receive DMs from.
        show_current_game: :class:`bool`
            Whether or not to display the game that you are currently playing.
        stream_notifications_enabled: :class:`bool`
            Whether stream notifications for friends will be received.
        theme: :class:`Theme`
            The theme of the Discord UI.
        timezone_offset: :class:`int`
            The timezone offset to use.
        view_nsfw_commands: :class:`bool`
            Whether or not to show NSFW application commands.

            .. versionadded:: 2.0
        view_nsfw_guilds: :class:`bool`
            Whether or not to show NSFW guilds on iOS.

        Raises
        -------
        HTTPException
            Editing the settings failed.

        Returns
        -------
        :class:`.UserSettings`
            The client user's updated settings.
        """
        return await self._state.user.edit_settings(**kwargs)  # type: ignore

    async def email_settings(self) -> EmailSettings:
        """|coro|

        Retrieves your :class:`EmailSettings`.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Getting the email settings failed.

        Returns
        -------
        :class:`.EmailSettings`
            The email settings.
        """
        data = await self._state.http.get_email_settings()
        return EmailSettings(data=data, state=self._state)

    async def fetch_tracking_settings(self) -> TrackingSettings:
        """|coro|

        Retrieves your :class:`TrackingSettings`.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the tracking settings failed.

        Returns
        -------
        :class:`Tracking`
            The tracking settings.
        """
        data = await self._state.http.get_tracking()
        return TrackingSettings(state=self._state, data=data)

    @property
    def tracking_settings(self) -> Optional[TrackingSettings]:
        """Optional[:class:`TrackingSettings`]: Returns your tracking settings if available.

        .. versionadded:: 2.0
        """
        return self._state.consents

    @property
    def activity_restricted_guilds(self) -> List[Guild]:
        """List[:class:`abc.Snowflake`]: A list of guilds that your current activity will not be shown in.

        .. versionadded:: 2.0
        """
        return list(map(self._get_guild, getattr(self, '_activity_restricted_guild_ids', [])))

    @property
    def activity_joining_restricted_guilds(self) -> List[Guild]:
        """List[:class:`abc.Snowflake`]: A list of guilds that will not be able to join your current activity.

        .. versionadded:: 2.0
        """
        return list(map(self._get_guild, getattr(self, '_activity_joining_restricted_guild_ids', [])))

    @property
    def animate_stickers(self) -> StickerAnimationOptions:
        """:class:`StickerAnimationOptions`: Whether or not to animate stickers in the chat."""
        return try_enum(StickerAnimationOptions, getattr(self, '_animate_stickers', 0))

    @property
    def custom_activity(self) -> Optional[CustomActivity]:
        """Optional[:class:`CustomActivity`]: The set custom activity."""
        return create_settings_activity(data=getattr(self, '_custom_status', None), state=self._state)

    @property
    def explicit_content_filter(self) -> UserContentFilter:
        """:class:`UserContentFilter`: The filter for explicit content in all messages."""
        return try_enum(UserContentFilter, getattr(self, '_explicit_content_filter', 0))

    @property
    def friend_source_flags(self) -> FriendFlags:
        """:class:`FriendFlags`: Who can add you as a friend."""
        return FriendFlags._from_dict(getattr(self, '_friend_source_flags', {'all': True}))

    @property
    def guild_folders(self) -> List[GuildFolder]:
        """List[:class:`GuildFolder`]: A list of guild folders."""
        state = self._state
        return [GuildFolder(data=folder, state=state) for folder in getattr(self, '_guild_folders', [])]

    @property
    def guild_positions(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds in order of the guild/guild icons that are on the left hand side of the UI."""
        return list(map(self._get_guild, getattr(self, '_guild_positions', [])))

    @property
    def locale(self) -> Locale:
        """:class:`Locale`: The :rfc:`3066` language identifier
        of the locale to use for the language of the Discord client.

        .. versionchanged:: 2.0
            This now returns a :class:`Locale` object instead of a string.
        """
        return try_enum(Locale, getattr(self, '_locale', 'en-US'))

    @property
    def passwordless(self) -> bool:
        """:class:`bool`: Whether the account is passwordless."""
        return getattr(self, '_passwordless', False)

    @property
    def restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that you will not receive DMs from."""
        return list(filter(None, map(self._get_guild, getattr(self, '_restricted_guilds', []))))

    @property
    def status(self) -> Status:
        """Optional[:class:`Status`]: The configured status."""
        return try_enum(Status, getattr(self, '_status', 'online'))

    @property
    def theme(self) -> Theme:
        """:class:`Theme`: The theme of the Discord UI."""
        return try_enum(Theme, getattr(self, '_theme', 'dark'))  # Sane default :)


class MuteConfig:
    """An object representing an object's mute status.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two items are muted.

        .. describe:: x != y

            Checks if two items are not muted.

        .. describe:: str(x)

            Returns the mute status as a string.

        .. describe:: int(x)

            Returns the mute status as an int.

    Attributes
    ----------
    muted: :class:`bool`
        Indicates if the object is muted.
    until: Optional[:class:`datetime.datetime`]
        When the mute will expire.
    """

    def __init__(self, muted: bool, config: Dict[str, str]) -> None:
        until = parse_time(config.get('end_time'))
        if until is not None:
            if until <= utcnow():
                muted = False
                until = None

        self.muted: bool = muted
        self.until: Optional[datetime] = until

    def __repr__(self) -> str:
        return str(self.muted)

    def __int__(self) -> int:
        return int(self.muted)

    def __bool__(self) -> bool:
        return self.muted

    def __eq__(self, other: object) -> bool:
        return self.muted == bool(other)

    def __ne__(self, other: object) -> bool:
        return not self.muted == bool(other)


class ChannelSettings:
    """Represents a channel's notification settings.

    .. versionadded:: 2.0

    Attributes
    ----------
    level: :class:`NotificationLevel`
        The notification level for the channel.
    muted: :class:`MuteConfig`
        The mute configuration for the channel.
    collapsed: :class:`bool`
        Whether the channel is collapsed.
        Only applicable to channels of type :attr:`ChannelType.category`.
    """

    if TYPE_CHECKING:
        _channel_id: int
        level: NotificationLevel
        muted: MuteConfig
        collapsed: bool

    def __init__(self, guild_id: Optional[int] = None, *, data: Dict[str, Any], state: ConnectionState) -> None:
        self._guild_id = guild_id
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<ChannelSettings channel={self.channel} level={self.level} muted={self.muted} collapsed={self.collapsed}>'

    def _update(self, data: Dict[str, Any]) -> None:
        # We consider everything optional because this class can be constructed with no data
        # to represent the default settings
        self._channel_id = int(data['channel_id'])
        self.collapsed = data.get('collapsed', False)

        self.level = try_enum(NotificationLevel, data.get('message_notifications', 3))
        self.muted = MuteConfig(data.get('muted', False), data.get('mute_config') or {})

    @property
    def channel(self) -> Union[GuildChannel, PrivateChannel]:
        """Union[:class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`]: Returns the channel these settings are for."""
        guild = self._state._get_guild(self._guild_id)
        if guild:
            channel = guild.get_channel(self._channel_id)
        else:
            channel = self._state._get_private_channel(self._channel_id)
        if not channel:
            channel = Object(id=self._channel_id)
        return channel  # type: ignore # Lying for better developer UX

    async def edit(
        self,
        *,
        muted_until: Optional[Union[bool, datetime]] = MISSING,
        collapsed: bool = MISSING,
        level: NotificationLevel = MISSING,
    ) -> ChannelSettings:
        """|coro|

        Edits the channel's notification settings.

        All parameters are optional.

        Parameters
        -----------
        muted_until: Optional[Union[:class:`datetime.datetime`, :class:`bool`]]
            The date this channel's mute should expire.
            This can be ``True`` to mute indefinitely, or ``False``/``None`` to unmute.

            This must be a timezone-aware datetime object. Consider using :func:`utils.utcnow`.
        collapsed: :class:`bool`
            Indicates if the channel should be collapsed or not.
            Only applicable to channels of type :attr:`ChannelType.category`.
        level: :class:`NotificationLevel`
            Determines what level of notifications you receive for the channel.

        Raises
        -------
        HTTPException
            Editing the settings failed.

        Returns
        --------
        :class:`ChannelSettings`
            The new notification settings.
        """
        state = self._state
        guild_id = self._guild_id
        channel_id = self._channel_id
        payload = {}

        if muted_until is not MISSING:
            if not muted_until:
                payload['muted'] = False
            else:
                payload['muted'] = True
                if muted_until is True:
                    payload['mute_config'] = {'selected_time_window': -1, 'end_time': None}
                else:
                    if muted_until.tzinfo is None:
                        raise TypeError(
                            'muted_until must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                        )

                    mute_config = {
                        'selected_time_window': (muted_until - utcnow()).total_seconds(),
                        'end_time': muted_until.isoformat(),
                    }
                    payload['mute_config'] = mute_config

        if collapsed is not MISSING:
            payload['collapsed'] = collapsed

        if level is not MISSING:
            payload['message_notifications'] = level.value

        fields = {'channel_overrides': {str(channel_id): payload}}
        data = await state.http.edit_guild_settings(guild_id or '@me', fields)

        override = find(lambda x: x.get('channel_id') == str(channel_id), data['channel_overrides']) or {
            'channel_id': channel_id
        }
        return ChannelSettings(guild_id, data=override, state=state)


class GuildSettings:
    """Represents a guild's notification settings.

    .. versionadded:: 2.0

    Attributes
    ----------
    level: :class:`NotificationLevel`
        The notification level for the guild.
    muted: :class:`MuteConfig`
        The mute configuration for the guild.
    suppress_everyone: :class:`bool`
        Whether to suppress @everyone/@here notifications.
    suppress_roles: :class:`bool`
        Whether to suppress role notifications.
    hide_muted_channels: :class:`bool`
        Whether to hide muted channels.
    mobile_push: :class:`bool`
        Whether to enable mobile push notifications.
    mute_scheduled_events: :class:`bool`
        Whether to mute scheduled events.
    notify_highlights: :class:`HighlightLevel`
        Whether to include highlights in notifications.
    version: :class:`int`
        The version of the guild's settings.
    """

    if TYPE_CHECKING:
        _channel_overrides: Dict[int, ChannelSettings]
        _guild_id: Optional[int]
        level: NotificationLevel
        muted: MuteConfig
        suppress_everyone: bool
        suppress_roles: bool
        hide_muted_channels: bool
        mobile_push: bool
        mute_scheduled_events: bool
        notify_highlights: HighlightLevel
        version: int

    def __init__(self, *, data: Dict[str, Any], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<GuildSettings guild={self.guild!r} level={self.level} muted={self.muted} suppress_everyone={self.suppress_everyone} suppress_roles={self.suppress_roles}>'

    def _update(self, data: Dict[str, Any]) -> None:
        # We consider everything optional because this class can be constructed with no data
        # to represent the default settings
        self._guild_id = guild_id = _get_as_snowflake(data, 'guild_id')
        self.level = try_enum(NotificationLevel, data.get('message_notifications', 3))
        self.suppress_everyone = data.get('suppress_everyone', False)
        self.suppress_roles = data.get('suppress_roles', False)
        self.hide_muted_channels = data.get('hide_muted_channels', False)
        self.mobile_push = data.get('mobile_push', True)
        self.mute_scheduled_events = data.get('mute_scheduled_events', False)
        self.notify_highlights = try_enum(HighlightLevel, data.get('notify_highlights', 0))
        self.version = data.get('version', -1)  # Overriden by real data

        self.muted = MuteConfig(data.get('muted', False), data.get('mute_config') or {})
        self._channel_overrides = overrides = {}
        state = self._state
        for override in data.get('channel_overrides', []):
            channel_id = int(override['channel_id'])
            overrides[channel_id] = ChannelSettings(guild_id, data=override, state=state)

    @property
    def guild(self) -> Union[Guild, ClientUser]:
        """Union[:class:`Guild`, :class:`ClientUser`]: Returns the guild that these settings are for.

        If the returned value is a :class:`ClientUser` then the settings are for the user's private channels.
        """
        if self._guild_id:
            return self._state._get_guild(self._guild_id) or Object(id=self._guild_id)  # type: ignore # Lying for better developer UX
        return self._state.user  # type: ignore # Should always be present here

    @property
    def channel_overrides(self) -> List[ChannelSettings]:
        """List[:class:`ChannelSettings`: Returns a list of all the overrided channel notification settings."""
        return list(self._channel_overrides.values())

    async def edit(
        self,
        muted_until: Optional[Union[bool, datetime]] = MISSING,
        level: NotificationLevel = MISSING,
        suppress_everyone: bool = MISSING,
        suppress_roles: bool = MISSING,
        mobile_push: bool = MISSING,
        hide_muted_channels: bool = MISSING,
        mute_scheduled_events: bool = MISSING,
        notify_highlights: HighlightLevel = MISSING,
    ) -> Optional[GuildSettings]:
        """|coro|

        Edits the guild's notification settings.

        All parameters are optional.

        Parameters
        -----------
        muted_until: Optional[Union[:class:`datetime.datetime`, :class:`bool`]]
            The date this guild's mute should expire.
            This can be ``True`` to mute indefinitely, or ``False``/``None`` to unmute.

            This must be a timezone-aware datetime object. Consider using :func:`utils.utcnow`.
        level: :class:`NotificationLevel`
            Determines what level of notifications you receive for the guild.
        suppress_everyone: :class:`bool`
            Indicates if @everyone mentions should be suppressed for the guild.
        suppress_roles: :class:`bool`
            Indicates if role mentions should be suppressed for the guild.
        mobile_push: :class:`bool`
            Indicates if push notifications should be sent to mobile devices for this guild.
        hide_muted_channels: :class:`bool`
            Indicates if channels that are muted should be hidden from the sidebar.
        mute_scheduled_events: :class:`bool`
            Indicates if scheduled events should be muted.
        notify_highlights: :class:`HighlightLevel`
            Indicates if highlights should be included in notifications.

        Raises
        -------
        HTTPException
            Editing the settings failed.

        Returns
        --------
        :class:`GuildSettings`
            The new notification settings.
        """
        payload = {}

        if muted_until is not MISSING:
            if not muted_until:
                payload['muted'] = False
            else:
                payload['muted'] = True
                if muted_until is True:
                    payload['mute_config'] = {'selected_time_window': -1, 'end_time': None}
                else:
                    if muted_until.tzinfo is None:
                        raise TypeError(
                            'muted_until must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                        )

                    mute_config = {
                        'selected_time_window': (muted_until - utcnow()).total_seconds(),
                        'end_time': muted_until.isoformat(),
                    }
                    payload['mute_config'] = mute_config

        if level is not MISSING:
            payload['message_notifications'] = level.value

        if suppress_everyone is not MISSING:
            payload['suppress_everyone'] = suppress_everyone

        if suppress_roles is not MISSING:
            payload['suppress_roles'] = suppress_roles

        if mobile_push is not MISSING:
            payload['mobile_push'] = mobile_push

        if hide_muted_channels is not MISSING:
            payload['hide_muted_channels'] = hide_muted_channels

        if mute_scheduled_events is not MISSING:
            payload['mute_scheduled_events'] = mute_scheduled_events

        if notify_highlights is not MISSING:
            payload['notify_highlights'] = notify_highlights.value

        data = await self._state.http.edit_guild_settings(self._guild_id or '@me', payload)
        return GuildSettings(data=data, state=self._state)


class TrackingSettings:
    """Represents your Discord tracking settings.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: bool(x)

            Checks if any tracking settings are enabled.

    Attributes
    ----------
    personalization: :class:`bool`
        Whether you have consented to your data being used for personalization.
    usage_statistics: :class:`bool`
        Whether you have consented to your data being used for usage statistics.
    """

    __slots__ = ('_state', 'personalization', 'usage_statistics')

    def __init__(self, *, data: Dict[str, Dict[str, bool]], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<TrackingSettings personalization={self.personalization} usage_statistics={self.usage_statistics}>'

    def __bool__(self) -> bool:
        return any({self.personalization, self.usage_statistics})

    def _update(self, data: Dict[str, Dict[str, bool]]):
        self.personalization = data.get('personalization', {}).get('consented', False)
        self.usage_statistics = data.get('usage_statistics', {}).get('consented', False)

    @overload
    async def edit(self) -> None:
        ...

    @overload
    async def edit(
        self,
        *,
        personalization: bool = ...,
        usage_statistics: bool = ...,
    ) -> None:
        ...

    async def edit(self, **kwargs) -> None:
        """|coro|

        Edits your tracking settings.

        Parameters
        ----------
        personalization: :class:`bool`
            Whether you have consented to your data being used for personalization.
        usage_statistics: :class:`bool`
            Whether you have consented to your data being used for usage statistics.
        """
        payload = {
            'grant': [k for k, v in kwargs.items() if v is True],
            'revoke': [k for k, v in kwargs.items() if v is False],
        }
        data = await self._state.http.edit_tracking(payload)
        self._update(data)


class EmailSettings:
    """Represents email communication preferences.

    .. versionadded:: 2.0

    Attributes
    ----------
    initialized: :class:`bool`
        Whether the email communication preferences have been initialized.
    communication: :class:`bool`
        Whether you want to receive emails for missed calls/messages.
    social: :class:`bool`
        Whether you want to receive emails for friend requests/suggestions or events.
    recommendations_and_events: :class:`bool`
        Whether you want to receive emails for recommended servers and events.
    tips: :class:`bool`
        Whether you want to receive emails for advice and tricks.
    updates_and_announcements: :class:`bool`
        Whether you want to receive emails for updates and new features.
    """

    __slots__ = (
        '_state',
        'initialized',
        'communication',
        'social',
        'recommendations_and_events',
        'tips',
        'updates_and_announcements',
    )

    def __init__(self, *, data: dict, state: ConnectionState):
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<EmailSettings initialized={self.initialized}>'

    def _update(self, data: dict):
        self.initialized = data.get('initialized', False)
        categories = data.get('categories', {})
        self.communication = categories.get('communication', False)
        self.social = categories.get('social', False)
        self.recommendations_and_events = categories.get('recommendations_and_events', False)
        self.tips = categories.get('tips', False)
        self.updates_and_announcements = categories.get('updates_and_announcements', False)

    @overload
    async def edit(self) -> None:
        ...

    @overload
    async def edit(
        self,
        *,
        communication: bool = MISSING,
        social: bool = MISSING,
        recommendations_and_events: bool = MISSING,
        tips: bool = MISSING,
        updates_and_announcements: bool = MISSING,
    ) -> None:
        ...

    async def edit(self, **kwargs) -> None:
        """|coro|

        Edits the email settings.

        All parameters are optional.

        Parameters
        -----------
        communication: :class:`bool`
            Indicates if you want to receive communication emails.
        social: :class:`bool`
            Indicates if you want to receive social emails.
        recommendations_and_events: :class:`bool`
            Indicates if you want to receive recommendations and events emails.
        tips: :class:`bool`
            Indicates if you want to receive tips emails.
        updates_and_announcements: :class:`bool`
            Indicates if you want to receive updates and announcements emails.

        Raises
        -------
        HTTPException
            Editing the settings failed.
        """
        payload = {}

        # It seems that initialized is settable, but it doesn't do anything
        # So we support just in case but leave it undocumented
        initialized = kwargs.pop('initialized', None)
        if initialized is not None:
            payload['initialized'] = initialized
        if kwargs:
            payload['categories'] = kwargs

        data = await self._state.http.edit_email_settings(**payload)
        self._update(data)
