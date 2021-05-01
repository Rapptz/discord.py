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

from typing import List, Literal, Optional, TypedDict, Union
from .snowflake import Snowflake, SnowflakeList
from .member import Member
from .user import User
from .emoji import PartialEmoji
from .embed import Embed
from .channel import ChannelType
from .interactions import MessageInteraction


class ChannelMention(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    type: ChannelType
    name: str


class Reaction(TypedDict):
    count: int
    me: bool
    emoji: PartialEmoji


class _AttachmentOptional(TypedDict, total=False):
    height: Optional[int]
    width: Optional[int]
    content_type: str
    spoiler: bool


class Attachment(_AttachmentOptional):
    id: Snowflake
    filename: str
    size: int
    url: str
    proxy_url: str


MessageActivityType = Literal[1, 2, 3, 5]


class MessageActivity(TypedDict):
    type: MessageActivityType
    party_id: str


class _MessageApplicationOptional(TypedDict, total=False):
    cover_image: str


class MessageApplication(_MessageApplicationOptional):
    id: Snowflake
    description: str
    icon: Optional[str]
    name: str


class MessageReference(TypedDict, total=False):
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Snowflake
    fail_if_not_exists: bool


class _StickerOptional(TypedDict, total=False):
    tags: str


StickerFormatType = Literal[1, 2, 3]


class Sticker(_StickerOptional):
    id: Snowflake
    pack_id: Snowflake
    name: str
    description: str
    asset: str
    preview_asset: str
    format_type: StickerFormatType


class _MessageOptional(TypedDict, total=False):
    guild_id: Snowflake
    member: Member
    mention_channels: List[ChannelMention]
    reactions: List[Reaction]
    nonce: Union[int, str]
    webhook_id: Snowflake
    activity: MessageActivity
    application: MessageApplication
    message_reference: MessageReference
    flags: int
    stickers: List[Sticker]
    referenced_message: Optional[Message]
    interaction: MessageInteraction


MessageType = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 19, 20]


class Message(_MessageOptional):
    id: Snowflake
    channel_id: Snowflake
    author: User
    content: str
    timestamp: str
    edited_timestamp: Optional[str]
    tts: bool
    mention_everyone: bool
    mentions: List[User]
    mention_roles: SnowflakeList
    attachments: List[Attachment]
    embeds: List[Embed]
    pinned: bool
    type: MessageType


AllowedMentionType = Literal['roles', 'users', 'everyone']


class AllowedMentions(TypedDict):
    parse: List[AllowedMentionType]
    roles: SnowflakeList
    users: SnowflakeList
    replied_user: bool
