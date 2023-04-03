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

from typing import TYPE_CHECKING, Optional

from .mixins import Hashable
from .utils import snowflake_time

if TYPE_CHECKING:
    import datetime
    from .types.soundboard import SoundboardSound as SoundboardSoundPayload

__all__ = ()


class BaseSoundboardSound(Hashable):
    """Represents a generic Discord soundboard sound.

    .. versionadded:: 2.3

    .. container:: operations

        .. describe:: x == y

            Checks if two sounds are equal.

        .. describe:: x != y

            Checks if two sounds are not equal.

        .. describe:: hash(x)

            Returns the sound's hash.

    Attributes
    ------------
    id: :class:`int`
        The ID of the sound.
    volume: :class:`float`
        The volume of the sound as floating point percentage (e.g. ``1.0`` for 100%).
    override_path: Optional[:class:`str`]
        The override path of the sound (e.g. 'default_quack.mp3').
    """

    __slots__ = ('id', 'volume', 'override_path')

    def __init__(self, *, data: SoundboardSoundPayload):
        self.id: int = int(data['id'])
        self.volume: float = data['volume']
        self.override_path: Optional[str] = data.get('override_path')

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    __hash__ = Hashable.__hash__

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the snowflake's creation time in UTC."""
        return snowflake_time(self.id)
