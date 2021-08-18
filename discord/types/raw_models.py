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

from typing import TypedDict, List
from .snowflake import Snowflake
from .member import Member
from .emoji import PartialEmoji


class _MessageEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class MessageDeleteEvent(_MessageEventOptional):
    id: Snowflake
    channel_id: Snowflake


class BulkMessageDeleteEvent(_MessageEventOptional):
    ids: List[Snowflake]
    channel_id: Snowflake


class _ReactionActionEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    member: Member


class MessageUpdateEvent(_MessageEventOptional):
    id: Snowflake
    channel_id: Snowflake


class ReactionActionEvent(_ReactionActionEventOptional):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji


class _ReactionClearEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class ReactionClearEvent(_ReactionClearEventOptional):
    channel_id: Snowflake
    message_id: Snowflake


class _ReactionClearEmojiEventOptional(TypedDict, total=False):
    guild_id: Snowflake


class ReactionClearEmojiEvent(_ReactionClearEmojiEventOptional):
    channel_id: int
    message_id: int
    emoji: PartialEmoji


class _IntegrationDeleteEventOptional(TypedDict, total=False):
    application_id: Snowflake


class IntegrationDeleteEvent(_IntegrationDeleteEventOptional):
    id: Snowflake
    guild_id: Snowflake
