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
from .emoji import PartialEmoji

ComponentType = Literal[1, 2, 3]
ButtonStyle = Literal[1, 2, 3, 4, 5]


class ActionRow(TypedDict):
    type: Literal[1]
    components: List[Component]


class _ButtonComponentOptional(TypedDict, total=False):
    custom_id: str
    url: str
    disabled: bool
    emoji: PartialEmoji
    label: str


class ButtonComponent(_ButtonComponentOptional):
    type: Literal[2]
    style: ButtonStyle


class _SelectMenuOptional(TypedDict, total=False):
    placeholder: str
    min_values: int
    max_values: int
    disabled: bool


class _SelectOptionsOptional(TypedDict, total=False):
    description: str
    emoji: PartialEmoji


class SelectOption(_SelectOptionsOptional):
    label: str
    value: str
    default: bool


class SelectMenu(_SelectMenuOptional):
    type: Literal[3]
    custom_id: str
    options: List[SelectOption]


Component = Union[ActionRow, ButtonComponent, SelectMenu]
