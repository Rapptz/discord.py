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

from typing import List, TYPE_CHECKING, Optional

from . import utils
from .asset import Asset
from .flags import ApplicationFlags
from .permissions import Permissions

if TYPE_CHECKING:
    from .guild import Guild
    from .types.appinfo import (
        AppInfo as AppInfoPayload,
        PartialAppInfo as PartialAppInfoPayload,
        Team as TeamPayload,
        InstallParams as InstallParamsPayload,
    )
    from .user import User
    from .state import ConnectionState

__all__ = (
    'AppInfo',
    'PartialAppInfo',
    'AppInstallParams',
)


class AppInfo:
    """Represents the application info for the bot provided by Discord.


    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    owner: :class:`User`
        The application owner.
    team: Optional[:class:`Team`]
        The application's team.

        .. versionadded:: 1.3

    description: :class:`str`
        The application description.
    bot_public: :class:`bool`
        Whether the bot can be invited by anyone or if it is locked
        to the application owner.
    bot_require_code_grant: :class:`bool`
        Whether the bot requires the completion of the full oauth2 code
        grant flow to join.
    rpc_origins: Optional[List[:class:`str`]]
        A list of RPC origin URLs, if RPC is enabled.

    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.

        .. versionadded:: 1.3

    guild_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the guild to which it has been linked to.

        .. versionadded:: 1.3

    primary_sku_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the id of the "Game SKU" that is created,
        if it exists.

        .. versionadded:: 1.3

    slug: Optional[:class:`str`]
        If this application is a game sold on Discord,
        this field will be the URL slug that links to the store page.

        .. versionadded:: 1.3

    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.

        .. versionadded:: 2.0

    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.

        .. versionadded:: 2.0

    tags: List[:class:`str`]
        The list of tags describing the functionality of the application.

        .. versionadded:: 2.0

    custom_install_url: List[:class:`str`]
        The custom authorization URL for the application, if enabled.

        .. versionadded:: 2.0

    install_params: Optional[:class:`AppInstallParams`]
        The settings for custom authorization URL of application, if enabled.

        .. versionadded:: 2.0
    """

    __slots__ = (
        '_state',
        'description',
        'id',
        'name',
        'rpc_origins',
        'bot_public',
        'bot_require_code_grant',
        'owner',
        '_icon',
        'verify_key',
        'team',
        'guild_id',
        'primary_sku_id',
        'slug',
        '_cover_image',
        '_flags',
        'terms_of_service_url',
        'privacy_policy_url',
        'tags',
        'custom_install_url',
        'install_params',
    )

    def __init__(self, state: ConnectionState, data: AppInfoPayload):
        from .team import Team

        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self._icon: Optional[str] = data['icon']
        self.rpc_origins: List[str] = data['rpc_origins']
        self.bot_public: bool = data['bot_public']
        self.bot_require_code_grant: bool = data['bot_require_code_grant']
        self.owner: User = state.create_user(data['owner'])

        team: Optional[TeamPayload] = data.get('team')
        self.team: Optional[Team] = Team(state, team) if team else None

        self.verify_key: str = data['verify_key']

        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')

        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.slug: Optional[str] = data.get('slug')
        self._flags: int = data.get('flags', 0)
        self._cover_image: Optional[str] = data.get('cover_image')
        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')
        self.tags: List[str] = data.get('tags', [])
        self.custom_install_url: Optional[str] = data.get('custom_install_url')

        params = data.get('install_params')
        self.install_params: Optional[AppInstallParams] = AppInstallParams(params) if params else None

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'description={self.description!r} public={self.bot_public} '
            f'owner={self.owner!r}>'
        )

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='app')

    @property
    def cover_image(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the cover image on a store embed, if any.

        This is only available if the application is a game sold on Discord.
        """
        if self._cover_image is None:
            return None
        return Asset._from_cover_image(self._state, self.id, self._cover_image)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: If this application is a game sold on Discord,
        this field will be the guild to which it has been linked

        .. versionadded:: 1.3
        """
        return self._state._get_guild(self.guild_id)

    @property
    def flags(self) -> ApplicationFlags:
        """:class:`ApplicationFlags`: The application's flags.

        .. versionadded:: 2.0
        """
        return ApplicationFlags._from_value(self._flags)


class PartialAppInfo:
    """Represents a partial AppInfo given by :func:`~discord.abc.GuildChannel.create_invite`

    .. versionadded:: 2.0

    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    description: :class:`str`
        The application description.
    rpc_origins: Optional[List[:class:`str`]]
        A list of RPC origin URLs, if RPC is enabled.
    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.
    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.
    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        'description',
        'rpc_origins',
        'verify_key',
        'terms_of_service_url',
        'privacy_policy_url',
        '_icon',
        '_flags',
    )

    def __init__(self, *, state: ConnectionState, data: PartialAppInfoPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data.get('icon')
        self._flags: int = data.get('flags', 0)
        self.description: str = data['description']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins')
        self.verify_key: str = data['verify_key']
        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r}>'

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='app')

    @property
    def flags(self) -> ApplicationFlags:
        """:class:`ApplicationFlags`: The application's flags.

        .. versionadded:: 2.0
        """
        return ApplicationFlags._from_value(self._flags)


class AppInstallParams:
    """Represents the settings for custom authorization URL of an application.

    .. versionadded:: 2.0

    Attributes
    ----------
    scopes: List[:class:`str`]
        The list of `OAuth2 scopes <https://discord.com/developers/docs/topics/oauth2#shared-resources-oauth2-scopes>`_
        to add the application to a guild with.
    permissions: :class:`Permissions`
        The permissions to give to application in the guild.
    """

    __slots__ = ('scopes', 'permissions')

    def __init__(self, data: InstallParamsPayload) -> None:
        self.scopes: List[str] = data.get('scopes', [])
        self.permissions: Permissions = Permissions(int(data['permissions']))
