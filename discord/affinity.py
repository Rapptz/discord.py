"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import TYPE_CHECKING

from .mixins import Hashable

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.user import UserAffinity as UserAffinityPayload, GuildAffinity as GuildAffinityPayload

__all__ = (
    'UserAffinity',
    'GuildAffinity',
)


class UserAffinity(Hashable):
    """Represents a user's affinity with another user.

    User affinities that the current user has a mutual guild with are treated as implicit relationships,
    meaning that you get their user presence synced like a friend.

    These implicit relationships are not *real* relationships, and are therefore not returned by the API.
    However, they are lazily added to cache by the library when detected.

    .. container:: operations

        .. describe:: x == y

            Checks if two affinities are equal.

        .. describe:: x != y

            Checks if two affinities are not equal.

        .. describe:: hash(x)

            Return the affinity's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    user_id: :class:`int`
        The ID of the user being compared.
    affinity: :class:`float`
        The affinity score.
    """

    __slots__ = ('_state', 'user_id', 'affinity')

    def __init__(self, *, state: ConnectionState, data: UserAffinityPayload):
        self._state = state
        self.user_id = int(data['user_id'])
        self.affinity = data['affinity']

    def __repr__(self) -> str:
        return f'<UserAffinity user_id={self.user_id} affinity={self.affinity}>'

    @property
    def id(self) -> int:
        """:class:`int`: The ID of the user being compared."""
        return self.user_id

    @property
    def user(self):
        """Optional[:class:`User`]: The user being compared."""
        return self._state.get_user(self.user_id)


class GuildAffinity(Hashable):
    """Represents a user's affinity with a guild.

    .. container:: operations

        .. describe:: x == y

            Checks if two affinities are equal.

        .. describe:: x != y

            Checks if two affinities are not equal.

        .. describe:: hash(x)

            Return the affinity's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    guild_id: :class:`int`
        The ID of the guild being compared.
    affinity: :class:`float`
        The affinity score.
    """

    __slots__ = ('_state', 'guild_id', 'affinity')

    def __init__(self, *, state: ConnectionState, data: GuildAffinityPayload):
        self._state = state
        self.guild_id = int(data['guild_id'])
        self.affinity = data['affinity']

    def __repr__(self) -> str:
        return f'<GuildAffinity guild_id={self.guild_id} affinity={self.affinity}>'

    @property
    def id(self) -> int:
        """:class:`int`: The ID of the guild being compared."""
        return self.guild_id

    @property
    def guild(self):
        """Optional[:class:`Guild`]: The guild being compared."""
        return self._state._get_guild(self.guild_id)
