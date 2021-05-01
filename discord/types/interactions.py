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

from typing import Dict, TypedDict, Union, List, Literal
from .snowflake import Snowflake
from .message import AllowedMentions
from .channel import PartialChannel
from .embed import Embed
from .member import Member
from .role import Role
from .user import User


class _ApplicationCommandOptional(TypedDict, total=False):
    options: List[ApplicationCommandOption]


class ApplicationCommand(_ApplicationCommandOptional):
    id: Snowflake
    application_id: Snowflake
    name: str
    description: str


class _ApplicationCommandOptionOptional(TypedDict, total=False):
    choices: List[ApplicationCommandOptionChoice]
    options: List[ApplicationCommandOption]


ApplicationCommandOptionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]


class ApplicationCommandOption(_ApplicationCommandOptionOptional):
    type: ApplicationCommandOptionType
    name: str
    description: str
    required: bool


class ApplicationCommandOptionChoice(TypedDict):
    name: str
    value: Union[str, int]


ApplicationCommandPermissionType = Literal[1, 2]


class ApplicationCommandPermissions(TypedDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool


class PartialGuildApplicationCommandPermissions(TypedDict):
    id: Snowflake
    permissions: List[ApplicationCommandPermissions]


class GuildApplicationCommandPermissions(PartialGuildApplicationCommandPermissions):
    application_id: Snowflake
    guild_id: Snowflake


InteractionType = Literal[1, 2]


class _ApplicationCommandInteractionDataOptionOptional(TypedDict, total=False):
    value: ApplicationCommandOptionType
    options: List[ApplicationCommandInteractionDataOption]


class ApplicationCommandInteractionDataOption(_ApplicationCommandInteractionDataOptionOptional):
    name: str
    type: ApplicationCommandOptionType


class ApplicationCommandInteractionDataResolved(TypedDict, total=False):
    users: Dict[Snowflake, User]
    members: Dict[Snowflake, Member]
    roles: Dict[Snowflake, Role]
    channels: Dict[Snowflake, PartialChannel]


class _ApplicationCommandInteractionDataOptional(TypedDict, total=False):
    options: List[ApplicationCommandInteractionDataOption]
    resolved: ApplicationCommandInteractionDataResolved


class ApplicationCommandInteractionData(_ApplicationCommandInteractionDataOptional):
    id: Snowflake
    name: str


class _InteractionOptional(TypedDict, total=False):
    data: ApplicationCommandInteractionData
    guild_id: Snowflake
    channel_id: Snowflake
    member: Member
    user: User


class Interaction(_InteractionOptional):
    id: Snowflake
    application_id: Snowflake
    type: InteractionType
    token: str
    version: int


class InteractionApplicationCommandCallbackData(TypedDict, total=False):
    tts: bool
    content: str
    embeds: List[Embed]
    allowed_mentions: AllowedMentions
    flags: int


InteractionResponseType = Literal[1, 2, 3, 4, 5]


class _InteractionResponseOptional(TypedDict, total=False):
    data: InteractionApplicationCommandCallbackData


class InteractionResponse(_InteractionResponseOptional):
    type: InteractionResponseType


class MessageInteraction(TypedDict):
    id: Snowflake
    type: InteractionType
    name: str
    user: User
