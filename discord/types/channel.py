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
from .user import PartialUser
from .snowflake import Snowflake
from .threads import ThreadMetadata, ThreadMember


OverwriteType = Literal[0, 1]


class PermissionOverwrite(TypedDict):
    id: Snowflake
    type: OverwriteType
    allow: str
    deny: str


ChannelType = Literal[0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13]


class _BaseChannel(TypedDict):
    id: Snowflake
    name: str


class _BaseGuildChannel(_BaseChannel):
    guild_id: Snowflake
    position: int
    permission_overwrites: List[PermissionOverwrite]
    nsfw: bool
    parent_id: Optional[Snowflake]


class PartialChannel(_BaseChannel):
    type: ChannelType


class _TextChannelOptional(TypedDict, total=False):
    topic: str
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: str
    rate_limit_per_user: int


class TextChannel(_BaseGuildChannel, _TextChannelOptional):
    type: Literal[0]


class NewsChannel(_BaseGuildChannel, _TextChannelOptional):
    type: Literal[5]


VideoQualityMode = Literal[1, 2]


class _VoiceChannelOptional(TypedDict, total=False):
    rtc_region: Optional[str]
    video_quality_mode: VideoQualityMode


class VoiceChannel(_BaseGuildChannel, _VoiceChannelOptional):
    type: Literal[2]
    bitrate: int
    user_limit: int


class CategoryChannel(_BaseGuildChannel):
    type: Literal[4]


class StoreChannel(_BaseGuildChannel):
    type: Literal[6]


class _StageChannelOptional(TypedDict, total=False):
    rtc_region: Optional[str]
    topic: str


class StageChannel(_BaseGuildChannel, _StageChannelOptional):
    type: Literal[13]
    bitrate: int
    user_limit: int


class _ThreadChannelOptional(TypedDict, total=False):
    member: ThreadMember
    owner_id: Snowflake
    rate_limit_per_user: int
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: str


class ThreadChannel(_BaseChannel, _ThreadChannelOptional):
    type: Literal[10, 11, 12]
    guild_id: Snowflake
    parent_id: Snowflake
    owner_id: Snowflake
    nsfw: bool
    last_message_id: Optional[Snowflake]
    rate_limit_per_user: int
    message_count: int
    member_count: int
    thread_metadata: ThreadMetadata


GuildChannel = Union[TextChannel, NewsChannel, VoiceChannel, CategoryChannel, StoreChannel, StageChannel, ThreadChannel]


class DMChannel(_BaseChannel):
    type: Literal[1]
    last_message_id: Optional[Snowflake]
    recipients: List[PartialUser]


class GroupDMChannel(_BaseChannel):
    type: Literal[3]
    icon: Optional[str]
    owner_id: Snowflake


Channel = Union[GuildChannel, DMChannel, GroupDMChannel]

PrivacyLevel = Literal[1, 2]


class StageInstance(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Snowflake
    topic: str
    privacy_level: PrivacyLevel
    discoverable_disabled: bool
