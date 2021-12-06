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

from typing import Optional

from .utils import MISSING


class PartialConnection:
    """Represents a partial Discord profile connection

    This is the info you get for other people's connections.

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

    def __init__(self, data):
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
    friend_sync: :class:`bool`
        Whether friends are synced over the connection.
    show_activity: :class:`bool`
        Whether activities from this connection will be shown in presences.
    access_token: :class:`str`
        The OAuth2 access token for the account, if applicable.
    """

    __slots__ = ('_state', 'visible', 'friend_sync', 'show_activity', 'access_token')

    def __init__(self, *, data, state):
        self._state = state
        super().__init__(data)

        self.visible: bool = bool(data.get('visibility', True))
        self.friend_sync: bool = data.get('friend_sync', False)
        self.show_activity: bool = data.get('show_activity', True)
        self.access_token: Optional[str] = data.get('access_token')

    async def edit(self, *, visible: bool = MISSING):
        """|coro|

        Edit the connection.

        All parameters are optional.

        Parameters
        ----------
        visible: :class:`bool`
            Whether the connection is visible on your profile.

        Raises
        ------
        HTTPException
            Editing the connection failed.

        Returns
        -------
        :class:`Connection`
            The new connection.
        """
        if visible is not MISSING:
            data = await self._state.http.edit_connection(self.type, self.id, visibility=visible)
            return Connection(data=data, state=self._state)
        else:
            return self

    async def delete(self):
        """|coro|

        Removes the connection.

        Raises
        ------
        HTTPException
            Deleting the connection failed.
        """
        await self._state.http.delete_connection(self.type, self.id)
