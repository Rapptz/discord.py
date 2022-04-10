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

from typing import Optional, TYPE_CHECKING

from .utils import MISSING

if TYPE_CHECKING:
    from .state import ConnectionState

__all__ = (
    'PartialConnection',
    'Connection',
)


class PartialConnection:
    """Represents a partial Discord profile connection

    This is the info you get for other people's connections.

    .. container:: operations

        .. describe:: x == y

            Checks if two connections are equal.

        .. describe:: x != y

            Checks if two connections are not equal.

        .. describe:: hash(x)

            Return the connection's hash.

        .. describe:: str(x)

            Returns the connection's name.

    Attributes
    ----------
    id: :class:`str`
        The connection's account ID.
    name: :class:`str`
        The connection's account name.
    type: :class:`str`
        The connection service (e.g. 'youtube')
    verified: :class:`bool`
        Whether the connection is verified.
    revoked: :class:`bool`
        Whether the connection is revoked.
    visible: :class:`bool`
        Whether the connection is visible on the user's profile.
    """

    __slots__ = ('id', 'name', 'type', 'verified', 'revoked', 'visible')

    def __init__(self, data: dict):
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} type={self.type!r} visible={self.visible}>'

    def __hash__(self) -> int:
        return hash((self.name, self.id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PartialConnection):
            return self.id == other.id and self.name == other.name
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, PartialConnection):
            return self.id != other.id or self.name != other.name
        return True

    def _update(self, data: dict):
        self.id: str = data['id']
        self.name: str = data['name']
        self.type: str = data['type']

        self.verified: bool = data['verified']
        self.revoked: bool = data.get('revoked', False)
        self.visible: bool = True


class Connection(PartialConnection):
    """Represents a Discord profile connection

    Attributes
    ----------
    friend_sync: :class:`bool`
        Whether friends are synced over the connection.
    show_activity: :class:`bool`
        Whether activities from this connection will be shown in presences.
    access_token: :class:`str`
        The OAuth2 access token for the account, if applicable.
    """

    __slots__ = ('_state', 'visible', 'friend_sync', 'show_activity', 'access_token')

    def __init__(self, *, data: dict, state: ConnectionState):
        super().__init__(data)
        self._state = state
        self.access_token: Optional[str] = None

    def _update(self, data: dict):
        super()._update(data)
        self.visible: bool = bool(data.get('visibility', True))
        self.friend_sync: bool = data.get('friend_sync', False)
        self.show_activity: bool = data.get('show_activity', True)

        # Only sometimes in the payload
        try:
            self.access_token: Optional[str] = data['access_token']
        except KeyError:
            pass

    async def edit(self, *, visible: bool = MISSING, show_activity: bool = MISSING):
        """|coro|

        Edit the connection.

        All parameters are optional.

        Parameters
        ----------
        visible: :class:`bool`
            Whether the connection is visible on your profile.
        show_activity: :class:`bool`
            Whether activities from this connection will be shown in presences.

        Raises
        ------
        HTTPException
            Editing the connection failed.
        """
        payload = {}
        if visible is not MISSING:
            payload['visibility'] = visible
        if show_activity is not MISSING:
            payload['show_activity'] = show_activity
        data = await self._state.http.edit_connection(self.type, self.id, **payload)
        self._update(data)

    async def delete(self) -> None:
        """|coro|

        Removes the connection.

        Raises
        ------
        HTTPException
            Deleting the connection failed.
        """
        await self._state.http.delete_connection(self.type, self.id)

    async def fetch_access_token(self) -> str:
        """|coro|

        Retrieves a new access token for the connection.

        Raises
        ------
        HTTPException
            Retrieving the access token failed.

        Returns
        -------
        :class:`str`
            The new access token.
        """
        data = await self._state.http.get_connection_token(self.type, self.id)
        self.access_token = token = data['access_token']
        return token
