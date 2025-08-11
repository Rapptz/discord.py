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
from typing import TYPE_CHECKING, Literal, Optional, TypedDict, List, Union

from .emoji import PartialEmoji
from .snowflake import Snowflake

if TYPE_CHECKING:
    from typing_extensions import NotRequired


PromptType = Literal[0, 1]
OnboardingMode = Literal[0, 1]


class _PromptOption(TypedDict):
    channel_ids: List[Snowflake]
    role_ids: List[Snowflake]
    title: str
    description: Optional[str]


class CreatePromptOption(_PromptOption):
    emoji_id: NotRequired[Snowflake]
    emoji_name: NotRequired[str]
    emoji_animated: NotRequired[bool]


class PromptOption(_PromptOption):
    id: Snowflake
    emoji: NotRequired[PartialEmoji]


class Prompt(TypedDict):
    id: Snowflake
    options: List[Union[PromptOption, CreatePromptOption]]
    title: str
    single_select: bool
    required: bool
    in_onboarding: bool
    type: PromptType


class Onboarding(TypedDict):
    guild_id: Snowflake
    prompts: List[Prompt]
    default_channel_ids: List[Snowflake]
    enabled: bool
    mode: OnboardingMode
