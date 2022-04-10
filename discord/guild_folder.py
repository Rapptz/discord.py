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

from typing import List, Optional, TYPE_CHECKING

from .colour import Colour
from .object import Object

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.snowflake import Snowflake

# fmt: off
__all__ = (
    'GuildFolder',
)
# fmt: on


class GuildFolder:
    """Represents a guild folder

    .. note::
        Guilds not in folders *are* actually in folders API wise, with them being the only member.
        Because Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two guild folders are equal.

        .. describe:: x != y

            Checks if two guild folders are not equal.

        .. describe:: hash(x)

            Return the folder's hash.

        .. describe:: str(x)

            Returns the folder's name.

        .. describe:: len(x)

            Returns the number of guilds in the folder.

    Attributes
    ----------
    id: Union[:class:`str`, :class:`int`]
        The ID of the folder.
    name: :class:`str`
        The name of the folder.
    guilds: List[:class:`Guild`]
        The guilds in the folder.
    """

    __slots__ = ('_state', 'id', 'name', '_colour', 'guilds')

    def __init__(self, *, data, state: ConnectionState) -> None:
        self._state = state
        self.id: Snowflake = data['id']
        self.name: str = data['name']
        self._colour: int = data['color']
        self.guilds: List[Guild] = list(filter(None, map(self._get_guild, data['guild_ids'])))  # type: ignore # Lying for better developer UX

    def __str__(self) -> str:
        return self.name or 'None'

    def __repr__(self) -> str:
        return f'<GuildFolder id={self.id} name={self.name} guilds={self.guilds!r}>'

    def __eq__(self, other) -> bool:
        return isinstance(other, GuildFolder) and self.id == other.id

    def __ne__(self, other) -> bool:
        if isinstance(other, GuildFolder):
            return self.id != other.id
        return True

    def __hash__(self) -> int:
        return hash(self.id)

    def __len__(self) -> int:
        return len(self.guilds)

    def _get_guild(self, id):
        return self._state._get_guild(int(id)) or Object(id=int(id))

    @property
    def colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`] The colour of the folder.

        There is an alias for this called :attr:`color`.
        """
        colour = self._colour
        return Colour(colour) if colour is not None else None

    @property
    def color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`] The color of the folder.

        This is an alias for :attr:`colour`.
        """
        return self.colour
