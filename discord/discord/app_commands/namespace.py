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

from typing import TYPE_CHECKING, Any, Dict, Iterable, Iterator, List, NamedTuple, Tuple
from ..member import Member
from ..object import Object
from ..role import Role
from ..message import Message, Attachment
from ..channel import PartialMessageable
from ..enums import AppCommandOptionType
from .models import AppCommandChannel, AppCommandThread

if TYPE_CHECKING:
    from ..interactions import Interaction
    from ..types.interactions import ResolvedData, ApplicationCommandInteractionDataOption

__all__ = ('Namespace',)


class ResolveKey(NamedTuple):
    id: str
    # CommandOptionType does not use 0 or negative numbers so those can be safe for library
    # internal use, if necessary. Likewise, only 6, 7, 8, and 11 are actually in use.
    type: int

    @classmethod
    def any_with(cls, id: str) -> ResolveKey:
        return ResolveKey(id=id, type=-1)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ResolveKey):
            return NotImplemented
        if self.type == -1 or o.type == -1:
            return self.id == o.id
        return (self.id, self.type) == (o.id, o.type)

    def __hash__(self) -> int:
        # Most of the time an ID lookup is all that is necessary
        # In case of collision then we look up both the ID and the type.
        return hash(self.id)


class Namespace:
    """An object that holds the parameters being passed to a command in a mostly raw state.

    This class is deliberately simple and just holds the option name and resolved value as a simple
    key-pair mapping. These attributes can be accessed using dot notation. For example, an option
    with the name of ``example`` can be accessed using ``ns.example``. If an attribute is not found,
    then ``None`` is returned rather than an attribute error.

    .. warning::

        The key names come from the raw Discord data, which means that if a parameter was renamed then the
        renamed key is used instead of the function parameter name.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two namespaces are equal by checking if all attributes are equal.
        .. describe:: x != y

            Checks if two namespaces are not equal.
        .. describe:: x[key]

            Returns an attribute if it is found, otherwise raises
            a :exc:`KeyError`.
        .. describe:: key in x

            Checks if the attribute is in the namespace.
        .. describe:: iter(x)

           Returns an iterator of ``(name, value)`` pairs. This allows it
           to be, for example, constructed as a dict or a list of pairs.

    This namespace object converts resolved objects into their appropriate form depending on their
    type. Consult the table below for conversion information.

    +-------------------------------------------+-------------------------------------------------------------------------------+
    |                Option Type                |                                 Resolved Type                                 |
    +===========================================+===============================================================================+
    | :attr:`.AppCommandOptionType.string`      | :class:`str`                                                                  |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.integer`     | :class:`int`                                                                  |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.boolean`     | :class:`bool`                                                                 |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.number`      | :class:`float`                                                                |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.user`        | :class:`~discord.User` or :class:`~discord.Member`                            |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.channel`     | :class:`.AppCommandChannel` or :class:`.AppCommandThread`                     |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.role`        | :class:`~discord.Role`                                                        |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.mentionable` | :class:`~discord.User` or :class:`~discord.Member`, or :class:`~discord.Role` |
    +-------------------------------------------+-------------------------------------------------------------------------------+
    | :attr:`.AppCommandOptionType.attachment`  | :class:`~discord.Attachment`                                                  |
    +-------------------------------------------+-------------------------------------------------------------------------------+

    .. note::

        In autocomplete interactions, the namespace might not be validated or filled in. Discord does not
        send the resolved data as well, so this means that certain fields end up just as IDs rather than
        the resolved data. In these cases, a :class:`discord.Object` is returned instead.

        This is a Discord limitation.
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
            focused = option.get('focused', False)
            if opt_type in (3, 4, 5):  # string, integer, boolean
                value = option['value']  # type: ignore # Key is there
                self.__dict__[name] = value
            elif opt_type == 10:  # number
                value = option['value']  # type: ignore # Key is there
                # This condition is written this way because 0 can be a valid float
                if value is None or value == '':
                    self.__dict__[name] = float('nan')
                else:
                    if not focused:
                        self.__dict__[name] = float(value)
                    else:
                        # Autocomplete focused values tend to be garbage in
                        self.__dict__[name] = value
            elif opt_type in (6, 7, 8, 9, 11):
                # Remaining ones should be snowflake based ones with resolved data
                snowflake: str = option['value']  # type: ignore # Key is there
                if opt_type == 9:  # Mentionable
                    # Mentionable is User | Role, these do not cause any conflict
                    key = ResolveKey.any_with(snowflake)
                else:
                    # The remaining keys can conflict, for example, a role and a channel
                    # could end up with the same ID in very old guilds since they used to default
                    # to sharing the guild ID. Old general channels no longer exist, but some old
                    # servers will still have them so this needs to be handled.
                    key = ResolveKey(id=snowflake, type=opt_type)

                value = completed.get(key) or Object(id=int(snowflake))
                self.__dict__[name] = value

    @classmethod
    def _get_resolved_items(cls, interaction: Interaction, resolved: ResolvedData) -> Dict[ResolveKey, Any]:
        completed: Dict[ResolveKey, Any] = {}
        state = interaction._state
        members = resolved.get('members', {})
        guild_id = interaction.guild_id
        guild = state._get_or_create_unavailable_guild(guild_id) if guild_id is not None else None
        type = AppCommandOptionType.user.value
        for (user_id, user_data) in resolved.get('users', {}).items():
            try:
                member_data = members[user_id]
            except KeyError:
                completed[ResolveKey(id=user_id, type=type)] = state.create_user(user_data)
            else:
                member_data['user'] = user_data
                # Guild ID can't be None in this case.
                # There's a type mismatch here that I don't actually care about
                member = Member(state=state, guild=guild, data=member_data)  # type: ignore
                completed[ResolveKey(id=user_id, type=type)] = member

        type = AppCommandOptionType.role.value
        completed.update(
            {
                # The guild ID can't be None in this case.
                ResolveKey(id=role_id, type=type): Role(guild=guild, state=state, data=role_data)  # type: ignore
                for role_id, role_data in resolved.get('roles', {}).items()
            }
        )

        type = AppCommandOptionType.channel.value
        for (channel_id, channel_data) in resolved.get('channels', {}).items():
            key = ResolveKey(id=channel_id, type=type)
            if channel_data['type'] in (10, 11, 12):
                # The guild ID can't be none in this case
                completed[key] = AppCommandThread(state=state, data=channel_data, guild_id=guild_id)  # type: ignore
            else:
                # The guild ID can't be none in this case
                completed[key] = AppCommandChannel(state=state, data=channel_data, guild_id=guild_id)  # type: ignore

        type = AppCommandOptionType.attachment.value
        completed.update(
            {
                ResolveKey(id=attachment_id, type=type): Attachment(data=attachment_data, state=state)
                for attachment_id, attachment_data in resolved.get('attachments', {}).items()
            }
        )

        guild = state._get_guild(guild_id)
        for (message_id, message_data) in resolved.get('messages', {}).items():
            channel_id = int(message_data['channel_id'])
            if guild is None:
                channel = PartialMessageable(state=state, guild_id=guild_id, id=channel_id)
            else:
                channel = guild.get_channel_or_thread(channel_id) or PartialMessageable(
                    state=state, guild_id=guild_id, id=channel_id
                )

            # Type checker doesn't understand this due to failure to narrow
            message = Message(state=state, channel=channel, data=message_data)  # type: ignore
            key = ResolveKey(id=message_id, type=-1)
            completed[key] = message

        return completed

    def __repr__(self) -> str:
        items = (f'{k}={v!r}' for k, v in self.__dict__.items())
        return '<{} {}>'.format(self.__class__.__name__, ' '.join(items))

    def __eq__(self, other: object) -> bool:
        if isinstance(self, Namespace) and isinstance(other, Namespace):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __contains__(self, key: str) -> Any:
        return key in self.__dict__

    def __getattr__(self, attr: str) -> Any:
        return None

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield from self.__dict__.items()

    def _update_with_defaults(self, defaults: Iterable[Tuple[str, Any]]) -> None:
        for key, value in defaults:
            self.__dict__.setdefault(key, value)
