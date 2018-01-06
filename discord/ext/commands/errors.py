# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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

from discord.errors import DiscordException


__all__ = [ 'CommandError', 'MissingRequiredArgument', 'BadArgument',
           'NoPrivateMessage', 'CheckFailure', 'CommandNotFound',
           'DisabledCommand', 'CommandInvokeError', 'TooManyArguments',
           'UserInputError', 'CommandOnCooldown', 'NotOwner',
           'MissingPermissions', 'BotMissingPermissions']

class CommandError(DiscordException):
    """The base exception type for all command related errors.

    This inherits from :exc:`discord.DiscordException`.

    This exception and exceptions derived from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.Bot`\, :func:`on_command_error`.
    """
    def __init__(self, message=None, *args):
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)

class UserInputError(CommandError):
    """The base exception type for errors that involve errors
    regarding user input.

    This inherits from :exc:`.CommandError`.
    """
    pass

class CommandNotFound(CommandError):
    """Exception raised when a command is attempted to be invoked
    but no command under that name is found.

    This is not raised for invalid subcommands, rather just the
    initial main command that is attempted to be invoked.
    """
    pass

class MissingRequiredArgument(UserInputError):
    """Exception raised when parsing a command and a parameter
    that is required is not encountered.

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The argument that is missing.
    """
    def __init__(self, param):
        self.param = param
        super().__init__('{0.name} is a required argument that is missing.'.format(param))

class TooManyArguments(UserInputError):
    """Exception raised when the command was passed too many arguments and its
    :attr:`.Command.ignore_extra` attribute was not set to ``True``.
    """
    pass

class BadArgument(UserInputError):
    """Exception raised when a parsing or conversion failure is encountered
    on an argument to pass into a command.
    """
    pass

class CheckFailure(CommandError):
    """Exception raised when the predicates in :attr:`.Command.checks` have failed."""
    pass

class NoPrivateMessage(CheckFailure):
    """Exception raised when an operation does not work in private message
    contexts.
    """
    pass

class NotOwner(CheckFailure):
    """Exception raised when the message author is not the owner of the bot."""
    pass

class DisabledCommand(CommandError):
    """Exception raised when the command being invoked is disabled."""
    pass

class CommandInvokeError(CommandError):
    """Exception raised when the command being invoked raised an exception.

    Attributes
    -----------
    original
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """
    def __init__(self, e):
        self.original = e
        super().__init__('Command raised an exception: {0.__class__.__name__}: {0}'.format(e))

class CommandOnCooldown(CommandError):
    """Exception raised when the command being invoked is on cooldown.

    Attributes
    -----------
    cooldown: Cooldown
        A class with attributes ``rate``, ``per``, and ``type`` similar to
        the :func:`.cooldown` decorator.
    retry_after: :class:`float`
        The amount of seconds to wait before you can retry again.
    """
    def __init__(self, cooldown, retry_after):
        self.cooldown = cooldown
        self.retry_after = retry_after
        super().__init__('You are on cooldown. Try again in {:.2f}s'.format(retry_after))

class MissingPermissions(CheckFailure):
    """Exception raised when the command invoker lacks permissions to run
    command.

    Attributes
    -----------
    missing_perms: :class:`list`
        The required permissions that are missing.
    """
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt =  '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'You are missing {} permission(s) to run command.'.format(fmt)
        super().__init__(message, *args)

class BotMissingPermissions(CheckFailure):
    """Exception raised when the bot lacks permissions to run command.

    Attributes
    -----------
    missing_perms: :class:`list`
        The required permissions that are missing.
    """
    def __init__(self, missing_perms, *args):
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt =  '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'Bot requires {} permission(s) to run command.'.format(fmt)
        super().__init__(message, *args)
