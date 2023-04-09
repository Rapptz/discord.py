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

from . import utils
from .mixins import Hashable
from .partial_emoji import PartialEmoji
from .user import User

if TYPE_CHECKING:
    from .types.soundboard import (
        BaseSoundboardSound as BaseSoundboardSoundPayload,
        DefaultSoundboardSound as DefaultSoundboardSoundPayload,
        SoundboardSound as SoundboardSoundPayload,
    )
    from .state import ConnectionState
    from .guild import Guild

__all__ = ('DefaultSoundboardSound', 'SoundboardSound')


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
        self.override_path: Optional[str] = data['override_path']
        self._update(data)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    __hash__ = Hashable.__hash__

    def _update(self, data: BaseSoundboardSoundPayload):
        self.volume: float = data['volume']


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

    def __init__(self, *, data: DefaultSoundboardSoundPayload):
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


class SoundboardSound(BaseSoundboardSound):
    """Represents a Discord soundboard sound.

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
    guild_id: Optional[:class:`int`]
        The ID of the guild in which the sound is uploaded.
    user: Optional[:class:`User`]
        The user who uploaded the sound.
    available: :class:`bool`
        Whether the sound is available or not.
    """

    __slots__ = ('_state', 'guild_id', 'name', 'emoji', 'user', 'available')

    def __init__(self, *, state: ConnectionState, data: SoundboardSoundPayload):
        super().__init__(data=data)
        self._state: ConnectionState = state
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')

        user = data.get('user')
        self.user: Optional[User] = User(state=self._state, data=user) if user is not None else None

        self._update(data)

    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('volume', self.volume),
            ('emoji', self.emoji),
            ('user', self.user),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f"<{self.__class__.__name__} {inner}>"

    def _update(self, data: SoundboardSoundPayload):
        super()._update(data)

        self.name: str = data['name']
        self.emoji: Optional[PartialEmoji] = None

        emoji_id = utils._get_as_snowflake(data, 'emoji_id')
        emoji_name = data['emoji_name']
        if emoji_id is not None or emoji_name is not None:
            self.emoji = PartialEmoji(id=emoji_id, name=emoji_name)

        self.available: bool = data['available']

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild in which the sound is uploaded."""
        return self._state._get_guild(self.guild_id)
