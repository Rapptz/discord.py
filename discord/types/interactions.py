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

from typing import Optional, TYPE_CHECKING, Dict, TypedDict, Union, List, Literal
from .snowflake import Snowflake
from .components import Component, ComponentType
from .embed import Embed
from .channel import ChannelType
from .member import Member
from .role import Role
from .user import User

if TYPE_CHECKING:
    from .message import AllowedMentions, Message


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


ApplicationCommandOptionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


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


class BaseGuildApplicationCommandPermissions(TypedDict):
    permissions: List[ApplicationCommandPermissions]


class PartialGuildApplicationCommandPermissions(BaseGuildApplicationCommandPermissions):
    id: Snowflake


class GuildApplicationCommandPermissions(PartialGuildApplicationCommandPermissions):
    application_id: Snowflake
    guild_id: Snowflake


InteractionType = Literal[1, 2, 3]


class _ApplicationCommandInteractionDataOption(TypedDict):
    name: str


class _ApplicationCommandInteractionDataOptionSubcommand(_ApplicationCommandInteractionDataOption):
    type: Literal[1, 2]
    options: List[ApplicationCommandInteractionDataOption]


class _ApplicationCommandInteractionDataOptionString(_ApplicationCommandInteractionDataOption):
    type: Literal[3]
    value: str


class _ApplicationCommandInteractionDataOptionInteger(_ApplicationCommandInteractionDataOption):
    type: Literal[4]
    value: int


class _ApplicationCommandInteractionDataOptionBoolean(_ApplicationCommandInteractionDataOption):
    type: Literal[5]
    value: bool


class _ApplicationCommandInteractionDataOptionSnowflake(_ApplicationCommandInteractionDataOption):
    type: Literal[6, 7, 8, 9]
    value: Snowflake


class _ApplicationCommandInteractionDataOptionNumber(_ApplicationCommandInteractionDataOption):
    type: Literal[10]
    value: float


ApplicationCommandInteractionDataOption = Union[
    _ApplicationCommandInteractionDataOptionString,
    _ApplicationCommandInteractionDataOptionInteger,
    _ApplicationCommandInteractionDataOptionSubcommand,
    _ApplicationCommandInteractionDataOptionBoolean,
    _ApplicationCommandInteractionDataOptionSnowflake,
    _ApplicationCommandInteractionDataOptionNumber,
]


class ApplicationCommandResolvedPartialChannel(TypedDict):
    id: Snowflake
    type: ChannelType
    permissions: str
    name: str


class ApplicationCommandInteractionDataResolved(TypedDict, total=False):
    users: Dict[Snowflake, User]
    members: Dict[Snowflake, Member]
    roles: Dict[Snowflake, Role]
    channels: Dict[Snowflake, ApplicationCommandResolvedPartialChannel]


class _ApplicationCommandInteractionDataOptional(TypedDict, total=False):
    options: List[ApplicationCommandInteractionDataOption]
    resolved: ApplicationCommandInteractionDataResolved


class ApplicationCommandInteractionData(_ApplicationCommandInteractionDataOptional):
    id: Snowflake
    name: str


class _ComponentInteractionDataOptional(TypedDict, total=False):
    values: List[str]


class ComponentInteractionData(_ComponentInteractionDataOptional):
    custom_id: str
    component_type: ComponentType


InteractionData = Union[ApplicationCommandInteractionData, ComponentInteractionData]


class _InteractionOptional(TypedDict, total=False):
    data: InteractionData
    guild_id: Snowflake
    channel_id: Snowflake
    member: Member
    user: User
    message: Message


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
    components: List[Component]


InteractionResponseType = Literal[1, 4, 5, 6, 7]


class _InteractionResponseOptional(TypedDict, total=False):
    data: InteractionApplicationCommandCallbackData


class InteractionResponse(_InteractionResponseOptional):
    type: InteractionResponseType


class MessageInteraction(TypedDict):
    id: Snowflake
    type: InteractionType
    name: str
    user: User


class EditApplicationCommand(TypedDict):
    name: str
    description: str
    options: Optional[List[ApplicationCommandOption]]
    default_permission: bool
