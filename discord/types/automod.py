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

from typing import Literal, TypedDict, List, Union, Optional
from typing_extensions import NotRequired

from .snowflake import Snowflake

AutoModerationRuleTriggerType = Literal[1, 2, 3, 4]
AutoModerationActionTriggerType = Literal[1, 2, 3]
AutoModerationRuleEventType = Literal[1]
AutoModerationTriggerPresets = Literal[1, 2, 3]


class Empty(TypedDict): ...


class _AutoModerationActionMetadataAlert(TypedDict):
    channel_id: Snowflake


class _AutoModerationActionMetadataTimeout(TypedDict):
    duration_seconds: int


class _AutoModerationActionMetadataCustomMessage(TypedDict):
    custom_message: str


class _AutoModerationActionBlockMessage(TypedDict):
    type: Literal[1]
    metadata: NotRequired[_AutoModerationActionMetadataCustomMessage]


class _AutoModerationActionAlert(TypedDict):
    type: Literal[2]
    metadata: _AutoModerationActionMetadataAlert


class _AutoModerationActionTimeout(TypedDict):
    type: Literal[3]
    metadata: _AutoModerationActionMetadataTimeout


AutoModerationAction = Union[_AutoModerationActionBlockMessage, _AutoModerationActionAlert, _AutoModerationActionTimeout]


class _AutoModerationTriggerMetadataKeyword(TypedDict):
    keyword_filter: List[str]
    regex_patterns: NotRequired[List[str]]


class _AutoModerationTriggerMetadataKeywordPreset(TypedDict):
    presets: List[AutoModerationTriggerPresets]
    allow_list: List[str]


class _AutoModerationTriggerMetadataMentionLimit(TypedDict):
    mention_total_limit: int
    mention_raid_protection_enabled: bool


AutoModerationTriggerMetadata = Union[
    _AutoModerationTriggerMetadataKeyword,
    _AutoModerationTriggerMetadataKeywordPreset,
    _AutoModerationTriggerMetadataMentionLimit,
    Empty,
]


class _BaseAutoModerationRule(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    name: str
    creator_id: Snowflake
    event_type: AutoModerationRuleEventType
    actions: List[AutoModerationAction]
    enabled: bool
    exempt_roles: List[Snowflake]
    exempt_channels: List[Snowflake]


class _AutoModerationRuleKeyword(_BaseAutoModerationRule):
    trigger_type: Literal[1]
    trigger_metadata: _AutoModerationTriggerMetadataKeyword


class _AutoModerationRuleKeywordPreset(_BaseAutoModerationRule):
    trigger_type: Literal[4]
    trigger_metadata: _AutoModerationTriggerMetadataKeywordPreset


class _AutoModerationRuleOther(_BaseAutoModerationRule):
    trigger_type: Literal[2, 3]


AutoModerationRule = Union[_AutoModerationRuleKeyword, _AutoModerationRuleKeywordPreset, _AutoModerationRuleOther]


class AutoModerationActionExecution(TypedDict):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: AutoModerationRuleTriggerType
    user_id: Snowflake
    channel_id: NotRequired[Snowflake]
    message_id: NotRequired[Snowflake]
    alert_system_message_id: NotRequired[Snowflake]
    content: str
    matched_keyword: Optional[str]
    matched_content: Optional[str]
