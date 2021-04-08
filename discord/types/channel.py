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

from .user import PartialUser
from .snowflake import Snowflake
from typing import List, Literal, Optional, TypedDict


class PermissionOverwrite(TypedDict):
    id: Snowflake
    type: Literal[0, 1]
    allow: str
    deny: str


ChannelType = Literal[0, 1, 2, 3, 4, 5, 6, 13]


class PartialChannel(TypedDict):
    id: str
    type: ChannelType
    name: str


class _TextChannelOptional(PartialChannel, total=False):
    topic: str
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: str
    rate_limit_per_user: int


class _VoiceChannelOptional(PartialChannel, total=False):
    rtc_region: Optional[str]
    bitrate: int
    user_limit: int


class _CategoryChannelOptional(PartialChannel, total=False):
    ...


class _StoreChannelOptional(PartialChannel, total=False):
    ...


class _StageChannelOptional(PartialChannel, total=False):
    rtc_region: Optional[str]
    bitrate: int
    user_limit: int
    topic: str


class GuildChannel(
    _TextChannelOptional, _VoiceChannelOptional, _CategoryChannelOptional, _StoreChannelOptional, _StageChannelOptional
):
    guild_id: Snowflake
    position: int
    permission_overwrites: List[PermissionOverwrite]
    nsfw: bool
    parent_id: Optional[Snowflake]


class DMChannel(PartialChannel):
    last_message_id: Optional[Snowflake]
    recipients: List[PartialUser]


class GroupDMChannel(DMChannel):
    icon: Optional[str]
    owner_id: Snowflake
