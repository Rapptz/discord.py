"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

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

from typing import List, TypedDict

from .automod import AutoModAction, AutoModTriggerType
from .emoji import PartialEmoji
from .member import Member
from .snowflake import Snowflake


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


class ThreadDeleteEvent(TypedDict, total=False):
    thread_id: Snowflake
    thread_type: int
    guild_id: Snowflake
    parent_id: Snowflake


class _TypingEventOptional(TypedDict, total=False):
    guild_id: Snowflake
    member: Member


class TypingEvent(_TypingEventOptional):
    channel_id: Snowflake
    user_id: Snowflake
    timestamp: int


class ScheduledEventSubscription(TypedDict, total=False):
    event_id: Snowflake
    user_id: Snowflake
    guild_id: Snowflake


class _AutoModActionExecutionEventOptional(TypedDict, total=False):
    channel_id: Snowflake
    message_id: Snowflake
    alert_system_message_id: Snowflake
    matched_keyword: str
    matched_content: str
        
        
class AutoModActionExecutionEvent(_AutoModActionExecutionEventOptional):
    guild_id: Snowflake
    action: AutoModAction
    rule_id: Snowflake
    rule_trigger_type: AutoModTriggerType
    user_id: Snowflake
    content: str
