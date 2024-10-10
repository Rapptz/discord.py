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
    Any,
    Coroutine,
    Dict,
    Hashable,
    Union,
    Callable,
    TypeVar,
    Optional,
    TYPE_CHECKING,
)

import time

from .commands import check
from .errors import (
    NoPrivateMessage,
    MissingRole,
    MissingAnyRole,
    MissingPermissions,
    BotMissingPermissions,
    CommandOnCooldown,
)

from ..user import User
from ..permissions import Permissions
from ..utils import get as utils_get, MISSING, maybe_coroutine

T = TypeVar('T')

if TYPE_CHECKING:
    from typing_extensions import Self
    from ..interactions import Interaction

    CooldownFunction = Union[
        Callable[[Interaction[Any]], Coroutine[Any, Any, T]],
        Callable[[Interaction[Any]], T],
    ]

__all__ = (
    'has_role',
    'has_any_role',
    'has_permissions',
    'bot_has_permissions',
    'cooldown',
    'dynamic_cooldown',
)


class Cooldown:
    """Represents a cooldown for a command.

    .. versionadded:: 2.0

    Attributes
    -----------
    rate: :class:`float`
        The total number of tokens available per :attr:`per` seconds.
    per: :class:`float`
        The length of the cooldown period in seconds.
    """

    __slots__ = ('rate', 'per', '_window', '_tokens', '_last')

    def __init__(self, rate: float, per: float) -> None:
        self.rate: int = int(rate)
        self.per: float = float(per)
        self._window: float = 0.0
        self._tokens: int = self.rate
        self._last: float = 0.0

    def get_tokens(self, current: Optional[float] = None) -> int:
        """Returns the number of available tokens before rate limiting is applied.

        Parameters
        ------------
        current: Optional[:class:`float`]
            The time in seconds since Unix epoch to calculate tokens at.
            If not supplied then :func:`time.time()` is used.

        Returns
        --------
        :class:`int`
            The number of tokens available before the cooldown is to be applied.
        """
        if not current:
            current = time.time()

        # the calculated tokens should be non-negative
        tokens = max(self._tokens, 0)

        if current > self._window + self.per:
            tokens = self.rate
        return tokens

    def get_retry_after(self, current: Optional[float] = None) -> float:
        """Returns the time in seconds until the cooldown will be reset.

        Parameters
        -------------
        current: Optional[:class:`float`]
            The current time in seconds since Unix epoch.
            If not supplied, then :func:`time.time()` is used.

        Returns
        -------
        :class:`float`
            The number of seconds to wait before this cooldown will be reset.
        """
        current = current or time.time()
        tokens = self.get_tokens(current)

        if tokens == 0:
            return self.per - (current - self._window)

        return 0.0

    def update_rate_limit(self, current: Optional[float] = None, *, tokens: int = 1) -> Optional[float]:
        """Updates the cooldown rate limit.

        Parameters
        -------------
        current: Optional[:class:`float`]
            The time in seconds since Unix epoch to update the rate limit at.
            If not supplied, then :func:`time.time()` is used.
        tokens: :class:`int`
            The amount of tokens to deduct from the rate limit.

        Returns
        -------
        Optional[:class:`float`]
            The retry-after time in seconds if rate limited.
        """
        current = current or time.time()
        self._last = current

        self._tokens = self.get_tokens(current)

        # first token used means that we start a new rate limit window
        if self._tokens == self.rate:
            self._window = current

        # decrement tokens by specified number
        self._tokens -= tokens

        # check if we are rate limited and return retry-after
        if self._tokens < 0:
            return self.per - (current - self._window)

    def reset(self) -> None:
        """Reset the cooldown to its initial state."""
        self._tokens = self.rate
        self._last = 0.0

    def copy(self) -> Self:
        """Creates a copy of this cooldown.

        Returns
        --------
        :class:`Cooldown`
            A new instance of this cooldown.
        """
        return self.__class__(self.rate, self.per)

    def __repr__(self) -> str:
        return f'<Cooldown rate: {self.rate} per: {self.per} window: {self._window} tokens: {self._tokens}>'


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
    the permissions listed. This relies on :attr:`discord.Interaction.app_permissions`.

    This check raises a special exception, :exc:`~discord.app_commands.BotMissingPermissions`
    that is inherited from :exc:`~discord.app_commands.CheckFailure`.

    .. versionadded:: 2.0
    """

    invalid = set(perms) - set(Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        permissions = interaction.app_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return check(predicate)


def _create_cooldown_decorator(
    key: CooldownFunction[Hashable], factory: CooldownFunction[Optional[Cooldown]]
) -> Callable[[T], T]:

    mapping: Dict[Any, Cooldown] = {}

    async def get_bucket(
        interaction: Interaction,
        *,
        mapping: Dict[Any, Cooldown] = mapping,
        key: CooldownFunction[Hashable] = key,
        factory: CooldownFunction[Optional[Cooldown]] = factory,
    ) -> Optional[Cooldown]:
        current = interaction.created_at.timestamp()
        dead_keys = [k for k, v in mapping.items() if current > v._last + v.per]
        for k in dead_keys:
            del mapping[k]

        k = await maybe_coroutine(key, interaction)
        if k not in mapping:
            bucket: Optional[Cooldown] = await maybe_coroutine(factory, interaction)
            if bucket is not None:
                mapping[k] = bucket
        else:
            bucket = mapping[k]

        return bucket

    async def predicate(interaction: Interaction) -> bool:
        bucket = await get_bucket(interaction)
        if bucket is None:
            return True

        retry_after = bucket.update_rate_limit(interaction.created_at.timestamp())
        if retry_after is None:
            return True

        raise CommandOnCooldown(bucket, retry_after)

    return check(predicate)


def cooldown(
    rate: float,
    per: float,
    *,
    key: Optional[CooldownFunction[Hashable]] = MISSING,
) -> Callable[[T], T]:
    """A decorator that adds a cooldown to a command.

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns are based off
    of the ``key`` function provided. If a ``key`` is not provided
    then it defaults to a user-level cooldown. The ``key`` function
    must take a single parameter, the :class:`discord.Interaction` and
    return a value that is used as a key to the internal cooldown mapping.

    The ``key`` function can optionally be a coroutine.

    If a cooldown is triggered, then :exc:`~discord.app_commands.CommandOnCooldown` is
    raised to the error handlers.

    Examples
    ---------

    Setting a one per 5 seconds per member cooldown on a command:

    .. code-block:: python3

        @tree.command()
        @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
        async def test(interaction: discord.Interaction):
            await interaction.response.send_message('Hello')

        @test.error
        async def on_test_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(str(error), ephemeral=True)

    Parameters
    ------------
    rate: :class:`int`
        The number of times a command can be used before triggering a cooldown.
    per: :class:`float`
        The amount of seconds to wait for a cooldown when it's been triggered.
    key: Optional[Callable[[:class:`discord.Interaction`], :class:`collections.abc.Hashable`]]
        A function that returns a key to the mapping denoting the type of cooldown.
        Can optionally be a coroutine. If not given then defaults to a user-level
        cooldown. If ``None`` is passed then it is interpreted as a "global" cooldown.
    """

    if key is MISSING:
        key_func = lambda interaction: interaction.user.id
    elif key is None:
        key_func = lambda i: None
    else:
        key_func = key

    factory = lambda interaction: Cooldown(rate, per)

    return _create_cooldown_decorator(key_func, factory)


def dynamic_cooldown(
    factory: CooldownFunction[Optional[Cooldown]],
    *,
    key: Optional[CooldownFunction[Hashable]] = MISSING,
) -> Callable[[T], T]:
    """A decorator that adds a dynamic cooldown to a command.

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns are based off
    of the ``key`` function provided. If a ``key`` is not provided
    then it defaults to a user-level cooldown. The ``key`` function
    must take a single parameter, the :class:`discord.Interaction` and
    return a value that is used as a key to the internal cooldown mapping.

    If a ``factory`` function is given, it must be a function that
    accepts a single parameter of type :class:`discord.Interaction` and must
    return a :class:`~discord.app_commands.Cooldown` or ``None``.
    If ``None`` is returned then that cooldown is effectively bypassed.

    Both ``key`` and ``factory`` can optionally be coroutines.

    If a cooldown is triggered, then :exc:`~discord.app_commands.CommandOnCooldown` is
    raised to the error handlers.

    Examples
    ---------

    Setting a cooldown for everyone but the owner.

    .. code-block:: python3

        def cooldown_for_everyone_but_me(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
            if interaction.user.id == 80088516616269824:
                return None
            return app_commands.Cooldown(1, 10.0)

        @tree.command()
        @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
        async def test(interaction: discord.Interaction):
            await interaction.response.send_message('Hello')

        @test.error
        async def on_test_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(str(error), ephemeral=True)

    Parameters
    ------------
    factory: Optional[Callable[[:class:`discord.Interaction`], Optional[:class:`~discord.app_commands.Cooldown`]]]
        A function that takes an interaction and returns a cooldown that will apply to that interaction
        or ``None`` if the interaction should not have a cooldown.
    key: Optional[Callable[[:class:`discord.Interaction`], :class:`collections.abc.Hashable`]]
        A function that returns a key to the mapping denoting the type of cooldown.
        Can optionally be a coroutine. If not given then defaults to a user-level
        cooldown. If ``None`` is passed then it is interpreted as a "global" cooldown.
    """

    if key is MISSING:
        key_func = lambda interaction: interaction.user.id
    elif key is None:
        key_func = lambda i: None
    else:
        key_func = key

    return _create_cooldown_decorator(key_func, factory)
