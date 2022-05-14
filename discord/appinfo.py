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

from typing import Collection, List, TYPE_CHECKING, Literal, Optional

from . import utils
from .asset import Asset
from .enums import ApplicationType, ApplicationVerificationState, RPCApplicationState, StoreApplicationState, try_enum
from .flags import ApplicationFlags
from .mixins import Hashable
from .object import Object
from .permissions import Permissions
from .user import User

if TYPE_CHECKING:
    from .abc import Snowflake, User as abcUser
    from .guild import Guild
    from .types.appinfo import (
        AppInfo as AppInfoPayload,
        PartialAppInfo as PartialAppInfoPayload,
        Team as TeamPayload,
    )
    from .state import ConnectionState

__all__ = (
    'ApplicationBot',
    'ApplicationCompany',
    'ApplicationExecutable',
    'Application',
    'PartialApplication',
    'InteractionApplication',
)

MISSING = utils.MISSING


class ApplicationBot(User):
    """Represents a bot attached to an application.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: :class:`Application`
        The application that the bot is attached to.
    public: :class:`bool`
        Whether the bot can be invited by anyone or if it is locked
        to the application owner.
    require_code_grant: :class:`bool`
        Whether the bot requires the completion of the full OAuth2 code
        grant flow to join.
    """

    __slots__ = ('public', 'require_code_grant')

    def __init__(self, *, data, state: ConnectionState, application: Application):
        super().__init__(state=state, data=data)
        self.application = application
        self.public: bool = data['public']
        self.require_code_grant: bool = data['require_code_grant']

    async def reset_token(self) -> None:
        """|coro|

        Resets the bot's token.

        Raises
        ------
        HTTPException
            Resetting the token failed.

        Returns
        -------
        :class:`str`
            The new token.
        """
        data = await self._state.http.reset_token(self.application.id)
        return data['token']

    async def edit(
        self,
        *,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
    ) -> None:
        """|coro|

        Edits the bot.

        Parameters
        -----------
        public: :class:`bool`
            Whether the bot is public or not.
        require_code_grant: :class:`bool`
            Whether the bot requires a code grant or not.

        Raises
        ------
        Forbidden
            You are not allowed to edit this bot.
        HTTPException
            Editing the bot failed.
        """
        payload = {}
        if public is not MISSING:
            payload['bot_public'] = public
        if require_code_grant is not MISSING:
            payload['bot_require_code_grant'] = require_code_grant

        data = await self._state.http.edit_application(self.application.id, payload=payload)
        self.public = data.get('bot_public', True)
        self.require_code_grant = data.get('bot_require_code_grant', False)
        self.application._update(data)


class ApplicationCompany(Hashable):
    """Represents a developer or publisher of an application.

    .. container:: operations

        .. describe:: x == y

            Checks if two companies are equal.

        .. describe:: x != y

            Checks if two companies are not equal.

        .. describe:: hash(x)

            Return the company's hash.

        .. describe:: str(x)

            Returns the company's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The company's ID.
    name: :class:`str`
        The company's name.
    application: Union[:class:`PartialApplication`, :class:`Application`]
        The application that the company developed or published.
    """

    __slots__ = (
        'id',
        'name',
        'application',
    )

    def __init__(self, *, data: dict, application: PartialApplication):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.application = application

    def __str__(self) -> str:
        return self.name


class ApplicationExecutable:
    """Represents an application executable.

    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The name of the executable.
    os: :class:`str`
        The operating system the executable is for.
    launcher: :class:`bool`
        Whether the executable is a launcher or not.
    application: Union[:class:`PartialApplication`, :class:`Application`]
        The application that the executable is for.
    """

    __slots__ = (
        'name',
        'os',
        'launcher',
        'application',
    )

    def __init__(self, *, data: dict, application: PartialApplication):
        self.name: str = data['name']
        self.os: Literal['win32', 'linux', 'darwin'] = data['os']
        self.launcher: bool = data['is_launcher']
        self.application = application


class PartialApplication(Hashable):
    """Represents a partial Application.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the application's hash.

        .. describe:: str(x)

            Returns the application's name.

    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    description: :class:`str`
        The application description.
    rpc_origins: List[:class:`str`]
        A list of RPC origin URLs, if RPC is enabled.
    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's `GetTicket <https://discord.com/developers/docs/game-sdk/applications#getticket>`_.
    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.
    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.
    public: :class:`bool`
        Whether the integration can be invited by anyone or if it is locked
        to the application owner.
    require_code_grant: :class:`bool`
        Whether the integration requires the completion of the full OAuth2 code
        grant flow to join
    max_participants: Optional[:class:`int`]
        The max number of people that can participate in the activity.
        Only available for embedded activities.
    premium_tier_level: Optional[:class:`int`]
        The required premium tier level to launch the activity.
        Only available for embedded activities.
    type: :class:`ApplicationType`
        The type of application.
    tags: List[:class:`str`]
        A list of tags that describe the application.
    overlay: :class:`bool`
        Whether the application has a Discord overlay or not.
    aliases: List[:class:`str`]
        A list of aliases that can be used to identify the application. Only available for specific applications.
    developers: List[:class:`ApplicationCompany`]
        A list of developers that developed the application. Only available for specific applications.
    publishers: List[:class:`ApplicationCompany`]
        A list of publishers that published the application. Only available for specific applications.
    executables: List[:class:`ApplicationExecutable`]
        A list of executables that are the application's. Only available for specific applications.
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
        '_splash',
        'public',
        'require_code_grant',
        'type',
        'hook',
        'premium_tier_level',
        'tags',
        'max_participants',
        'install_url',
        'overlay',
        'overlay_compatibility_hook',
        'aliases',
        'developers',
        'publishers',
        'executables',
    )

    def __init__(self, *, state: ConnectionState, data: PartialAppInfoPayload):
        self._state: ConnectionState = state
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def _update(self, data: PartialAppInfoPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins') or []
        self.verify_key: str = data['verify_key']

        self.developers: List[ApplicationCompany] = [
            ApplicationCompany(data=d, application=self) for d in data.get('developers', [])
        ]
        self.publishers: List[ApplicationCompany] = [
            ApplicationCompany(data=d, application=self) for d in data.get('publishers', [])
        ]
        self.executables: List[ApplicationExecutable] = [
            ApplicationExecutable(data=e, application=self) for e in data.get('executables', [])
        ]
        self.aliases: List[str] = data.get('aliases', [])

        self._icon: Optional[str] = data.get('icon')
        self._cover_image: Optional[str] = data.get('cover_image')
        self._splash: Optional[str] = data.get('splash')

        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')
        self._flags: int = data.get('flags', 0)
        self.type: ApplicationType = try_enum(ApplicationType, data.get('type'))
        self.hook: bool = data.get('hook', False)
        self.max_participants: Optional[int] = data.get('max_participants')
        self.premium_tier_level: Optional[int] = data.get('embedded_activity_config', {}).get('activity_premium_tier_level')
        self.tags: List[str] = data.get('tags', [])
        self.overlay: bool = data.get('overlay', False)
        self.overlay_compatibility_hook: bool = data.get('overlay_compatibility_hook', False)

        install_params = data.get('install_params', {})
        self.install_url = (
            data.get('custom_install_url')
            if not install_params
            else utils.oauth_url(
                self.id,
                permissions=Permissions(int(install_params.get('permissions', 0))),
                scopes=install_params.get('scopes', utils.MISSING),
            )
        )

        self.public: bool = data.get(
            'integration_public', data.get('bot_public', True)
        )  # The two seem to be used interchangeably?
        self.require_code_grant: bool = data.get(
            'integration_require_code_grant', data.get('bot_require_code_grant', False)
        )  # Same here

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
        """Optional[:class:`.Asset`]: Retrieves the cover image on a store embed, if any.

        This is only available if the application is a game sold on Discord.
        """
        if self._cover_image is None:
            return None
        return Asset._from_cover_image(self._state, self.id, self._cover_image)

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's splash asset, if any."""
        if self._splash is None:
            return None
        return Asset._from_application_asset(self._state, self.id, self._splash)

    @property
    def flags(self) -> ApplicationFlags:
        """:class:`ApplicationFlags`: The flags of this application."""
        return ApplicationFlags._from_value(self._flags)


class Application(PartialApplication):
    """Represents application info for an application you own.

    .. versionadded:: 2.0

    Attributes
    -------------
    owner: :class:`abc.User`
        The application owner.
    team: Optional[:class:`Team`]
        The application's team.
    bot: Optional[:class:`ApplicationBot`]
        The bot attached to the application, if any.
    guild_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the guild to which it has been linked to.
    primary_sku_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the id of the "Game SKU" that is created,
        if it exists.
    slug: Optional[:class:`str`]
        If this application is a game sold on Discord,
        this field will be the URL slug that links to the store page.
    interactions_endpoint_url: Optional[:class:`str`]
        The URL interactions will be sent to, if set.
    redirect_uris: List[:class:`str`]
        A list of redirect URIs authorized for this application.
    verification_state: :class:`ApplicationVerificationState`
        The verification state of the application.
    store_application_state: :class:`StoreApplicationState`
        The approval state of the commerce application.
    rpc_application_state: :class:`RPCApplicationState`
        The approval state of the RPC usage application.
    """

    __slots__ = (
        'owner',
        'team',
        'guild_id',
        'primary_sku_id',
        'slug',
        'redirect_uris',
        'bot',
        'verification_state',
        'store_application_state',
        'rpc_application_state',
        'interactions_endpoint_url',
    )

    def _update(self, data: AppInfoPayload) -> None:
        super()._update(data)
        from .team import Team

        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.redirect_uris: List[str] = data.get('redirect_uris', [])
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.slug: Optional[str] = data.get('slug')
        self.interactions_endpoint_url: Optional[str] = data.get('interactions_endpoint_url')

        self.verification_state = try_enum(ApplicationVerificationState, data['verification_state'])
        self.store_application_state = try_enum(StoreApplicationState, data.get('store_application_state', 1))
        self.rpc_application_state = try_enum(RPCApplicationState, data.get('rpc_application_state', 0))

        state = self._state
        team: Optional[TeamPayload] = data.get('team')
        self.team: Optional[Team] = Team(state, team) if team else None

        if bot := data.get('bot'):
            bot['public'] = data.get('bot_public', self.public)
            bot['require_code_grant'] = data.get('bot_require_code_grant', self.require_code_grant)
        self.bot: Optional[ApplicationBot] = ApplicationBot(data=bot, state=state, application=self) if bot else None

        owner = data.get('owner')
        if owner is not None:
            self.owner: abcUser = state.create_user(owner)
        else:
            self.owner: abcUser = state.user  # type: ignore # state.user will always be present here

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'description={self.description!r} public={self.public} '
            f'owner={self.owner!r}>'
        )

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: If this application is a game sold on Discord,
        this field will be the guild to which it has been linked.
        """
        return self._state._get_guild(self.guild_id)

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        icon: Optional[bytes] = MISSING,
        cover_image: Optional[bytes] = MISSING,
        tags: Collection[str] = MISSING,
        terms_of_service_url: Optional[str] = MISSING,
        privacy_policy_url: Optional[str] = MISSING,
        interactions_endpoint_url: Optional[str] = MISSING,
        redirect_uris: Collection[str] = MISSING,
        rpc_origins: Collection[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
        flags: ApplicationFlags = MISSING,
        team: Snowflake = MISSING,
    ) -> None:
        """|coro|

        Edits the application.

        Parameters
        -----------
        name: :class:`str`
            The name of the application.
        description: :class:`str`
            The description of the application.
        icon: Optional[:class:`bytes`]
            The icon of the application.
        cover_image: Optional[:class:`bytes`]
            The cover image of the application.
        tags: List[:class:`str`]
            A list of tags that describe the application.
        terms_of_service_url: Optional[:class:`str`]
            The URL to the terms of service of the application.
        privacy_policy_url: Optional[:class:`str`]
            The URL to the privacy policy of the application.
        interactions_endpoint_url: Optional[:class:`str`]
            The URL interactions will be sent to, if set.
        redirect_uris: List[:class:`str`]
            A list of redirect URIs authorized for this application.
        rpc_origins: List[:class:`str`]
            A list of RPC origins authorized for this application.
        public: :class:`bool`
            Whether the application is public or not.
        require_code_grant: :class:`bool`
            Whether the application requires a code grant or not.
        flags: :class:`ApplicationFlags`
            The flags of the application.
        team: :class:`~abc.Snowflake`
            The team to transfer the application to.

        Raises
        -------
        Forbidden
            You do not have permissions to edit this application.
        HTTPException
            Editing the application failed.
        """
        payload = {}
        if name is not MISSING:
            payload['name'] = name or ''
        if description is not MISSING:
            payload['description'] = description or ''
        if icon is not MISSING:
            if icon is not None:
                payload['icon'] = utils._bytes_to_base64_data(icon)
            else:
                payload['icon'] = ''
        if cover_image is not MISSING:
            if cover_image is not None:
                payload['cover_image'] = utils._bytes_to_base64_data(cover_image)
            else:
                payload['cover_image'] = ''
        if tags is not MISSING:
            payload['tags'] = tags
        if terms_of_service_url is not MISSING:
            payload['terms_of_service_url'] = terms_of_service_url or ''
        if privacy_policy_url is not MISSING:
            payload['privacy_policy_url'] = privacy_policy_url or ''
        if interactions_endpoint_url is not MISSING:
            payload['interactions_endpoint_url'] = interactions_endpoint_url or ''
        if redirect_uris is not MISSING:
            payload['redirect_uris'] = redirect_uris
        if rpc_origins is not MISSING:
            payload['rpc_origins'] = rpc_origins
        if public is not MISSING:
            payload['integration_public'] = public
        if require_code_grant is not MISSING:
            payload['integration_require_code_grant'] = require_code_grant
        if flags is not MISSING:
            payload['flags'] = flags.value

        if team is not MISSING:
            await self._state.http.transfer_application(self.id, team.id)

        data = await self._state.http.edit_application(self.id, payload)

        self._update(data)

    async def reset_secret(self) -> str:
        """|coro|

        Resets the application's secret.

        Raises
        ------
        Forbidden
            You do not have permissions to reset the secret.
        HTTPException
            Resetting the secret failed.

        Returns
        -------
        :class:`str`
            The new secret.
        """
        data = await self._state.http.reset_secret(self.id)
        return data['secret']  # type: ignore # Usually not there

    async def create_bot(self) -> ApplicationBot:
        """|coro|

        Creates a bot attached to this application.

        Raises
        ------
        Forbidden
            You do not have permissions to create bots.
        HTTPException
            Creating the bot failed.

        Returns
        -------
        :class:`ApplicationBot`
            The newly created bot.
        """
        state = self._state
        data = await state.http.botify_app(self.id)

        data['public'] = self.public
        data['require_code_grant'] = self.require_code_grant

        bot = ApplicationBot(data=data, state=state, application=self)
        self.bot = bot
        return bot


class InteractionApplication(Hashable):
    """Represents a very partial Application received in interaction contexts.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the application's hash.

        .. describe:: str(x)

            Returns the application's name.

    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    bot: :class:`User`
        The bot attached to the application.
    description: Optional[:class:`str`]
        The application description.
    type: Optional[:class:`ApplicationType`]
        The type of application.
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        'description',
        '_icon',
        'type',
        'bot',
    )

    def __init__(self, *, state: ConnectionState, data: dict):
        self._state: ConnectionState = state
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def _update(self, data: dict) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data.get('description') or ''
        self._icon: Optional[str] = data.get('icon')
        self.type: Optional[ApplicationType] = try_enum(ApplicationType, data['type']) if 'type' in data else None

        self.bot: User  # User data should always be available, but these payloads are volatile
        user = data.get('bot')
        if user is not None:
            self.bot = self._state.create_user(user)
        else:
            self.bot = Object(id=self.id)  # type: ignore

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='app')
