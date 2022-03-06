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

from typing import List, Literal, Optional, TypedDict


from .activity import PartialPresenceUpdate
from .voice import GuildVoiceState
from .integration import BaseIntegration, IntegrationApplication
from .role import Role
from .channel import ChannelType, StageInstance
from .interactions import Interaction
from .invite import InviteTargetType
from .emoji import Emoji, PartialEmoji
from .member import MemberWithUser
from .snowflake import Snowflake
from .message import Message
from .sticker import GuildSticker
from .appinfo import GatewayAppInfo, PartialAppInfo
from .guild import Guild, UnavailableGuild
from .user import User
from .threads import Thread, ThreadMember
from .scheduled_event import GuildScheduledEvent


class SessionStartLimit(TypedDict):
    total: int
    remaining: int
    reset_after: int
    max_concurrency: int


class Gateway(TypedDict):
    url: str


class GatewayBot(Gateway):
    shards: int
    session_start_limit: SessionStartLimit


class ShardInfo(TypedDict):
    shard_id: int
    shard_count: int


class ReadyEvent(TypedDict):
    v: int
    user: User
    guilds: List[UnavailableGuild]
    session_id: str
    shard: ShardInfo
    application: GatewayAppInfo


ResumedEvent = Literal[None]

MessageCreateEvent = Message


class _MessageDeleteEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageDeleteEvent(_MessageDeleteEventOptional):
    id: Snowflake
    channel_id: Snowflake


class _MessageDeleteBulkEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageDeleteBulkEvent(_MessageDeleteBulkEventOptional):
    ids: List[Snowflake]
    channel_id: Snowflake


class MessageUpdateEvent(Message):
    channel_id: Snowflake


class _MessageReactionAddEventOptional(TypedDict, total=False):
    member: MemberWithUser
    guild_id: Snowflake


class MessageReactionAddEvent(_MessageReactionAddEventOptional):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji


class _MessageReactionRemoveEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageReactionRemoveEvent(_MessageReactionRemoveEventOptional):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji


class _MessageReactionRemoveAllEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageReactionRemoveAllEvent(_MessageReactionRemoveAllEventOptional):
    message_id: Snowflake
    channel_id: Snowflake


class _MessageReactionRemoveEmojiEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageReactionRemoveEmojiEvent(_MessageReactionRemoveEmojiEventOptional):
    emoji: PartialEmoji
    message_id: Snowflake
    channel_id: Snowflake


InteractionCreateEvent = Interaction


PresenceUpdateEvent = PartialPresenceUpdate


UserUpdateEvent = User


class _InviteCreateEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    inviter: User
    target_type: InviteTargetType
    target_user: User
    target_application: PartialAppInfo


class InviteCreateEvent(_InviteCreateEventOptional):
    channel_id: Snowflake
    code: str
    created_at: str
    max_age: int
    max_uses: int
    temporary: bool
    uses: Literal[0]


class _InviteDeleteEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class InviteDeleteEvent(_InviteDeleteEventOptional):
    channel_id: Snowflake
    code: str


class _ChannelEvent(TypedDict):
    id: Snowflake
    type: ChannelType


ChannelCreateEvent = ChannelUpdateEvent = ChannelDeleteEvent = _ChannelEvent


class _ChannelPinsUpdateEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    last_pin_timestamp: Optional[str]


class ChannelPinsUpdateEvent(_ChannelPinsUpdateEventOptional):
    channel_id: Snowflake


class _ThreadCreateEventOptional(TypedDict, total=False):
    newly_created: bool
    members: List[ThreadMember]


class ThreadCreateEvent(Thread, _ThreadCreateEventOptional):
    ...


ThreadUpdateEvent = Thread


class ThreadDeleteEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    parent_id: Snowflake
    type: ChannelType


class _ThreadListSyncEventOptional(TypedDict, total=False):
    channel_ids: List[Snowflake]


class ThreadListSyncEvent(_ThreadListSyncEventOptional):
    guild_id: Snowflake
    threads: List[Thread]
    members: List[ThreadMember]


class ThreadMemberUpdate(ThreadMember):
    guild_id: Snowflake


class _ThreadMembersUpdateOptional(TypedDict, total=False):
    added_members: List[ThreadMember]
    removed_member_ids: List[Snowflake]


class ThreadMembersUpdate(_ThreadMembersUpdateOptional):
    id: Snowflake
    guild_id: Snowflake
    member_count: int


class GuildMemberAddEvent(MemberWithUser):
    guild_id: Snowflake


class GuildMemberRemoveEvent(TypedDict):
    guild_id: Snowflake
    user: User


class _GuildMemberUpdateEventOptional(TypedDict, total=False):
    nick: str
    premium_since: Optional[str]
    deaf: bool
    mute: bool
    pending: bool
    communication_disabled_until: str


class GuildMemberUpdateEvent(_GuildMemberUpdateEventOptional):
    guild_id: Snowflake
    roles: List[Snowflake]
    user: User
    avatar: Optional[str]
    joined_at: Optional[str]


class GuildEmojisUpdateEvent(TypedDict):
    guild_id: Snowflake
    emojis: List[Emoji]


class GuildStickersUpdateEvent(TypedDict):
    guild_id: Snowflake
    stickers: List[GuildSticker]


GuildCreateEvent = GuildUpdateEvent = Guild
GuildDeleteEvent = UnavailableGuild


class _GuildBanEvent(TypedDict):
    guild_id: Snowflake
    user: User


GuildBanAddEvent = GuildBanRemoveEvent = _GuildBanEvent


class _GuildRoleEvent(TypedDict):
    guild_id: Snowflake
    role: Role


class GuildRoleDeleteEvent(TypedDict):
    guild_id: Snowflake
    role_id: Snowflake


GuildRoleCreateEvent = GuildRoleUpdateEvent = _GuildRoleEvent


class _GuildMembersChunkEventOptional(TypedDict, total=False):
    not_found: List[Snowflake]
    presences: List[PresenceUpdateEvent]
    nonce: str


class GuildMembersChunkEvent(_GuildMembersChunkEventOptional):
    guild_id: Snowflake
    members: List[MemberWithUser]
    chunk_index: int
    chunk_count: int


class GuildIntegrationsUpdateEvent(TypedDict):
    guild_id: Snowflake


class _IntegrationEventOptional(BaseIntegration, total=False):
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    subscriber_count: int
    revoked: bool
    application: IntegrationApplication


class _IntegrationEvent(_IntegrationEventOptional):
    guild_id: Snowflake


IntegrationCreateEvent = IntegrationUpdateEvent = _IntegrationEvent


class _IntegrationDeleteEventOptional(TypedDict, total=False):
    application_id: Snowflake


class IntegrationDeleteEvent(_IntegrationDeleteEventOptional):
    id: Snowflake
    guild_id: Snowflake


class WebhooksUpdateEvent(TypedDict):
    guild_id: Snowflake
    channel_id: Snowflake


StageInstanceCreateEvent = StageInstanceUpdateEvent = StageInstanceDeleteEvent = StageInstance

GuildScheduledEventCreateEvent = GuildScheduledEventUpdateEvent = GuildScheduledEventDeleteEvent = GuildScheduledEvent


class _GuildScheduledEventUsersEvent(TypedDict):
    guild_scheduled_event_id: Snowflake
    user_id: Snowflake
    guild_id: Snowflake


GuildScheduledEventUserAdd = GuildScheduledEventUserRemove = _GuildScheduledEventUsersEvent

VoiceStateUpdateEvent = GuildVoiceState


class VoiceServerUpdateEvent(TypedDict):
    token: str
    guild_id: Snowflake
    endpoint: Optional[str]


class _TypingStartEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    member: MemberWithUser


class TypingStartEvent(_TypingStartEventOptional):
    channel_id: Snowflake
    user_id: Snowflake
    timestamp: int
