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

from typing import (
    Union,
    Callable,
    TypeVar,
    TYPE_CHECKING,
)

from .commands import check
from .errors import (
    NoPrivateMessage,
    MissingRole,
    MissingAnyRole,
    MissingPermissions,
    BotMissingPermissions,
)

from ..user import User
from ..permissions import Permissions
from ..utils import get as utils_get

T = TypeVar('T')

if TYPE_CHECKING:
    from ..interactions import Interaction

__all__ = (
    'has_role',
    'has_any_role',
    'has_permissions',
    'bot_has_permissions',
)


def has_role(item: Union[int, str], /) -> Callable[[T], T]:
    """A :func:`~discord.app_commands.check` that is added that checks if the member invoking the
    command has the role specified via the name or ID specified.

    If a string is specified, you must give the exact name of the role, including
    caps and spelling.

    If an integer is specified, you must give the exact snowflake ID of the role.

    This check raises one of two special exceptions, :exc:`~discord.app_commands.MissingRole`
    if the user is missing a role, or :exc:`~discord.app_commands.NoPrivateMessage` if
    it is used in a private message. Both inherit from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    .. note::

        This is different from the permission system that Discord provides for application
        commands. This is done entirely locally in the program rather than being handled
        by Discord.

    Parameters
    -----------
    item: Union[:class:`int`, :class:`str`]
        The name or ID of the role to check.
    """

    def predicate(interaction: Interaction) -> bool:
        if isinstance(interaction.user, User):
            raise NoPrivateMessage()

        if isinstance(item, int):
            role = interaction.user.get_role(item)
        else:
            role = utils_get(interaction.user.roles, name=item)

        if role is None:
            raise MissingRole(item)
        return True

    return check(predicate)


def has_any_role(*items: Union[int, str]) -> Callable[[T], T]:
    r"""A :func:`~discord.app_commands.check` that is added that checks if the member
    invoking the command has **any** of the roles specified. This means that if they have
    one out of the three roles specified, then this check will return ``True``.

    Similar to :func:`has_role`\, the names or IDs passed in must be exact.

    This check raises one of two special exceptions, :exc:`~discord.app_commands.MissingAnyRole`
    if the user is missing all roles, or :exc:`~discord.app_commands.NoPrivateMessage` if
    it is used in a private message. Both inherit from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    .. note::

        This is different from the permission system that Discord provides for application
        commands. This is done entirely locally in the program rather than being handled
        by Discord.

    Parameters
    -----------
    items: List[Union[:class:`str`, :class:`int`]]
        An argument list of names or IDs to check that the member has roles wise.

    Example
    --------

    .. code-block:: python3

        @tree.command()
        @app_commands.checks.has_any_role('Library Devs', 'Moderators', 492212595072434186)
        async def cool(interaction: discord.Interaction):
            await interaction.response.send_message('You are cool indeed')
    """

    def predicate(interaction: Interaction) -> bool:
        if isinstance(interaction.user, User):
            raise NoPrivateMessage()

        if any(
            interaction.user.get_role(item) is not None
            if isinstance(item, int)
            else utils_get(interaction.user.roles, name=item) is not None
            for item in items
        ):
            return True
        raise MissingAnyRole(list(items))

    return check(predicate)


def has_permissions(**perms: bool) -> Callable[[T], T]:
    r"""A :func:`~discord.app_commands.check` that is added that checks if the member
    has all of the permissions necessary.

    Note that this check operates on the permissions given by
    :attr:`discord.Interaction.permissions`.

    The permissions passed in must be exactly like the properties shown under
    :class:`discord.Permissions`.

    This check raises a special exception, :exc:`~discord.app_commands.MissingPermissions`
    that is inherited from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0

    .. note::

        This is different from the permission system that Discord provides for application
        commands. This is done entirely locally in the program rather than being handled
        by Discord.

    Parameters
    ------------
    \*\*perms: :class:`bool`
        Keyword arguments denoting the permissions to check for.

    Example
    ---------

    .. code-block:: python3

        @tree.command()
        @app_commands.checks.has_permissions(manage_messages=True)
        async def test(interaction: discord.Interaction):
            await interaction.response.send_message('You can manage messages.')

    """

    invalid = perms.keys() - Permissions.VALID_FLAGS.keys()
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        permissions = interaction.permissions

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(missing)

    return check(predicate)


def bot_has_permissions(**perms: bool) -> Callable[[T], T]:
    """Similar to :func:`has_permissions` except checks if the bot itself has
    the permissions listed.

    This check raises a special exception, :exc:`~discord.app_commands.BotMissingPermissions`
    that is inherited from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0
    """

    invalid = set(perms) - set(Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        guild = interaction.guild
        me = guild.me if guild is not None else interaction.client.user
        if interaction.channel is None:
            permissions = Permissions.none()
        else:
            permissions = interaction.channel.permissions_for(me)  # type: ignore

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return check(predicate)
