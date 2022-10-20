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

from typing import List, Literal, TypedDict, Union
from typing_extensions import NotRequired

from .emoji import PartialEmoji
from .channel import ChannelType

ComponentType = Literal[1, 2, 3, 4]
ButtonStyle = Literal[1, 2, 3, 4, 5]
TextStyle = Literal[1, 2]


class ActionRow(TypedDict):
    type: Literal[1]
    components: List[ActionRowChildComponent]


class ButtonComponent(TypedDict):
    type: Literal[2]
    style: ButtonStyle
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    emoji: NotRequired[PartialEmoji]
    label: NotRequired[str]


class SelectOption(TypedDict):
    label: str
    value: str
    default: bool
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]


class SelectComponent(TypedDict):
    custom_id: str
    placeholder: NotRequired[str]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]


class StringSelectComponent(SelectComponent):
    type: Literal[3]
    options: NotRequired[List[SelectOption]]


class UserSelectComponent(SelectComponent):
    type: Literal[5]


class RoleSelectComponent(SelectComponent):
    type: Literal[6]


class MentionableSelectComponent(SelectComponent):
    type: Literal[7]


class ChannelSelectComponent(SelectComponent):
    type: Literal[8]
    channel_types: NotRequired[List[ChannelType]]


class TextInput(TypedDict):
    type: Literal[4]
    custom_id: str
    style: TextStyle
    label: str
    placeholder: NotRequired[str]
    value: NotRequired[str]
    required: NotRequired[bool]
    min_length: NotRequired[int]
    max_length: NotRequired[int]


class SelectMenu(SelectComponent):
    type: Literal[3, 5, 6, 7, 8]
    options: NotRequired[List[SelectOption]]
    channel_types: NotRequired[List[ChannelType]]


ActionRowChildComponent = Union[ButtonComponent, SelectMenu, TextInput]
Component = Union[ActionRow, ActionRowChildComponent]
