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
from .snowflake import Snowflake
from .channel import GuildChannel
from .voice import PartialVoiceState
from .welcome_screen import WelcomeScreen
from .activity import PartialPresenceUpdate
from .role import Role
from .member import Member
from .emoji import Emoji
from .user import User


class Ban(TypedDict):
    reason: Optional[str]
    user: User


class _UnavailableGuildOptional(TypedDict, total=False):
    unavailable: bool


class UnavailableGuild(_UnavailableGuildOptional):
    id: Snowflake


class _GuildOptional(TypedDict, total=False):
    icon_hash: Optional[str]
    owner: bool
    permissions: str
    widget_enabled: bool
    widget_channel_id: Optional[Snowflake]
    joined_at: Optional[str]
    large: bool
    member_count: int
    voice_states: List[PartialVoiceState]
    members: List[Member]
    channels: List[GuildChannel]
    presences: List[PartialPresenceUpdate]
    max_presences: Optional[int]
    max_members: int
    premium_subscription_count: int
    max_video_channel_users: int


DefaultMessageNotificationLevel = Literal[0, 1]
ExplicitContentFilterLevel = Literal[0, 1, 2]
MFALevel = Literal[0, 1]
VerificationLevel = Literal[0, 1, 2, 3, 4]
PremiumTier = Literal[0, 1, 2, 3]
GuildFeature = Literal[
    'INVITE_SPLASH',
    'VIP_REGIONS',
    'VANITY_URL',
    'VERIFIED',
    'PARTNERED',
    'COMMUNITY',
    'COMMERCE',
    'NEWS',
    'DISCOVERABLE',
    'FEATURABLE',
    'ANIMATED_ICON',
    'BANNER',
    'WELCOME_SCREEN_ENABLED',
    'MEMBER_VERIFICATION_GATE_ENABLED',
    'PREVIEW_ENABLED',
]


class _BaseGuildPreview(UnavailableGuild):
    name: str
    icon: Optional[str]
    splash: Optional[str]
    discovery_splash: Optional[str]
    emojis: List[Emoji]
    features: List[GuildFeature]
    description: Optional[str]


class _GuildPreviewUnique(TypedDict):
    approximate_member_count: int
    approximate_presence_count: int


class GuildPreview(_BaseGuildPreview, _GuildPreviewUnique):
    ...


class Guild(_BaseGuildPreview, _GuildOptional):
    owner_id: Snowflake
    region: str
    afk_channel_id: Optional[Snowflake]
    afk_timeout: int
    verification_level: VerificationLevel
    default_message_notifications: DefaultMessageNotificationLevel
    explicit_content_filter: ExplicitContentFilterLevel
    roles: List[Role]
    mfa_level: MFALevel
    nsfw: bool
    application_id: Optional[Snowflake]
    system_channel_id: Optional[Snowflake]
    system_channel_flags: int
    rules_channel_id: Optional[Snowflake]
    vanity_url_code: Optional[str]
    banner: Optional[str]
    premium_tier: PremiumTier
    preferred_locale: str
    public_updates_channel_id: Optional[Snowflake]


class InviteGuild(Guild, total=False):
    welcome_screen: WelcomeScreen


class GuildWithCounts(Guild, _GuildPreviewUnique):
    ...
