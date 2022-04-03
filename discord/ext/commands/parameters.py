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

import inspect
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Literal, OrderedDict, Type, Union

from ...utils import MISSING, maybe_coroutine
from . import converter
from .errors import MissingRequiredArgument

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...channel import TextChannel
    from ...guild import Guild
    from ...member import Member
    from ...user import User
    from .context import Context

__all__ = (
    "Parameter",
    "parameter",
    "param",
    "Author",
    "CurrentChannel",
    "CurrentGuild",
)


ParamKinds = Union[
    Literal[inspect.Parameter.POSITIONAL_ONLY],
    Literal[inspect.Parameter.POSITIONAL_OR_KEYWORD],
    Literal[inspect.Parameter.VAR_POSITIONAL],
    Literal[inspect.Parameter.KEYWORD_ONLY],
    Literal[inspect.Parameter.VAR_KEYWORD],
]

empty: Any = inspect.Parameter.empty


class Parameter(inspect.Parameter):
    def __init__(
        self,
        name: str,
        kind: ParamKinds,
        default: Any = empty,
        annotation: Any = empty,
        displayed_default: str = empty,
    ) -> None:
        super().__init__(name=name, kind=kind, default=default, annotation=annotation)
        self._name = name
        self._kind = kind
        self._default = default
        self._annotation = annotation
        self._displayed_default = displayed_default

    def replace(
        self,
        *,
        name: str = MISSING,  # MISSING here cause empty is valid
        kind: ParamKinds = MISSING,
        default: Any = MISSING,
        annotation: Any = MISSING,
        displayed_default: Any = MISSING,
    ) -> Self:
        if name is MISSING:
            name = self._name
        if kind is MISSING:
            kind = self._kind  # type: ignore  # this assignment is actually safe
        if default is MISSING:
            default = self._default
        if annotation is MISSING:
            annotation = self._annotation
        if displayed_default is MISSING:
            displayed_default = self._displayed_default

        return self.__class__(
            name=name, kind=kind, default=default, annotation=annotation, displayed_default=displayed_default
        )

    if not TYPE_CHECKING:  # this is to prevent anything breaking if inspect internals change
        name = property(attrgetter("_name"), lambda self, name: setattr(self, "_name", name), doc="The parameter's name.")
        kind = property(attrgetter("_kind"), lambda self, kind: setattr(self, "_kind", kind), doc="The parameter's kind.")
        default = property(
            attrgetter("_default"),
            lambda self, default: setattr(self, "_default", default),
            doc="The parameter's default value.",
        )
        annotation = property(
            attrgetter("_annotation"),
            lambda self, annotation: setattr(self, "_annotation", annotation),
            doc="The parameter's annotation.",
        )

    @property
    def required(self) -> bool:
        return self.default is empty

    @property
    def converter(self) -> Type[Any]:
        """The converter that should be used for this parameter.

        Note
        ----
        This is the same as :attr:`annotation` if it's non-empty otherwise it's the type of :attr:`default` or :class:`str`
        if the parameter has no default.
        """
        if self.annotation is empty:
            return type(self.default) if self.default not in (empty, None) else str

        return self.annotation

    @property
    def displayed_default(self) -> str | None:
        """The displayed default in :class:`Command.signature`."""
        if self._displayed_default is not empty:
            return self._displayed_default

        return None if self.required else str(self.default)

    async def get_default(self, ctx: Context) -> Any:
        """|coro|

        Gets this parameter's default value.
        """
        # pre-condition: required is False
        if callable(self.default):
            return await maybe_coroutine(self.default, ctx)  # type: ignore
        return self.default


def parameter(
    *,
    converter: Any = empty,
    default: Any = empty,
    displayed_default: str = empty,
) -> Any:
    r"""parameter(*, converter=..., default=..., displayed_default=...)

    A way to assign custom metadata for a :class:`Command`\'s parameter.

    Examples
    --------

    A custom converter, whilst annotating a parameter with a custom converter works at runtime, type checkers don't like it
    cause they can't understand what's going on.

    .. code-block:: python3

        class SomeType:
            foo: int

        class MyVeryCoolConverter(commands.Converter[SomeType]):
            ...  # implementation left as an exercise for the reader

        @bot.command()
        async def bar(ctx, cool_value: MyVeryCoolConverter):
            cool_value.foo  # type checker warns MyVeryCoolConverter has no value foo (uh-oh)

    However, fear not we can use :func:`parameter` to tell type checkers what's going on.

    .. code-block:: python3

        @bot.command()
        async def bar(ctx, cool_value: SomeType = commands.parameter(converter=MyVeryCoolConverter)):
            cool_value.foo  # no error (hurray)

    A custom default can be used to have late binding behaviour

    .. code-block:: python3

        @bot.command()
        async def wave(to: discord.User = commands.parameter(default=lambda ctx: ctx.author)):
            await ctx.send(f'Hello {to.mention} :wave:')

    Because this is such a common use-case, the library provides :obj:`.Author`, :obj:`.CurrentChannel` and
    :obj:`.CurrentGuild`, armed with this we can simplify ``wave`` to:

    .. code-block:: python3

        @bot.command()
        async def wave(to: discord.User = commands.Author):
            await ctx.send(f'Hello {to.mention} :wave:')

    :obj:`Author` and co also have other benefits like having the displayed default being filled.

    .. versionadded:: 2.0.0

    Parameters
    ----------
    converter: Any
        The converter to use for this parameter, this replaces the annotation at runtime which is transparent to type checkers.
    default: Any
        The default value for the parameter, if this is a :term:`callable` or a |coroutine_link|_ it is called with a
        positional :class:`Context` argument.
    displayed_default: :class:`str`
        The displayed default in :attr:`Command.signature`.
    """
    return Parameter(
        name="empty",
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        annotation=converter,
        default=default,
        displayed_default=displayed_default,
    )


param = parameter
"""param(*, converter=..., default=..., displayed_default=...)

An alias for :func:`parameter`.
"""

# some handy defaults
Author: Union[Member, User] = parameter(
    default=attrgetter("author"),
    displayed_default="<you>",
    converter=Union[converter.MemberConverter, converter.UserConverter],
)
"""A default :class:`Parameter` which returns the :attr:`~.Context.author` for this context."""

CurrentChannel: TextChannel = parameter(
    default=attrgetter("channel"), displayed_default="<this channel>", converter=converter.TextChannelConverter
)
"""A default :class:`Parameter` which returns the :attr:`~.Context.channel` for this context."""


def default_guild(ctx: Context) -> Guild:
    if ctx.guild is not None:
        return ctx.guild
    raise MissingRequiredArgument(ctx.current_parameter)  # type: ignore  # this is never going to be None


CurrentGuild: Guild = parameter(default=default_guild, displayed_default="<this server>", converter=converter.GuildConverter)
"""A default :class:`Parameter` which returns the :attr:`~.Context.guild` for this context."""


class Signature(inspect.Signature):
    _parameter_cls = Parameter
    parameters: OrderedDict[str, Parameter]
