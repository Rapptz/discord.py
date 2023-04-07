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

from typing import Any, Dict, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from .integration import ConnectionIntegration
from .snowflake import Snowflake


class PartialUser(TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    avatar: Optional[str]
    avatar_decoration: NotRequired[Optional[str]]
    public_flags: NotRequired[int]
    bot: NotRequired[bool]
    system: NotRequired[bool]


ConnectionType = Literal[
    'battlenet',
    'contacts',
    'crunchyroll',
    'ebay',
    'epicgames',
    'facebook',
    'github',
    'leagueoflegends',
    'paypal',
    'playstation',
    'reddit',
    'riotgames',
    'samsung',
    'spotify',
    'skype',
    'steam',
    'tiktok',
    'twitch',
    'twitter',
    'youtube',
    'xbox',
]
ConnectionVisibilty = Literal[0, 1]
PremiumType = Literal[0, 1, 2, 3]


class APIUser(PartialUser):
    banner: Optional[str]
    accent_color: Optional[int]


class User(APIUser, total=False):
    mfa_enabled: bool
    locale: str
    verified: bool
    email: Optional[str]
    flags: int
    purchased_flags: int
    premium_usage_flags: int
    premium_type: PremiumType
    bio: str
    analytics_token: str
    phone: Optional[str]
    token: str
    nsfw_allowed: Optional[bool]


class PartialConnection(TypedDict):
    id: str
    type: ConnectionType
    name: str
    verified: bool
    metadata: NotRequired[Dict[str, Any]]


class Connection(PartialConnection):
    revoked: bool
    visibility: Literal[0, 1]
    metadata_visibility: Literal[0, 1]
    show_activity: bool
    friend_sync: bool
    two_way_link: bool
    integrations: NotRequired[List[ConnectionIntegration]]
    access_token: NotRequired[str]


class ConnectionAccessToken(TypedDict):
    access_token: str


class ConnectionAuthorization(TypedDict):
    url: str


RelationshipType = Literal[-1, 0, 1, 2, 3, 4, 5, 6]


class Relationship(TypedDict):
    id: Snowflake
    type: RelationshipType
    user: PartialUser
    nickname: Optional[str]
    since: NotRequired[str]


class ProtoSettings(TypedDict):
    settings: str


ProtoSettingsType = Literal[1, 2, 3]


class UserAffinity(TypedDict):
    user_id: Snowflake
    affinity: float


class UserAffinities(TypedDict):
    user_affinities: List[UserAffinity]
    inverse_user_affinities: List[UserAffinity]


class GuildAffinity(TypedDict):
    guild_id: Snowflake
    affinity: float


class GuildAffinities(TypedDict):
    guild_affinities: List[GuildAffinity]


class Note(TypedDict):
    note: str
    user_id: Snowflake
    note_user_id: Snowflake
