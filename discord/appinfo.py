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

from typing import List, TYPE_CHECKING, Optional, Tuple, Iterator

from . import utils
from .asset import Asset, AssetMixin
from .flags import ApplicationFlags
from .permissions import Permissions
from .utils import MISSING
from .partial_emoji import _EmojiTag, PartialEmoji

if TYPE_CHECKING:
    from typing import Dict, Any
    from typing_extensions import Self

    from .guild import Guild
    from .types.appinfo import (
        AppInfo as AppInfoPayload,
        PartialAppInfo as PartialAppInfoPayload,
        Team as TeamPayload,
        InstallParams as InstallParamsPayload,
    )
    from .user import User
    from .state import ConnectionState
    from .role import Role
    from .types.emoji import Emoji as EmojiPayload
    from datetime import datetime

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
        GameSDK's :ddocs:`GetTicket <game-sdk/applications#getticket>`.

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
    role_connections_verification_url: Optional[:class:`str`]
        The application's connection verification URL which will render the application as
        a verification method in the guild's role verification configuration.

        .. versionadded:: 2.2
    interactions_endpoint_url: Optional[:class:`str`]
        The interactions endpoint url of the application to receive interactions over this endpoint rather than
        over the gateway, if configured.

        .. versionadded:: 2.4
    redirect_uris: List[:class:`str`]
        A list of authentication redirect URIs.

        .. versionadded:: 2.4
    approximate_guild_count: :class:`int`
        The approximate count of the guilds the bot was added to.

        .. versionadded:: 2.4
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
        'role_connections_verification_url',
        'interactions_endpoint_url',
        'redirect_uris',
        'approximate_guild_count',
    )

    def __init__(self, state: ConnectionState, data: AppInfoPayload):
        from .team import Team

        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self._icon: Optional[str] = data['icon']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins')
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
        self.role_connections_verification_url: Optional[str] = data.get('role_connections_verification_url')

        params = data.get('install_params')
        self.install_params: Optional[AppInstallParams] = AppInstallParams(params) if params else None
        self.interactions_endpoint_url: Optional[str] = data.get('interactions_endpoint_url')
        self.redirect_uris: List[str] = data.get('redirect_uris', [])
        self.approximate_guild_count: int = data.get('approximate_guild_count', 0)

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

    async def edit(
        self,
        *,
        reason: Optional[str] = MISSING,
        custom_install_url: Optional[str] = MISSING,
        description: Optional[str] = MISSING,
        role_connections_verification_url: Optional[str] = MISSING,
        install_params_scopes: Optional[List[str]] = MISSING,
        install_params_permissions: Optional[Permissions] = MISSING,
        flags: Optional[ApplicationFlags] = MISSING,
        icon: Optional[bytes] = MISSING,
        cover_image: Optional[bytes] = MISSING,
        interactions_endpoint_url: Optional[str] = MISSING,
        tags: Optional[List[str]] = MISSING,
    ) -> AppInfo:
        r"""|coro|

        Edits the application info.

        .. versionadded:: 2.4

        Parameters
        ----------
        custom_install_url: Optional[:class:`str`]
            The new custom authorization URL for the application. Can be ``None`` to remove the URL.
        description: Optional[:class:`str`]
            The new application description. Can be ``None`` to remove the description.
        role_connections_verification_url: Optional[:class:`str`]
            The new application’s connection verification URL which will render the application
            as a verification method in the guild’s role verification configuration. Can be ``None`` to remove the URL.
        install_params_scopes: Optional[List[:class:`str`]]
            The new list of :ddocs:`OAuth2 scopes <topics/oauth2#shared-resources-oauth2-scopes>` of
            the :attr:`~install_params`. Can be ``None`` to remove the scopes.
        install_params_permissions: Optional[:class:`Permissions`]
            The new permissions of the :attr:`~install_params`. Can be ``None`` to remove the permissions.
        flags: Optional[:class:`ApplicationFlags`]
            The new application’s flags. Only limited intent flags (:attr:`~ApplicationFlags.gateway_presence_limited`,
            :attr:`~ApplicationFlags.gateway_guild_members_limited`, :attr:`~ApplicationFlags.gateway_message_content_limited`)
            can be edited. Can be ``None`` to remove the flags.

            .. warning::

                Editing the limited intent flags leads to the termination of the bot.

        icon: Optional[:class:`bytes`]
            The new application’s icon as a :term:`py:bytes-like object`. Can be ``None`` to remove the icon.
        cover_image: Optional[:class:`bytes`]
            The new application’s cover image as a :term:`py:bytes-like object` on a store embed.
            The cover image is only available if the application is a game sold on Discord.
            Can be ``None`` to remove the image.
        interactions_endpoint_url: Optional[:class:`str`]
            The new interactions endpoint url of the application to receive interactions over this endpoint rather than
            over the gateway. Can be ``None`` to remove the URL.
        tags: Optional[List[:class:`str`]]
            The new list of tags describing the functionality of the application. Can be ``None`` to remove the tags.
        reason: Optional[:class:`str`]
            The reason for editing the application. Shows up on the audit log.

        Raises
        -------
        HTTPException
            Editing the application failed
        ValueError
            The image format passed in to ``icon`` or ``cover_image`` is invalid. This is also raised
            when ``install_params_scopes`` and ``install_params_permissions`` are incompatible with each other.

        Returns
        -------
        :class:`AppInfo`
            The newly updated application info.
        """
        payload: Dict[str, Any] = {}

        if custom_install_url is not MISSING:
            payload['custom_install_url'] = custom_install_url

        if description is not MISSING:
            payload['description'] = description

        if role_connections_verification_url is not MISSING:
            payload['role_connections_verification_url'] = role_connections_verification_url

        if install_params_scopes is not MISSING:
            install_params: Optional[Dict[str, Any]] = {}
            if install_params_scopes is None:
                install_params = None
            else:
                if "bot" not in install_params_scopes and install_params_permissions is not MISSING:
                    raise ValueError("'bot' must be in install_params_scopes if install_params_permissions is set")

                install_params['scopes'] = install_params_scopes

                if install_params_permissions is MISSING:
                    install_params['permissions'] = 0
                else:
                    if install_params_permissions is None:
                        install_params['permissions'] = 0
                    else:
                        install_params['permissions'] = install_params_permissions.value

            payload['install_params'] = install_params

        else:
            if install_params_permissions is not MISSING:
                raise ValueError("install_params_scopes must be set if install_params_permissions is set")

        if flags is not MISSING:
            if flags is None:
                payload['flags'] = flags
            else:
                payload['flags'] = flags.value

        if icon is not MISSING:
            if icon is None:
                payload['icon'] = icon
            else:
                payload['icon'] = utils._bytes_to_base64_data(icon)

        if cover_image is not MISSING:
            if cover_image is None:
                payload['cover_image'] = cover_image
            else:
                payload['cover_image'] = utils._bytes_to_base64_data(cover_image)

        if interactions_endpoint_url is not MISSING:
            payload['interactions_endpoint_url'] = interactions_endpoint_url

        if tags is not MISSING:
            payload['tags'] = tags
        data = await self._state.http.edit_application_info(reason=reason, payload=payload)
        return AppInfo(data=data, state=self._state)


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
        GameSDK's :ddocs:`GetTicket <game-sdk/applications#getticket>`.
    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.
    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.
    approximate_guild_count: :class:`int`
        The approximate count of the guilds the bot was added to.

        .. versionadded:: 2.3
    redirect_uris: List[:class:`str`]
        A list of authentication redirect URIs.

        .. versionadded:: 2.3
    interactions_endpoint_url: Optional[:class:`str`]
        The interactions endpoint url of the application to receive interactions over this endpoint rather than
        over the gateway, if configured.

        .. versionadded:: 2.3
    role_connections_verification_url: Optional[:class:`str`]
        The application's connection verification URL which will render the application as
        a verification method in the guild's role verification configuration.

        .. versionadded:: 2.3
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
        '_cover_image',
        'approximate_guild_count',
        'redirect_uris',
        'interactions_endpoint_url',
        'role_connections_verification_url',
    )

    def __init__(self, *, state: ConnectionState, data: PartialAppInfoPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data.get('icon')
        self._flags: int = data.get('flags', 0)
        self._cover_image: Optional[str] = data.get('cover_image')
        self.description: str = data['description']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins')
        self.verify_key: str = data['verify_key']
        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')
        self.approximate_guild_count: int = data.get('approximate_guild_count', 0)
        self.redirect_uris: List[str] = data.get('redirect_uris', [])
        self.interactions_endpoint_url: Optional[str] = data.get('interactions_endpoint_url')
        self.role_connections_verification_url: Optional[str] = data.get('role_connections_verification_url')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r}>'

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='app')

    @property
    def cover_image(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the cover image of the application's default rich presence.

        This is only available if the application is a game sold on Discord.

        .. versionadded:: 2.3
        """
        if self._cover_image is None:
            return None
        return Asset._from_cover_image(self._state, self.id, self._cover_image)

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
        The list of :ddocs:`OAuth2 scopes <topics/oauth2#shared-resources-oauth2-scopes>`
        to add the application to a guild with.
    permissions: :class:`Permissions`
        The permissions to give to application in the guild.
    """

    __slots__ = ('scopes', 'permissions')

    def __init__(self, data: InstallParamsPayload) -> None:
        self.scopes: List[str] = data.get('scopes', [])
        self.permissions: Permissions = Permissions(int(data['permissions']))


class AppEmoji(_EmojiTag, AssetMixin):
    """Represents an emoji from an application.

    .. versionadded:: 2.5.1

    .. container:: operations

        .. describe:: x == y

            Checks if two app emoji are the same.

        .. describe:: x != y

            Checks if two app emoji are not the same.

        .. describe:: hash(x)

            Return the app emoji's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.

        .. describe:: str(x)

            Returns the app emoji rendered for discord.

    Attributes
    -----------
    application_id: :class:`int`
        The ID of the application that owns this emoji.
    name: :class:`str`
        The name of the emoji.
    id: :class:`int`
        The emoji's ID.
    require_colons: :class:`bool`
        If colons are required to use this emoji in the client (:PJSalt: vs PJSalt).
    animated: :class:`bool`
        Whether an emoji is animated or not.
    managed: :class:`bool`
        If this emoji is managed by a Twitch integration.
    available: :class:`bool`
        Whether the emoji is available for use.
    user: Optional[:class:`User`]
        The team member that uploaded the emoji from the app's settings, or for
        the bot user if uploaded using the API. This can only be retrieved
        using :meth:`~discord.Client.fetch_emoji` or :meth:`~discord.Client.fetch_emojis`
    """

    __slots__: Tuple[str, ...] = (
        'application_id',
        'require_colons',
        'animated',
        'managed',
        'id',
        'name',
        '_roles',
        '_state',
        'user',
        'available',
    )

    def __init__(self, *, application_id: int, state: ConnectionState, data: EmojiPayload) -> None:
        self.application_id: int = application_id
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, emoji: EmojiPayload) -> None:
        from .user import User  # circular import

        self.require_colons: bool = emoji.get('require_colons', False)
        self.managed: bool = emoji.get('managed', False)
        self.id: int = int(emoji['id'])  # type: ignore # This won't be None for full emoji objects.
        self.name: str = emoji['name']  # type: ignore # This won't be None for full emoji objects.
        self.animated: bool = emoji.get('animated', False)
        self.available: bool = emoji.get('available', True)
        self._roles: utils.SnowflakeList = utils.SnowflakeList(map(int, emoji.get('roles', [])))
        user = emoji.get('user')
        self.user: Optional[User] = User(state=self._state, data=user) if user else None

    def _to_partial(self) -> PartialEmoji:
        return PartialEmoji(name=self.name, animated=self.animated, id=self.id)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        for attr in self.__slots__:
            if attr[0] != '_':
                value = getattr(self, attr, None)
                if value is not None:
                    yield (attr, value)

    def __str__(self) -> str:
        if self.animated:
            return f'<a:{self.name}:{self.id}>'
        return f'<:{self.name}:{self.id}>'

    def __repr__(self) -> str:
        return f'<Emoji id={self.id} name={self.name!r} animated={self.animated} managed={self.managed}>'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _EmojiTag) and self.id == other.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the emoji's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the emoji."""
        fmt = 'gif' if self.animated else 'png'
        return f'{Asset.BASE}/emojis/{self.id}.{fmt}'

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: A :class:`list` of roles that is allowed to use this emoji.

        If roles is empty, the emoji is unrestricted.
        """
        return []  # there is no way to set roles for app emojis (yet?)

    async def delete(
        self,
    ) -> None:
        """|coro|

        Deletes the app emoji.

        Raises
        -------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_application_emoji(
            self.application_id,
            self.id,
        )

    async def edit(
        self,
        name: str = MISSING,
    ) -> Self:
        r"""|coro|

        Edits the app emoji.

        Parameters
        -----------
        name: :class:`str`
            The new emoji name.

        Raises
        -------
        Forbidden
            You are not allowed to edit emojis.
        HTTPException
            An error occurred editing the emoji.

        Returns
        --------
        :class:`AppEmoji`
            The newly updated emoji.
        """

        payload: Dict[str, Any] = {}
        if name is not MISSING:
            payload['name'] = name

        data = await self._state.http.edit_application_emoji(
            application_id=self.application_id,
            emoji_id=self.id,
            payload=payload,
        )
        return self.__class__(application_id=self.application_id, state=self._state, data=data)
