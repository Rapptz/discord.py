"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

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

from typing import Callable

from ..permissions import Permissions
from .core import ApplicationCommand

__all__ = (
    "default_permissions",
    "guild_only",
)


def default_permissions(**perms: bool) -> Callable:
    """A decorator that limits the usage of a slash command to members with certain
    permissions.

    The permissions passed in must be exactly like the properties shown under
    :class:`.discord.Permissions`.

    .. note::
        These permissions can be updated by server administrators per-guild. As such, these are only "defaults", as the
        name suggests. If you want to make sure that a user **always** has the specified permissions regardless, you
        should use an internal check such as :func:`~.ext.commands.has_permissions`.

    Parameters
    ------------
    perms
        An argument list of permissions to check for.

    Example
    ---------

    .. code-block:: python3

        from discord import default_permissions

        @bot.slash_command()
        @default_permissions(manage_messages=True)
        async def test(ctx):
            await ctx.respond('You can manage messages.')

    """

    invalid = set(perms) - set(Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def inner(command: Callable):
        if isinstance(command, ApplicationCommand):
            if command.parent is not None:
                raise RuntimeError("Permission restrictions can only be set on top-level commands")
            command.default_member_permissions = Permissions(**perms)
        else:
            command.__default_member_permissions__ = Permissions(**perms)
        return command

    return inner


def guild_only() -> Callable:
    """A decorator that limits the usage of a slash command to guild contexts.
    The command won't be able to be used in private message channels.

    Example
    ---------

    .. code-block:: python3

        from discord import guild_only

        @bot.slash_command()
        @guild_only()
        async def test(ctx):
            await ctx.respond('You\'re in a guild.')

    """

    def inner(command: Callable):
        if isinstance(command, ApplicationCommand):
            command.guild_only = True
        else:
            command.__guild_only__ = True
        return command

    return inner
