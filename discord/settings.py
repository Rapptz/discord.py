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

import base64
from datetime import datetime, timezone
import struct
import logging
from typing import TYPE_CHECKING, Any, Collection, Dict, List, Literal, Optional, Sequence, Tuple, Type, Union, overload

from google.protobuf.json_format import MessageToDict, ParseDict
from discord_protos import PreloadedUserSettings  # , FrecencyUserSettings

from .activity import CustomActivity
from .colour import Colour
from .enums import (
    EmojiPickerSection,
    HighlightLevel,
    InboxTab,
    Locale,
    NotificationLevel,
    Status,
    SpoilerRenderOptions,
    StickerAnimationOptions,
    StickerPickerSection,
    Theme,
    UserContentFilter,
    try_enum,
)
from .flags import FriendDiscoveryFlags, FriendSourceFlags, HubProgressFlags, OnboardingProgressFlags
from .object import Object
from .utils import MISSING, _get_as_snowflake, _ocast, parse_time, parse_timestamp, utcnow, find

if TYPE_CHECKING:
    from google.protobuf.message import Message
    from typing_extensions import Self

    from .abc import GuildChannel, Snowflake
    from .channel import DMChannel, GroupChannel
    from .guild import Guild
    from .state import ConnectionState
    from .user import ClientUser, User

    PrivateChannel = Union[DMChannel, GroupChannel]

__all__ = (
    'UserSettings',
    'GuildFolder',
    'GuildProgress',
    'AudioContext',
    'LegacyUserSettings',
    'MuteConfig',
    'ChannelSettings',
    'GuildSettings',
    'TrackingSettings',
    'EmailSettings',
)

_log = logging.getLogger(__name__)


class _ProtoSettings:
    __slots__ = (
        '_state',
        'settings',
    )

    PROTOBUF_CLS: Type[Message] = MISSING
    settings: Any

    # I honestly wish I didn't have to vomit properties everywhere like this,
    # but unfortunately it's probably the best way to do it
    # The discord-protos library is maintained seperately, so any changes
    # to the protobufs will have to be reflected here;
    # this is why I'm keeping the `settings` attribute public
    # I love protobufs :blobcatcozystars:

    def __init__(self, state: ConnectionState, data: str):
        self._state: ConnectionState = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.settings == other.settings
        return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.settings != other.settings
        return True

    def _update(self, data: str, *, partial: bool = False):
        if partial:
            self.merge_from_base64(data)
        else:
            self.from_base64(data)

    @classmethod
    def _copy(cls, self: Self, /) -> Self:
        new = cls.__new__(cls)
        new._state = self._state
        new.settings = cls.PROTOBUF_CLS()
        new.settings.CopyFrom(self.settings)
        return new

    @overload
    def _get_guild(self, id: int, /, *, always_guild: Literal[True] = ...) -> Guild:
        ...

    @overload
    def _get_guild(self, id: int, /, *, always_guild: Literal[False] = ...) -> Union[Guild, Object]:
        ...

    def _get_guild(self, id: int, /, *, always_guild: bool = False) -> Union[Guild, Object]:
        id = int(id)
        if always_guild:
            return self._state._get_or_create_unavailable_guild(id)
        return self._state._get_guild(id) or Object(id=id)

    def to_dict(self, *, with_defaults: bool = False) -> Dict[str, Any]:
        return MessageToDict(
            self.settings,
            including_default_value_fields=with_defaults,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )

    def dict_to_base64(self, data: Dict[str, Any]) -> str:
        message = ParseDict(data, self.PROTOBUF_CLS())
        return base64.b64encode(message.SerializeToString()).decode('ascii')

    def from_base64(self, data: str):
        self.settings = self.PROTOBUF_CLS().FromString(base64.b64decode(data))

    def merge_from_base64(self, data: str):
        self.settings.MergeFromString(base64.b64decode(data))

    def to_base64(self) -> str:
        return base64.b64encode(self.settings.SerializeToString()).decode('ascii')


class UserSettings(_ProtoSettings):
    """Represents the Discord client settings.

    .. versionadded:: 2.0
    """

    __slots__ = ()

    PROTOBUF_CLS = PreloadedUserSettings

    # Client versions are supposed to be backwards compatible
    # If the client supports a version newer than the one in data,
    # it does a migration and updates the version in data
    SUPPORTED_CLIENT_VERSION = 17
    SUPPORTED_SERVER_VERSION = 0

    def __init__(self, *args):
        super().__init__(*args)
        if self.client_version < self.SUPPORTED_CLIENT_VERSION:
            # Migrations are mostly for client state, but we'll throw a debug log anyway
            _log.debug('PreloadedUserSettings client version is outdated, migration needed. Unexpected behaviour may occur.')
        if self.server_version > self.SUPPORTED_SERVER_VERSION:
            # At the time of writing, the server version is not provided (so it's always 0)
            # The client does not use the field at all, so there probably won't be any server-side migrations anytime soon
            _log.debug('PreloadedUserSettings server version is newer than supported. Unexpected behaviour may occur.')

    @property
    def data_version(self) -> int:
        """:class:`int`: The version of the settings. Increases on every change."""
        return self.settings.versions.data_version

    @property
    def client_version(self) -> int:
        """:class:`int`: The client version of the settings. Used for client-side data migrations."""
        return self.settings.versions.client_version

    @property
    def server_version(self) -> int:
        """:class:`int`: The server version of the settings. Used for server-side data migrations."""
        return self.settings.versions.server_version

    # Inbox Settings

    @property
    def inbox_tab(self) -> InboxTab:
        """:class:`InboxTab`: The current (last opened) inbox tab."""
        return try_enum(InboxTab, self.settings.inbox.current_tab)

    @property
    def inbox_tutorial_viewed(self) -> bool:
        """:class:`bool`: Whether the inbox tutorial has been viewed."""
        return self.settings.inbox.viewed_tutorial

    # Guild Settings

    @property
    def guild_progress_settings(self) -> List[GuildProgress]:
        """List[:class:`GuildProgress`]: A list of guild progress settings."""
        state = self._state
        return [
            GuildProgress._from_settings(guild_id, data=settings, state=state)
            for guild_id, settings in self.settings.guilds.guilds.items()
        ]

    # User Content Settings

    @property
    def dismissed_contents(self) -> Tuple[int, ...]:
        """Tuple[:class:`int`]: A list of enum values representing dismissable content in the app.

        .. note::

            For now, this just returns the raw values without converting to a proper enum,
            as the enum values change too often to be viably maintained.
        """
        contents = self.settings.user_content.dismissed_contents
        return struct.unpack(f'>{len(contents)}B', contents)

    @property
    def last_dismissed_promotion_start_date(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: The date the last dismissed promotion started."""
        return parse_time(self.settings.user_content.last_dismissed_outbound_promotion_start_date.value or None)

    @property
    def nitro_basic_modal_dismissed_at(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: The date the Nitro Basic modal was dismissed."""
        return (
            self.settings.user_content.premium_tier_0_modal_dismissed_at.ToDatetime(tzinfo=timezone.utc)
            if self.settings.user_content.HasField('premium_tier_0_modal_dismissed_at')
            else None
        )

    # Voice and Video Settings

    # TODO: Video filters

    # @property
    # def video_filter_background_blur(self) -> bool:
    #     return self.settings.voice_and_video.blur.use_blur

    @property
    def always_preview_video(self) -> bool:
        """Whether to always show the preview modal when the user turns on their camera."""
        return self.settings.voice_and_video.always_preview_video.value

    @property
    def afk_timeout(self) -> int:
        """:class:`int`: How long (in seconds) the user needs to be AFK until Discord sends push notifications to mobile devices (30-600)."""
        return self.settings.voice_and_video.afk_timeout.value or 600

    @property
    def stream_notifications_enabled(self) -> bool:
        """:class:`bool`: Whether stream notifications for friends will be received."""
        return (
            self.settings.voice_and_video.stream_notifications_enabled.value
            if self.settings.voice_and_video.HasField('stream_notifications_enabled')
            else True
        )

    @property
    def native_phone_integration_enabled(self) -> bool:
        """:class:`bool`: Whether to enable the Discord mobile Callkit."""
        return (
            self.settings.voice_and_video.native_phone_integration_enabled.value
            if self.settings.voice_and_video.HasField('native_phone_integration_enabled')
            else True
        )

    @property
    def soundboard_volume(self) -> float:
        """:class:`float`: The volume of the soundboard (0-100)."""
        return (
            self.settings.voice_and_video.soundboard_settings.volume
            if self.settings.voice_and_video.HasField('soundboard_settings')
            else 100.0
        )

    # Text and Images Settings

    @property
    def diversity_surrogate(self) -> Optional[str]:
        """Optional[:class:`str`]: The unicode character used as the diversity surrogate for supported emojis (i.e. emoji skin tones, ``🏻``)."""
        return self.settings.text_and_images.diversity_surrogate.value or None

    @property
    def use_thread_sidebar(self) -> bool:
        """:class:`bool`: Whether to open threads in split view."""
        return (
            self.settings.text_and_images.use_thread_sidebar.value
            if self.settings.text_and_images.HasField('use_thread_sidebar')
            else True
        )

    @property
    def render_spoilers(self) -> SpoilerRenderOptions:
        """:class:`SpoilerRenderOptions`: When to show spoiler content."""
        return try_enum(SpoilerRenderOptions, self.settings.text_and_images.render_spoilers.value or 'ON_CLICK')

    @property
    def collapsed_emoji_picker_sections(self) -> Tuple[Union[EmojiPickerSection, Guild], ...]:
        """Tuple[Union[:class:`EmojiPickerSection`, :class:`Guild`]]: A list of emoji picker sections (including guild IDs) that are collapsed."""
        return tuple(
            self._get_guild(section, always_guild=True) if section.isdigit() else try_enum(EmojiPickerSection, section)
            for section in self.settings.text_and_images.emoji_picker_collapsed_sections
        )

    @property
    def collapsed_sticker_picker_sections(self) -> Tuple[Union[StickerPickerSection, Guild, Object], ...]:
        """Tuple[Union[:class:`StickerPickerSection`, :class:`Guild`, :class:`Object`]]: A list of sticker picker sections (including guild and sticker pack IDs) that are collapsed."""
        return tuple(
            self._get_guild(section, always_guild=False) if section.isdigit() else try_enum(StickerPickerSection, section)
            for section in self.settings.text_and_images.sticker_picker_collapsed_sections
        )

    @property
    def view_image_descriptions(self) -> bool:
        """:class:`bool`: Whether to display the alt text of attachments."""
        return self.settings.text_and_images.view_image_descriptions.value

    @property
    def show_command_suggestions(self) -> bool:
        """:class:`bool`: Whether to show application command suggestions in-chat."""
        return (
            self.settings.text_and_images.show_command_suggestions.value
            if self.settings.text_and_images.HasField('show_command_suggestions')
            else True
        )

    @property
    def inline_attachment_media(self) -> bool:
        """:class:`bool`: Whether to display attachments when they are uploaded in chat."""
        return (
            self.settings.text_and_images.inline_attachment_media.value
            if self.settings.text_and_images.HasField('inline_attachment_media')
            else True
        )

    @property
    def inline_embed_media(self) -> bool:
        """:class:`bool`: Whether to display videos and images from links posted in chat."""
        return (
            self.settings.text_and_images.inline_embed_media.value
            if self.settings.text_and_images.HasField('inline_embed_media')
            else True
        )

    @property
    def gif_auto_play(self) -> bool:
        """:class:`bool`: Whether to automatically play GIFs that are in the chat.."""
        return (
            self.settings.text_and_images.gif_auto_play.value
            if self.settings.text_and_images.HasField('gif_auto_play')
            else True
        )

    @property
    def render_embeds(self) -> bool:
        """:class:`bool`: Whether to render embeds that are sent in the chat."""
        return (
            self.settings.text_and_images.render_embeds.value
            if self.settings.text_and_images.HasField('render_embeds')
            else True
        )

    @property
    def render_reactions(self) -> bool:
        """:class:`bool`: Whether to render reactions that are added to messages."""
        return (
            self.settings.text_and_images.render_reactions.value
            if self.settings.text_and_images.HasField('render_reactions')
            else True
        )

    @property
    def animate_emojis(self) -> bool:
        """:class:`bool`: Whether to animate emojis in the chat."""
        return (
            self.settings.text_and_images.animate_emoji.value
            if self.settings.text_and_images.HasField('animate_emoji')
            else True
        )

    @property
    def animate_stickers(self) -> StickerAnimationOptions:
        """:class:`StickerAnimationOptions`: Whether to animate stickers in the chat."""
        return try_enum(StickerAnimationOptions, self.settings.text_and_images.animate_stickers.value)

    @property
    def enable_tts_command(self) -> bool:
        """:class:`bool`: Whether to allow TTS messages to be played/sent."""
        return (
            self.settings.text_and_images.enable_tts_command.value
            if self.settings.text_and_images.HasField('enable_tts_command')
            else True
        )

    @property
    def message_display_compact(self) -> bool:
        """:class:`bool`: Whether to use the compact Discord display mode."""
        return self.settings.text_and_images.message_display_compact.value

    @property
    def explicit_content_filter(self) -> UserContentFilter:
        """:class:`UserContentFilter`: The filter for explicit content in all messages."""
        return try_enum(
            UserContentFilter,
            self.settings.text_and_images.explicit_content_filter.value
            if self.settings.text_and_images.HasField('explicit_content_filter')
            else 1,
        )

    @property
    def view_nsfw_guilds(self) -> bool:
        """:class:`bool`: Whether to show NSFW guilds on iOS."""
        return self.settings.text_and_images.view_nsfw_guilds.value

    @property
    def convert_emoticons(self) -> bool:
        r""":class:`bool`: Whether to automatically convert emoticons into emojis (e.g. ``:)`` -> 😃)."""
        return (
            self.settings.text_and_images.convert_emoticons.value
            if self.settings.text_and_images.HasField('convert_emoticons')
            else True
        )

    @property
    def show_expression_suggestions(self) -> bool:
        """:class:`bool`: Whether to show expression (emoji/sticker/soundboard) suggestions in-chat."""
        return (
            self.settings.text_and_images.expression_suggestions_enabled.value
            if self.settings.text_and_images.HasField('expression_suggestions_enabled')
            else True
        )

    @property
    def view_nsfw_commands(self) -> bool:
        """:class:`bool`: Whether to show NSFW application commands in DMs."""
        return self.settings.text_and_images.view_nsfw_commands.value

    @property
    def use_legacy_chat_input(self) -> bool:
        """:class:`bool`: Whether to use the legacy chat input over the new rich input."""
        return self.settings.text_and_images.use_legacy_chat_input.value

    # Notifications Settings

    @property
    def in_app_notifications(self) -> bool:
        """:class:`bool`: Whether to show notifications directly in the app."""
        return (
            self.settings.notifications.show_in_app_notifications.value
            if self.settings.notifications.HasField('show_in_app_notifications')
            else True
        )

    @property
    def send_stream_notifications(self) -> bool:
        """:class:`bool`: Whether to send notifications to friends when using the go live feature."""
        return self.settings.notifications.notify_friends_on_go_live.value

    @property
    def notification_center_acked_before_id(self) -> int:
        """:class:`int`: The ID of the last notification that was acknowledged in the notification center."""
        return self.settings.notifications.notification_center_acked_before_id

    # Privacy Settings

    @property
    def allow_activity_friend_joins(self) -> bool:
        """:class:`bool`: Whether to allow friends to join your activity without sending a request."""
        return (
            self.settings.privacy.allow_activity_party_privacy_friends.value
            if self.settings.privacy.HasField('allow_activity_party_privacy_friends')
            else True
        )

    @property
    def allow_activity_voice_channel_joins(self) -> bool:
        """:class:`bool`: Whether to allow people in the same voice channel as you to join your activity without sending a request. Does not apply to Community guilds."""
        return (
            self.settings.privacy.allow_activity_party_privacy_voice_channel.value
            if self.settings.privacy.HasField('allow_activity_party_privacy_voice_channel')
            else True
        )

    @property
    def restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that you will not receive DMs from."""
        return list(map(self._get_guild, self.settings.privacy.restricted_guild_ids))

    @property
    def default_guilds_restricted(self) -> bool:
        """:class:`bool`: Whether to automatically disable DMs between you and members of new guilds you join."""
        return self.settings.privacy.default_guilds_restricted

    @property
    def allow_accessibility_detection(self) -> bool:
        """:class:`bool`: Whether to allow Discord to track screen reader usage."""
        return self.settings.privacy.allow_accessibility_detection

    @property
    def detect_platform_accounts(self) -> bool:
        """:class:`bool`: Whether to automatically detect accounts from services like Steam and Blizzard when you open the Discord client."""
        return (
            self.settings.privacy.detect_platform_accounts.value
            if self.settings.privacy.HasField('detect_platform_accounts')
            else True
        )

    @property
    def passwordless(self) -> bool:
        """:class:`bool`: Whether to enable passwordless login."""
        return self.settings.privacy.passwordless.value if self.settings.privacy.HasField('passwordless') else True

    @property
    def contact_sync_enabled(self) -> bool:
        """:class:`bool`: Whether to enable the contact sync on Discord mobile."""
        return self.settings.privacy.contact_sync_enabled.value

    @property
    def friend_source_flags(self) -> FriendSourceFlags:
        """:class:`FriendSourceFlags`: Who can add you as a friend."""
        return (
            FriendSourceFlags._from_value(self.settings.privacy.friend_source_flags.value)
            if self.settings.privacy.HasField('friend_source_flags')
            else FriendSourceFlags.all()
        )

    @property
    def friend_discovery_flags(self) -> FriendDiscoveryFlags:
        """:class:`FriendDiscoveryFlags`: How you get recommended friends."""
        return FriendDiscoveryFlags._from_value(self.settings.privacy.friend_discovery_flags.value)

    @property
    def activity_restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that your current activity will not be shown in."""
        return list(map(self._get_guild, self.settings.privacy.activity_restricted_guild_ids))

    @property
    def default_guilds_activity_restricted(self) -> bool:
        """:class:`bool`: Whether to automatically disable showing your current activity in new large (over 200 member) guilds you join."""
        return self.settings.privacy.default_guilds_activity_restricted

    @property
    def activity_joining_restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that will not be able to join your current activity."""
        return list(map(self._get_guild, self.settings.privacy.activity_joining_restricted_guild_ids))

    @property
    def message_request_restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds whose originating DMs will not be filtered into your message requests."""
        return list(map(self._get_guild, self.settings.privacy.message_request_restricted_guild_ids))

    @property
    def default_message_request_restricted(self) -> bool:
        """:class:`bool`: Whether to automatically disable the message request system in new guilds you join."""
        return self.settings.privacy.default_message_request_restricted.value

    @property
    def drops(self) -> bool:
        """:class:`bool`: Whether the Discord drops feature is enabled."""
        return not self.settings.privacy.drops_opted_out.value

    @property
    def non_spam_retraining(self) -> Optional[bool]:
        """Optional[:class:`bool`]: Whether to help improve Discord spam models when marking messages as non-spam; staff only."""
        return (
            self.settings.privacy.non_spam_retraining_opt_in.value
            if self.settings.privacy.HasField('non_spam_retraining_opt_in')
            else None
        )

    # Debug Settings

    @property
    def rtc_panel_show_voice_states(self) -> bool:
        """:class:`bool`: Whether to show voice states in the RTC panel."""
        return self.settings.debug.rtc_panel_show_voice_states.value

    # Game Library Settings

    @property
    def install_shortcut_desktop(self) -> bool:
        """:class:`bool`: Whether to install a desktop shortcut for games."""
        return self.settings.game_library.install_shortcut_desktop.value

    @property
    def install_shortcut_start_menu(self) -> bool:
        """:class:`bool`: Whether to install a start menu shortcut for games."""
        return (
            self.settings.game_library.install_shortcut_start_menu.value
            if self.settings.game_library.HasField('install_shortcut_start_menu')
            else True
        )

    @property
    def disable_games_tab(self) -> bool:
        """:class:`bool`: Whether to disable the showing of the Games tab."""
        return self.settings.game_library.disable_games_tab.value

    # Status Settings

    @property
    def status(self) -> Status:
        """:class:`Status`: The configured status."""
        return try_enum(Status, self.settings.status.status.value or 'unknown')

    @property
    def custom_activity(self) -> Optional[CustomActivity]:
        """:class:`CustomActivity`: The set custom activity."""
        return (
            CustomActivity._from_settings(data=self.settings.status.custom_status, state=self._state)
            if self.settings.status.HasField('custom_status')
            else None
        )

    @property
    def show_current_game(self) -> bool:
        """:class:`bool`: Whether to show the current game."""
        return self.settings.status.show_current_game.value if self.settings.status.HasField('show_current_game') else True

    # Localization Settings

    @property
    def locale(self) -> Locale:
        """:class:`Locale`: The :rfc:`3066` language identifier of the locale to use for the language of the Discord client."""
        return try_enum(Locale, self.settings.localization.locale.value or 'en-US')

    @property
    def timezone_offset(self) -> int:
        """:class:`int`: The timezone offset from UTC to use (in minutes)."""
        return self.settings.localization.timezone_offset.value

    # Appearance Settings

    @property
    def theme(self) -> Theme:
        """:class:`Theme`: The overall theme of the Discord UI."""
        return Theme.from_int(self.settings.appearance.theme)

    @property
    def client_theme(self) -> Optional[Tuple[int, int, float]]:
        """Optional[Tuple[:class:`int`, :class:`int`, :class:`float`]]: The client theme settings, in order of primary color, gradient preset, and gradient angle."""
        return (
            (
                self.settings.appearance.client_theme_settings.primary_color.value,
                self.settings.appearance.client_theme_settings.background_gradient_preset_id.value,
                self.settings.appearance.client_theme_settings.background_gradient_angle.value,
            )
            if self.settings.appearance.HasField('client_theme_settings')
            else None
        )

    @property
    def developer_mode(self) -> bool:
        """:class:`bool`: Whether to enable developer mode."""
        return self.settings.appearance.developer_mode

    @property
    def disable_mobile_redesign(self) -> bool:
        """:class:`bool`: Whether to opt-out of the mobile redesign."""
        return self.settings.appearance.mobile_redesign_disabled

    # Guild Folder Settings

    @property
    def guild_folders(self) -> List[GuildFolder]:
        """List[:class:`GuildFolder`]: A list of guild folders."""
        state = self._state
        return [GuildFolder._from_settings(data=folder, state=state) for folder in self.settings.guild_folders.folders]

    @property
    def guild_positions(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds in order of the guild/guild icons that are on the left hand side of the UI."""
        return list(map(self._get_guild, self.settings.guild_folders.guild_positions))

    # Favorites Settings

    # TODO: Favorites

    # Audio Settings

    @property
    def user_audio_settings(self) -> List[AudioContext]:
        """List[:class:`AudioContext`]: A list of audio context settings for users."""
        state = self._state
        return [
            AudioContext._from_settings(user_id, data=data, state=state)
            for user_id, data in self.settings.audio_context_settings.user.items()
        ]

    @property
    def stream_audio_settings(self) -> List[AudioContext]:
        """List[:class:`AudioContext`]: A list of audio context settings for streams."""
        state = self._state
        return [
            AudioContext._from_settings(stream_id, data=data, state=state)
            for stream_id, data in self.settings.audio_context_settings.stream.items()
        ]

    # Communities Settings

    @property
    def home_auto_navigation(self) -> bool:
        """:class:`bool`: Whether to automatically redirect to guild home for guilds that have not been accessed in a while."""
        return not self.settings.communities.disable_home_auto_nav.value

    @overload
    async def edit(self) -> Self:
        ...

    @overload
    async def edit(
        self,
        *,
        require_version: Union[bool, int] = False,
        client_version: int = ...,
        inbox_tab: InboxTab = ...,
        inbox_tutorial_viewed: bool = ...,
        guild_progress_settings: Sequence[GuildProgress] = ...,
        dismissed_contents: Sequence[int] = ...,
        last_dismissed_promotion_start_date: datetime = ...,
        nitro_basic_modal_dismissed_at: datetime = ...,
        soundboard_volume: float = ...,
        afk_timeout: int = ...,
        always_preview_video: bool = ...,
        native_phone_integration_enabled: bool = ...,
        stream_notifications_enabled: bool = ...,
        diversity_surrogate: Optional[str] = ...,
        render_spoilers: SpoilerRenderOptions = ...,
        collapsed_emoji_picker_sections: Sequence[Union[EmojiPickerSection, Snowflake]] = ...,
        collapsed_sticker_picker_sections: Sequence[Union[StickerPickerSection, Snowflake]] = ...,
        animate_emojis: bool = ...,
        animate_stickers: StickerAnimationOptions = ...,
        explicit_content_filter: UserContentFilter = ...,
        show_expression_suggestions: bool = ...,
        use_thread_sidebar: bool = ...,
        view_image_descriptions: bool = ...,
        show_command_suggestions: bool = ...,
        inline_attachment_media: bool = ...,
        inline_embed_media: bool = ...,
        gif_auto_play: bool = ...,
        render_embeds: bool = ...,
        render_reactions: bool = ...,
        enable_tts_command: bool = ...,
        message_display_compact: bool = ...,
        view_nsfw_guilds: bool = ...,
        convert_emoticons: bool = ...,
        view_nsfw_commands: bool = ...,
        use_legacy_chat_input: bool = ...,
        in_app_notifications: bool = ...,
        send_stream_notifications: bool = ...,
        notification_center_acked_before_id: int = ...,
        allow_activity_friend_joins: bool = ...,
        allow_activity_voice_channel_joins: bool = ...,
        friend_source_flags: FriendSourceFlags = ...,
        friend_discovery_flags: FriendDiscoveryFlags = ...,
        drops: bool = ...,
        non_spam_retraining: Optional[bool] = ...,
        restricted_guilds: Sequence[Snowflake] = ...,
        default_guilds_restricted: bool = ...,
        allow_accessibility_detection: bool = ...,
        detect_platform_accounts: bool = ...,
        passwordless: bool = ...,
        contact_sync_enabled: bool = ...,
        activity_restricted_guilds: Sequence[Snowflake] = ...,
        default_guilds_activity_restricted: bool = ...,
        activity_joining_restricted_guilds: Sequence[Snowflake] = ...,
        message_request_restricted_guilds: Sequence[Snowflake] = ...,
        default_message_request_restricted: bool = ...,
        rtc_panel_show_voice_states: bool = ...,
        install_shortcut_desktop: bool = ...,
        install_shortcut_start_menu: bool = ...,
        disable_games_tab: bool = ...,
        status: Status = ...,
        custom_activity: Optional[CustomActivity] = ...,
        show_current_game: bool = ...,
        locale: Locale = ...,
        timezone_offset: int = ...,
        theme: Theme = ...,
        client_theme: Optional[Tuple[int, int, float]] = ...,
        disable_mobile_redesign: bool = ...,
        developer_mode: bool = ...,
        guild_folders: Sequence[GuildFolder] = ...,
        guild_positions: Sequence[Snowflake] = ...,
        user_audio_settings: Collection[AudioContext] = ...,
        stream_audio_settings: Collection[AudioContext] = ...,
        home_auto_navigation: bool = ...,
    ) -> Self:
        ...

    async def edit(self, *, require_version: Union[bool, int] = False, **kwargs: Any) -> Self:
        r"""|coro|

        Edits the current user's settings.

        .. note::

            Settings subsections are not idempotently updated. This means if you change one setting in a subsection\* on an outdated
            instance of :class:`UserSettings` then the other settings in that subsection\* will be reset to the value of the instance.

            When operating on the cached user settings (i.e. :attr:`Client.settings`), this should not be an issue. However, if you
            are operating on a fetched instance, consider using the ``require_version`` parameter to ensure you don't overwrite
            newer settings.

            Any field may be explicitly set to ``MISSING`` to reset it to the default value.

            \* A subsection is a group of settings that are stored in the same top-level protobuf message.
            Examples include Privacy, Text and Images, Voice and Video, etc.

        .. note::

            This method is ratelimited heavily. Updates should be batched together and sent at intervals.

            Infrequent actions do not need a delay. Frequent actions should be delayed by 10 seconds and batched.
            Automated actions (such as migrations or frecency updates) should be delayed by 30 seconds and batched.
            Daily actions (things that change often and are not meaningful, such as emoji frencency) should be delayed by 1 day and batched.

        Parameters
        ----------
        require_version: Union[:class:`bool`, :class:`int`]
            Whether to require the current version of the settings to be the same as the provided version.
            If this is ``True`` then the current version is used.
        \*\*kwargs
            The settings to edit. Refer to the :class:`UserSettings` properties for the valid fields. Unknown fields are ignored.

        Raises
        ------
        HTTPException
            Editing the settings failed.
        TypeError
            At least one setting is required to edit.

        Returns
        -------
        :class:`UserSettings`
            The edited settings. Note that this is a new instance and not the same as the cached instance as mentioned above.
        """
        # As noted above, entire sections MUST be sent, or they will be reset to default values
        # Conversely, we want to omit fields that the user requests to be set to default (by explicitly passing MISSING)
        # For this, we then remove fields set to MISSING from the payload in the payload construction at the end

        if not kwargs:
            raise TypeError('edit() missing at least 1 required keyword-only argument')

        # Only client_version should ever really be sent
        versions = {}
        for field in ('data_version', 'client_version', 'server_version'):
            if field in kwargs:
                versions[field] = kwargs.pop(field)

        inbox = {}
        if 'inbox_tab' in kwargs:
            inbox['current_tab'] = _ocast(kwargs.pop('inbox_tab'), int)
        if 'inbox_tutorial_viewed' in kwargs:
            inbox['viewed_tutorial'] = kwargs.pop('inbox_tutorial_viewed')

        guilds = {}
        if 'guild_progress_settings' in kwargs and kwargs['guild_progress_settings'] is not MISSING:
            guilds['guilds'] = (
                {guild.guild_id: guild.to_dict() for guild in kwargs.pop('guild_progress_settings')}
                if kwargs['guild_progress_settings'] is not MISSING
                else MISSING
            )

        user_content = {}
        if 'dismissed_contents' in kwargs:
            contents = kwargs.pop('dismissed_contents')
            user_content['dismissed_contents'] = (
                struct.pack(f'>{len(contents)}B', *contents) if contents is not MISSING else MISSING
            )
        if 'last_dismissed_promotion_start_date' in kwargs:
            user_content['last_dismissed_outbound_promotion_start_date'] = (
                kwargs.pop('last_dismissed_promotion_start_date').isoformat()
                if kwargs['last_dismissed_promotion_start_date'] is not MISSING
                else MISSING
            )
        if 'nitro_basic_modal_dismissed_at' in kwargs:
            user_content['premium_tier_0_modal_dismissed_at'] = (
                kwargs.pop('nitro_basic_modal_dismissed_at').isoformat()
                if kwargs['nitro_basic_modal_dismissed_at'] is not MISSING
                else MISSING
            )

        voice_and_video = {}
        if 'soundboard_volume' in kwargs:
            voice_and_video['soundboard_settings'] = (
                {'volume': kwargs.pop('soundboard_volume')} if kwargs['soundboard_volume'] is not MISSING else {}
            )
        for field in (
            'afk_timeout',
            'always_preview_video',
            'native_phone_integration_enabled',
            'stream_notifications_enabled',
        ):
            if field in kwargs:
                voice_and_video[field] = kwargs.pop(field)

        text_and_images = {}
        if 'diversity_surrogate' in kwargs:
            text_and_images['diversity_surrogate'] = (
                kwargs.pop('diversity_surrogate') or '' if kwargs['diversity_surrogate'] is not MISSING else MISSING
            )
        if 'render_spoilers' in kwargs:
            text_and_images['render_spoilers'] = _ocast(kwargs.pop('render_spoilers'), str)
        if 'collapsed_emoji_picker_sections' in kwargs:
            text_and_images['emoji_picker_collapsed_sections'] = (
                [str(getattr(x, 'id', x)) for x in kwargs.pop('collapsed_emoji_picker_sections')]
                if kwargs['collapsed_emoji_picker_sections'] is not MISSING
                else MISSING
            )
        if 'collapsed_sticker_picker_sections' in kwargs:
            text_and_images['sticker_picker_collapsed_sections'] = (
                [str(getattr(x, 'id', x)) for x in kwargs.pop('collapsed_sticker_picker_sections')]
                if kwargs['collapsed_sticker_picker_sections'] is not MISSING
                else MISSING
            )
        if 'animate_emojis' in kwargs:
            text_and_images['animate_emoji'] = kwargs.pop('animate_emojis')
        if 'animate_stickers' in kwargs:
            text_and_images['animate_stickers'] = _ocast(kwargs.pop('animate_stickers'), int)
        if 'explicit_content_filter' in kwargs:
            text_and_images['explicit_content_filter'] = _ocast(kwargs.pop('explicit_content_filter'), int)
        if 'show_expression_suggestions' in kwargs:
            text_and_images['expression_suggestions_enabled'] = kwargs.pop('show_expression_suggestions')
        for field in (
            'use_thread_sidebar',
            'view_image_descriptions',
            'show_command_suggestions',
            'inline_attachment_media',
            'inline_embed_media',
            'gif_auto_play',
            'render_embeds',
            'render_reactions',
            'enable_tts_command',
            'message_display_compact',
            'view_nsfw_guilds',
            'convert_emoticons',
            'view_nsfw_commands',
            'use_legacy_chat_input',
            'use_rich_chat_input',
        ):
            if field in kwargs:
                text_and_images[field] = kwargs.pop(field)

        notifications = {}
        if 'in_app_notifications' in kwargs:
            notifications['show_in_app_notifications'] = kwargs.pop('in_app_notifications')
        if 'send_stream_notifications' in kwargs:
            notifications['notify_friends_on_go_live'] = kwargs.pop('send_stream_notifications')
        for field in ('notification_center_acked_before_id',):
            if field in kwargs:
                notifications[field] = kwargs.pop(field)

        privacy = {}
        if 'allow_activity_friend_joins' in kwargs:
            privacy['allow_activity_party_privacy_friends'] = kwargs.pop('allow_activity_friend_joins')
        if 'allow_activity_voice_channel_joins' in kwargs:
            privacy['allow_activity_party_privacy_voice_channel'] = kwargs.pop('allow_activity_voice_channel_joins')
        if 'friend_source_flags' in kwargs:
            privacy['friend_source_flags'] = (
                kwargs.pop('friend_source_flags').value if kwargs['friend_source_flags'] is not MISSING else MISSING
            )
        if 'friend_discovery_flags' in kwargs:
            privacy['friend_discovery_flags'] = (
                kwargs.pop('friend_discovery_flags').value if kwargs['friend_discovery_flags'] is not MISSING else MISSING
            )
        if 'drops' in kwargs:
            privacy['drops_opted_out'] = not kwargs.pop('drops') if kwargs['drops'] is not MISSING else MISSING
        if 'non_spam_retraining' in kwargs:
            privacy['non_spam_retraining_opt_in'] = (
                kwargs.pop('non_spam_retraining') if kwargs['non_spam_retraining'] not in {None, MISSING} else MISSING
            )
        for field in (
            'restricted_guilds',
            'default_guilds_restricted',
            'allow_accessibility_detection',
            'detect_platform_accounts',
            'passwordless',
            'contact_sync_enabled',
            'activity_restricted_guilds',
            'default_guilds_activity_restricted',
            'activity_joining_restricted_guilds',
            'message_request_restricted_guilds',
            'default_message_request_restricted',
        ):
            if field in kwargs:
                if field.endswith('_guilds'):
                    privacy[field.replace('_guilds', '_guild_ids')] = [g.id for g in kwargs.pop(field)]
                else:
                    privacy[field] = kwargs.pop(field)

        debug = {}
        for field in ('rtc_panel_show_voice_states',):
            if field in kwargs:
                debug[field] = kwargs.pop(field)

        game_library = {}
        for field in ('install_shortcut_desktop', 'install_shortcut_start_menu', 'disable_games_tab'):
            if field in kwargs:
                game_library[field] = kwargs.pop(field)

        status = {}
        if 'status' in kwargs:
            status['status'] = _ocast(kwargs.pop('status'), str)
        if 'custom_activity' in kwargs:
            status['custom_status'] = (
                kwargs.pop('custom_activity').to_settings_dict()
                if kwargs['custom_activity'] not in {MISSING, None}
                else MISSING
            )
        for field in ('show_current_game',):
            if field in kwargs:
                status[field] = kwargs.pop(field)

        localization = {}
        if 'locale' in kwargs:
            localization['locale'] = _ocast(kwargs.pop('locale'), str)
        for field in ('timezone_offset',):
            if field in kwargs:
                localization[field] = kwargs.pop(field)

        appearance = {}
        if 'theme' in kwargs:
            appearance['theme'] = _ocast(kwargs.pop('theme'), int)
        if 'client_theme' in kwargs:
            provided: tuple = kwargs.pop('client_theme')
            client_theme_settings = {} if provided is not MISSING else MISSING
            if provided:
                if provided[0] is not MISSING:
                    client_theme_settings['primary_color'] = provided[0]
                if len(provided) > 1 and provided[1] is not MISSING:
                    client_theme_settings['background_gradient_preset_id'] = provided[1]
                if len(provided) > 2 and provided[2] is not MISSING:
                    client_theme_settings['background_gradient_angle'] = float(provided[2])
                appearance['client_theme_settings'] = client_theme_settings
        if 'disable_mobile_redesign' in kwargs:
            appearance['mobile_redesign_disabled'] = kwargs.pop('disable_mobile_redesign')
        for field in ('developer_mode',):
            if field in kwargs:
                appearance[field] = kwargs.pop(field)

        guild_folders = {}
        if 'guild_folders' in kwargs:
            guild_folders['folders'] = (
                [f.to_dict() for f in kwargs.pop('guild_folders')] if kwargs['guild_folders'] is not MISSING else MISSING
            )
        if 'guild_positions' in kwargs:
            guild_folders['guild_positions'] = (
                [g.id for g in kwargs.pop('guild_positions')] if kwargs['guild_positions'] is not MISSING else MISSING
            )

        audio_context_settings = {}
        if 'user_audio_settings' in kwargs:
            audio_context_settings['user'] = (
                {s.id: s.to_dict() for s in kwargs.pop('user_audio_settings')}
                if kwargs['user_audio_settings'] is not MISSING
                else MISSING
            )
        if 'stream_audio_settings' in kwargs:
            audio_context_settings['stream'] = (
                {s.id: s.to_dict() for s in kwargs.pop('stream_audio_settings')}
                if kwargs['stream_audio_settings'] is not MISSING
                else MISSING
            )

        communities = {}
        if 'home_auto_navigation' in kwargs:
            communities['disable_home_auto_nav'] = (
                not kwargs.pop('home_auto_navigation') if kwargs['home_auto_navigation'] is not MISSING else MISSING
            )

        # Now, we do the actual patching
        existing = self.to_dict()
        payload = {}
        for subsetting in (
            'versions',
            'inbox',
            'guilds',
            'user_content',
            'voice_and_video',
            'text_and_images',
            'notifications',
            'privacy',
            'debug',
            'game_library',
            'status',
            'localization',
            'appearance',
            'guild_folders',
            'audio_context_settings',
            'communities',
        ):
            subsetting_dict = locals()[subsetting]
            if subsetting_dict:
                original = existing.get(subsetting, {})
                original.update(subsetting_dict)
                for k, v in dict(original).items():
                    if v is MISSING:
                        del original[k]
                payload[subsetting] = original

        state = self._state
        require_version = self.data_version if require_version == True else require_version
        ret = await state.http.edit_proto_settings(1, self.dict_to_base64(payload), require_version or None)
        return UserSettings(state, ret['settings'])


class GuildFolder:
    """Represents a guild folder.

    All properties have setters to faciliate editing the class for use with :meth:`UserSettings.edit`.

    .. container:: operations

        .. describe:: str(x)

            Returns the folder's name.

        .. describe:: len(x)

            Returns the number of guilds in the folder.

    .. versionadded:: 1.9

    .. versionchanged:: 2.0

        Removed various operations and made ``id`` and ``name`` optional.

    .. note::

        Guilds not in folders *are* actually in folders API wise, with them being the only member.

        These folders do not have an ID or name.

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of the folder.
    name: Optional[:class:`str`]
        The name of the folder.
    """

    __slots__ = ('_state', 'id', 'name', '_colour', '_guild_ids')

    def __init__(
        self,
        *,
        id: Optional[int] = None,
        name: Optional[str] = None,
        colour: Optional[Colour] = None,
        guilds: Sequence[Snowflake] = MISSING,
    ):
        self._state: Optional[ConnectionState] = None
        self.id: Optional[int] = id
        self.name: Optional[str] = name
        self._colour: Optional[int] = colour.value if colour else None
        self._guild_ids: List[int] = [guild.id for guild in guilds] if guilds else []

    def __str__(self) -> str:
        return self.name or ', '.join(guild.name for guild in [guild for guild in self.guilds if isinstance(guild, Guild)])

    def __repr__(self) -> str:
        return f'<GuildFolder id={self.id} name={self.name!r} guilds={self.guilds!r}>'

    def __len__(self) -> int:
        return len(self._guild_ids)

    @classmethod
    def _from_legacy_settings(cls, *, data: Dict[str, Any], state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.id = _get_as_snowflake(data, 'id')
        self.name = data.get('name')
        self._colour = data.get('color')
        self._guild_ids = [int(guild_id) for guild_id in data['guild_ids']]
        return self

    @classmethod
    def _from_settings(cls, *, data: Any, state: ConnectionState) -> Self:
        """
        message GuildFolder {
            repeated fixed64 guild_ids = 1;
            optional google.protobuf.Int64Value id = 2;
            optional google.protobuf.StringValue name = 3;
            optional google.protobuf.UInt64Value color = 4;
        }
        """
        self = cls.__new__(cls)
        self._state = state
        self.id = data.id.value
        self.name = data.name.value
        self._colour = data.color.value if data.HasField('color') else None
        self._guild_ids = data.guild_ids
        return self

    def _get_guild(self, id, /) -> Union[Guild, Object]:
        from .guild import Guild  # circular import

        id = int(id)
        return self._state._get_or_create_unavailable_guild(id) if self._state else Object(id=id, type=Guild)

    def to_dict(self) -> dict:
        ret = {}
        if self.id is not None:
            ret['id'] = self.id
        if self.name is not None:
            ret['name'] = self.name
        if self._colour is not None:
            ret['color'] = self._colour
        ret['guild_ids'] = [str(guild_id) for guild_id in self._guild_ids]
        return ret

    def copy(self) -> Self:
        """Returns a shallow copy of the folder."""
        return self.__class__._from_legacy_settings(data=self.to_dict(), state=self._state)  # type: ignore

    def add_guild(self, guild: Snowflake) -> Self:
        """Adds a guild to the folder.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 2.0

        Parameters
        -----------
        guild: :class:`abc.Snowflake`
            The guild to add to the folder.
        """
        self._guild_ids.append(guild.id)
        return self

    def insert_guild_at(self, index: int, guild: Snowflake) -> Self:
        """Inserts a guild before a specified index to the folder.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 2.0

        Parameters
        -----------
        index: :class:`int`
            The index of where to insert the field.
        guild: :class:`abc.Snowflake`
            The guild to add to the folder.
        """
        self._guild_ids.insert(index, guild.id)
        return self

    def clear_guilds(self) -> None:
        """Removes all guilds from this folder.

        .. versionadded:: 2.0
        """
        self._guild_ids.clear()

    def remove_guild(self, index: int) -> None:
        """Removes a guild at a specified index.

        If the index is invalid or out of bounds then the error is
        silently swallowed.

        .. note::

            When deleting a field by index, the index of the other fields
            shift to fill the gap just like a regular list.

        .. versionadded:: 2.0

        Parameters
        -----------
        index: :class:`int`
            The index of the field to remove.
        """
        try:
            del self._guild_ids[index]
        except IndexError:
            pass

    def set_guild_at(self, index: int, guild: Snowflake) -> Self:
        """Modifies a guild to the guild object.

        The index must point to a valid pre-existing guild.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 2.0

        Parameters
        -----------
        index: :class:`int`
            The index of the field to modify.
        guild: :class:`abc.Snowflake`
            The guild to add to the folder.

        Raises
        -------
        IndexError
            An invalid index was provided.
        """
        self._guild_ids[index] = guild.id

        try:
            self._guild_ids[index] = guild.id
        except (TypeError, IndexError):
            raise IndexError('field index out of range')
        return self

    @property
    def guilds(self) -> List[Union[Guild, Object]]:
        """List[Union[:class:`Guild`, :class:`Object`]]: The guilds in the folder. Always :class:`Object` if state is not attached."""
        return [self._get_guild(guild_id) for guild_id in self._guild_ids]

    @guilds.setter
    def guilds(self, value: Sequence[Snowflake]) -> None:
        self._guild_ids = [guild.id for guild in value]

    @property
    def colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: The colour code of the folder. There is an alias for this named :attr:`colour`."""
        return Colour(self._colour) if self._colour is not None else None

    @colour.setter
    def colour(self, value: Optional[Union[int, Colour]]) -> None:
        if value is None:
            self._colour = None
        elif isinstance(value, Colour):
            self._colour = value.value
        elif isinstance(value, int):
            self._colour = value
        else:
            raise TypeError(f'Expected discord.Colour, int, or None but received {value.__class__.__name__} instead.')

    @property
    def color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: The colour code of the folder. There is an alias for this named :attr:`colour`."""
        return self.colour

    @color.setter
    def color(self, value: Optional[Union[int, Colour]]) -> None:
        self.colour = value


class GuildProgress:
    """Represents a guild's settings revolving around upsells, promotions, and feature progress.

    All properties have setters to faciliate editing the class for use with :meth:`UserSettings.edit`.

    .. versionadded:: 2.0

    Attributes
    ----------
    guild_id: :class:`int`
        The ID of the guild.
    recents_dismissed_at: Optional[:class:`datetime.datetime`]
        When the guild recents were last dismissed.
    """

    __slots__ = (
        'guild_id',
        '_hub_progress',
        '_onboarding_progress',
        'recents_dismissed_at',
        '_dismissed_contents',
        '_collapsed_channel_ids',
        '_state',
    )

    def __init__(
        self,
        guild_id: int,
        *,
        hub_progress: HubProgressFlags,
        onboarding_progress: OnboardingProgressFlags,
        recents_dismissed_at: Optional[datetime] = None,
        dismissed_contents: Sequence[int] = MISSING,
        collapsed_channels: List[Snowflake] = MISSING,
    ) -> None:
        self._state: Optional[ConnectionState] = None
        self.guild_id = guild_id
        self._hub_progress = hub_progress.value
        self._onboarding_progress = onboarding_progress.value
        self.recents_dismissed_at: Optional[datetime] = recents_dismissed_at
        self._dismissed_contents = self._pack_dismissed_contents(dismissed_contents or [])
        self._collapsed_channel_ids = [channel.id for channel in collapsed_channels] or []

    def __repr__(self) -> str:
        return f'<GuildProgress guild_id={self.guild_id} hub_progress={self.hub_progress!r} onboarding_progress={self.onboarding_progress!r}>'

    @classmethod
    def _from_settings(cls, guild_id: int, *, data: Any, state: ConnectionState) -> Self:
        """
        message ChannelSettings {
            bool collapsed_in_inbox = 1;
        }

        message GuildSettings {
            map<fixed64, ChannelSettings> channels = 1;
            uint32 hub_progress = 2;
            uint32 guild_onboarding_progress = 3;
            optional google.protobuf.Timestamp guild_recents_dismissed_at = 4;
            bytes dismissed_guild_content = 5;
        }

        message AllGuildSettings {
            map<fixed64, GuildSettings> guilds = 1;
        }
        """
        self = cls.__new__(cls)
        self._state = state
        self.guild_id = guild_id
        self._hub_progress = data.hub_progress
        self._onboarding_progress = data.guild_onboarding_progress
        self.recents_dismissed_at = (
            data.guild_recents_dismissed_at.ToDatetime(tzinfo=timezone.utc)
            if data.HasField('guild_recents_dismissed_at')
            else None
        )
        self._dismissed_contents = data.dismissed_guild_content
        self._collapsed_channel_ids = [
            channel_id for channel_id, settings in data.channels.items() if settings.collapsed_in_inbox
        ]
        return self

    def _get_channel(self, id: int, /) -> Union[GuildChannel, Object]:
        id = int(id)
        return self.guild.get_channel(id) or Object(id=id) if self.guild is not None else Object(id=id)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'hub_progress': self._hub_progress,
            'guild_onboarding_progress': self._onboarding_progress,
            'dismissed_guild_content': self._dismissed_contents,
            'channels': {id: {'collapsed_in_inbox': True} for id in self._collapsed_channel_ids},
        }
        if self.recents_dismissed_at is not None:
            data['guild_recents_dismissed_at'] = self.recents_dismissed_at.isoformat()
        return data

    def copy(self) -> Self:
        """Returns a shallow copy of the progress settings."""
        cls = self.__class__(self.guild_id, hub_progress=self.hub_progress, onboarding_progress=self.onboarding_progress, recents_dismissed_at=self.recents_dismissed_at, dismissed_contents=self.dismissed_contents, collapsed_channels=self.collapsed_channels)  # type: ignore
        cls._state = self._state
        return cls

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this progress belongs to. ``None`` if state is not attached."""
        return self._state._get_or_create_unavailable_guild(self.guild_id) if self._state is not None else None

    @property
    def hub_progress(self) -> HubProgressFlags:
        """:class:`HubProgressFlags`: The hub's usage and feature progress."""
        return HubProgressFlags._from_value(self._hub_progress)

    @hub_progress.setter
    def hub_progress(self, value: HubProgressFlags) -> None:
        self._hub_progress = value.value

    @property
    def onboarding_progress(self) -> OnboardingProgressFlags:
        """:class:`OnboardingProgressFlags`: The guild's onboarding usage and feature progress."""
        return OnboardingProgressFlags._from_value(self._onboarding_progress)

    @onboarding_progress.setter
    def onboarding_progress(self, value: OnboardingProgressFlags) -> None:
        self._onboarding_progress = value.value

    @staticmethod
    def _pack_dismissed_contents(contents: Sequence[int]) -> bytes:
        return struct.pack(f'>{len(contents)}B', *contents)

    @property
    def dismissed_contents(self) -> Tuple[int, ...]:
        """Tuple[:class:`int`]: A list of enum values representing per-guild dismissable content in the app.

        .. note::

            For now, this just returns the raw values without converting to a proper enum,
            as the enum values change too often to be viably maintained.
        """
        contents = self._dismissed_contents
        return struct.unpack(f'>{len(contents)}B', contents)

    @dismissed_contents.setter
    def dismissed_contents(self, value: Sequence[int]) -> None:
        self._dismissed_contents = self._pack_dismissed_contents(value)

    @property
    def collapsed_channels(self) -> List[Union[GuildChannel, Object]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`Object`]]: A list of guild channels that are collapsed in the inbox. Always :class:`Object` if state is not attached."""
        return list(map(self._get_channel, self._collapsed_channel_ids))

    @collapsed_channels.setter
    def collapsed_channels(self, value: Sequence[Snowflake]) -> None:
        self._collapsed_channel_ids = [channel.id for channel in value]


class AudioContext:
    """Represents saved audio settings for a user or stream.

    All properties have setters to faciliate editing the class for use with :meth:`UserSettings.edit`.

    .. versionadded:: 2.0

    Attributes
    ----------
    user_id: :class:`int`
        The ID of the user.
    muted: :class:`bool`
        Whether the user or stream is muted.
    volume: :class:`float`
        The volume of the user or stream (0-100).
    modified_at: :class:`datetime.datetime`
        The time the settings were last modified.
    """

    __slots__ = ('_state', 'user_id', 'muted', 'volume', 'modified_at')

    def __init__(self, user_id: int, *, muted: bool = False, volume: float) -> None:
        self._state: Optional[ConnectionState] = None
        self.user_id = user_id
        self.muted = muted
        self.volume = volume
        self.modified_at = utcnow()

    def __repr__(self) -> str:
        return (
            f'<AudioContext user_id={self.user_id} muted={self.muted} volume={self.volume} modified_at={self.modified_at!r}>'
        )

    @classmethod
    def _from_settings(cls, user_id: int, *, data: Any, state: ConnectionState) -> Self:
        """
        message AudioContextSetting {
            bool muted = 1;
            float volume = 2;
            fixed64 modified_at = 3;
        }
        """
        self = cls.__new__(cls)
        self._state = state
        self.user_id = user_id
        self.muted = data.muted
        self.volume = data.volume
        self.modified_at = parse_timestamp(data.modified_at)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Converts the object to a dictionary."""
        return {
            'user_id': self.user_id,
            'muted': self.muted,
            'volume': self.volume,
            'modified_at': self.modified_at.isoformat(),
        }

    def copy(self) -> Self:
        """Returns a shallow copy of the audio context."""
        cls = self.__class__(self.user_id, muted=self.muted, volume=self.volume)
        cls.modified_at = self.modified_at
        cls._state = self._state
        return cls

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`User`]: The user the settings are for. ``None`` if state is not attached."""
        return self._state.get_user(self.user_id) if self._state is not None else None


class LegacyUserSettings:
    """Represents the legacy Discord client settings.

    .. versionadded:: 1.9

    .. deprecated:: 2.0

    .. note::

        Discord has migrated user settings to a new protocol buffer format.
        While these legacy settings still exist, they are no longer sent to newer clients (so they will have to be fetched).

        The new settings are available in :class:`UserSettings`, and this class has been deprecated and renamed to :class:`LegacyUserSettings`.
        All options in this class are available in the new format, and changes are reflected in both.

    Attributes
    ----------
    afk_timeout: :class:`int`
        How long (in seconds) the user needs to be AFK until Discord
        sends push notifications to mobile devices (30-600).
    allow_accessibility_detection: :class:`bool`
        Whether to allow Discord to track screen reader usage.
    animate_emojis: :class:`bool`
        Whether to animate emojis in the chat.
    contact_sync_enabled: :class:`bool`
        Whether to enable the contact sync on Discord mobile.
    convert_emoticons: :class:`bool`
        Whether to automatically convert emoticons into emojis (e.g. :) -> 😃).
    default_guilds_restricted: :class:`bool`
        Whether to automatically disable DMs between you and
        members of new guilds you join.
    detect_platform_accounts: :class:`bool`
        Whether to automatically detect accounts from services
        like Steam and Blizzard when you open the Discord client.
    developer_mode: :class:`bool`
        Whether to enable developer mode.
    disable_games_tab: :class:`bool`
        Whether to disable the showing of the Games tab.
    enable_tts_command: :class:`bool`
        Whether to allow TTS messages to be played/sent.
    gif_auto_play: :class:`bool`
        Whether to automatically play GIFs that are in the chat.
    inline_attachment_media: :class:`bool`
        Whether to display attachments when they are uploaded in chat.
    inline_embed_media: :class:`bool`
        Whether to display videos and images from links posted in chat.
    message_display_compact: :class:`bool`
        Whether to use the compact Discord display mode.
    native_phone_integration_enabled: :class:`bool`
        Whether to enable the new Discord mobile phone number friend
        requesting features.
    render_embeds: :class:`bool`
        Whether to render embeds that are sent in the chat.
    render_reactions: :class:`bool`
        Whether to render reactions that are added to messages.
    show_current_game: :class:`bool`
        Whether to display the game that you are currently playing.
    stream_notifications_enabled: :class:`bool`
        Whether stream notifications for friends will be received.
    timezone_offset: :class:`int`
        The timezone offset from UTC to use (in minutes).
    view_nsfw_commands: :class:`bool`
        Whether to show NSFW application commands in DMs.

        .. versionadded:: 2.0
    view_nsfw_guilds: :class:`bool`
        Whether to show NSFW guilds on iOS.
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
        return '<LegacyUserSettings>'

    def _get_guild(self, id: int, /) -> Guild:
        return self._state._get_or_create_unavailable_guild(int(id))

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

    async def edit(self, **kwargs) -> Self:
        """|coro|

        Edits the client user's settings.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited settings are returned.

        .. deprecated:: 2.0

        Parameters
        ----------
        activity_restricted_guilds: List[:class:`~discord.abc.Snowflake`]
            A list of guilds that your current activity will not be shown in.

            .. versionadded:: 2.0
        activity_joining_restricted_guilds: List[:class:`~discord.abc.Snowflake`]
            A list of guilds that will not be able to join your current activity.

            .. versionadded:: 2.0
        afk_timeout: :class:`int`
            How long (in seconds) the user needs to be AFK until Discord
            sends push notifications to mobile device (30-600).
        allow_accessibility_detection: :class:`bool`
            Whether to allow Discord to track screen reader usage.
        animate_emojis: :class:`bool`
            Whether to animate emojis in the chat.
        animate_stickers: :class:`.StickerAnimationOptions`
            Whether to animate stickers in the chat.
        contact_sync_enabled: :class:`bool`
            Whether to enable the contact sync on Discord mobile.
        convert_emoticons: :class:`bool`
            Whether to automatically convert emoticons into emojis (e.g. :) -> 😃).
        default_guilds_restricted: :class:`bool`
            Whether to automatically disable DMs between you and
            members of new guilds you join.
        detect_platform_accounts: :class:`bool`
            Whether to automatically detect accounts from services
            like Steam and Blizzard when you open the Discord client.
        developer_mode: :class:`bool`
            Whether to enable developer mode.
        disable_games_tab: :class:`bool`
            Whether to disable the showing of the Games tab.
        enable_tts_command: :class:`bool`
            Whether to allow TTS messages to be played/sent.
        explicit_content_filter: :class:`.UserContentFilter`
            The filter for explicit content in all messages.
        friend_source_flags: :class:`.FriendSourceFlags`
            Who can add you as a friend.
        friend_discovery_flags: :class:`.FriendDiscoveryFlags`
            How you get recommended friends.
        gif_auto_play: :class:`bool`
            Whether to automatically play GIFs that are in the chat.
        guild_positions: List[:class:`~discord.abc.Snowflake`]
            A list of guilds in order of the guild/guild icons that are on
            the left hand side of the UI.
        inline_attachment_media: :class:`bool`
            Whether to display attachments when they are uploaded in chat.
        inline_embed_media: :class:`bool`
            Whether to display videos and images from links posted in chat.
        locale: :class:`.Locale`
            The :rfc:`3066` language identifier of the locale to use for the language
            of the Discord client.
        message_display_compact: :class:`bool`
            Whether to use the compact Discord display mode.
        native_phone_integration_enabled: :class:`bool`
            Whether to enable the new Discord mobile phone number friend
            requesting features.
        passwordless: :class:`bool`
            Whether to enable passwordless login.
        render_embeds: :class:`bool`
            Whether to render embeds that are sent in the chat.
        render_reactions: :class:`bool`
            Whether to render reactions that are added to messages.
        restricted_guilds: List[:class:`~discord.abc.Snowflake`]
            A list of guilds that you will not receive DMs from.
        show_current_game: :class:`bool`
            Whether to display the game that you are currently playing.
        stream_notifications_enabled: :class:`bool`
            Whether stream notifications for friends will be received.
        theme: :class:`.Theme`
            The overall theme of the Discord UI.
        timezone_offset: :class:`int`
            The timezone offset to use.
        view_nsfw_commands: :class:`bool`
            Whether to show NSFW application commands in DMs.

            .. versionadded:: 2.0
        view_nsfw_guilds: :class:`bool`
            Whether to show NSFW guilds on iOS.

            .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Editing the settings failed.

        Returns
        -------
        :class:`.UserSettings`
            The client user's updated settings.
        """
        return await self._state.client.edit_legacy_settings(**kwargs)

    @property
    def activity_restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that your current activity will not be shown in.

        .. versionadded:: 2.0
        """
        return list(map(self._get_guild, getattr(self, '_activity_restricted_guild_ids', [])))

    @property
    def activity_joining_restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that will not be able to join your current activity.

        .. versionadded:: 2.0
        """
        return list(map(self._get_guild, getattr(self, '_activity_joining_restricted_guild_ids', [])))

    @property
    def animate_stickers(self) -> StickerAnimationOptions:
        """:class:`StickerAnimationOptions`: Whether to animate stickers in the chat."""
        return try_enum(StickerAnimationOptions, getattr(self, '_animate_stickers', 0))

    @property
    def custom_activity(self) -> Optional[CustomActivity]:
        """Optional[:class:`CustomActivity`]: The set custom activity."""
        return CustomActivity._from_legacy_settings(data=getattr(self, '_custom_status', None), state=self._state)

    @property
    def explicit_content_filter(self) -> UserContentFilter:
        """:class:`UserContentFilter`: The filter for explicit content in all messages."""
        return try_enum(UserContentFilter, getattr(self, '_explicit_content_filter', 0))

    @property
    def friend_source_flags(self) -> FriendSourceFlags:
        """:class:`FriendSourceFlags`: Who can add you as a friend."""
        return FriendSourceFlags._from_dict(getattr(self, '_friend_source_flags', {'all': True}))

    @property
    def friend_discovery_flags(self) -> FriendDiscoveryFlags:
        """:class:`FriendDiscoveryFlags`: How you get recommended friends."""
        return FriendDiscoveryFlags._from_value(getattr(self, '_friend_discovery_flags', 0))

    @property
    def guild_folders(self) -> List[GuildFolder]:
        """List[:class:`GuildFolder`]: A list of guild folders."""
        state = self._state
        return [
            GuildFolder._from_legacy_settings(data=folder, state=state) for folder in getattr(self, '_guild_folders', [])
        ]

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
        """:class:`bool`: Whether to enable passwordless login."""
        return getattr(self, '_passwordless', False)

    @property
    def restricted_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: A list of guilds that you will not receive DMs from."""
        return list(map(self._get_guild, getattr(self, '_restricted_guilds', [])))

    @property
    def status(self) -> Status:
        """Optional[:class:`Status`]: The configured status."""
        return try_enum(Status, getattr(self, '_status', 'online'))

    @property
    def theme(self) -> Theme:
        """:class:`Theme`: The overall theme of the Discord UI."""
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
        """Union[:class:`abc.GuildChannel`, :class:`abc.PrivateChannel`]: Returns the channel these settings are for."""
        guild = self._state._get_or_create_unavailable_guild(self._guild_id) if self._guild_id else None
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
            return self._state._get_or_create_unavailable_guild(self._guild_id)
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
