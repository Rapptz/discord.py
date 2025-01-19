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

from typing import Any, TYPE_CHECKING, List, Optional, Sequence, Union

from ..enums import AppCommandOptionType, AppCommandType, Locale
from ..errors import DiscordException, HTTPException, _flatten_error_dict, MissingApplicationID as MissingApplicationID
from ..utils import _human_join

__all__ = (
    'AppCommandError',
    'CommandInvokeError',
    'TransformerError',
    'TranslationError',
    'CheckFailure',
    'CommandAlreadyRegistered',
    'CommandSignatureMismatch',
    'CommandNotFound',
    'CommandLimitReached',
    'NoPrivateMessage',
    'MissingRole',
    'MissingAnyRole',
    'MissingPermissions',
    'BotMissingPermissions',
    'CommandOnCooldown',
    'MissingApplicationID',
    'CommandSyncFailure',
)

if TYPE_CHECKING:
    from .commands import Command, Group, ContextMenu, Parameter
    from .transformers import Transformer
    from .translator import TranslationContextTypes, locale_str
    from ..types.snowflake import Snowflake, SnowflakeList
    from .checks import Cooldown

    CommandTypes = Union[Command[Any, ..., Any], Group, ContextMenu]


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

    If an exception occurs while converting that does not subclass
    :exc:`AppCommandError` then the exception is wrapped into this exception.
    The original exception can be retrieved using the ``__cause__`` attribute.
    Otherwise if the exception derives from :exc:`AppCommandError` then it will
    be propagated as-is.

    .. versionadded:: 2.0

    Attributes
    -----------
    value: Any
        The value that failed to convert.
    type: :class:`~discord.AppCommandOptionType`
        The type of argument that failed to convert.
    transformer: :class:`Transformer`
        The transformer that failed the conversion.
    """

    def __init__(self, value: Any, opt_type: AppCommandOptionType, transformer: Transformer):
        self.value: Any = value
        self.type: AppCommandOptionType = opt_type
        self.transformer: Transformer = transformer

        super().__init__(f'Failed to convert {value} to {transformer._error_display_name!s}')


class TranslationError(AppCommandError):
    """An exception raised when the library fails to translate a string.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    If an exception occurs while calling :meth:`Translator.translate` that does
    not subclass this then the exception is wrapped into this exception.
    The original exception can be retrieved using the ``__cause__`` attribute.
    Otherwise it will be propagated as-is.

    .. versionadded:: 2.0

    Attributes
    -----------
    string: Optional[Union[:class:`str`, :class:`locale_str`]]
        The string that caused the error, if any.
    locale: Optional[:class:`~discord.Locale`]
        The locale that caused the error, if any.
    context: :class:`~discord.app_commands.TranslationContext`
        The context of the translation that triggered the error.
    """

    def __init__(
        self,
        *msg: str,
        string: Optional[Union[str, locale_str]] = None,
        locale: Optional[Locale] = None,
        context: TranslationContextTypes,
    ) -> None:
        self.string: Optional[Union[str, locale_str]] = string
        self.locale: Optional[Locale] = locale
        self.context: TranslationContextTypes = context

        if msg:
            super().__init__(*msg)
        else:
            ctx = context.location.name.replace('_', ' ')
            fmt = f'Failed to translate {self.string!r} in a {ctx}'
            if self.locale is not None:
                fmt = f'{fmt} in the {self.locale.value} locale'

            super().__init__(fmt)


class CheckFailure(AppCommandError):
    """An exception raised when check predicates in a command have failed.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. versionadded:: 2.0
    """

    pass


class NoPrivateMessage(CheckFailure):
    """An exception raised when a command does not work in a direct message.

    This inherits from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or 'This command cannot be used in direct messages.')


class MissingRole(CheckFailure):
    """An exception raised when the command invoker lacks a role to run a command.

    This inherits from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~discord.app_commands.checks.has_role`.
    """

    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f'Role {missing_role!r} is required to run this command.'
        super().__init__(message)


class MissingAnyRole(CheckFailure):
    """An exception raised when the command invoker lacks any of the roles
    specified to run a command.

    This inherits from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the invoker is missing.
        These are the parameters passed to :func:`~discord.app_commands.checks.has_any_role`.
    """

    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles

        fmt = _human_join([f"'{role}'" for role in missing_roles])
        message = f'You are missing at least one of the required roles: {fmt}'
        super().__init__(message)


class MissingPermissions(CheckFailure):
    """An exception raised when the command invoker lacks permissions to run a
    command.

    This inherits from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """

    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]
        fmt = _human_join(missing, final='and')
        message = f'You are missing {fmt} permission(s) to run this command.'
        super().__init__(message, *args)


class BotMissingPermissions(CheckFailure):
    """An exception raised when the bot's member lacks permissions to run a
    command.

    This inherits from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """

    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_permissions]
        fmt = _human_join(missing, final='and')
        message = f'Bot requires {fmt} permission(s) to run this command.'
        super().__init__(message, *args)


class CommandOnCooldown(CheckFailure):
    """An exception raised when the command being invoked is on cooldown.

    This inherits from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    Attributes
    -----------
    cooldown: :class:`~discord.app_commands.Cooldown`
        The cooldown that was triggered.
    retry_after: :class:`float`
        The amount of seconds to wait before you can retry again.
    """

    def __init__(self, cooldown: Cooldown, retry_after: float) -> None:
        self.cooldown: Cooldown = cooldown
        self.retry_after: float = retry_after
        super().__init__(f'You are on cooldown. Try again in {retry_after:.2f}s')


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


class CommandLimitReached(AppCommandError):
    """An exception raised when the maximum number of application commands was reached
    either globally or in a guild.

    This inherits from :exc:`~discord.app_commands.AppCommandError`.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`~discord.AppCommandType`
        The type of command that reached the limit.
    guild_id: Optional[:class:`int`]
        The guild ID that reached the limit or ``None`` if it was global.
    limit: :class:`int`
        The limit that was hit.
    """

    def __init__(self, guild_id: Optional[int], limit: int, type: AppCommandType = AppCommandType.chat_input):
        self.guild_id: Optional[int] = guild_id
        self.limit: int = limit
        self.type: AppCommandType = type

        lookup = {
            AppCommandType.chat_input: 'slash commands',
            AppCommandType.message: 'message context menu commands',
            AppCommandType.user: 'user context menu commands',
        }
        desc = lookup.get(type, 'application commands')
        ns = 'globally' if self.guild_id is None else f'for guild ID {self.guild_id}'
        super().__init__(f'maximum number of {desc} exceeded {limit} {ns}')


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


def _get_command_error(
    index: str,
    inner: Any,
    objects: Sequence[Union[Parameter, CommandTypes]],
    messages: List[str],
    indent: int = 0,
) -> None:
    # Import these here to avoid circular imports
    from .commands import Command, Group, ContextMenu

    indentation = ' ' * indent

    # Top level errors are:
    # <number>: { <key>: <error> }
    # The dicts could be nested, e.g.
    # <number>: { <key>: { <second>: <error> } }
    # Luckily, this is already handled by the flatten_error_dict utility
    if not index.isdigit():
        errors = _flatten_error_dict(inner, index)
        messages.extend(f'In {k}: {v}' for k, v in errors.items())
        return

    idx = int(index)
    try:
        obj = objects[idx]
    except IndexError:
        dedent_one_level = ' ' * (indent - 2)
        errors = _flatten_error_dict(inner, index)
        messages.extend(f'{dedent_one_level}In {k}: {v}' for k, v in errors.items())
        return

    children: Sequence[Union[Parameter, CommandTypes]] = []
    if isinstance(obj, Command):
        messages.append(f'{indentation}In command {obj.qualified_name!r} defined in function {obj.callback.__qualname__!r}')
        children = obj.parameters
    elif isinstance(obj, Group):
        messages.append(f'{indentation}In group {obj.qualified_name!r} defined in module {obj.module!r}')
        children = obj.commands
    elif isinstance(obj, ContextMenu):
        messages.append(
            f'{indentation}In context menu {obj.qualified_name!r} defined in function {obj.callback.__qualname__!r}'
        )
    else:
        messages.append(f'{indentation}In parameter {obj.name!r}')

    for key, remaining in inner.items():
        # Special case the 'options' key since they have well defined meanings
        if key == 'options':
            for index, d in remaining.items():
                _get_command_error(index, d, children, messages, indent=indent + 2)
        elif key == '_errors':
            errors = [x.get('message', '') for x in remaining]

            messages.extend(f'{indentation}  {message}' for message in errors)
        else:
            if isinstance(remaining, dict):
                try:
                    inner_errors = remaining['_errors']
                except KeyError:
                    errors = _flatten_error_dict(remaining, key=key)
                else:
                    errors = {key: ' '.join(x.get('message', '') for x in inner_errors)}

            if isinstance(errors, dict):
                messages.extend(f'{indentation}  {k}: {v}' for k, v in errors.items())


class CommandSyncFailure(AppCommandError, HTTPException):
    """An exception raised when :meth:`CommandTree.sync` failed.

    This provides syncing failures in a slightly more readable format.

    This inherits from :exc:`~discord.app_commands.AppCommandError`
    and :exc:`~discord.HTTPException`.

    .. versionadded:: 2.0
    """

    def __init__(self, child: HTTPException, commands: List[CommandTypes]) -> None:
        # Consume the child exception and make it seem as if we are that exception
        self.__dict__.update(child.__dict__)

        messages = [f'Failed to upload commands to Discord (HTTP status {self.status}, error code {self.code})']

        if self._errors:
            # Handle case where the errors dict has no actual chain such as APPLICATION_COMMAND_TOO_LARGE
            if len(self._errors) == 1 and '_errors' in self._errors:
                errors = self._errors['_errors']
                if len(errors) == 1:
                    extra = errors[0].get('message')
                    if extra:
                        messages[0] += f': {extra}'
                else:
                    messages.extend(f'Error {e.get("code", "")}: {e.get("message", "")}' for e in errors)
            else:
                for index, inner in self._errors.items():
                    _get_command_error(index, inner, commands, messages)

        # Equivalent to super().__init__(...) but skips other constructors
        self.args = ('\n'.join(messages),)
