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
from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .types.soundboard import (
        BaseSoundboardSound as BaseSoundboardSoundPayload,
        SoundboardSound as SoundboardSoundPayload,
    )

__all__ = ('DefaultSoundboardSound',)


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

    def __init__(self, *, data: BaseSoundboardSoundPayload):
        self.id: int = int(data['sound_id'])
        self.volume: float = data['volume']
        self.override_path: Optional[str] = data['override_path']

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    __hash__ = Hashable.__hash__


class DefaultSoundboardSound(BaseSoundboardSound):
    """Represents a Discord default soundboard sound.

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
    name: :class:`str`
        The name of the sound.
    emoji: :class:`PartialEmoji`
        The emoji of the sound.
    """

    __slots__ = ('name', 'emoji')

    def __init__(self, *, data: SoundboardSoundPayload):
        self.name: str = data['name']
        self.emoji: PartialEmoji = PartialEmoji(name=data['emoji_name'])
        super().__init__(data=data)

    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('volume', self.volume),
            ('emoji', self.emoji),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f"<{self.__class__.__name__} {inner}>"
