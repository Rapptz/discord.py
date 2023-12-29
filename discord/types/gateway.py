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

from typing import Generic, List, Literal, Optional, TypedDict, TypeVar, Union
from typing_extensions import NotRequired, Required

from .activity import Activity, BasePresenceUpdate, PartialPresenceUpdate, StatusType
from .application import BaseAchievement
from .audit_log import AuditLogEntry
from .automod import AutoModerationAction, AutoModerationRuleTriggerType
from .channel import ChannelType, DMChannel, GroupDMChannel, StageInstance
from .emoji import Emoji, PartialEmoji
from .entitlements import Entitlement, GatewayGift
from .experiment import GuildExperiment, UserExperiment
from .guild import ApplicationCommandCounts, Guild, SupplementalGuild, UnavailableGuild
from .integration import BaseIntegration, IntegrationApplication
from .interactions import Modal
from .invite import _InviteTargetType
from .library import LibraryApplication
from .member import MemberWithPresence, MemberWithUser
from .message import Message
from .payments import Payment
from .read_state import ReadState, ReadStateType
from .role import Role
from .scheduled_event import GuildScheduledEvent
from .snowflake import Snowflake
from .sticker import GuildSticker
from .subscriptions import PremiumGuildSubscriptionSlot
from .threads import Thread, ThreadMember
from .user import (
    Connection,
    FriendSuggestion,
    PartialConsentSettings,
    PartialUser,
    ProtoSettingsType,
    Relationship,
    RelationshipType,
    User,
    UserGuildSettings,
)
from .voice import GuildVoiceState, PrivateVoiceState, VoiceState

T = TypeVar('T')


class UserPresenceUpdateEvent(BasePresenceUpdate):
    ...


PresenceUpdateEvent = Union[PartialPresenceUpdate, UserPresenceUpdateEvent]


class Gateway(TypedDict):
    url: str


class ShardInfo(TypedDict):
    shard_id: int
    shard_count: int


class ResumedEvent(TypedDict):
    _trace: List[str]


class ReadyEvent(ResumedEvent):
    _trace: List[str]
    api_code_version: int
    analytics_token: str
    auth_session_id_hash: str
    auth_token: NotRequired[str]
    connected_accounts: List[Connection]
    consents: PartialConsentSettings
    country_code: str
    experiments: List[UserExperiment]
    friend_suggestion_count: int
    geo_ordered_rtc_regions: List[str]
    guild_experiments: List[GuildExperiment]
    guilds: List[Guild]
    merged_members: List[List[MemberWithUser]]
    pending_payments: NotRequired[List[Payment]]
    private_channels: List[Union[DMChannel, GroupDMChannel]]
    read_state: Versioned[ReadState]
    relationships: List[Relationship]
    resume_gateway_url: str
    required_action: NotRequired[str]
    sessions: List[Session]
    session_id: str
    session_type: Literal['normal']
    shard: NotRequired[ShardInfo]
    tutorial: Optional[Tutorial]
    user: User
    user_guild_settings: Versioned[UserGuildSettings]
    user_settings_proto: NotRequired[str]
    users: List[PartialUser]
    v: int


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


class MergedPresences(TypedDict):
    friends: List[UserPresenceUpdateEvent]
    guilds: List[List[PartialPresenceUpdate]]


class ReadySupplementalEvent(TypedDict):
    guilds: List[SupplementalGuild]
    merged_members: List[List[MemberWithUser]]
    merged_presences: MergedPresences
    lazy_private_channels: List[Union[DMChannel, GroupDMChannel]]
    disclose: List[str]


class Versioned(TypedDict, Generic[T]):
    entries: List[T]
    version: int
    partial: bool


class Tutorial(TypedDict):
    indicators_suppressed: bool
    indicators_confirmed: List[str]


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
    message_author_id: NotRequired[Snowflake]


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


UserUpdateEvent = User


class InviteCreateEvent(_InviteTargetType):
    code: str
    type: Literal[0]
    channel_id: Snowflake
    guild_id: Snowflake
    inviter: NotRequired[PartialUser]
    expires_at: Optional[str]
    created_at: str
    uses: int
    max_age: int
    max_uses: int
    temporary: bool
    flags: NotRequired[int]


class InviteDeleteEvent(TypedDict):
    code: str
    channel_id: Snowflake
    guild_id: Snowflake


class _ChannelEvent(TypedDict):
    id: Snowflake
    type: ChannelType


ChannelCreateEvent = ChannelUpdateEvent = ChannelDeleteEvent = _ChannelEvent


class ChannelRecipientEvent(TypedDict):
    channel_id: Snowflake
    user: PartialUser


class ChannelPinsUpdateEvent(TypedDict):
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]
    last_pin_timestamp: NotRequired[Optional[str]]


class ChannelPinsAckEvent(TypedDict):
    channel_id: Snowflake
    timestamp: str
    version: int


class MessageAckEvent(TypedDict):
    channel_id: Snowflake
    message_id: Snowflake
    flags: Optional[int]
    last_viewed: Optional[int]
    manual: NotRequired[bool]
    mention_count: NotRequired[int]
    ack_type: NotRequired[ReadStateType]
    version: int


class NonChannelAckEvent(TypedDict):
    entity_id: Snowflake
    resource_id: Snowflake
    ack_type: int
    version: int


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

VoiceStateUpdateEvent = Union[GuildVoiceState, PrivateVoiceState]


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


FriendSuggestionCreateEvent = FriendSuggestion


class FriendSuggestionDeleteEvent(TypedDict):
    suggested_user_id: Snowflake


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
    voice_states: NotRequired[List[VoiceState]]
    members: NotRequired[List[MemberWithUser]]


class GuildApplicationCommandIndexUpdateEvent(TypedDict):
    guild_id: Snowflake
    application_command_counts: ApplicationCommandCounts


class UserNoteUpdateEvent(TypedDict):
    id: Snowflake
    note: str


UserGuildSettingsEvent = UserGuildSettings


class InteractionEvent(TypedDict):
    id: Snowflake
    nonce: NotRequired[Snowflake]


InteractionModalCreateEvent = Modal


class CallCreateEvent(TypedDict):
    channel_id: Snowflake
    message_id: Snowflake
    embedded_activities: List[dict]
    region: str
    ringing: List[Snowflake]
    voice_states: List[VoiceState]
    unavailable: NotRequired[bool]


class CallUpdateEvent(TypedDict):
    channel_id: Snowflake
    guild_id: Optional[Snowflake]  # ???
    message_id: Snowflake
    region: str
    ringing: List[Snowflake]


class CallDeleteEvent(TypedDict):
    channel_id: Snowflake
    unavailable: NotRequired[bool]


class _GuildMemberListGroup(TypedDict):
    id: Union[Snowflake, Literal['online', 'offline']]


class GuildMemberListGroup(_GuildMemberListGroup):
    count: int


class _GuildMemberListGroupItem(TypedDict):
    group: _GuildMemberListGroup


class _GuildMemberListMemberItem(TypedDict):
    member: MemberWithPresence


GuildMemberListItem = Union[_GuildMemberListGroupItem, _GuildMemberListMemberItem]


class GuildMemberListSyncOP(TypedDict):
    op: Literal['SYNC']
    range: tuple[int, int]
    items: List[GuildMemberListItem]


class GuildMemberListUpdateOP(TypedDict):
    op: Literal['UPDATE']
    index: int
    item: _GuildMemberListMemberItem


class GuildMemberListInsertOP(TypedDict):
    op: Literal['INSERT']
    index: int
    item: _GuildMemberListMemberItem


class GuildMemberListDeleteOP(TypedDict):
    op: Literal['DELETE']
    index: int


class GuildMemberListInvalidateOP(TypedDict):
    op: Literal['INVALIDATE']
    range: tuple[int, int]


GuildMemberListOP = Union[
    GuildMemberListSyncOP,
    GuildMemberListUpdateOP,
    GuildMemberListInsertOP,
    GuildMemberListDeleteOP,
    GuildMemberListInvalidateOP,
]


class GuildMemberListUpdateEvent(TypedDict):
    id: Union[Snowflake, Literal['everyone']]
    guild_id: Snowflake
    member_count: int
    online_count: int
    groups: List[GuildMemberListGroup]
    ops: List[GuildMemberListOP]
