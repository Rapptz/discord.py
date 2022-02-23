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

from .channel import ChannelType
from .snowflake import Snowflake

ApplicationCommandType = Literal[1, 2, 3]
ApplicationCommandOptionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


class _BaseApplicationCommandOption(TypedDict):
    name: str
    description: str


class _SubCommandCommandOption(_BaseApplicationCommandOption):
    type: Literal[1]
    options: List[_ValueApplicationCommandOption]


class _SubCommandGroupCommandOption(_BaseApplicationCommandOption):
    type: Literal[2]
    options: List[_SubCommandCommandOption]


class _BaseValueApplicationCommandOption(_BaseApplicationCommandOption, total=False):
    required: bool


class _StringApplicationCommandOptionChoice(TypedDict):
    name: str
    value: str


class _StringApplicationCommandOptionOptional(_BaseValueApplicationCommandOption, total=False):
    choices: List[_StringApplicationCommandOptionChoice]
    autocomplete: bool


class _StringApplicationCommandOption(_StringApplicationCommandOptionOptional):
    type: Literal[3]


class _IntegerApplicationCommandOptionChoice(TypedDict):
    name: str
    value: int


class _IntegerApplicationCommandOptionOptional(_BaseValueApplicationCommandOption, total=False):
    min_value: int
    max_value: int
    choices: List[_IntegerApplicationCommandOptionChoice]
    autocomplete: bool


class _IntegerApplicationCommandOption(_IntegerApplicationCommandOptionOptional):
    type: Literal[4]


class _BooleanApplicationCommandOption(_BaseValueApplicationCommandOption):
    type: Literal[5]


class _ChannelApplicationCommandOptionChoiceOptional(_BaseApplicationCommandOption, total=False):
    channel_types: List[ChannelType]


class _ChannelApplicationCommandOptionChoice(_ChannelApplicationCommandOptionChoiceOptional):
    type: Literal[7]


class _NonChannelSnowflakeApplicationCommandOptionChoice(_BaseValueApplicationCommandOption):
    type: Literal[6, 8, 9, 11]


_SnowflakeApplicationCommandOptionChoice = Union[
    _ChannelApplicationCommandOptionChoice,
    _NonChannelSnowflakeApplicationCommandOptionChoice,
]


class _NumberApplicationCommandOptionChoice(TypedDict):
    name: str
    value: float


class _NumberApplicationCommandOptionOptional(_BaseValueApplicationCommandOption, total=False):
    min_value: float
    max_value: float
    choices: List[_NumberApplicationCommandOptionChoice]
    autocomplete: bool


class _NumberApplicationCommandOption(_NumberApplicationCommandOptionOptional):
    type: Literal[10]


_ValueApplicationCommandOption = Union[
    _StringApplicationCommandOption,
    _IntegerApplicationCommandOption,
    _BooleanApplicationCommandOption,
    _SnowflakeApplicationCommandOptionChoice,
    _NumberApplicationCommandOption,
]

ApplicationCommandOption = Union[
    _SubCommandGroupCommandOption,
    _SubCommandCommandOption,
    _ValueApplicationCommandOption,
]

ApplicationCommandOptionChoice = Union[
    _StringApplicationCommandOptionChoice,
    _IntegerApplicationCommandOptionChoice,
    _NumberApplicationCommandOptionChoice,
]


class _BaseApplicationCommand(TypedDict):
    id: Snowflake
    application_id: Snowflake
    name: str
    version: Snowflake


class _ChatInputApplicationCommandOptional(_BaseApplicationCommand, total=False):
    type: Literal[1]
    options: Union[
        List[_ValueApplicationCommandOption],
        List[Union[_SubCommandCommandOption, _SubCommandGroupCommandOption]],
    ]


class _ChatInputApplicationCommand(_ChatInputApplicationCommandOptional):
    description: str


class _BaseContextMenuApplicationCommand(_BaseApplicationCommand):
    description: Literal[""]


class _UserApplicationCommand(_BaseContextMenuApplicationCommand):
    type: Literal[2]


class _MessageApplicationCommand(_BaseContextMenuApplicationCommand):
    type: Literal[3]


GlobalApplicationCommand = Union[
    _ChatInputApplicationCommand,
    _UserApplicationCommand,
    _MessageApplicationCommand,
]


class _GuildChatInputApplicationCommand(_ChatInputApplicationCommand):
    guild_id: Snowflake


class _GuildUserApplicationCommand(_UserApplicationCommand):
    guild_id: Snowflake


class _GuildMessageApplicationCommand(_MessageApplicationCommand):
    guild_id: Snowflake


GuildApplicationCommand = Union[
    _GuildChatInputApplicationCommand,
    _GuildUserApplicationCommand,
    _GuildMessageApplicationCommand,
]


ApplicationCommand = Union[
    GlobalApplicationCommand,
    GuildApplicationCommand,
]


ApplicationCommandPermissionType = Literal[1, 2]


class ApplicationCommandPermissions(TypedDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool


class GuildApplicationCommandPermissions(TypedDict):
    id: Snowflake
    application_id: Snowflake
    guild_id: Snowflake
    permissions: List[ApplicationCommandPermissions]
