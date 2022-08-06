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

from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required

from .channel import ChannelType
from .snowflake import Snowflake

ApplicationCommandType = Literal[1, 2, 3]
ApplicationCommandOptionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


class _BaseApplicationCommandOption(TypedDict):
    name: str
    description: str
    name_localizations: NotRequired[Optional[Dict[str, str]]]
    description_localizations: NotRequired[Optional[Dict[str, str]]]


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
    name_localizations: NotRequired[Optional[Dict[str, str]]]
    value: str


class _StringApplicationCommandOption(_BaseApplicationCommandOption):
    type: Literal[3]
    choices: NotRequired[List[_StringApplicationCommandOptionChoice]]
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    autocomplete: NotRequired[bool]


class _IntegerApplicationCommandOptionChoice(TypedDict):
    name: str
    name_localizations: NotRequired[Optional[Dict[str, str]]]
    value: int


class _IntegerApplicationCommandOption(_BaseApplicationCommandOption, total=False):
    type: Required[Literal[4]]
    min_value: int
    max_value: int
    choices: List[_IntegerApplicationCommandOptionChoice]
    autocomplete: bool


class _BooleanApplicationCommandOption(_BaseValueApplicationCommandOption):
    type: Literal[5]


class _ChannelApplicationCommandOptionChoice(_BaseApplicationCommandOption):
    type: Literal[7]
    channel_types: NotRequired[List[ChannelType]]


class _NonChannelSnowflakeApplicationCommandOptionChoice(_BaseValueApplicationCommandOption):
    type: Literal[6, 8, 9, 11]


_SnowflakeApplicationCommandOptionChoice = Union[
    _ChannelApplicationCommandOptionChoice,
    _NonChannelSnowflakeApplicationCommandOptionChoice,
]


class _NumberApplicationCommandOptionChoice(TypedDict):
    name: str
    name_localizations: NotRequired[Optional[Dict[str, str]]]
    value: float


class _NumberApplicationCommandOption(_BaseValueApplicationCommandOption, total=False):
    type: Required[Literal[10]]
    min_value: float
    max_value: float
    choices: List[_NumberApplicationCommandOptionChoice]
    autocomplete: bool


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
    dm_permission: NotRequired[Optional[bool]]
    default_member_permissions: NotRequired[Optional[str]]
    nsfw: NotRequired[bool]
    version: Snowflake
    name_localizations: NotRequired[Optional[Dict[str, str]]]
    description_localizations: NotRequired[Optional[Dict[str, str]]]


class _ChatInputApplicationCommand(_BaseApplicationCommand, total=False):
    description: Required[str]
    type: Literal[1]
    options: Union[
        List[_ValueApplicationCommandOption],
        List[Union[_SubCommandCommandOption, _SubCommandGroupCommandOption]],
    ]


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


ApplicationCommandPermissionType = Literal[1, 2, 3]


class ApplicationCommandPermissions(TypedDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool


class GuildApplicationCommandPermissions(TypedDict):
    id: Snowflake
    application_id: Snowflake
    guild_id: Snowflake
    permissions: List[ApplicationCommandPermissions]
