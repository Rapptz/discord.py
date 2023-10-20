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

from typing import Any, List, Literal, Optional, TypedDict, Dict
from typing_extensions import NotRequired

from .scheduled_event import GuildScheduledEvent
from .sticker import GuildSticker
from .snowflake import Snowflake
from .channel import GuildChannel, StageInstance
from .voice import GuildVoiceState
from .welcome_screen import WelcomeScreen
from .activity import PartialPresenceUpdate
from .role import Role
from .member import Member
from .emoji import Emoji
from .user import User
from .threads import Thread
from .asset import Asset


class Ban(TypedDict):
    reason: Optional[str]
    user: User


class UnavailableGuild(TypedDict):
    id: Snowflake
    unavailable: NotRequired[bool]


DefaultMessageNotificationLevel = Literal[0, 1]
ExplicitContentFilterLevel = Literal[0, 1, 2]
MFALevel = Literal[0, 1]
VerificationLevel = Literal[0, 1, 2, 3, 4]
NSFWLevel = Literal[0, 1, 2, 3]
PremiumTier = Literal[0, 1, 2, 3]
GuildFeature = Literal[
    'ANIMATED_BANNER',
    'ANIMATED_ICON',
    'APPLICATION_COMMAND_PERMISSIONS_V2',
    'AUTO_MODERATION',
    'BANNER',
    'COMMUNITY',
    'CREATOR_MONETIZABLE_PROVISIONAL',
    'CREATOR_STORE_PAGE',
    'DEVELOPER_SUPPORT_SERVER',
    'DISCOVERABLE',
    'FEATURABLE',
    'INVITE_SPLASH',
    'INVITES_DISABLED',
    'MEMBER_VERIFICATION_GATE_ENABLED',
    'MONETIZATION_ENABLED',
    'MORE_EMOJI',
    'MORE_STICKERS',
    'NEWS',
    'PARTNERED',
    'PREVIEW_ENABLED',
    'ROLE_ICONS',
    'ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE',
    'ROLE_SUBSCRIPTIONS_ENABLED',
    'TICKETED_EVENTS_ENABLED',
    'VANITY_URL',
    'VERIFIED',
    'VIP_REGIONS',
    'WELCOME_SCREEN_ENABLED',
    'RAID_ALERTS_DISABLED',
]


class _BaseGuildPreview(UnavailableGuild):
    name: str
    icon: Optional[str]
    splash: Optional[str]
    discovery_splash: Optional[str]
    emojis: List[Emoji]
    stickers: List[GuildSticker]
    features: List[GuildFeature]
    description: Optional[str]


class _GuildPreviewUnique(TypedDict):
    approximate_member_count: int
    approximate_presence_count: int


class GuildPreview(_BaseGuildPreview, _GuildPreviewUnique):
    ...


class Guild(_BaseGuildPreview):
    owner_id: Snowflake
    region: str
    afk_channel_id: Optional[Snowflake]
    afk_timeout: int
    verification_level: VerificationLevel
    default_message_notifications: DefaultMessageNotificationLevel
    explicit_content_filter: ExplicitContentFilterLevel
    roles: List[Role]
    mfa_level: MFALevel
    nsfw_level: NSFWLevel
    application_id: Optional[Snowflake]
    system_channel_id: Optional[Snowflake]
    system_channel_flags: int
    rules_channel_id: Optional[Snowflake]
    vanity_url_code: Optional[str]
    banner: Optional[str]
    premium_tier: PremiumTier
    preferred_locale: str
    public_updates_channel_id: Optional[Snowflake]
    stickers: List[GuildSticker]
    stage_instances: List[StageInstance]
    guild_scheduled_events: List[GuildScheduledEvent]
    icon_hash: NotRequired[Optional[str]]
    owner: NotRequired[bool]
    permissions: NotRequired[str]
    widget_enabled: NotRequired[bool]
    widget_channel_id: NotRequired[Optional[Snowflake]]
    joined_at: NotRequired[Optional[str]]
    large: NotRequired[bool]
    member_count: NotRequired[int]
    voice_states: NotRequired[List[GuildVoiceState]]
    members: NotRequired[List[Member]]
    channels: NotRequired[List[GuildChannel]]
    presences: NotRequired[List[PartialPresenceUpdate]]
    threads: NotRequired[List[Thread]]
    max_presences: NotRequired[Optional[int]]
    max_members: NotRequired[int]
    premium_subscription_count: NotRequired[int]
    max_video_channel_users: NotRequired[int]


class InviteGuild(Guild, total=False):
    welcome_screen: WelcomeScreen


class GuildWithCounts(Guild, _GuildPreviewUnique):
    ...


class GuildPrune(TypedDict):
    pruned: Optional[int]


class GuildMFALevel(TypedDict):
    level: MFALevel


class _ProductPrice(TypedDict):
    amount: float
    currency: str
    currency_exponent: int

class _ProductAttachments(TypedDict): # does not derive from Attachment type because this is more like a "partial attachment"
    id: Snowflake
    filename: str
    size: int
    content_type: str

class ActiveTrial(TypedDict):
    id: Snowflake
    interval: int
    interval_count: int
    sku_id: Snowflake

class GuildShopProduct(TypedDict):
    id: Snowflake
    application_id: Snowflake
    guild_id: Snowflake
    name: str
    description: str
    image_asset: Asset
    role_id: NotRequired[Optional[Snowflake]]
    published: bool
    has_entitlement: bool
    attachments_count: int
    published_at: NotRequired[str]
    price: _ProductPrice
    price_tier: float
    attachments: List[_ProductAttachments]
    
class GuildShopProductsListings(TypedDict):
    listings: List[GuildShopProduct]


class GuildShop(TypedDict):
    guild_id: Snowflake
    full_server_gate: bool
    description: NotRequired[Optional[str]]
    store_page_primary_color: NotRequired[Optional[Any]] # Will use typing.Any until a guild sets this up
    store_page_trailer_url: NotRequired[Optional[str]]
    store_page_show_subscriber_count: bool
    store_page_guild_products_default_sort: int
    cover_image_asset: NotRequired[Optional[Asset]]
    store_page_slug: NotRequired[Optional[str]]

class GuildProductTrial(TypedDict):
    id: Snowflake
    num_active_trial_users: int
    max_num_active_trial_users: Optional[int]
    active_trial: ActiveTrial

class GuildSubscriptionPlan(TypedDict):
    id: Snowflake
    name: str
    interval: int
    interval_count: int
    tax_inclusive: bool
    sku_id: Snowflake
    currency: str
    price: float
    price_tier: NotRequired[Optional[float]]
    prices: NotRequired[Dict[str, Dict[Literal['country_codes'], List[_ProductPrice]]]] # using Dict[str, Dict[Literal['country_code'], _ProductPrice]] because
                                                                                        # the returning payload is {"(any integer, but as string)": {"country_prices": _ProductPrice}}

class GuildSubscription(TypedDict):
    id: Snowflake
    name: str
    description: NotRequired[Optional[str]]
    image_asset: NotRequired[Optional[Asset]]
    subscription_plans: List[GuildSubscriptionPlan]

class ChannelPositionUpdate(TypedDict):
    id: Snowflake
    position: Optional[int]
    lock_permissions: Optional[bool]
    parent_id: Optional[Snowflake]


class _RolePositionRequired(TypedDict):
    id: Snowflake


class RolePositionUpdate(_RolePositionRequired, total=False):
    position: Optional[Snowflake]
