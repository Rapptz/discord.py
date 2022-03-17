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

from typing import Any, TYPE_CHECKING, List, Optional, Type, Union


from ..enums import AppCommandOptionType, AppCommandType
from ..errors import DiscordException

__all__ = (
    'AppCommandError',
    'CommandInvokeError',
    'TransformerError',
    'CommandAlreadyRegistered',
    'CommandSignatureMismatch',
    'CommandNotFound',
)

if TYPE_CHECKING:
    from .commands import Command, Group, ContextMenu
    from .transformers import Transformer


class AppCommandError(DiscordException):
    """The base exception type for all application command related errors.

    This inherits from :exc:`discord.DiscordException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into various error handlers
    in this order:

    - :meth:`Command.error <discord.app_commands.Command.error>`
    - :meth:`Group.on_error <discord.app_commands.Group.on_error>`
    - :meth:`CommandTree.on_error <discord.app_commands.CommandTree.on_error>`

    .. versionadded:: 2.0
    """

    pass


class CommandInvokeError(AppCommandError):
    """An exception raised when the command being invoked raised an exception.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. versionadded:: 2.0

    Attributes
    -----------
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    command: Union[:class:`Command`, :class:`ContextMenu`]
        The command that failed.
    """

    def __init__(self, command: Union[Command[Any, ..., Any], ContextMenu], e: Exception) -> None:
        self.original: Exception = e
        self.command: Union[Command[Any, ..., Any], ContextMenu] = command
        super().__init__(f'Command {command.name!r} raised an exception: {e.__class__.__name__}: {e}')


class TransformerError(AppCommandError):
    """An exception raised when a :class:`Transformer` or type annotation fails to
    convert to its target type.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. note::

        If the transformer raises a custom :exc:`AppCommandError` then it will
        be propagated rather than wrapped into this exception.

    .. versionadded:: 2.0

    Attributes
    -----------
    value: Any
        The value that failed to convert.
    type: :class:`~discord.AppCommandOptionType`
        The type of argument that failed to convert.
    transformer: Type[:class:`Transformer`]
        The transformer that failed the conversion.
    """

    def __init__(self, value: Any, opt_type: AppCommandOptionType, transformer: Type[Transformer]):
        self.value: Any = value
        self.type: AppCommandOptionType = opt_type
        self.transformer: Type[Transformer] = transformer

        try:
            result_type = transformer.transform.__annotations__['return']
        except KeyError:
            name = transformer.__name__
            if name.endswith('Transformer'):
                result_type = name[:-11]
            else:
                result_type = name
        else:
            if isinstance(result_type, type):
                result_type = result_type.__name__

        super().__init__(f'Failed to convert {value} to {result_type!s}')


class CommandAlreadyRegistered(AppCommandError):
    """An exception raised when a command is already registered.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The name of the command already registered.
    guild_id: Optional[:class:`int`]
        The guild ID this command was already registered at.
        If ``None`` then it was a global command.
    """

    def __init__(self, name: str, guild_id: Optional[int]):
        self.name: str = name
        self.guild_id: Optional[int] = guild_id
        super().__init__(f'Command {name!r} already registered.')


class CommandNotFound(AppCommandError):
    """An exception raised when an application command could not be found.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. versionadded:: 2.0

    Attributes
    ------------
    name: :class:`str`
        The name of the application command not found.
    parents: List[:class:`str`]
        A list of parent command names that were previously found
        prior to the application command not being found.
    type: :class:`~discord.AppCommandType`
        The type of command that was not found.
    """

    def __init__(self, name: str, parents: List[str], type: AppCommandType = AppCommandType.chat_input):
        self.name: str = name
        self.parents: List[str] = parents
        self.type: AppCommandType = type
        super().__init__(f'Application command {name!r} not found')


class CommandSignatureMismatch(AppCommandError):
    """An exception raised when an application command from Discord has a different signature
    from the one provided in the code. This happens because your command definition differs
    from the command definition you provided Discord. Either your code is out of date or the
    data from Discord is out of sync.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. versionadded:: 2.0

    Attributes
    ------------
    command: Union[:class:`~.app_commands.Command`, :class:`~.app_commands.ContextMenu`, :class:`~.app_commands.Group`]
        The command that had the signature mismatch.
    """

    def __init__(self, command: Union[Command[Any, ..., Any], ContextMenu, Group]):
        self.command: Union[Command[Any, ..., Any], ContextMenu, Group] = command
        msg = (
            f'The signature for command {command.name!r} is different from the one provided by Discord. '
            'This can happen because either your code is out of date or you have not synced the '
            'commands with Discord, causing the mismatch in data. It is recommended to sync the '
            'command tree to fix this issue.'
        )
        super().__init__(msg)
