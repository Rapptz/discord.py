from typing import Any, Optional, Union, List
from mypy_extensions import TypedDict

from .embeds import _EmptyEmbed

class BaseRawUserDict(TypedDict):
    id: int
    username: str
    discriminator: str
    avatar: Optional[str]

class RawUserDict(BaseRawUserDict, total=False):
    bot: bool
    mfa_enabled: bool
    verified: bool
    email: str
    premium: bool

class RawAttachmentDict(TypedDict):
    id: int
    filename: str
    size: int
    url: str
    proxy_url: str
    height: Optional[int]
    width: Optional[int]

class RawEmbedFooterDict(TypedDict, total=False):
    text: str
    icon_url: str
    proxy_icon_url: str

class BaseRawEmbedMediaDict(TypedDict):
    url: str

class RawEmbedMediaDict(BaseRawEmbedMediaDict, total=False):
    height: int
    width: int

class RawEmbedImageDict(RawEmbedMediaDict, total=False):
    proxy_url: str

class RawEmbedProviderDict(TypedDict):
    name: str
    url: str

class RawEmbedAuthorDict(TypedDict, total=False):
    name: str
    url: str
    icon_url: str
    proxy_icon_url: str

class BaseRawEmbedFieldDict(TypedDict):
    name: str
    value: str

class RawEmbedFieldDict(BaseRawEmbedFieldDict, total=False):
    inline: bool

class RawEmbedDict(TypedDict, total=False):
    type: str
    title: str
    description: str
    url: str
    timestamp: str
    color: int
    footer: RawEmbedFooterDict
    image: RawEmbedImageDict
    thumbnail: RawEmbedImageDict
    video: RawEmbedMediaDict
    provider: RawEmbedProviderDict
    author: RawEmbedAuthorDict
    fields: List[RawEmbedFieldDict]

class RawRoleDict(TypedDict):
    id: int
    name: str
    color: int
    hoist: bool
    position: int
    permissions: int
    managed: bool
    mentionable: bool

class BaseRawPartialEmojiDict(TypedDict):
    id: Optional[int]
    name: str

class RawPartialEmojiDict(BaseRawPartialEmojiDict, total=False):
    animated: bool

class BaseRawEmojiDict(TypedDict):
    id: int
    name: str

class RawEmojiDict(BaseRawEmojiDict, total=False):
    animated: bool
    roles: List[int]
    user: RawUserDict
    require_colons: bool
    managed: bool

class RawReactionDict(TypedDict):
    count: int
    me: bool
    emoji: RawPartialEmojiDict

class BaseRawMessageActivityDict(TypedDict):
    type: int

class RawMessageActivityDict(BaseRawMessageActivityDict, total=False):
    party_id: str

class RawApplicationDict(TypedDict):
    id: int
    cover_image: str
    description: str
    icon: str
    name: str

class RawMessageCallDict(TypedDict, total=False):
    participants: List[int]

class BaseRawMessageDict(TypedDict):
    id: int
    channel_id: int
    author: RawUserDict
    content: str
    timestamp: str
    edited_timestamp: Optional[str]
    tts: bool
    mention_everyone: bool
    mentions: List[RawUserDict]
    mention_roles: List[int]
    attachments: List[RawAttachmentDict]
    embeds: List[RawEmbedDict]
    pinned: bool
    type: int

class RawMessageDict(BaseRawMessageDict, total=False):
    reactions: List[RawReactionDict]
    nonce: int
    webhook_id: int
    activity: RawMessageActivityDict
    application: Any
    call: RawMessageCallDict
    guild_id: int

class BaseRawApplicationInfoDict(TypedDict):
    id: int
    name: str
    bot_public: bool
    bot_require_code_grant: bool
    owner: RawUserDict

class RawApplicationInfoDict(BaseRawApplicationInfoDict, total=False):
    icon: str
    description: str
    rpc_origins: List[str]

class BaseRawGuildMemberDict(TypedDict):
    user: RawUserDict
    roles: List[int]
    joined_at: str
    deaf: bool
    mute: bool

class RawGuildMemberDict(BaseRawGuildMemberDict, total=False):
    nick: str
    guild_id: str

class RawGuildMemberRemoveDict(TypedDict):
    guild_id: str
    user: RawUserDict

class RawGuildMemberUpdateDict(TypedDict):
    guild_id: str
    roles: List[int]
    user: RawUserDict
    nick: str

class BaseRawInviteDict(TypedDict):
    code: str
    guild: Any
    channel: Any

class RawInviteDict(BaseRawInviteDict, total=False):
    approximate_presence_count: int
    approximate_member_count: int

class RawInviteMetaDict(RawInviteDict):
    inviter: RawUserDict
    uses: int
    max_uses: int
    max_age: int
    temporary: bool
    created_at: str
    revoked: bool

class RawTimestampsDict(TypedDict, total=False):
    start: int
    end: int

class RawActivityPartyDict(TypedDict, total=False):
    id: str
    size: List[int]

class RawActivityAssetsDict(TypedDict, total=False):
    large_image: str
    large_text: str
    small_image: str
    small_text: str

class BaseRawActivityDict(TypedDict):
    name: str
    type: int

class RawActivityDict(BaseRawActivityDict, total=False):
    url: Optional[str]
    timestamps: RawTimestampsDict
    application_id: int
    details: Optional[str]
    state: Optional[str]
    party: RawActivityPartyDict
    assets: RawActivityAssetsDict

class RawSpotifyActivityDict(TypedDict, total=False):
    name: str
    url: Optional[str]
    timestamps: RawTimestampsDict
    application_id: int
    details: Optional[str]
    state: Optional[str]
    party: RawActivityPartyDict
    assets: RawActivityAssetsDict
    flags: int
    sync_id: str
    session_id: str

class RawPresenceUpdateDict(TypedDict):
    user: RawUserDict
    roles: List[int]
    game: Optional[RawActivityDict]
    guild_id: int
    status: str

class RawOverwriteDict(TypedDict):
    id: int
    type: str
    allow: int
    deny: int

class BaseRawChannelDict(TypedDict):
    id: int
    type: int

class RawChannelDict(BaseRawChannelDict, total=False):
    guild_id: int
    position: int
    permission_overwrites: List[RawOverwriteDict]
    name: str
    topic: str
    nsfw: bool
    last_message_id: Optional[int]
    bitrate: int
    user_limit: int
    recipients: List[RawUserDict]
    icon: Optional[str]
    owner_id: int
    application_id: int
    parent_id: Optional[int]
    last_pin_timestamp: str

class BaseRawChannelPinsDict(TypedDict):
    channel_id: int

class RawChannelPinsDict(BaseRawChannelPinsDict, total=False):
    last_pin_timestamp: str

class RawGuildEmojisUpdateDict(TypedDict):
    guild_id: int
    emojis: List[RawEmojiDict]

class BaseRawVoiceStateDict(TypedDict):
    channel_id: Optional[int]
    user_id: int
    session_id: str
    deaf: bool
    mute: bool
    self_deaf: bool
    self_mute: bool
    suppress: bool

class RawVoiceStateDict(BaseRawVoiceStateDict, total=False):
    guild_id: int

class BaseRawGuildDict(TypedDict):
    id: int
    name: str
    icon: Optional[str]
    splash: Optional[str]
    owner_id: int
    region: str
    afk_channel_id: Optional[int]
    afk_timeout: int
    verification_level: int
    default_message_notifications: int
    explicit_content_filter: int
    roles: List[RawRoleDict]
    emojis: List[RawEmojiDict]
    features: List[str]
    mfa_level: int
    application_id: Optional[int]
    system_channel_id: Optional[int]

class RawGuildDict(BaseRawGuildDict, total=False):
    owner: bool
    permissions: int
    embed_enabled: bool
    embed_channel_id: int
    widget_enabled: bool
    widget_channel_id: int
    joined_at: str
    large: bool
    unavailable: bool
    member_count: int
    voice_states: List[Any]
    members: List[RawGuildMemberDict]
    channels: List[RawChannelDict]
    presences: List[RawPresenceUpdateDict]

class RawGuildBanActionDict(TypedDict):
    guild_id: int
    user: RawUserDict

class RawGuildRoleActionDict(TypedDict):
    guild_id: int
    role: RawRoleDict

class RawGuildRoleDeleteDict(TypedDict):
    guild_id: int
    role_id: int

class RawGuildMembersChunkDict(TypedDict):
    guild_id: int
    members: List[RawGuildMemberDict]

class BaseRawVoiceServerUpdateDict(TypedDict):
    token: str
    endpoint: str

class RawVoiceServerUpdateDict(BaseRawVoiceServerUpdateDict, total=False):
    channel_id: int
    guild_id: int

class RawTypingStartDict(TypedDict):
    channel_id: int
    user_id: int
    timestamp: int

class RawUnavailableGuildDict(TypedDict):
    id: int
    unavailable: bool

class RawRelationshipDict(TypedDict):
    user: RawUserDict
    type: int

class BaseRawReadyDict(TypedDict):
    v: int
    user: RawUserDict
    guilds: List[RawUnavailableGuildDict]
    session_id: str
    _trace: List[str]

class RawReadyDict(BaseRawReadyDict, total=False):
    private_channels: List[RawChannelDict]
    relationships: List[RawRelationshipDict]

class BaseRawWebhookDict(TypedDict):
    id: int
    token: str

class RawWebhookDict(BaseRawWebhookDict, total=False):
    channel_id: int
    name: Optional[str]
    avatar: Optional[str]
    guild_id: int
    user: RawUserDict

class BaseRawAuditLogChangeDict(TypedDict):
    key: str

class RawAuditLogChangeDict(BaseRawAuditLogChangeDict, total=False):
    new_value: Any
    old_value: Any

class BaseRawAuditLogEntryDict(TypedDict):
    target_id: Optional[str]
    user_id: int
    id: int
    action_type: int

class RawAuditLogEntryDict(BaseRawAuditLogEntryDict, total=False):
    changes: List[RawAuditLogChangeDict]
    options: Any
    reason: str

class RawAuditLogDict(TypedDict):
    webhooks: List[RawWebhookDict]
    users: List[RawUserDict]
    audit_log_entries: List[RawAuditLogEntryDict]

class RawGuildBanDict(TypedDict):
    reason: Optional[str]
    user: RawUserDict

class RawGuildPruneDict(TypedDict):
    pruned: int

class BaseRawBulkMessageDeleteDict(TypedDict, total=False):
    guild_id: str

class RawBulkMessageDeleteDict(BaseRawBulkMessageDeleteDict):
    ids: List[str]
    channel_id: str

class BaseRawReactionActionDict(TypedDict):
    message_id: str
    channel_id: str
    user_id: str
    emoji: 'RawPartialEmojiDict'

class RawReactionActionDict(BaseRawReactionActionDict, total=False):
    guild_id: str

class BaseRawReactionClearDict(TypedDict):
    channel_id: int
    message_id: int

class RawReactionClearDict(BaseRawReactionClearDict, total=False):
    guild_id: int

class EmbedFooterData(TypedDict):
    text: Union[str, _EmptyEmbed]
    icon_url: Union[str, _EmptyEmbed]

class EmbedImageData(TypedDict):
    url: Union[str, _EmptyEmbed]
    proxy_url: Union[str, _EmptyEmbed]
    height: Union[int, _EmptyEmbed]
    width: Union[int, _EmptyEmbed]

class EmbedVideoData(TypedDict):
    url: Union[str, _EmptyEmbed]
    height: Union[int, _EmptyEmbed]
    width: Union[int, _EmptyEmbed]

class EmbedProviderData(TypedDict):
    name: Union[str, _EmptyEmbed]
    url: Union[str, _EmptyEmbed]

class EmbedAuthorData(TypedDict):
    name: Union[str, _EmptyEmbed]
    url: Union[str, _EmptyEmbed]
    icon_url: Union[str, _EmptyEmbed]
    proxy_icon_url: Union[str, _EmptyEmbed]

class EmbedFieldData(TypedDict):
    name: Union[str, _EmptyEmbed]
    value: Union[str, _EmptyEmbed]
    inline: Union[bool, _EmptyEmbed]

class RawCurrentUserGuildDict(TypedDict):
    id: int
    name: str
    icon: str
    owner: bool
    permissions: int

class RawWidgetChannelDict(TypedDict):
    id: int
    name: str
    position: int

class BaseRawWidgetMemberDict(TypedDict):
    id: int
    username: str
    discriminator: str
    nick: str
    status: str

class RawWidgetMemberDict(BaseRawWidgetMemberDict, total=False):
    channel_id: int
    avatar: str
    bot: bool
    deaf: bool
    self_deaf: bool
    mute: bool
    self_mute: bool
    suppress: bool
    activity: Union[RawActivityDict, RawSpotifyActivityDict]

class BaseRawWidgetDict(TypedDict):
    id: int
    name: str

class RawWidgetDict(BaseRawWidgetDict, total=False):
    instant_invite: Optional[str]
    channels: List[RawWidgetChannelDict]
    members: List[RawWidgetMemberDict]

__all__ = (
    'RawUserDict', 'RawAttachmentDict', 'RawEmbedFooterDict', 'RawEmbedMediaDict', 'RawEmbedImageDict',
    'RawEmbedProviderDict', 'RawEmbedAuthorDict', 'RawEmbedFieldDict', 'RawEmbedDict', 'RawRoleDict',
    'RawPartialEmojiDict', 'RawEmojiDict', 'RawReactionDict', 'RawMessageActivityDict', 'RawApplicationDict',
    'RawMessageCallDict', 'RawMessageDict', 'RawApplicationInfoDict', 'RawGuildMemberDict',
    'RawGuildMemberRemoveDict', 'RawGuildMemberUpdateDict', 'RawInviteDict', 'RawInviteMetaDict',
    'RawTimestampsDict', 'RawActivityPartyDict', 'RawActivityAssetsDict', 'RawActivityDict',
    'RawPresenceUpdateDict', 'RawOverwriteDict', 'RawChannelDict', 'RawChannelPinsDict',
    'RawGuildEmojisUpdateDict', 'RawVoiceStateDict', 'RawGuildDict', 'RawGuildBanActionDict',
    'RawGuildRoleActionDict', 'RawGuildRoleDeleteDict', 'RawGuildMembersChunkDict',
    'RawVoiceServerUpdateDict', 'RawTypingStartDict', 'RawUnavailableGuildDict', 'RawReadyDict', 'RawWebhookDict',
    'RawAuditLogEntryDict', 'RawAuditLogChangeDict', 'RawAuditLogDict', 'RawSpotifyActivityDict',
    'RawGuildBanDict', 'RawGuildPruneDict', 'RawBulkMessageDeleteDict', 'RawReactionActionDict',
    'RawReactionClearDict', 'EmbedFooterData', 'EmbedImageData', 'EmbedVideoData', 'EmbedProviderData',
    'EmbedAuthorData', 'EmbedFieldData', 'RawCurrentUserGuildDict', 'RawWidgetChannelDict', 'RawWidgetMemberDict',
    'RawWidgetDict'
)
