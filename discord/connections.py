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

from typing import TYPE_CHECKING, List, Optional

from .enums import ConnectionType, try_enum
from .integrations import Integration
from .metadata import Metadata
from .utils import MISSING

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.integration import ConnectionIntegration as IntegrationPayload
    from .types.user import Connection as ConnectionPayload, PartialConnection as PartialConnectionPayload

__all__ = (
    'PartialConnection',
    'Connection',
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
    metadata: Optional[:class:`Metadata`]
        Various metadata about the connection.

        The contents of this are always subject to change.
    """

    __slots__ = ('id', 'name', 'type', 'verified', 'visible', 'metadata')

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

        self.metadata: Optional[Metadata] = Metadata(data['metadata']) if 'metadata' in data else None

    @property
    def url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns a URL linking to the connection's profile, if available."""
        if self.type == ConnectionType.twitch:
            return f'https://www.twitch.tv/{self.name}'
        elif self.type == ConnectionType.youtube:
            return f'https://www.youtube.com/{self.id}'
        elif self.type == ConnectionType.skype:
            return f'skype:{self.id}?userinfo'
        elif self.type == ConnectionType.steam:
            return f'https://steamcommunity.com/profiles/{self.id}'
        elif self.type == ConnectionType.reddit:
            return f'https://www.reddit.com/u/{self.name}'
        elif self.type == ConnectionType.facebook:
            return f'https://www.facebook.com/{self.name}'
        elif self.type == ConnectionType.twitter:
            return f'https://twitter.com/{self.name}'
        elif self.type == ConnectionType.spotify:
            return f'https://open.spotify.com/user/{self.id}'
        elif self.type == ConnectionType.xbox:
            return f'https://account.xbox.com/en-US/Profile?Gamertag={self.name}'
        elif self.type == ConnectionType.github:
            return f'https://github.com/{self.name}'
        elif self.type == ConnectionType.tiktok:
            return f'https://tiktok.com/@{self.name}'


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
    metadata: Optional[:class:`Metadata`]
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
        Only applicable for connections of type:attr:`ConnectionType.twitch`,
        :attr:`ConnectionType.youtube`, and :attr:`ConnectionType.spotify`.

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
