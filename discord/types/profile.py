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

from typing import List, Optional, Tuple, TypedDict
from typing_extensions import NotRequired, Required

from .application import ApplicationInstallParams, RoleConnection
from .emoji import Emoji
from .member import PrivateMember as ProfileMember
from .snowflake import Snowflake
from .user import APIUser, PartialConnection, PremiumType


class ProfileUser(APIUser):
    bio: str


class ProfileEffect(TypedDict):
    id: Snowflake
    expires_at: Optional[int]


class ProfileMetadata(TypedDict, total=False):
    guild_id: int
    bio: str
    banner: Optional[str]
    accent_color: Optional[int]
    theme_colors: Optional[Tuple[int, int]]
    emoji: Optional[Emoji]
    popout_animation_particle_type: Optional[Snowflake]
    profile_effect: Optional[ProfileEffect]
    pronouns: Required[str]


class MutualGuild(TypedDict):
    id: Snowflake
    nick: Optional[str]


class ProfileApplication(TypedDict):
    id: Snowflake
    verified: bool
    storefront_available: bool
    popular_application_command_ids: NotRequired[List[Snowflake]]
    primary_sku_id: NotRequired[Snowflake]
    flags: int
    custom_install_url: NotRequired[str]
    install_params: NotRequired[ApplicationInstallParams]


class ProfileBadge(TypedDict):
    id: str
    description: str
    icon: str
    link: NotRequired[str]


class Profile(TypedDict):
    user: ProfileUser
    user_profile: Optional[ProfileMetadata]
    badges: List[ProfileBadge]
    guild_member: NotRequired[ProfileMember]
    guild_member_profile: NotRequired[Optional[ProfileMetadata]]
    guild_badges: List[ProfileBadge]
    mutual_guilds: NotRequired[List[MutualGuild]]
    mutual_friends: NotRequired[List[APIUser]]
    mutual_friends_count: NotRequired[int]
    connected_accounts: List[PartialConnection]
    application_role_connections: NotRequired[List[RoleConnection]]
    premium_type: Optional[PremiumType]
    premium_since: Optional[str]
    premium_guild_since: Optional[str]
    legacy_username: Optional[str]
    application: NotRequired[ProfileApplication]
