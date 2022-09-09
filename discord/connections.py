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

from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Tuple

from .enums import ConnectionType, try_enum
from .integrations import Integration
from .utils import MISSING

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.integration import ConnectionIntegration as IntegrationPayload
    from .types.user import Connection as ConnectionPayload, PartialConnection as PartialConnectionPayload

__all__ = (
    'PartialConnection',
    'Connection',
    'ConnectionMetadata',
)


class PartialConnection:
    """Represents a partial Discord profile connection.

    This is the info you get for other users' connections.

    .. versionadded:: 2.0

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
    type: :class:`ConnectionType`
        The connection service type (e.g. youtube, twitch, etc.).
    verified: :class:`bool`
        Whether the connection is verified.
    visible: :class:`bool`
        Whether the connection is visible on the user's profile.
    """

    __slots__ = ('id', 'name', 'type', 'verified', 'visible')

    def __init__(self, data: PartialConnectionPayload):
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} type={self.type!r} visible={self.visible}>'

    def __hash__(self) -> int:
        return hash((self.type.value, self.id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PartialConnection):
            return self.id == other.id and self.name == other.name
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, PartialConnection):
            return self.id != other.id or self.name != other.name
        return True

    def _update(self, data: PartialConnectionPayload):
        self.id: str = data['id']
        self.name: str = data['name']
        self.type: ConnectionType = try_enum(ConnectionType, data['type'])
        self.verified: bool = data['verified']
        self.visible: bool = True  # If we have a partial connection, it's visible


class Connection(PartialConnection):
    """Represents a Discord profile connection.

    .. versionadded:: 2.0

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
    revoked: :class:`bool`
        Whether the connection is revoked.
    friend_sync: :class:`bool`
        Whether friends are synced over the connection.
    show_activity: :class:`bool`
        Whether activities from this connection will be shown in presences.
    two_way_link: :class:`bool`
        Whether the connection is authorized both ways (i.e. it's both a connection and an authorization).
    metadata_visible: :class:`bool`
        Whether the connection's metadata is visible.
    metadata: Optional[:class:`ConnectionMetadata`]
        Various metadata about the connection.

        The contents of this are always subject to change.
    access_token: Optional[:class:`str`]
        The OAuth2 access token for the account, if applicable.
    integrations: List[:class:`Integration`]
        The integrations attached to the connection.
    """

    __slots__ = (
        '_state',
        'revoked',
        'friend_sync',
        'show_activity',
        'two_way_link',
        'metadata_visible',
        'metadata',
        'access_token',
        'integrations',
    )

    def __init__(self, *, data: ConnectionPayload, state: ConnectionState):
        self._update(data)
        self._state = state
        self.access_token: Optional[str] = None

    def _update(self, data: ConnectionPayload):
        super()._update(data)
        self.revoked: bool = data.get('revoked', False)
        self.visible: bool = bool(data.get('visibility', False))
        self.friend_sync: bool = data.get('friend_sync', False)
        self.show_activity: bool = data.get('show_activity', True)
        self.two_way_link: bool = data.get('two_way_link', False)
        self.metadata_visible: bool = bool(data.get('metadata_visibility', False))
        self.metadata: Optional[ConnectionMetadata] = ConnectionMetadata(data['metadata']) if 'metadata' in data else None

        # Only sometimes in the payload
        try:
            self.access_token: Optional[str] = data['access_token']
        except KeyError:
            pass

        self.integrations: List[Integration] = [
            Integration(data=i, guild=self._resolve_guild(i)) for i in data.get('integrations') or []
        ]

    def _resolve_guild(self, data: IntegrationPayload) -> Guild:
        from .guild import Guild

        state = self._state
        guild_data = data.get('guild')
        if not guild_data:
            return None  # type: ignore

        guild_id = int(guild_data['id'])
        guild = state._get_guild(guild_id)
        if guild is None:
            guild = Guild(data=guild_data, state=state)
        return guild

    async def edit(
        self,
        *,
        name: str = MISSING,
        visible: bool = MISSING,
        friend_sync: bool = MISSING,
        show_activity: bool = MISSING,
        metadata_visible: bool = MISSING,
    ) -> Connection:
        """|coro|

        Edit the connection.

        All parameters are optional.

        Parameters
        ----------
        name: :class:`str`
            The new name of the connection. Only editable for certain connection types.
        visible: :class:`bool`
            Whether the connection is visible on your profile.
        show_activity: :class:`bool`
            Whether activities from this connection will be shown in presences.
        friend_sync: :class:`bool`
            Whether friends are synced over the connection.
        metadata_visible: :class:`bool`
            Whether the connection's metadata is visible.

        Raises
        ------
        HTTPException
            Editing the connection failed.

        Returns
        -------
        :class:`Connection`
            The edited connection.
        """
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if visible is not MISSING:
            payload['visibility'] = visible
        if show_activity is not MISSING:
            payload['show_activity'] = show_activity
        if friend_sync is not MISSING:
            payload['friend_sync'] = friend_sync
        if metadata_visible is not MISSING:
            payload['metadata_visibility'] = metadata_visible
        data = await self._state.http.edit_connection(self.type.value, self.id, **payload)
        return Connection(data=data, state=self._state)

    async def refresh(self) -> None:
        """|coro|

        Refreshes the connection. This updates the connection's :attr:`metadata`.

        Raises
        ------
        HTTPException
            Refreshing the connection failed.
        """
        await self._state.http.refresh_connection(self.type.value, self.id)

    async def delete(self) -> None:
        """|coro|

        Removes the connection.

        Raises
        ------
        HTTPException
            Deleting the connection failed.
        """
        await self._state.http.delete_connection(self.type.value, self.id)

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
        data = await self._state.http.get_connection_token(self.type.value, self.id)
        return data['access_token']


class ConnectionMetadata:
    """Represents a connection's metadata.

    Because of how unstable and wildly varying this metadata can be, this is a simple class that just
    provides access ro the raw data using dot notation. This means if an attribute is not present,
    ``None`` will be returned instead of raising an AttributeError.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two metadata objects are equal.

        .. describe:: x != y

            Checks if two metadata objects are not equal.

        .. describe:: x[key]

            Returns a metadata value if it is found, otherwise raises a :exc:`KeyError`.

        .. describe:: key in x

            Checks if a metadata value is present.

        .. describe:: iter(x)
            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.
    """

    __slots__ = ()

    def __init__(self, data: Optional[dict]) -> None:
        self.__dict__.update(data or {})

    def __repr__(self) -> str:
        return f'<ConnectionMetadata {" ".join(f"{k}={v!r}" for k, v in self.__dict__.items())}>'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConnectionMetadata):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, ConnectionMetadata):
            return True
        return self.__dict__ != other.__dict__

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield from self.__dict__.items()

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __getattr__(self, attr: str) -> Any:
        return None

    def __contains__(self, key: str) -> bool:
        return key in self.__dict__
