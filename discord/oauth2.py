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

from .application import PartialApplication
from .guild import UserGuild
from .mixins import Hashable
from .utils import MISSING

if TYPE_CHECKING:
    from .abc import Snowflake
    from .permissions import Permissions
    from .state import ConnectionState
    from .user import User
    from .types.oauth2 import OAuth2Authorization as OAuth2AuthorizationPayload, OAuth2Token as OAuth2TokenPayload

__all__ = (
    'OAuth2Token',
    'OAuth2Authorization',
)


class OAuth2Token(Hashable):
    """Represents an authorized OAuth2 application for a user.

    .. container:: operations

        .. describe:: x == y

            Checks if two authorizations are equal.

        .. describe:: x != y

            Checks if two authorizations are not equal.

        .. describe:: hash(x)

            Return the authorizations's hash.

        .. describe:: str(x)

            Returns the authorizations's name.

    .. versionadded:: 2.1

    Attributes
    -----------
    id: :class:`int`
        The ID of the authorization.
    application: :class:`PartialApplication`
        The application that the authorization is for.
    scopes: List[:class:`str`]
        The scopes that the authorization has.
    """

    __slots__ = ('id', 'application', 'scopes', '_state')

    def __init__(self, *, state: ConnectionState, data: OAuth2TokenPayload):
        self._state = state
        self.id: int = int(data['id'])
        self.application: PartialApplication = PartialApplication(state=state, data=data['application'])
        self.scopes: List[str] = data['scopes']

    def __repr__(self):
        return f'<OAuth2Token id={self.id} application={self.application!r} scopes={self.scopes!r}>'

    def __str__(self):
        return self.application.name

    @property
    def authorized(self) -> bool:
        """:class:`bool`: Whether the user has already authorized the application.

        This is here for compatibility purposes and is always ``True``.
        """
        return True

    async def revoke(self):
        """|coro|

        Revokes the application's authorization.

        Raises
        -------
        HTTPException
            Deauthorizing the application failed.
        """
        await self._state.http.revoke_oauth2_token(self.id)


class OAuth2Authorization:
    """Represents a Discord OAuth2 application authorization.

    .. versionadded:: 2.1

    Attributes
    -----------
    scopes: List[:class:`str`]
        The scopes that the authorization has.
    response_type: Optional[:class:`str`]
        The response type that will be used for the authorization, if using the full OAuth2 flow.
    code_challenge_method: Optional[:class:`str`]
        The code challenge method that will be used for the PKCE authorization, if using the full OAuth2 flow.
    code_challenge: Optional[:class:`str`]
        The code challenge that will be used for the PKCE authorization, if using the full OAuth2 flow.
    state: Optional[:class:`str`]
        The state that will be used for authorization security.
    authorized: :class:`bool`
        Whether the user has already authorized the application.
    application: :class:`PartialApplication`
        The application that the authorization is for.
    bot: Optional[:class:`User`]
        The bot user associated with the application, provided if authorizing with the ``bot`` scope.
    approximate_guild_count: Optional[:class:`int`]
        The approximate number of guilds the bot is in, provided if authorizing with the ``bot`` scope.
    guilds: List[:class:`UserGuild`]
        The guilds the current user is in, provided if authorizing with the ``bot`` scope.
    redirect_uri: Optional[:class:`str`]
        The redirect URI that will be used for the authorization, if using the full OAuth2 flow and a redirect URI exists.
    """

    __slots__ = (
        'authorized',
        'application',
        'bot',
        'approximate_guild_count',
        'guilds',
        'redirect_uri',
        'scopes',
        'response_type',
        'code_challenge_method',
        'code_challenge',
        'state',
        '_state',
    )

    def __init__(
        self,
        *,
        _state: ConnectionState,
        data: OAuth2AuthorizationPayload,
        scopes: List[str],
        response_type: Optional[str],
        code_challenge_method: Optional[str] = None,
        code_challenge: Optional[str] = None,
        state: Optional[str],
    ):
        self._state = _state
        self.scopes: List[str] = scopes
        self.response_type: Optional[str] = response_type
        self.code_challenge_method: Optional[str] = code_challenge_method
        self.code_challenge: Optional[str] = code_challenge
        self.state: Optional[str] = state
        self.authorized: bool = data['authorized']
        self.application: PartialApplication = PartialApplication(state=_state, data=data['application'])
        self.bot: Optional[User] = _state.store_user(data['bot']) if 'bot' in data else None
        self.approximate_guild_count: Optional[int] = (
            data['bot'].get('approximate_guild_count', 0) if 'bot' in data else None
        )
        self.guilds: List[UserGuild] = [UserGuild(state=_state, data=g) for g in data.get('guilds', [])]
        self.redirect_uri: Optional[str] = data.get('redirect_uri')

    def __repr__(self):
        return f'<OAuth2Authorization authorized={self.authorized} application={self.application!r} scopes={self.scopes!r} response_type={self.response_type!r} redirect_uri={self.redirect_uri}>'

    async def authorize(
        self, *, guild: Snowflake = MISSING, channel: Snowflake = MISSING, permissions: Permissions = MISSING
    ) -> str:
        """|coro|

        Authorizes the application for the user. A shortcut for :meth:`Client.create_authorization`.

        Parameters
        -----------
        guild: :class:`Guild`
            The guild to authorize for, if authorizing with the ``applications.commands`` or ``bot`` scopes.
        channel: Union[:class:`TextChannel`, :class:`VoiceChannel`, :class:`StageChannel`]
            The channel to authorize for, if authorizing with the ``webhooks.incoming`` scope. See :meth:`Guild.webhook_channels`.
        permissions: :class:`Permissions`
            The permissions to grant, if authorizing with the ``bot`` scope.

        Raises
        -------
        HTTPException
            Authorizing the application failed.

        Returns
        --------
        :class:`str`
            The URL to redirect the user to. May be an error page.
        """
        data = await self._state.http.authorize_oauth2(
            self.application.id,
            self.scopes,
            self.response_type,
            self.redirect_uri,
            self.code_challenge_method,
            self.code_challenge,
            self.state,
            guild_id=guild.id if guild else None,
            webhook_channel_id=channel.id if channel else None,
            permissions=permissions.value if permissions else None,
        )
        return data['location']
