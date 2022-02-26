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

from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple
from ..interactions import Interaction
from ..member import Member
from ..object import Object
from ..role import Role
from ..message import Message, Attachment
from ..channel import PartialMessageable
from .models import AppCommandChannel, AppCommandThread

if TYPE_CHECKING:
    from ..types.interactions import ResolvedData, ApplicationCommandInteractionDataOption


class Namespace:
    """An object that holds the parameters being passed to a command in a mostly raw state.

    This class is deliberately simple and just holds the option name and resolved value as a simple
    key-pair mapping. These attributes can be accessed using dot notation. For example, an option
    with the name of ``example`` can be accessed using ``ns.example``.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two namespaces are equal by checking if all attributes are equal.
        .. describe:: x != y

            Checks if two namespaces are not equal.

    This namespace object converts resolved objects into their appropriate form depending on their
    type. Consult the table below for conversion information.

    +------------------------------------------+-------------------------------------------------------------------------------+
    |               Option Type                |                                 Resolved Type                                 |
    +==========================================+===============================================================================+
    | :attr:`AppCommandOptionType.string`      | :class:`str`                                                                  |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.integer`     | :class:`int`                                                                  |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.boolean`     | :class:`bool`                                                                 |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.number`      | :class:`float`                                                                |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.user`        | :class:`~discord.User` or :class:`~discord.Member`                            |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.channel`     | :class:`.AppCommandChannel` or :class:`.AppCommandThread`                     |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.role`        | :class:`~discord.Role`                                                        |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.mentionable` | :class:`~discord.User` or :class:`~discord.Member`, or :class:`~discord.Role` |
    +------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`AppCommandOptionType.attachment`  | :class:`~discord.Attachment`                                                  |
    +------------------------------------------+-------------------------------------------------------------------------------+
    """

    def __init__(
        self,
        interaction: Interaction,
        resolved: ResolvedData,
        options: List[ApplicationCommandInteractionDataOption],
    ):
        completed = self._get_resolved_items(interaction, resolved)
        for option in options:
            opt_type = option['type']
            name = option['name']
            if opt_type in (3, 4, 5):  # string, integer, boolean
                value = option['value']  # type: ignore -- Key is there
                self.__dict__[name] = value
            elif opt_type == 10:  # number
                value = option['value']  # type: ignore -- Key is there
                if value is None:
                    self.__dict__[name] = float('nan')
                else:
                    self.__dict__[name] = float(value)
            elif opt_type in (6, 7, 8, 9, 11):
                # Remaining ones should be snowflake based ones with resolved data
                snowflake: str = option['value']  # type: ignore -- Key is there
                value = completed.get(snowflake)
                self.__dict__[name] = value

    @classmethod
    def _get_resolved_items(cls, interaction: Interaction, resolved: ResolvedData) -> Dict[str, Any]:
        completed: Dict[str, Any] = {}
        state = interaction._state
        members = resolved.get('members', {})
        guild_id = interaction.guild_id
        guild = (state._get_guild(guild_id) or Object(id=guild_id)) if guild_id is not None else None
        for (user_id, user_data) in resolved.get('users', {}).items():
            try:
                member_data = members[user_id]
            except KeyError:
                completed[user_id] = state.create_user(user_data)
            else:
                member_data['user'] = user_data
                # Guild ID can't be None in this case.
                # There's a type mismatch here that I don't actually care about
                member = Member(state=state, guild=guild, data=member_data)  # type: ignore
                completed[user_id] = member

        completed.update(
            {
                # The guild ID can't be None in this case.
                role_id: Role(guild=guild, state=state, data=role_data)  # type: ignore
                for role_id, role_data in resolved.get('roles', {}).items()
            }
        )

        for (channel_id, channel_data) in resolved.get('channels', {}).items():
            if channel_data['type'] in (10, 11, 12):
                # The guild ID can't be none in this case
                completed[channel_id] = AppCommandThread(state=state, data=channel_data, guild_id=guild_id)  # type: ignore
            else:
                # The guild ID can't be none in this case
                completed[channel_id] = AppCommandChannel(state=state, data=channel_data, guild_id=guild_id)  # type: ignore

        completed.update(
            {
                attachment_id: Attachment(data=attachment_data, state=state)
                for attachment_id, attachment_data in resolved.get('attachments', {}).items()
            }
        )

        guild = state._get_guild(guild_id)
        for (message_id, message_data) in resolved.get('messages', {}).items():
            channel_id = int(message_data['channel_id'])
            if guild is None:
                channel = PartialMessageable(state=state, id=channel_id)
            else:
                channel = guild.get_channel_or_thread(channel_id) or PartialMessageable(state=state, id=channel_id)

            # Type checker doesn't understand this due to failure to narrow
            completed[message_id] = Message(state=state, channel=channel, data=message_data)  # type: ignore

        return completed

    def __repr__(self) -> str:
        items = (f'{k}={v!r}' for k, v in self.__dict__.items())
        return '<{} {}>'.format(self.__class__.__name__, ' '.join(items))

    def __eq__(self, other: object) -> bool:
        if isinstance(self, Namespace) and isinstance(other, Namespace):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def _update_with_defaults(self, defaults: Iterable[Tuple[str, Any]]) -> None:
        for key, value in defaults:
            self.__dict__.setdefault(key, value)
