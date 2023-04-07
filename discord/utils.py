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

import array
import asyncio
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Coroutine,
    Dict,
    ForwardRef,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    Set,
    Sequence,
    SupportsIndex,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
    TYPE_CHECKING,
)
import collections
import unicodedata
from base64 import b64encode
from bisect import bisect_left
import datetime
import functools
from inspect import isawaitable as _isawaitable, signature as _signature
from operator import attrgetter
from urllib.parse import urlencode
import json
import logging
import os
import random
import re
import string
import sys
from threading import Timer
import types
import warnings
import logging

import yarl

try:
    import orjson  # type: ignore
except ModuleNotFoundError:
    HAS_ORJSON = False
else:
    HAS_ORJSON = True

from .enums import Locale, try_enum


__all__ = (
    'oauth_url',
    'snowflake_time',
    'time_snowflake',
    'find',
    'get',
    'sleep_until',
    'utcnow',
    'remove_markdown',
    'escape_markdown',
    'escape_mentions',
    'maybe_coroutine',
    'as_chunks',
    'format_dt',
    'set_target',
    'MISSING',
    'setup_logging',
)

DISCORD_EPOCH = 1420070400000

_log = logging.getLogger(__name__)


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __hash__(self):
        return 0

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()


class _cached_property:
    def __init__(self, function):
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value


if TYPE_CHECKING:
    from aiohttp import ClientSession
    from functools import cached_property as cached_property

    from typing_extensions import ParamSpec, Self, TypeGuard

    from .permissions import Permissions
    from .abc import Messageable, Snowflake
    from .invite import Invite
    from .message import Message
    from .template import Template
    from .commands import ApplicationCommand
    from .entitlements import Gift

    class _RequestLike(Protocol):
        headers: Mapping[str, Any]

    P = ParamSpec('P')

    MaybeAwaitableFunc = Callable[P, 'MaybeAwaitable[T]']

    _SnowflakeListBase = array.array[int]

else:
    cached_property = _cached_property
    _SnowflakeListBase = array.array


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
_Iter = Union[Iterable[T], AsyncIterable[T]]
Coro = Coroutine[Any, Any, T]
MaybeAwaitable = Union[T, Awaitable[T]]


class CachedSlotProperty(Generic[T, T_co]):
    def __init__(self, name: str, function: Callable[[T], T_co]) -> None:
        self.name = name
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    @overload
    def __get__(self, instance: None, owner: Type[T]) -> CachedSlotProperty[T, T_co]:
        ...

    @overload
    def __get__(self, instance: T, owner: Type[T]) -> T_co:
        ...

    def __get__(self, instance: Optional[T], owner: Type[T]) -> Any:
        if instance is None:
            return self

        try:
            return getattr(instance, self.name)
        except AttributeError:
            value = self.function(instance)
            setattr(instance, self.name, value)
            return value


class classproperty(Generic[T_co]):
    def __init__(self, fget: Callable[[Any], T_co]) -> None:
        self.fget = fget

    def __get__(self, instance: Optional[Any], owner: Type[Any]) -> T_co:
        return self.fget(owner)

    def __set__(self, instance: Optional[Any], value: Any) -> None:
        raise AttributeError('cannot set attribute')


def cached_slot_property(name: str) -> Callable[[Callable[[T], T_co]], CachedSlotProperty[T, T_co]]:
    def decorator(func: Callable[[T], T_co]) -> CachedSlotProperty[T, T_co]:
        return CachedSlotProperty(name, func)

    return decorator


class SequenceProxy(Sequence[T_co]):
    """A proxy of a sequence that only creates a copy when necessary."""

    def __init__(self, proxied: Collection[T_co], *, sorted: bool = False):
        self.__proxied: Collection[T_co] = proxied
        self.__sorted: bool = sorted

    @cached_property
    def __copied(self) -> List[T_co]:
        if self.__sorted:
            # The type checker thinks the variance is wrong, probably due to the comparison requirements
            self.__proxied = sorted(self.__proxied)  # type: ignore
        else:
            self.__proxied = list(self.__proxied)
        return self.__proxied

    def __repr__(self) -> str:
        return f"SequenceProxy({self.__proxied!r})"

    @overload
    def __getitem__(self, idx: SupportsIndex) -> T_co:
        ...

    @overload
    def __getitem__(self, idx: slice) -> List[T_co]:
        ...

    def __getitem__(self, idx: Union[SupportsIndex, slice]) -> Union[T_co, List[T_co]]:
        return self.__copied[idx]

    def __len__(self) -> int:
        return len(self.__proxied)

    def __contains__(self, item: Any) -> bool:
        return item in self.__copied

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.__copied)

    def __reversed__(self) -> Iterator[T_co]:
        return reversed(self.__copied)

    def index(self, value: Any, *args: Any, **kwargs: Any) -> int:
        return self.__copied.index(value, *args, **kwargs)

    def count(self, value: Any) -> int:
        return self.__copied.count(value)


@overload
def parse_time(timestamp: None) -> None:
    ...


@overload
def parse_time(timestamp: str) -> datetime.datetime:
    ...


@overload
def parse_time(timestamp: Optional[str]) -> Optional[datetime.datetime]:
    ...


def parse_time(timestamp: Optional[str]) -> Optional[datetime.datetime]:
    if timestamp:
        return datetime.datetime.fromisoformat(timestamp)
    return None


@overload
def parse_date(date: None) -> None:
    ...


@overload
def parse_date(date: str) -> datetime.date:
    ...


@overload
def parse_date(date: Optional[str]) -> Optional[datetime.date]:
    ...


def parse_date(date: Optional[str]) -> Optional[datetime.date]:
    if date:
        return parse_time(date).date()
    return None


@overload
def parse_timestamp(timestamp: None) -> None:
    ...


@overload
def parse_timestamp(timestamp: float) -> datetime.datetime:
    ...


@overload
def parse_timestamp(timestamp: Optional[float]) -> Optional[datetime.datetime]:
    ...


def parse_timestamp(timestamp: Optional[float]) -> Optional[datetime.datetime]:
    if timestamp:
        return datetime.datetime.fromtimestamp(timestamp / 1000.0, tz=datetime.timezone.utc)


def copy_doc(original: Callable[..., Any]) -> Callable[[T], T]:
    def decorator(overridden: T) -> T:
        overridden.__doc__ = original.__doc__
        overridden.__signature__ = _signature(original)  # type: ignore
        return overridden

    return decorator


def deprecated(instead: Optional[str] = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def actual_decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> T:
            warnings.simplefilter('always', DeprecationWarning)  # turn off filter
            if instead:
                fmt = "{0.__name__} is deprecated, use {1} instead."
            else:
                fmt = '{0.__name__} is deprecated.'

            warnings.warn(fmt.format(func, instead), stacklevel=3, category=DeprecationWarning)
            warnings.simplefilter('default', DeprecationWarning)  # reset filter
            return func(*args, **kwargs)

        return decorated

    return actual_decorator


def oauth_url(
    client_id: Union[int, str],
    *,
    permissions: Permissions = MISSING,
    guild: Snowflake = MISSING,
    redirect_uri: str = MISSING,
    scopes: Iterable[str] = MISSING,
    disable_guild_select: bool = False,
    state: str = MISSING,
) -> str:
    """A helper function that returns the OAuth2 URL for inviting a bot
    into guilds.

    .. versionchanged:: 2.0

        ``permissions``, ``guild``, ``redirect_uri``, ``scopes`` and ``state`` parameters
        are now keyword-only.

    Parameters
    -----------
    client_id: Union[:class:`int`, :class:`str`]
        The client ID for the bot.
    permissions: :class:`~discord.Permissions`
        The permissions you're requesting. If not given then you won't be requesting any
        permissions.
    guild: :class:`~discord.abc.Snowflake`
        The guild to pre-select in the authorization screen, if available.
    redirect_uri: :class:`str`
        An optional valid redirect URI.
    scopes: Iterable[:class:`str`]
        An optional valid list of scopes. Defaults to ``('bot', 'applications.commands')``.

        .. versionadded:: 1.7
    disable_guild_select: :class:`bool`
        Whether to disallow the user from changing the guild dropdown.

        .. versionadded:: 2.0
    state: :class:`str`
        The state to return after the authorization.

        .. versionadded:: 2.0

    Returns
    --------
    :class:`str`
        The OAuth2 URL for inviting the bot into guilds.
    """
    url = f'https://discord.com/oauth2/authorize?client_id={client_id}'
    url += '&scope=' + '+'.join(scopes or ('bot', 'applications.commands'))
    if permissions is not MISSING:
        url += f'&permissions={permissions.value}'
    if guild is not MISSING:
        url += f'&guild_id={guild.id}'
    if disable_guild_select:
        url += '&disable_guild_select=true'
    if redirect_uri is not MISSING:
        url += '&response_type=code&' + urlencode({'redirect_uri': redirect_uri})
    if state is not MISSING:
        url += f'&{urlencode({"state": state})}'
    return url


def snowflake_time(id: int, /) -> datetime.datetime:
    """Returns the creation time of the given snowflake.

    .. versionchanged:: 2.0
        The ``id`` parameter is now positional-only.

    Parameters
    -----------
    id: :class:`int`
        The snowflake ID.

    Returns
    --------
    :class:`datetime.datetime`
        An aware datetime in UTC representing the creation time of the snowflake.
    """
    timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def time_snowflake(dt: datetime.datetime, /, *, high: bool = False) -> int:
    """Returns a numeric snowflake pretending to be created at the given date.

    When using as the lower end of a range, use ``time_snowflake(dt, high=False) - 1``
    to be inclusive, ``high=True`` to be exclusive.

    When using as the higher end of a range, use ``time_snowflake(dt, high=True) + 1``
    to be inclusive, ``high=False`` to be exclusive.

    .. versionchanged:: 2.0
        The ``high`` parameter is now keyword-only and the ``dt`` parameter is now
        positional-only.

    Parameters
    -----------
    dt: :class:`datetime.datetime`
        A datetime object to convert to a snowflake.
        If naive, the timezone is assumed to be local time.
    high: :class:`bool`
        Whether or not to set the lower 22 bit to high or low.

    Returns
    --------
    :class:`int`
        The snowflake representing the time given.
    """
    discord_millis = int(dt.timestamp() * 1000 - DISCORD_EPOCH)
    return (discord_millis << 22) + (2**22 - 1 if high else 0)


def _find(predicate: Callable[[T], Any], iterable: Iterable[T], /) -> Optional[T]:
    return next((element for element in iterable if predicate(element)), None)


async def _afind(predicate: Callable[[T], Any], iterable: AsyncIterable[T], /) -> Optional[T]:
    async for element in iterable:
        if predicate(element):
            return element

    return None


@overload
def find(predicate: Callable[[T], Any], iterable: AsyncIterable[T], /) -> Coro[Optional[T]]:
    ...


@overload
def find(predicate: Callable[[T], Any], iterable: Iterable[T], /) -> Optional[T]:
    ...


def find(predicate: Callable[[T], Any], iterable: _Iter[T], /) -> Union[Optional[T], Coro[Optional[T]]]:
    r"""A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = discord.utils.find(lambda m: m.name == 'Mighty', channel.guild.members)

    would find the first :class:`~discord.Member` whose name is 'Mighty' and return it.
    If an entry is not found, then ``None`` is returned.

    This is different from :func:`py:filter` due to the fact it stops the moment it finds
    a valid entry.

    .. versionchanged:: 2.0

        Both parameters are now positional-only.

    .. versionchanged:: 2.0

        The ``iterable`` parameter supports :term:`asynchronous iterable`\s.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    iterable: Union[:class:`collections.abc.Iterable`, :class:`collections.abc.AsyncIterable`]
        The iterable to search through. Using a :class:`collections.abc.AsyncIterable`,
        makes this function return a :term:`coroutine`.
    """

    return (
        _afind(predicate, iterable)  # type: ignore
        if hasattr(iterable, '__aiter__')  # isinstance(iterable, collections.abc.AsyncIterable) is too slow
        else _find(predicate, iterable)  # type: ignore
    )


def _get(iterable: Iterable[T], /, **attrs: Any) -> Optional[T]:
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        return next((elem for elem in iterable if pred(elem) == v), None)

    converted = [(attrget(attr.replace('__', '.')), value) for attr, value in attrs.items()]
    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


async def _aget(iterable: AsyncIterable[T], /, **attrs: Any) -> Optional[T]:
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        async for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [(attrget(attr.replace('__', '.')), value) for attr, value in attrs.items()]

    async for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


@overload
def get(iterable: AsyncIterable[T], /, **attrs: Any) -> Coro[Optional[T]]:
    ...


@overload
def get(iterable: Iterable[T], /, **attrs: Any) -> Optional[T]:
    ...


def get(iterable: _Iter[T], /, **attrs: Any) -> Union[Optional[T], Coro[Optional[T]]]:
    r"""A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``. This is an alternative for
    :func:`~discord.utils.find`.

    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.

    If nothing is found that matches the attributes passed, then
    ``None`` is returned.

    .. versionchanged:: 2.0

        The ``iterable`` parameter is now positional-only.

    .. versionchanged:: 2.0

        The ``iterable`` parameter supports :term:`asynchronous iterable`\s.

    Examples
    ---------

    Basic usage:

    .. code-block:: python3

        member = discord.utils.get(message.guild.members, name='Foo')

    Multiple attribute matching:

    .. code-block:: python3

        channel = discord.utils.get(guild.voice_channels, name='Foo', bitrate=64000)

    Nested attribute matching:

    .. code-block:: python3

        channel = discord.utils.get(client.get_all_channels(), guild__name='Cool', name='general')

    Async iterables:

    .. code-block:: python3

        msg = await discord.utils.get(channel.history(), author__name='Dave')

    Parameters
    -----------
    iterable: Union[:class:`collections.abc.Iterable`, :class:`collections.abc.AsyncIterable`]
        The iterable to search through. Using a :class:`collections.abc.AsyncIterable`,
        makes this function return a :term:`coroutine`.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """

    return (
        _aget(iterable, **attrs)  # type: ignore
        if hasattr(iterable, '__aiter__')  # isinstance(iterable, collections.abc.AsyncIterable) is too slow
        else _get(iterable, **attrs)  # type: ignore
    )


def _unique(iterable: Iterable[T]) -> List[T]:
    return [x for x in dict.fromkeys(iterable)]


def _get_as_snowflake(data: Any, key: str) -> Optional[int]:
    try:
        value = data[key]
    except KeyError:
        return None
    else:
        return value and int(value)


def _ocast(value: Any, type: Any):
    if value is MISSING:
        return MISSING
    return type(value)


def _get_mime_type_for_image(data: bytes, with_video: bool = False, fallback: bool = False) -> str:
    if data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        return 'image/png'
    elif data[0:3] == b'\xff\xd8\xff' or data[6:10] in (b'JFIF', b'Exif'):
        return 'image/jpeg'
    elif data.startswith((b'\x47\x49\x46\x38\x37\x61', b'\x47\x49\x46\x38\x39\x61')):
        return 'image/gif'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'
    elif data.startswith(b'\x66\x74\x79\x70\x69\x73\x6F\x6D') and with_video:
        return 'video/mp4'
    else:
        if fallback:
            return 'application/octet-stream'
        raise ValueError('Unsupported image type given')


def _get_extension_for_mime_type(mime_type: str) -> str:
    if mime_type == 'image/png':
        return 'png'
    elif mime_type == 'image/jpeg':
        return 'jpg'
    elif mime_type == 'image/gif':
        return 'gif'
    elif mime_type == 'video/mp4':
        return 'mp4'
    else:
        return 'webp'


def _bytes_to_base64_data(data: bytes) -> str:
    fmt = 'data:{mime};base64,{data}'
    mime = _get_mime_type_for_image(data, fallback=True)
    b64 = b64encode(data).decode('ascii')
    return fmt.format(mime=mime, data=b64)


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(parent + '.')


def _handle_metadata(obj):
    try:
        return dict(obj)
    except Exception:
        raise TypeError(f'Type {obj.__class__.__name__} is not JSON serializable')


if HAS_ORJSON:

    def _to_json(obj: Any) -> str:
        return orjson.dumps(obj, default=_handle_metadata).decode('utf-8')

    _from_json = orjson.loads  # type: ignore

else:

    def _to_json(obj: Any) -> str:
        return json.dumps(obj, separators=(',', ':'), ensure_ascii=True, default=_handle_metadata)

    _from_json = json.loads


def _parse_ratelimit_header(request: Any, *, use_clock: bool = False) -> float:
    reset_after: Optional[str] = request.headers.get('X-Ratelimit-Reset-After')
    if use_clock or not reset_after:
        utc = datetime.timezone.utc
        now = datetime.datetime.now(utc)
        reset = datetime.datetime.fromtimestamp(float(request.headers['X-Ratelimit-Reset']), utc)
        return (reset - now).total_seconds()
    else:
        return float(reset_after)


async def maybe_coroutine(f: MaybeAwaitableFunc[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    r"""|coro|

    A helper function that will await the result of a function if it's a coroutine
    or return the result if it's not.

    This is useful for functions that may or may not be coroutines.

    .. versionadded:: 2.0

    Parameters
    -----------
    f: Callable[..., Any]
        The function or coroutine to call.
    \*args
        The arguments to pass to the function.
    \*\*kwargs
        The keyword arguments to pass to the function.

    Returns
    --------
    Any
        The result of the function or coroutine.
    """

    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    else:
        return value  # type: ignore


async def async_all(
    gen: Iterable[Union[T, Awaitable[T]]],
    *,
    check: Callable[[Union[T, Awaitable[T]]], TypeGuard[Awaitable[T]]] = _isawaitable,
) -> bool:
    for elem in gen:
        if check(elem):
            elem = await elem
        if not elem:
            return False
    return True


async def sane_wait_for(futures: Iterable[Awaitable[T]], *, timeout: Optional[float]) -> Set[asyncio.Task[T]]:
    ensured = [asyncio.ensure_future(fut) for fut in futures]
    done, pending = await asyncio.wait(ensured, timeout=timeout, return_when=asyncio.ALL_COMPLETED)

    if len(pending) != 0:
        raise asyncio.TimeoutError()

    return done


def get_slots(cls: Type[Any]) -> Iterator[str]:
    for mro in reversed(cls.__mro__):
        try:
            yield from mro.__slots__  # type: ignore
        except AttributeError:
            continue


def compute_timedelta(dt: datetime.datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.astimezone()
    now = datetime.datetime.now(datetime.timezone.utc)
    return max((dt - now).total_seconds(), 0)


@overload
async def sleep_until(when: datetime.datetime, result: T) -> T:
    ...


@overload
async def sleep_until(when: datetime.datetime) -> None:
    ...


async def sleep_until(when: datetime.datetime, result: Optional[T] = None) -> Optional[T]:
    """|coro|

    Sleep until a specified time.

    If the time supplied is in the past this function will yield instantly.

    .. versionadded:: 1.3

    Parameters
    -----------
    when: :class:`datetime.datetime`
        The timestamp in which to sleep until. If the datetime is naive then
        it is assumed to be local time.
    result: Any
        If provided is returned to the caller when the coroutine completes.
    """
    delta = compute_timedelta(when)
    return await asyncio.sleep(delta, result)


def utcnow() -> datetime.datetime:
    """A helper function to return an aware UTC datetime representing the current time.

    This should be preferred to :meth:`datetime.datetime.utcnow` since it is an aware
    datetime, compared to the naive datetime in the standard library.

    .. versionadded:: 2.0

    Returns
    --------
    :class:`datetime.datetime`
        The current aware datetime in UTC.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def valid_icon_size(size: int) -> bool:
    """Icons must be power of 2 within [16, 4096]."""
    ADDITIONAL_SIZES = (20, 22, 24, 28, 40, 44, 48, 56, 60, 80, 96, 100, 160, 240, 300, 320, 480, 600, 640, 1280, 1536, 3072)
    return (not size & (size - 1) and 4096 >= size >= 16) or size in ADDITIONAL_SIZES


class SnowflakeList(_SnowflakeListBase):
    """Internal data storage class to efficiently store a list of snowflakes.

    This should have the following characteristics:

    - Low memory usage
    - O(n) iteration (obviously)
    - O(n log n) initial creation if data is unsorted
    - O(log n) search and indexing
    - O(n) insertion
    """

    __slots__ = ()

    if TYPE_CHECKING:

        def __init__(self, data: Iterable[int], *, is_sorted: bool = False):
            ...

    def __new__(cls, data: Iterable[int], *, is_sorted: bool = False) -> Self:
        return array.array.__new__(cls, 'Q', data if is_sorted else sorted(data))  # type: ignore

    def add(self, element: int) -> None:
        i = bisect_left(self, element)
        self.insert(i, element)

    def get(self, element: int) -> Optional[int]:
        i = bisect_left(self, element)
        return self[i] if i != len(self) and self[i] == element else None

    def has(self, element: int) -> bool:
        i = bisect_left(self, element)
        return i != len(self) and self[i] == element


_IS_ASCII = re.compile(r'^[\x00-\x7f]+$')


def _string_width(string: str, *, _IS_ASCII=_IS_ASCII) -> int:
    """Returns string's width."""
    match = _IS_ASCII.match(string)
    if match:
        return match.endpos

    UNICODE_WIDE_CHAR_TYPE = 'WFA'
    func = unicodedata.east_asian_width
    return sum(2 if func(char) in UNICODE_WIDE_CHAR_TYPE else 1 for char in string)


class ResolvedInvite(NamedTuple):
    code: str
    event: Optional[int]


def resolve_invite(invite: Union[Invite, str]) -> ResolvedInvite:
    """Resolves an invite from a :class:`~discord.Invite`, URL or code.

    .. versionchanged:: 2.0
        Now returns a :class:`.ResolvedInvite` instead of a
        :class:`str`.

    Parameters
    -----------
    invite: Union[:class:`~discord.Invite`, :class:`str`]
        The invite.

    Returns
    --------
    :class:`.ResolvedInvite`
        A data class containing the invite code and the event ID.
    """
    from .invite import Invite  # circular import

    if isinstance(invite, Invite):
        return ResolvedInvite(invite.code, invite.scheduled_event_id)
    else:
        rx = r'(?:https?\:\/\/)?discord(?:\.gg|(?:app)?\.com\/invite)\/[^/]+'
        m = re.match(rx, invite)

        if m:
            url = yarl.URL(invite)
            code = url.parts[-1]
            event_id = url.query.get('event')

            return ResolvedInvite(code, int(event_id) if event_id else None)
    return ResolvedInvite(invite, None)


def resolve_template(code: Union[Template, str]) -> str:
    """
    Resolves a template code from a :class:`~discord.Template`, URL or code.

    .. versionadded:: 1.4

    Parameters
    -----------
    code: Union[:class:`~discord.Template`, :class:`str`]
        The code.

    Returns
    --------
    :class:`str`
        The template code.
    """
    from .template import Template  # circular import

    if isinstance(code, Template):
        return code.code
    else:
        rx = r'(?:https?\:\/\/)?discord(?:\.new|(?:app)?\.com\/template)\/(.+)'
        m = re.match(rx, code)
        if m:
            return m.group(1)
    return code


def resolve_gift(code: Union[Gift, str]) -> str:
    """
    Resolves a gift code from a :class:`~discord.Gift`, URL or code.

    .. versionadded:: 2.0

    Parameters
    -----------
    code: Union[:class:`~discord.Gift`, :class:`str`]
        The code.

    Returns
    --------
    :class:`str`
        The gift code.
    """
    from .entitlements import Gift  # circular import

    if isinstance(code, Gift):
        return code.code
    else:
        rx = r'(?:https?\:\/\/)?(?:discord(?:app)?\.com\/(?:gifts|billing\/promotions)|promos\.discord\.gg|discord.gift)\/(.+)'
        m = re.match(rx, code)
        if m:
            return m.group(1)
    return code


_MARKDOWN_ESCAPE_SUBREGEX = '|'.join(r'\{0}(?=([\s\S]*((?<!\{0})\{0})))'.format(c) for c in ('*', '`', '_', '~', '|'))

_MARKDOWN_ESCAPE_COMMON = r'^>(?:>>)?\s|\[.+\]\(.+\)'

_MARKDOWN_ESCAPE_REGEX = re.compile(fr'(?P<markdown>{_MARKDOWN_ESCAPE_SUBREGEX}|{_MARKDOWN_ESCAPE_COMMON})', re.MULTILINE)

_URL_REGEX = r'(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])'

_MARKDOWN_STOCK_REGEX = fr'(?P<markdown>[_\\~|\*`]|{_MARKDOWN_ESCAPE_COMMON})'


def remove_markdown(text: str, *, ignore_links: bool = True) -> str:
    """A helper function that removes markdown characters.

    .. versionadded:: 1.7

    .. note::
            This function is not markdown aware and may remove meaning from the original text. For example,
            if the input contains ``10 * 5`` then it will be converted into ``10  5``.

    Parameters
    -----------
    text: :class:`str`
        The text to remove markdown from.
    ignore_links: :class:`bool`
        Whether to leave links alone when removing markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. Defaults to ``True``.

    Returns
    --------
    :class:`str`
        The text with the markdown special characters removed.
    """

    def replacement(match):
        groupdict = match.groupdict()
        return groupdict.get('url', '')

    regex = _MARKDOWN_STOCK_REGEX
    if ignore_links:
        regex = f'(?:{_URL_REGEX}|{regex})'
    return re.sub(regex, replacement, text, 0, re.MULTILINE)


def escape_markdown(text: str, *, as_needed: bool = False, ignore_links: bool = True) -> str:
    r"""A helper function that escapes Discord's markdown.

    Parameters
    -----------
    text: :class:`str`
        The text to escape markdown from.
    as_needed: :class:`bool`
        Whether to escape the markdown characters as needed. This
        means that it does not escape extraneous characters if it's
        not necessary, e.g. ``**hello**`` is escaped into ``\*\*hello**``
        instead of ``\*\*hello\*\*``. Note however that this can open
        you up to some clever syntax abuse. Defaults to ``False``.
    ignore_links: :class:`bool`
        Whether to leave links alone when escaping markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. This option is not supported with ``as_needed``.
        Defaults to ``True``.

    Returns
    --------
    :class:`str`
        The text with the markdown special characters escaped with a slash.
    """

    if not as_needed:

        def replacement(match):
            groupdict = match.groupdict()
            is_url = groupdict.get('url')
            if is_url:
                return is_url
            return '\\' + groupdict['markdown']

        regex = _MARKDOWN_STOCK_REGEX
        if ignore_links:
            regex = f'(?:{_URL_REGEX}|{regex})'
        return re.sub(regex, replacement, text, 0, re.MULTILINE)
    else:
        text = re.sub(r'\\', r'\\\\', text)
        return _MARKDOWN_ESCAPE_REGEX.sub(r'\\\1', text)


def escape_mentions(text: str) -> str:
    """A helper function that escapes everyone, here, role, and user mentions.

    .. note::

        This does not include channel mentions.

    .. note::

        For more granular control over what mentions should be escaped
        within messages, refer to the :class:`~discord.AllowedMentions`
        class.

    Parameters
    -----------
    text: :class:`str`
        The text to escape mentions from.

    Returns
    --------
    :class:`str`
        The text with the mentions removed.
    """
    return re.sub(r'@(everyone|here|[!&]?[0-9]{17,20})', '@\u200b\\1', text)


def _chunk(iterator: Iterable[T], max_size: int) -> Iterator[List[T]]:
    ret = []
    n = 0
    for item in iterator:
        ret.append(item)
        n += 1
        if n == max_size:
            yield ret
            ret = []
            n = 0
    if ret:
        yield ret


async def _achunk(iterator: AsyncIterable[T], max_size: int) -> AsyncIterator[List[T]]:
    ret = []
    n = 0
    async for item in iterator:
        ret.append(item)
        n += 1
        if n == max_size:
            yield ret
            ret = []
            n = 0
    if ret:
        yield ret


@overload
def as_chunks(iterator: AsyncIterable[T], max_size: int) -> AsyncIterator[List[T]]:
    ...


@overload
def as_chunks(iterator: Iterable[T], max_size: int) -> Iterator[List[T]]:
    ...


def as_chunks(iterator: _Iter[T], max_size: int) -> _Iter[List[T]]:
    """A helper function that collects an iterator into chunks of a given size.

    .. versionadded:: 2.0

    Parameters
    ----------
    iterator: Union[:class:`collections.abc.Iterable`, :class:`collections.abc.AsyncIterable`]
        The iterator to chunk, can be sync or async.
    max_size: :class:`int`
        The maximum chunk size.


    .. warning::

        The last chunk collected may not be as large as ``max_size``.

    Returns
    --------
    Union[:class:`Iterator`, :class:`AsyncIterator`]
        A new iterator which yields chunks of a given size.
    """
    if max_size <= 0:
        raise ValueError('Chunk sizes must be greater than 0.')

    if isinstance(iterator, AsyncIterable):
        return _achunk(iterator, max_size)
    return _chunk(iterator, max_size)


PY_310 = sys.version_info >= (3, 10)


def flatten_literal_params(parameters: Iterable[Any]) -> Tuple[Any, ...]:
    params = []
    literal_cls = type(Literal[0])
    for p in parameters:
        if isinstance(p, literal_cls):
            params.extend(p.__args__)
        else:
            params.append(p)
    return tuple(params)


def normalise_optional_params(parameters: Iterable[Any]) -> Tuple[Any, ...]:
    none_cls = type(None)
    return tuple(p for p in parameters if p is not none_cls) + (none_cls,)


def evaluate_annotation(
    tp: Any,
    globals: Dict[str, Any],
    locals: Dict[str, Any],
    cache: Dict[str, Any],
    *,
    implicit_str: bool = True,
) -> Any:
    if isinstance(tp, ForwardRef):
        tp = tp.__forward_arg__
        # ForwardRefs always evaluate their internals
        implicit_str = True

    if implicit_str and isinstance(tp, str):
        if tp in cache:
            return cache[tp]
        evaluated = evaluate_annotation(eval(tp, globals, locals), globals, locals, cache)
        cache[tp] = evaluated
        return evaluated

    if hasattr(tp, '__metadata__'):
        # Annotated[X, Y] can access Y via __metadata__
        metadata = tp.__metadata__[0]
        return evaluate_annotation(metadata, globals, locals, cache)

    if hasattr(tp, '__args__'):
        implicit_str = True
        is_literal = False
        args = tp.__args__
        if not hasattr(tp, '__origin__'):
            if PY_310 and tp.__class__ is types.UnionType:  # type: ignore
                converted = Union[args]  # type: ignore
                return evaluate_annotation(converted, globals, locals, cache)

            return tp
        if tp.__origin__ is Union:
            try:
                if args.index(type(None)) != len(args) - 1:
                    args = normalise_optional_params(tp.__args__)
            except ValueError:
                pass
        if tp.__origin__ is Literal:
            if not PY_310:
                args = flatten_literal_params(tp.__args__)
            implicit_str = False
            is_literal = True

        evaluated_args = tuple(evaluate_annotation(arg, globals, locals, cache, implicit_str=implicit_str) for arg in args)

        if is_literal and not all(isinstance(x, (str, int, bool, type(None))) for x in evaluated_args):
            raise TypeError('Literal arguments must be of type str, int, bool, or NoneType.')

        try:
            return tp.copy_with(evaluated_args)
        except AttributeError:
            return tp.__origin__[evaluated_args]

    return tp


def resolve_annotation(
    annotation: Any,
    globalns: Dict[str, Any],
    localns: Optional[Dict[str, Any]],
    cache: Optional[Dict[str, Any]],
) -> Any:
    if annotation is None:
        return type(None)
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)

    locals = globalns if localns is None else localns
    if cache is None:
        cache = {}
    return evaluate_annotation(annotation, globalns, locals, cache)


def is_inside_class(func: Callable[..., Any]) -> bool:
    # For methods defined in a class, the qualname has a dotted path
    # denoting which class it belongs to. So, e.g. for A.foo the qualname
    # would be A.foo while a global foo() would just be foo.
    #
    # Unfortunately, for nested functions this breaks. So inside an outer
    # function named outer, those two would end up having a qualname with
    # outer.<locals>.A.foo and outer.<locals>.foo

    if func.__qualname__ == func.__name__:
        return False
    (remaining, _, _) = func.__qualname__.rpartition('.')
    return not remaining.endswith('<locals>')


TimestampStyle = Literal['f', 'F', 'd', 'D', 't', 'T', 'R']


def format_dt(dt: datetime.datetime, /, style: Optional[TimestampStyle] = None) -> str:
    """A helper function to format a :class:`datetime.datetime` for presentation within Discord.

    This allows for a locale-independent way of presenting data using Discord specific Markdown.

    +-------------+----------------------------+-----------------+
    |    Style    |       Example Output       |   Description   |
    +=============+============================+=================+
    | t           | 22:57                      | Short Time      |
    +-------------+----------------------------+-----------------+
    | T           | 22:57:58                   | Long Time       |
    +-------------+----------------------------+-----------------+
    | d           | 17/05/2016                 | Short Date      |
    +-------------+----------------------------+-----------------+
    | D           | 17 May 2016                | Long Date       |
    +-------------+----------------------------+-----------------+
    | f (default) | 17 May 2016 22:57          | Short Date Time |
    +-------------+----------------------------+-----------------+
    | F           | Tuesday, 17 May 2016 22:57 | Long Date Time  |
    +-------------+----------------------------+-----------------+
    | R           | 5 years ago                | Relative Time   |
    +-------------+----------------------------+-----------------+

    Note that the exact output depends on the user's locale setting in the client. The example output
    presented is using the ``en-GB`` locale.

    .. versionadded:: 2.0

    Parameters
    -----------
    dt: :class:`datetime.datetime`
        The datetime to format.
    style: :class:`str`
        The style to format the datetime with.

    Returns
    --------
    :class:`str`
        The formatted string.
    """
    if style is None:
        return f'<t:{int(dt.timestamp())}>'
    return f'<t:{int(dt.timestamp())}:{style}>'


def set_target(
    items: Iterable[ApplicationCommand],
    *,
    channel: Optional[Messageable] = MISSING,
    message: Optional[Message] = MISSING,
    user: Optional[Snowflake] = MISSING,
) -> None:
    """A helper function to set the target for a list of items.

    This is used to set the target for a list of application commands.

    Suppresses all AttributeErrors so you can pass multiple types of commands and
    not worry about which elements support which parameter.

    Parameters
    -----------
    items: Iterable[:class:`.abc.ApplicationCommand`]
        A list of items to set the target for.
    channel: Optional[:class:`.abc.Messageable`]
        The channel to target.
    message: Optional[:class:`.Message`]
        The message to target.
    user: Optional[:class:`~discord.abc.Snowflake`]
        The user to target.
    """
    attrs = {}
    if channel is not MISSING:
        attrs['target_channel'] = channel
    if message is not MISSING:
        attrs['target_message'] = message
    if user is not MISSING:
        attrs['target_user'] = user

    for item in items:
        for k, v in attrs.items():
            try:
                setattr(item, k, v)
            except AttributeError:
                pass


def _generate_session_id() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def _generate_nonce() -> str:
    return str(time_snowflake(utcnow()))


def _parse_localizations(data: Any, key: str) -> tuple[Any, dict]:
    values = data.get(key)
    values = values if isinstance(values, dict) else {'default': values}
    string = values['default']
    localizations = {
        try_enum(Locale, k): v for k, v in (values.get('localizations', data.get(f'{key}_localizations')) or {}).items()
    }
    return string, localizations


class ExpiringString(collections.UserString):
    def __init__(self, data: str, timeout: int) -> None:
        super().__init__(data)
        self._timer: Timer = Timer(timeout, self._destruct)
        self._timer.start()

    def _update(self, data: str, timeout: int) -> None:
        try:
            self._timer.cancel()
        except:
            pass
        self.data = data
        self._timer: Timer = Timer(timeout, self._destruct)
        self._timer.start()

    def _destruct(self) -> None:
        self.data = ''

    def destroy(self) -> None:
        self._destruct()
        self._timer.cancel()


async def _get_info(session: ClientSession) -> Tuple[Dict[str, Any], str]:
    for _ in range(3):
        try:
            async with session.post('https://cordapi.dolfi.es/api/v2/properties/web', timeout=5) as resp:
                json = await resp.json()
                return json['properties'], json['encoded']
        except Exception:
            continue

    _log.warning('Info API down. Falling back to manual fetching...')
    ua = await _get_user_agent(session)
    bn = await _get_build_number(session)
    bv = _get_browser_version(ua)

    properties = {
        'os': 'Windows',
        'browser': 'Chrome',
        'device': '',
        'browser_user_agent': ua,
        'browser_version': bv,
        'os_version': '10',
        'referrer': '',
        'referring_domain': '',
        'referrer_current': '',
        'referring_domain_current': '',
        'release_channel': 'stable',
        'system_locale': 'en-US',
        'client_build_number': bn,
        'client_event_source': None,
        'design_id': 0,
    }
    return properties, b64encode(_to_json(properties).encode()).decode('utf-8')


async def _get_build_number(session: ClientSession) -> int:  # Thank you Discord-S.C.U.M
    """Fetches client build number"""
    try:
        login_page_request = await session.get('https://discord.com/login', timeout=7)
        login_page = await login_page_request.text()
        build_url = 'https://discord.com/assets/' + re.compile(r'assets/+([a-z0-9]+)\.js').findall(login_page)[-2] + '.js'
        build_request = await session.get(build_url, timeout=7)
        build_file = await build_request.text()
        build_index = build_file.find('buildNumber') + 24
        return int(build_file[build_index : build_index + 6])
    except asyncio.TimeoutError:
        _log.critical('Could not fetch client build number. Falling back to hardcoded value...')
        return 9999


async def _get_user_agent(session: ClientSession) -> str:
    """Fetches the latest Windows 10/Chrome user-agent."""
    try:
        request = await session.request('GET', 'https://jnrbsn.github.io/user-agents/user-agents.json', timeout=7)
        response = json.loads(await request.text())
        return response[0]
    except asyncio.TimeoutError:
        _log.critical('Could not fetch user-agent. Falling back to hardcoded value...')
        return (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        )


def _get_browser_version(user_agent: str) -> str:
    """Fetches the latest Windows 10/Chrome version."""
    return user_agent.split('Chrome/')[1].split()[0]


def is_docker() -> bool:
    path = '/proc/self/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.isfile(path) and any('docker' in line for line in open(path)))


def stream_supports_colour(stream: Any) -> bool:
    # Pycharm and Vscode support colour in their inbuilt editors
    if 'PYCHARM_HOSTED' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
        return True

    is_a_tty = hasattr(stream, 'isatty') and stream.isatty()
    if sys.platform != 'win32':
        # Docker does not consistently have a tty attached to it
        return is_a_tty or is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ('ANSICON' in os.environ or 'WT_SESSION' in os.environ)


class _ColourFormatter(logging.Formatter):

    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to colour.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    LEVEL_COLOURS = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


def setup_logging(
    *,
    handler: logging.Handler = MISSING,
    formatter: logging.Formatter = MISSING,
    level: int = MISSING,
    root: bool = True,
) -> None:
    """A helper function to setup logging.

    This is superficially similar to :func:`logging.basicConfig` but
    uses different defaults and a colour formatter if the stream can
    display colour.

    This is used by the :class:`~discord.Client` to set up logging
    if ``log_handler`` is not ``None``.

    .. versionadded:: 2.0

    Parameters
    -----------
    handler: :class:`logging.Handler`
        The log handler to use for the library's logger.

        The default log handler if not provided is :class:`logging.StreamHandler`.
    formatter: :class:`logging.Formatter`
        The formatter to use with the given log handler. If not provided then it
        defaults to a colour based logging formatter (if available). If colour
        is not available then a simple logging formatter is provided.
    level: :class:`int`
        The default log level for the library's logger. Defaults to ``logging.INFO``.
    root: :class:`bool`
        Whether to set up the root logger rather than the library logger.
        Unlike the default for :class:`~discord.Client`, this defaults to ``True``.
    """

    if level is MISSING:
        level = logging.INFO

    if handler is MISSING:
        handler = logging.StreamHandler()

    if formatter is MISSING:
        if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream):
            formatter = _ColourFormatter()
        else:
            dt_fmt = '%Y-%m-%d %H:%M:%S'
            formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

    if root:
        logger = logging.getLogger()
    else:
        library, _, _ = __name__.partition('.')
        logger = logging.getLogger(library)

    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)
