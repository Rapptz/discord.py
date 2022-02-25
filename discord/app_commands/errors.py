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

from typing import TYPE_CHECKING, List, Optional, Union
from ..errors import DiscordException

__all__ = (
    'CommandAlreadyRegistered',
    'CommandSignatureMismatch',
    'CommandNotFound',
)

if TYPE_CHECKING:
    from .commands import Command, Group


class CommandAlreadyRegistered(DiscordException):
    """An exception raised when a command is already registered.

    Attributes
    -----------
    name: :class:`str`
        The name of the command already registered.
    guild_id: Optional[:class:`int`]
        The guild ID this command was already registered at.
        If ``None`` then it was a global command.
    """

    def __init__(self, name: str, guild_id: Optional[int]):
        self.name = name
        self.guild_id = guild_id
        super().__init__(f'Command {name!r} already registered.')


class CommandNotFound(DiscordException):
    """An exception raised when an application command could not be found.

    Attributes
    ------------
    name: :class:`str`
        The name of the application command not found.
    parents: List[:class:`str`]
        A list of parent command names that were previously found
        prior to the application command not being found.
    """

    def __init__(self, name: str, parents: List[str]):
        self.name = name
        self.parents = parents
        super().__init__(f'Application command {name!r} not found')


class CommandSignatureMismatch(DiscordException):
    """An exception raised when an application command from Discord has a different signature
    from the one provided in the code. This happens because your command definition differs
    from the command definition you provided Discord. Either your code is out of date or the
    data from Discord is out of sync.

    Attributes
    ------------
    command: Union[:class:`~discord.app_commands.Command`, :class:`~discord.app_commands.Group`]
        The command that had the signature mismatch.
    """

    def __init__(self, command: Union[Command, Group]):
        self.command: Union[Command, Group] = command
        msg = (
            f'The signature for command {command!r} is different from the one provided by Discord. '
            'This can happen because either your code is out of date or you have not synced the '
            'commands with Discord, causing the mismatch in data. It is recommended to sync the '
            'command tree to fix this issue.'
        )
        super().__init__(msg)
