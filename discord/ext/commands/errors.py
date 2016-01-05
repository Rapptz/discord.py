# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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
           'NoPrivateMessage', 'CheckFailure', 'CommandNotFound' ]

class CommandError(DiscordException):
    """The base exception type for all command related errors.

    This inherits from :exc:`discord.DiscordException`.

    This exception and exceptions derived from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`Bot`\, :func:`on_command_error`.
    """
    pass

class CommandNotFound(CommandError):
    """Exception raised when a command is attempted to be invoked
    but no command under that name is found.

    This is not raised for invalid subcommands, rather just the
    initial main command that is attempted to be invoked.
    """

class MissingRequiredArgument(CommandError):
    """Exception raised when parsing a command and a parameter
    that is required is not encountered.
    """
    pass

class BadArgument(CommandError):
    """Exception raised when a parsing or conversion failure is encountered
    on an argument to pass into a command.
    """
    pass

class NoPrivateMessage(CommandError):
    """Exception raised when an operation does not work in private message
    contexts.
    """
    pass

class CheckFailure(CommandError):
    """Exception raised when the predicates in :attr:`Command.checks` have failed."""
    pass
