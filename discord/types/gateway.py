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

from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required

from .activity import Activity, ClientStatus, PartialPresenceUpdate, StatusType
from .automod import AutoModerationAction, AutoModerationRuleTriggerType
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
from .application import BaseAchievement, PartialApplication
from .guild import ApplicationCommandCounts, Guild, UnavailableGuild, SupplementalGuild
from .user import Connection, User, PartialUser, ProtoSettingsType, Relationship, RelationshipType
from .threads import Thread, ThreadMember
from .scheduled_event import GuildScheduledEvent
from .channel import DMChannel, GroupDMChannel
from .subscriptions import PremiumGuildSubscriptionSlot
from .payments import Payment
from .entitlements import Entitlement, GatewayGift
from .library import LibraryApplication
from .audit_log import AuditLogEntry


class UserPresenceUpdateEvent(TypedDict):
    user: PartialUser
    status: StatusType
    activities: List[Activity]
    client_status: ClientStatus
    last_modified: int


PresenceUpdateEvent = Union[PartialPresenceUpdate, UserPresenceUpdateEvent]


class Gateway(TypedDict):
    url: str


class ShardInfo(TypedDict):
    shard_id: int
    shard_count: int


class ClientInfo(TypedDict):
    version: int
    os: str
    client: str


class Session(TypedDict):
    session_id: str
    active: NotRequired[bool]
    client_info: ClientInfo
    status: StatusType
    activities: List[Activity]


class ResumedEvent(TypedDict):
    _trace: List[str]


class ReadyEvent(ResumedEvent):
    _trace: List[str]
    api_code_version: int
    analytics_token: str
    auth_session_id_hash: str
    auth_token: NotRequired[str]
    connected_accounts: List[Connection]
    country_code: str
    friend_suggestion_count: int
    geo_ordered_rtc_regions: List[str]
    guilds: List[Guild]
    merged_members: List[List[MemberWithUser]]
    pending_payments: NotRequired[List[Payment]]
    private_channels: List[Union[DMChannel, GroupDMChannel]]
    relationships: List[Relationship]
    resume_gateway_url: str
    required_action: NotRequired[str]
    sessions: List[Session]
    session_id: str
    session_type: str
    shard: NotRequired[ShardInfo]
    user: User
    user_guild_settings: dict
    user_settings: NotRequired[dict]
    user_settings_proto: str
    users: List[PartialUser]
    v: int


class MergedPresences(TypedDict):
    friends: List[UserPresenceUpdateEvent]
    guilds: List[List[PartialPresenceUpdate]]


class ReadySupplementalEvent(TypedDict):
    guilds: List[SupplementalGuild]
    merged_members: List[List[MemberWithUser]]
    merged_presences: MergedPresences


NoEvent = Literal[None]

MessageCreateEvent = Message


SessionsReplaceEvent = List[Session]


class MessageDeleteEvent(TypedDict):
    id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class MessageDeleteBulkEvent(TypedDict):
    ids: List[Snowflake]
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class MessageUpdateEvent(Message):
    channel_id: Snowflake


class MessageReactionAddEvent(TypedDict):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji
    member: NotRequired[MemberWithUser]
    guild_id: NotRequired[Snowflake]


class MessageReactionRemoveEvent(TypedDict):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji
    guild_id: NotRequired[Snowflake]


class MessageReactionRemoveAllEvent(TypedDict):
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class MessageReactionRemoveEmojiEvent(TypedDict):
    emoji: PartialEmoji
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


InteractionCreateEvent = Interaction


UserUpdateEvent = User


class InviteCreateEvent(TypedDict):
    channel_id: Snowflake
    code: str
    created_at: str
    max_age: int
    max_uses: int
    temporary: bool
    uses: Literal[0]
    guild_id: NotRequired[Snowflake]
    inviter: NotRequired[PartialUser]
    target_type: NotRequired[InviteTargetType]
    target_user: NotRequired[PartialUser]
    target_application: NotRequired[PartialApplication]


class InviteDeleteEvent(TypedDict):
    channel_id: Snowflake
    code: str
    guild_id: NotRequired[Snowflake]


class _ChannelEvent(TypedDict):
    id: Snowflake
    type: ChannelType


ChannelCreateEvent = ChannelUpdateEvent = ChannelDeleteEvent = _ChannelEvent


class ChannelPinsUpdateEvent(TypedDict):
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]
    last_pin_timestamp: NotRequired[Optional[str]]


class ThreadCreateEvent(Thread, total=False):
    newly_created: bool
    members: List[ThreadMember]


ThreadUpdateEvent = Thread


class ThreadDeleteEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    parent_id: Snowflake
    type: ChannelType


class ThreadListSyncEvent(TypedDict):
    guild_id: Snowflake
    threads: List[Thread]
    members: List[ThreadMember]
    channel_ids: NotRequired[List[Snowflake]]
    most_recent_messages: List[Message]


class ThreadMemberUpdate(ThreadMember):
    guild_id: Snowflake


class ThreadMembersUpdate(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    member_count: int
    added_members: NotRequired[List[ThreadMember]]
    removed_member_ids: NotRequired[List[Snowflake]]


class GuildMemberAddEvent(MemberWithUser):
    guild_id: Snowflake


class SnowflakeUser(TypedDict):
    id: Snowflake


class GuildMemberRemoveEvent(TypedDict):
    guild_id: Snowflake
    user: Union[PartialUser, SnowflakeUser]


class GuildMemberUpdateEvent(TypedDict):
    guild_id: Snowflake
    roles: List[Snowflake]
    user: PartialUser
    avatar: Optional[str]
    joined_at: Optional[str]
    flags: int
    nick: NotRequired[str]
    premium_since: NotRequired[Optional[str]]
    deaf: NotRequired[bool]
    mute: NotRequired[bool]
    pending: NotRequired[bool]
    communication_disabled_until: NotRequired[str]


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
    user: PartialUser


GuildBanAddEvent = GuildBanRemoveEvent = _GuildBanEvent


class _GuildRoleEvent(TypedDict):
    guild_id: Snowflake
    role: Role


class GuildRoleDeleteEvent(TypedDict):
    guild_id: Snowflake
    role_id: Snowflake


GuildRoleCreateEvent = GuildRoleUpdateEvent = _GuildRoleEvent


class GuildMembersChunkEvent(TypedDict):
    guild_id: Snowflake
    members: List[MemberWithUser]
    chunk_index: int
    chunk_count: int
    not_found: NotRequired[List[Snowflake]]
    presences: NotRequired[List[PartialPresenceUpdate]]
    nonce: NotRequired[str]


class GuildIntegrationsUpdateEvent(TypedDict):
    guild_id: Snowflake


class _IntegrationEvent(BaseIntegration, total=False):
    guild_id: Required[Snowflake]
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    subscriber_count: int
    revoked: bool
    application: IntegrationApplication


IntegrationCreateEvent = IntegrationUpdateEvent = _IntegrationEvent


class IntegrationDeleteEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    application_id: NotRequired[Snowflake]


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
    channel_id: Snowflake
    endpoint: Optional[str]


class TypingStartEvent(TypedDict):
    channel_id: Snowflake
    user_id: Snowflake
    timestamp: int
    guild_id: NotRequired[Snowflake]
    member: NotRequired[MemberWithUser]


ConnectionEvent = Connection


class PartialConnectionEvent(TypedDict):
    user_id: Snowflake


class ConnectionsLinkCallbackEvent(TypedDict):
    provider: str
    callback_code: str
    callback_state: str


class OAuth2TokenRevokeEvent(TypedDict):
    access_token: str


class AuthSessionChangeEvent(TypedDict):
    auth_session_id_hash: str


class PaymentClientAddEvent(TypedDict):
    purchase_token_hash: str
    expires_at: str


class AchievementUpdatePayload(TypedDict):
    application_id: Snowflake
    achievement: BaseAchievement
    percent_complete: int


PremiumGuildSubscriptionSlotEvent = PremiumGuildSubscriptionSlot


class RequiredActionEvent(TypedDict):
    required_action: str


class BillingPopupBridgeCallbackEvent(TypedDict):
    payment_source_type: int
    state: str
    path: str
    query: str


PaymentUpdateEvent = Payment

GiftCreateEvent = GiftUpdateEvent = GatewayGift

EntitlementEvent = Entitlement

LibraryApplicationUpdateEvent = LibraryApplication


class RelationshipAddEvent(Relationship):
    should_notify: NotRequired[bool]


class RelationshipEvent(TypedDict):
    id: Snowflake
    type: RelationshipType
    nickname: Optional[str]


class ProtoSettings(TypedDict):
    proto: str
    type: ProtoSettingsType


class ProtoSettingsEvent(TypedDict):
    settings: ProtoSettings
    partial: bool


class RecentMentionDeleteEvent(TypedDict):
    message_id: Snowflake


class AutoModerationActionExecution(TypedDict):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: AutoModerationRuleTriggerType
    user_id: Snowflake
    channel_id: NotRequired[Snowflake]
    message_id: NotRequired[Snowflake]
    alert_system_message_id: NotRequired[Snowflake]
    content: str
    matched_keyword: Optional[str]
    matched_content: Optional[str]


class GuildAuditLogEntryCreate(AuditLogEntry):
    guild_id: Snowflake


class PartialUpdateChannel(TypedDict):
    id: Snowflake
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: NotRequired[Optional[str]]


class PassiveUpdateEvent(TypedDict):
    guild_id: Snowflake
    channels: List[PartialUpdateChannel]
    voice_states: NotRequired[List[GuildVoiceState]]
    members: NotRequired[List[MemberWithUser]]


class GuildApplicationCommandIndexUpdateEvent(TypedDict):
    guild_id: Snowflake
    application_command_counts: ApplicationCommandCounts


class UserNoteUpdateEvent(TypedDict):
    id: Snowflake
    note: str
