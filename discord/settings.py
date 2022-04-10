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

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .activity import create_settings_activity
from .enums import (
    FriendFlags,
    Locale,
    NotificationLevel,
    Status,
    StickerAnimationOptions,
    Theme,
    UserContentFilter,
    try_enum,
)
from .guild_folder import GuildFolder
from .utils import MISSING, parse_time, utcnow

if TYPE_CHECKING:
    from .abc import GuildChannel
    from .activity import CustomActivity
    from .guild import Guild
    from .state import ConnectionState
    from .tracking import Tracking

__all__ = (
    'ChannelSettings',
    'GuildSettings',
    'UserSettings',
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
        Unknown.
    timezone_offset: :class:`int`
        The timezone offset to use.
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
        view_nsfw_guilds: bool

    def __init__(self, *, data, state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return '<Settings>'

    def _get_guild(self, id: int) -> Optional[Guild]:
        return self._state._get_guild(int(id))

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
            Unknown.
        render_embeds: :class:`bool`
            Whether or not to render embeds that are sent in the chat.
        render_reactions: :class:`bool`
            Whether or not to render reactions that are added to messages.
        restricted_guilds: List[:class:`abc.Snowflake`]
            A list of guilds that you will not receive DMs from.
        show_current_game: :class:`bool`
            Whether or not to display the game that you are currently playing.
        stream_notifications_enabled: :class:`bool`
            Unknown.
        theme: :class:`Theme`
            The theme of the Discord UI.
        timezone_offset: :class:`int`
            The timezone offset to use.
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

    async def fetch_tracking(self) -> Tracking:
        """|coro|

        Retrieves your :class:`Tracking` settings.

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
        return Tracking(state=self._state, data=data)

    @property
    def tracking(self) -> Optional[Tracking]:
        """Optional[:class:`Tracking`]: Returns your tracking settings if available."""
        return self._state.consents

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
        return list(filter(None, map(self._get_guild, getattr(self, '_guild_positions', []))))

    @property
    def locale(self) -> Locale:
        """:class:`Locale`: The :rfc:`3066` language identifier
        of the locale to use for the language of the Discord client."""
        return try_enum(Locale, getattr(self, '_locale', 'en-US'))

    @property
    def passwordless(self) -> bool:
        """:class:`bool`: Unknown."""
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

        for item in {'__bool__', '__eq__', '__float__', '__int__', '__str__'}:
            setattr(self, item, getattr(muted, item))

    def __repr__(self) -> str:
        return f'<MuteConfig muted={self.muted} until={self.until}>'

    def __str__(self) -> str:
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

    Attributes
    ----------
    level: :class:`NotificationLevel`
        The notification level for the channel.
    muted: :class:`MuteConfig`
        The mute configuration for the channel.
    collapsed: :class:`bool`
        Unknown.
    """

    if TYPE_CHECKING:
        _channel_id: int
        level: NotificationLevel
        muted: MuteConfig
        collapsed: bool

    def __init__(self, guild_id, *, data: Dict[str, Any] = {}, state: ConnectionState) -> None:
        self._guild_id: int = guild_id
        self._state = state
        self._update(data)

    def _update(self, data: Dict[str, Any]) -> None:
        self._channel_id = int(data['channel_id'])
        self.collapsed = data.get('collapsed', False)

        self.level = try_enum(NotificationLevel, data.get('message_notifications', 3))
        self.muted = MuteConfig(data.get('muted', False), data.get('mute_config') or {})

    @property
    def channel(self) -> Optional[GuildChannel]:
        """Optional[:class:`.abc.GuildChannel`]: Returns the channel these settings are for."""
        guild = self._state._get_guild(self._guild_id)
        return guild and guild.get_channel(self._channel_id)

    async def edit(
        self,
        *,
        muted: bool = MISSING,
        duration: Optional[int] = MISSING,
        collapsed: bool = MISSING,
        level: NotificationLevel = MISSING,
    ) -> Optional[ChannelSettings]:
        """|coro|

        Edits the channel's notification settings.

        All parameters are optional.

        Parameters
        -----------
        muted: :class:`bool`
            Indicates if the channel should be muted or not.
        duration: Optional[Union[:class:`int`, :class:`float`]]
            The amount of time in hours that the channel should be muted for.
            Defaults to indefinite.
        collapsed: :class:`bool`
            Unknown.
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
        payload = {}

        if muted is not MISSING:
            payload['muted'] = muted

        if duration is not MISSING:
            if muted is MISSING:
                payload['muted'] = True

            if duration is not None:
                mute_config = {
                    'selected_time_window': duration * 3600,
                    'end_time': (datetime.utcnow() + timedelta(hours=duration)).isoformat(),
                }
                payload['mute_config'] = mute_config

        if collapsed is not MISSING:
            payload['collapsed'] = collapsed

        if level is not MISSING:
            payload['message_notifications'] = level.value

        fields = {'channel_overrides': {str(self._channel_id): payload}}
        data = await self._state.http.edit_guild_settings(self._guild_id, fields)

        return ChannelSettings(self._guild_id, data=data['channel_overrides'][str(self._channel_id)], state=self._state)


class GuildSettings:
    """Represents a guild's notification settings.

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
    mobile_push_notifications: :class:`bool`
        Whether to enable mobile push notifications.
    version: :class:`int`
        The version of the guild's settings.
    """

    if TYPE_CHECKING:
        _channel_overrides: Dict[int, ChannelSettings]
        _guild_id: int
        version: int
        muted: MuteConfig
        suppress_everyone: bool
        suppress_roles: bool
        hide_muted_channels: bool
        mobile_push_notifications: bool
        level: NotificationLevel

    def __init__(self, *, data: Dict[str, Any], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def _update(self, data: Dict[str, Any]) -> None:
        self._guild_id = guild_id = int(data['guild_id'])
        self.version = data.get('version', -1)  # Overriden by real data
        self.suppress_everyone = data.get('suppress_everyone', False)
        self.suppress_roles = data.get('suppress_roles', False)
        self.hide_muted_channels = data.get('hide_muted_channels', False)
        self.mobile_push_notifications = data.get('mobile_push', True)

        self.level = try_enum(NotificationLevel, data.get('message_notifications', 3))
        self.muted = MuteConfig(data.get('muted', False), data.get('mute_config') or {})
        self._channel_overrides = overrides = {}
        state = self._state
        for override in data.get('channel_overrides', []):
            channel_id = int(override['channel_id'])
            overrides[channel_id] = ChannelSettings(guild_id, data=override, state=state)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: Returns the guild that these settings are for."""
        return self._state._get_guild(self._guild_id)

    @property
    def channel_overrides(self) -> List[ChannelSettings]:
        """List[:class:`ChannelSettings`: Returns a list of all the overrided channel notification settings."""
        return list(self._channel_overrides.values())

    async def edit(
        self,
        muted: bool = MISSING,
        duration: Optional[int] = MISSING,
        level: NotificationLevel = MISSING,
        suppress_everyone: bool = MISSING,
        suppress_roles: bool = MISSING,
        mobile_push_notifications: bool = MISSING,
        hide_muted_channels: bool = MISSING,
    ) -> Optional[GuildSettings]:
        """|coro|

        Edits the guild's notification settings.

        All parameters are optional.

        Parameters
        -----------
        muted: :class:`bool`
            Indicates if the guild should be muted or not.
        duration: Optional[Union[:class:`int`, :class:`float`]]
            The amount of time in hours that the guild should be muted for.
            Defaults to indefinite.
        level: :class:`NotificationLevel`
            Determines what level of notifications you receive for the guild.
        suppress_everyone: :class:`bool`
            Indicates if @everyone mentions should be suppressed for the guild.
        suppress_roles: :class:`bool`
            Indicates if role mentions should be suppressed for the guild.
        mobile_push_notifications: :class:`bool`
            Indicates if push notifications should be sent to mobile devices for this guild.
        hide_muted_channels: :class:`bool`
            Indicates if channels that are muted should be hidden from the sidebar.

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

        if muted is not MISSING:
            payload['muted'] = muted

        if duration is not MISSING:
            if muted is MISSING:
                payload['muted'] = True

            if duration is not None:
                mute_config = {
                    'selected_time_window': duration * 3600,
                    'end_time': (datetime.utcnow() + timedelta(hours=duration)).isoformat(),
                }
                payload['mute_config'] = mute_config

        if level is not MISSING:
            payload['message_notifications'] = level.value

        if suppress_everyone is not MISSING:
            payload['suppress_everyone'] = suppress_everyone

        if suppress_roles is not MISSING:
            payload['suppress_roles'] = suppress_roles

        if mobile_push_notifications is not MISSING:
            payload['mobile_push'] = mobile_push_notifications

        if hide_muted_channels is not MISSING:
            payload['hide_muted_channels'] = hide_muted_channels

        data = await self._state.http.edit_guild_settings(self._guild_id, payload)

        return GuildSettings(data=data, state=self._state)
