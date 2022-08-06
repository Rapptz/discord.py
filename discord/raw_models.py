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

import datetime
from typing import TYPE_CHECKING, Optional, Set, List, Tuple, Union

from .enums import ChannelType, try_enum
from .utils import _get_as_snowflake
from .app_commands import AppCommandPermissions

if TYPE_CHECKING:
    from .types.gateway import (
        MessageDeleteEvent,
        MessageDeleteBulkEvent as BulkMessageDeleteEvent,
        MessageReactionAddEvent,
        MessageReactionRemoveEvent,
        MessageReactionRemoveAllEvent as ReactionClearEvent,
        MessageReactionRemoveEmojiEvent as ReactionClearEmojiEvent,
        MessageUpdateEvent,
        IntegrationDeleteEvent,
        ThreadUpdateEvent,
        ThreadDeleteEvent,
        ThreadMembersUpdate,
        TypingStartEvent,
        GuildMemberRemoveEvent,
    )
    from .types.command import GuildApplicationCommandPermissions
    from .message import Message
    from .partial_emoji import PartialEmoji
    from .member import Member
    from .threads import Thread
    from .user import User
    from .state import ConnectionState
    from .guild import Guild

    ReactionActionEvent = Union[MessageReactionAddEvent, MessageReactionRemoveEvent]


__all__ = (
    'RawMessageDeleteEvent',
    'RawBulkMessageDeleteEvent',
    'RawMessageUpdateEvent',
    'RawReactionActionEvent',
    'RawReactionClearEvent',
    'RawReactionClearEmojiEvent',
    'RawIntegrationDeleteEvent',
    'RawThreadUpdateEvent',
    'RawThreadDeleteEvent',
    'RawThreadMembersUpdate',
    'RawTypingEvent',
    'RawMemberRemoveEvent',
    'RawAppCommandPermissionsUpdateEvent',
)


class _RawReprMixin:
    __slots__: Tuple[str, ...] = ()

    def __repr__(self) -> str:
        value = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'<{self.__class__.__name__} {value}>'


class RawMessageDeleteEvent(_RawReprMixin):
    """Represents the event payload for a :func:`on_raw_message_delete` event.

    Attributes
    ------------
    channel_id: :class:`int`
        The channel ID where the deletion took place.
    guild_id: Optional[:class:`int`]
        The guild ID where the deletion took place, if applicable.
    message_id: :class:`int`
        The message ID that got deleted.
    cached_message: Optional[:class:`Message`]
        The cached message, if found in the internal message cache.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'cached_message')

    def __init__(self, data: MessageDeleteEvent) -> None:
        self.message_id: int = int(data['id'])
        self.channel_id: int = int(data['channel_id'])
        self.cached_message: Optional[Message] = None
        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None


class RawBulkMessageDeleteEvent(_RawReprMixin):
    """Represents the event payload for a :func:`on_raw_bulk_message_delete` event.

    Attributes
    -----------
    message_ids: Set[:class:`int`]
        A :class:`set` of the message IDs that were deleted.
    channel_id: :class:`int`
        The channel ID where the message got deleted.
    guild_id: Optional[:class:`int`]
        The guild ID where the message got deleted, if applicable.
    cached_messages: List[:class:`Message`]
        The cached messages, if found in the internal message cache.
    """

    __slots__ = ('message_ids', 'channel_id', 'guild_id', 'cached_messages')

    def __init__(self, data: BulkMessageDeleteEvent) -> None:
        self.message_ids: Set[int] = {int(x) for x in data.get('ids', [])}
        self.channel_id: int = int(data['channel_id'])
        self.cached_messages: List[Message] = []

        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None


class RawMessageUpdateEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_message_edit` event.

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got updated.
    channel_id: :class:`int`
        The channel ID where the update took place.

        .. versionadded:: 1.3
    guild_id: Optional[:class:`int`]
        The guild ID where the message got updated, if applicable.

        .. versionadded:: 1.7

    data: :class:`dict`
        The raw data given by the :ddocs:`gateway <topics/gateway#message-update>`
    cached_message: Optional[:class:`Message`]
        The cached message, if found in the internal message cache. Represents the message before
        it is modified by the data in :attr:`RawMessageUpdateEvent.data`.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'data', 'cached_message')

    def __init__(self, data: MessageUpdateEvent) -> None:
        self.message_id: int = int(data['id'])
        self.channel_id: int = int(data['channel_id'])
        self.data: MessageUpdateEvent = data
        self.cached_message: Optional[Message] = None

        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None


class RawReactionActionEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_reaction_add` or
    :func:`on_raw_reaction_remove` event.

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got or lost a reaction.
    user_id: :class:`int`
        The user ID who added the reaction or whose reaction was removed.
    channel_id: :class:`int`
        The channel ID where the reaction got added or removed.
    guild_id: Optional[:class:`int`]
        The guild ID where the reaction got added or removed, if applicable.
    emoji: :class:`PartialEmoji`
        The custom or unicode emoji being used.
    member: Optional[:class:`Member`]
        The member who added the reaction. Only available if `event_type` is `REACTION_ADD` and the reaction is inside a guild.

        .. versionadded:: 1.3

    event_type: :class:`str`
        The event type that triggered this action. Can be
        ``REACTION_ADD`` for reaction addition or
        ``REACTION_REMOVE`` for reaction removal.

        .. versionadded:: 1.3
    """

    __slots__ = ('message_id', 'user_id', 'channel_id', 'guild_id', 'emoji', 'event_type', 'member')

    def __init__(self, data: ReactionActionEvent, emoji: PartialEmoji, event_type: str) -> None:
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])
        self.user_id: int = int(data['user_id'])
        self.emoji: PartialEmoji = emoji
        self.event_type: str = event_type
        self.member: Optional[Member] = None

        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None


class RawReactionClearEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_reaction_clear` event.

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got its reactions cleared.
    channel_id: :class:`int`
        The channel ID where the reactions got cleared.
    guild_id: Optional[:class:`int`]
        The guild ID where the reactions got cleared.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id')

    def __init__(self, data: ReactionClearEvent) -> None:
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])

        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None


class RawReactionClearEmojiEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_reaction_clear_emoji` event.

    .. versionadded:: 1.3

    Attributes
    -----------
    message_id: :class:`int`
        The message ID that got its reactions cleared.
    channel_id: :class:`int`
        The channel ID where the reactions got cleared.
    guild_id: Optional[:class:`int`]
        The guild ID where the reactions got cleared.
    emoji: :class:`PartialEmoji`
        The custom or unicode emoji being removed.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', 'emoji')

    def __init__(self, data: ReactionClearEmojiEvent, emoji: PartialEmoji) -> None:
        self.emoji: PartialEmoji = emoji
        self.message_id: int = int(data['message_id'])
        self.channel_id: int = int(data['channel_id'])

        try:
            self.guild_id: Optional[int] = int(data['guild_id'])
        except KeyError:
            self.guild_id: Optional[int] = None


class RawIntegrationDeleteEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_integration_delete` event.

    .. versionadded:: 2.0

    Attributes
    -----------
    integration_id: :class:`int`
        The ID of the integration that got deleted.
    application_id: Optional[:class:`int`]
        The ID of the bot/OAuth2 application for this deleted integration.
    guild_id: :class:`int`
        The guild ID where the integration got deleted.
    """

    __slots__ = ('integration_id', 'application_id', 'guild_id')

    def __init__(self, data: IntegrationDeleteEvent) -> None:
        self.integration_id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])

        try:
            self.application_id: Optional[int] = int(data['application_id'])
        except KeyError:
            self.application_id: Optional[int] = None


class RawThreadUpdateEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_thread_update` event.

    .. versionadded:: 2.0

    Attributes
    ----------
    thread_id: :class:`int`
        The ID of the thread that was updated.
    thread_type: :class:`discord.ChannelType`
        The channel type of the updated thread.
    guild_id: :class:`int`
        The ID of the guild the thread is in.
    parent_id: :class:`int`
        The ID of the channel the thread belongs to.
    data: :class:`dict`
        The raw data given by the :ddocs:`gateway <topics/gateway#thread-update>`
    thread: Optional[:class:`discord.Thread`]
        The thread, if it could be found in the internal cache.
    """

    __slots__ = ('thread_id', 'thread_type', 'parent_id', 'guild_id', 'data', 'thread')

    def __init__(self, data: ThreadUpdateEvent) -> None:
        self.thread_id: int = int(data['id'])
        self.thread_type: ChannelType = try_enum(ChannelType, data['type'])
        self.guild_id: int = int(data['guild_id'])
        self.parent_id: int = int(data['parent_id'])
        self.data: ThreadUpdateEvent = data
        self.thread: Optional[Thread] = None


class RawThreadDeleteEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_thread_delete` event.

    .. versionadded:: 2.0

    Attributes
    ----------
    thread_id: :class:`int`
        The ID of the thread that was deleted.
    thread_type: :class:`discord.ChannelType`
        The channel type of the deleted thread.
    guild_id: :class:`int`
        The ID of the guild the thread was deleted in.
    parent_id: :class:`int`
        The ID of the channel the thread belonged to.
    thread: Optional[:class:`discord.Thread`]
        The thread, if it could be found in the internal cache.
    """

    __slots__ = ('thread_id', 'thread_type', 'parent_id', 'guild_id', 'thread')

    def __init__(self, data: ThreadDeleteEvent) -> None:
        self.thread_id: int = int(data['id'])
        self.thread_type: ChannelType = try_enum(ChannelType, data['type'])
        self.guild_id: int = int(data['guild_id'])
        self.parent_id: int = int(data['parent_id'])
        self.thread: Optional[Thread] = None


class RawThreadMembersUpdate(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_thread_member_remove` event.

    .. versionadded:: 2.0

    Attributes
    ----------
    thread_id: :class:`int`
        The ID of the thread that was updated.
    guild_id: :class:`int`
        The ID of the guild the thread is in.
    member_count: :class:`int`
        The approximate number of members in the thread. This caps at 50.
    data: :class:`dict`
        The raw data given by the :ddocs:`gateway <topics/gateway#thread-members-update>`.
    """

    __slots__ = ('thread_id', 'guild_id', 'member_count', 'data')

    def __init__(self, data: ThreadMembersUpdate) -> None:
        self.thread_id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.member_count: int = int(data['member_count'])
        self.data: ThreadMembersUpdate = data


class RawTypingEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_typing` event.

    .. versionadded:: 2.0

    Attributes
    ----------
    channel_id: :class:`int`
        The ID of the channel the user started typing in.
    user_id: :class:`int`
        The ID of the user that started typing.
    user: Optional[Union[:class:`discord.User`, :class:`discord.Member`]]
        The user that started typing, if they could be found in the internal cache.
    timestamp: :class:`datetime.datetime`
        When the typing started as an aware datetime in UTC.
    guild_id: Optional[:class:`int`]
        The ID of the guild the user started typing in, if applicable.
    """

    __slots__ = ('channel_id', 'user_id', 'user', 'timestamp', 'guild_id')

    def __init__(self, data: TypingStartEvent, /) -> None:
        self.channel_id: int = int(data['channel_id'])
        self.user_id: int = int(data['user_id'])
        self.user: Optional[Union[User, Member]] = None
        self.timestamp: datetime.datetime = datetime.datetime.fromtimestamp(data['timestamp'], tz=datetime.timezone.utc)
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')


class RawMemberRemoveEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_member_remove` event.

    .. versionadded:: 2.0

    Attributes
    ----------
    user: Union[:class:`discord.User`, :class:`discord.Member`]
        The user that left the guild.
    guild_id: :class:`int`
        The ID of the guild the user left.
    """

    __slots__ = ('user', 'guild_id')

    def __init__(self, data: GuildMemberRemoveEvent, user: User, /) -> None:
        self.user: Union[User, Member] = user
        self.guild_id: int = int(data['guild_id'])


class RawAppCommandPermissionsUpdateEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_app_command_permissions_update` event.

    .. versionadded:: 2.0

    Attributes
    ----------
    target_id: :class:`int`
        The ID of the command or application whose permissions were updated.
        When this is the application ID instead of a command ID, the permissions
        apply to all commands that do not contain explicit overwrites.
    application_id: :class:`int`
        The ID of the application that the command belongs to.
    guild: :class:`~discord.Guild`
        The guild where the permissions were updated.
    permissions: List[:class:`~discord.app_commands.AppCommandPermissions`]
        List of new permissions for the app command.
    """

    __slots__ = ('target_id', 'application_id', 'guild', 'permissions')

    def __init__(self, *, data: GuildApplicationCommandPermissions, state: ConnectionState):
        self.target_id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.guild: Guild = state._get_or_create_unavailable_guild(int(data['guild_id']))
        self.permissions: List[AppCommandPermissions] = [
            AppCommandPermissions(data=perm, guild=self.guild, state=state) for perm in data['permissions']
        ]
