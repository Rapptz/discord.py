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

from .mixins import Hashable
from .utils import snowflake_time, MISSING

from typing import (
    SupportsInt,
    TYPE_CHECKING,
    Type,
    Union,
)

if TYPE_CHECKING:
    import datetime
    from . import abc

    SupportsIntCast = Union[SupportsInt, str, bytes, bytearray]

# fmt: off
__all__ = (
    'Object',
)
# fmt: on


class Object(Hashable):
    """Represents a generic Discord object.

    The purpose of this class is to allow you to create 'miniature'
    versions of data classes if you want to pass in just an ID. Most functions
    that take in a specific data class with an ID can also take in this class
    as a substitute instead. Note that even though this is the case, not all
    objects (if any) actually inherit from this class.

    There are also some cases where some websocket events are received
    in :issue:`strange order <21>` and when such events happened you would
    receive this class rather than the actual data class. These cases are
    extremely rare.

    .. container:: operations

        .. describe:: x == y

            Checks if two objects are equal.

        .. describe:: x != y

            Checks if two objects are not equal.

        .. describe:: hash(x)

            Returns the object's hash.

    Attributes
    -----------
    id: :class:`int`
        The ID of the object.
    type: Type[:class:`abc.Snowflake`]
        The discord.py model type of the object, if not specified, defaults to this class.

        .. note::

            In instances where there are multiple applicable types, use a shared base class.
            for example, both :class:`Member` and :class:`User` are subclasses of :class:`abc.User`.

        .. versionadded:: 2.0
    """

    def __init__(self, id: SupportsIntCast, *, type: Type[abc.Snowflake] = MISSING):
        try:
            id = int(id)
        except ValueError:
            raise TypeError(f'id parameter must be convertible to int not {id.__class__!r}') from None
        self.id: int = id
        self.type: Type[abc.Snowflake] = type or self.__class__

    def __repr__(self) -> str:
        return f'<Object id={self.id!r} type={self.type!r}>'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.type):
            return self.id == other.id
        return NotImplemented

    __hash__ = Hashable.__hash__

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the snowflake's creation time in UTC."""
        return snowflake_time(self.id)


OLDEST_OBJECT = Object(id=0)
