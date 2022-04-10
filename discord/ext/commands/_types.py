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


from typing import Any, Awaitable, Callable, Coroutine, TYPE_CHECKING, TypeVar, Union, Tuple


T = TypeVar('T')

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    from .bot import Bot
    from .context import Context
    from .cog import Cog
    from .errors import CommandError

    _Bot = Bot
    P = ParamSpec('P')
    MaybeAwaitableFunc = Callable[P, 'MaybeAwaitable[T]']
else:
    _Bot = 'Bot'

    P = TypeVar('P')
    MaybeAwaitableFunc = Tuple[P, T]

Coro = Coroutine[Any, Any, T]
CoroFunc = Callable[..., Coro[Any]]
MaybeCoro = Union[T, Coro[T]]
MaybeAwaitable = Union[T, Awaitable[T]]

Check = Union[Callable[["Cog", "ContextT"], MaybeCoro[bool]], Callable[["ContextT"], MaybeCoro[bool]]]
Hook = Union[Callable[["Cog", "ContextT"], Coro[Any]], Callable[["ContextT"], Coro[Any]]]
Error = Union[Callable[["Cog", "ContextT", "CommandError"], Coro[Any]], Callable[["ContextT", "CommandError"], Coro[Any]]]

ContextT = TypeVar('ContextT', bound='Context[Any]')
BotT = TypeVar('BotT', bound='Bot', covariant=True)
ErrorT = TypeVar('ErrorT', bound='Error[Context[Any]]')
HookT = TypeVar('HookT', bound='Hook[Context[Any]]')


# This is merely a tag type to avoid circular import issues.
# Yes, this is a terrible solution but ultimately it is the only solution.
class _BaseCommand:
    __slots__ = ()
