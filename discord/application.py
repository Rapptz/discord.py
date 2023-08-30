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

from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Collection, List, Mapping, Optional, Sequence, Tuple, Union, overload
from urllib.parse import quote

from . import utils
from .asset import Asset, AssetMixin
from .entitlements import Entitlement, GiftBatch
from .enums import (
    ApplicationAssetType,
    ApplicationBuildStatus,
    ApplicationDiscoverabilityState,
    ApplicationMembershipState,
    ApplicationType,
    ApplicationVerificationState,
    Distributor,
    EmbeddedActivityLabelType,
    EmbeddedActivityOrientation,
    EmbeddedActivityPlatform,
    EmbeddedActivityReleasePhase,
    Locale,
    OperatingSystem,
    RPCApplicationState,
    StoreApplicationState,
    UserFlags,
    try_enum,
)
from .flags import ApplicationDiscoveryFlags, ApplicationFlags
from .mixins import Hashable
from .object import OLDEST_OBJECT, Object
from .permissions import Permissions
from .store import SKU, StoreAsset, StoreListing, SystemRequirements
from .team import Team
from .user import User, _UserTag
from .utils import _bytes_to_base64_data, _parse_localizations

if TYPE_CHECKING:
    from datetime import date

    from typing_extensions import Self

    from .abc import Snowflake, SnowflakeTime
    from .enums import SKUAccessLevel, SKUFeature, SKUGenre, SKUType
    from .file import File
    from .guild import Guild
    from .metadata import MetadataObject
    from .state import ConnectionState
    from .store import ContentRating
    from .types.application import (
        EULA as EULAPayload,
        Achievement as AchievementPayload,
        ActivityStatistics as ActivityStatisticsPayload,
        Application as ApplicationPayload,
        ApplicationExecutable as ApplicationExecutablePayload,
        ApplicationInstallParams as ApplicationInstallParamsPayload,
        Asset as AssetPayload,
        BaseApplication as BaseApplicationPayload,
        Branch as BranchPayload,
        Build as BuildPayload,
        Company as CompanyPayload,
        EmbeddedActivityConfig as EmbeddedActivityConfigPayload,
        EmbeddedActivityPlatform as EmbeddedActivityPlatformValues,
        EmbeddedActivityPlatformConfig as EmbeddedActivityPlatformConfigPayload,
        GlobalActivityStatistics as GlobalActivityStatisticsPayload,
        InteractionsVersion,
        Manifest as ManifestPayload,
        ManifestLabel as ManifestLabelPayload,
        PartialApplication as PartialApplicationPayload,
        ThirdPartySKU as ThirdPartySKUPayload,
        UnverifiedApplication as UnverifiedApplicationPayload,
        WhitelistedUser as WhitelistedUserPayload,
    )
    from .types.user import PartialUser as PartialUserPayload

__all__ = (
    'Company',
    'EULA',
    'Achievement',
    'ThirdPartySKU',
    'EmbeddedActivityPlatformConfig',
    'EmbeddedActivityConfig',
    'ApplicationBot',
    'ApplicationExecutable',
    'ApplicationInstallParams',
    'ApplicationAsset',
    'ApplicationActivityStatistics',
    'ManifestLabel',
    'Manifest',
    'ApplicationBuild',
    'ApplicationBranch',
    'ApplicationTester',
    'PartialApplication',
    'Application',
    'IntegrationApplication',
    'UnverifiedApplication',
)

MISSING = utils.MISSING


class Company(Hashable):
    """Represents a Discord company. This is usually the developer or publisher of an application.

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
    """

    __slots__ = ('id', 'name')

    def __init__(self, data: CompanyPayload):
        self.id: int = int(data['id'])
        self.name: str = data['name']

    def __repr__(self) -> str:
        return f'<Company id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name


class EULA(Hashable):
    """Represents the EULA for an application.

    This is usually found on applications that are a game.

    .. container:: operations

        .. describe:: x == y

            Checks if two EULAs are equal.

        .. describe:: x != y

            Checks if two EULAs are not equal.

        .. describe:: hash(x)

            Returns the EULA's hash.

        .. describe:: str(x)

            Returns the EULA's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The EULA's ID.
    name: :class:`str`
        The EULA's name.
    content: :class:`str`
        The EULA's content.
    """

    __slots__ = ('id', 'name', 'content')

    def __init__(self, data: EULAPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.content: str = data['content']

    def __repr__(self) -> str:
        return f'<EULA id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name


class Achievement(Hashable):
    """Represents a Discord application achievement.

    .. container:: operations

        .. describe:: x == y

            Checks if two achievements are equal.

        .. describe:: x != y

            Checks if two achievements are not equal.

        .. describe:: hash(x)

            Return the achievement's hash.

        .. describe:: str(x)

            Returns the achievement's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The achievement's ID.
    name: :class:`str`
        The achievement's name.
    name_localizations: Dict[:class:`Locale`, :class:`str`]
        The achievement's name localized to other languages, if available.
    description: :class:`str`
        The achievement's description.
    description_localizations: Dict[:class:`Locale`, :class:`str`]
        The achievement's description localized to other languages, if available.
    application_id: :class:`int`
        The application ID that the achievement belongs to.
    secure: :class:`bool`
        Whether the achievement is secure.
    secret: :class:`bool`
        Whether the achievement is secret.
    """

    __slots__ = (
        'id',
        'name',
        'name_localizations',
        'description',
        'description_localizations',
        'application_id',
        'secure',
        'secret',
        '_icon',
        '_state',
    )

    if TYPE_CHECKING:
        name: str
        name_localizations: dict[Locale, str]
        description: str
        description_localizations: dict[Locale, str]

    def __init__(self, *, data: AchievementPayload, state: ConnectionState):
        self._state = state
        self._update(data)

    def _update(self, data: AchievementPayload):
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.secure: bool = data.get('secure', False)
        self.secret: bool = data.get('secret', False)
        self._icon = data.get('icon', data.get('icon_hash'))

        self.name, self.name_localizations = _parse_localizations(data, 'name')
        self.description, self.description_localizations = _parse_localizations(data, 'description')

    def __repr__(self) -> str:
        return f'<Achievement id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def icon(self) -> Asset:
        """:class:`Asset`: Returns the achievement's icon."""
        return Asset._from_achievement_icon(self._state, self.application_id, self.id, self._icon)

    async def edit(
        self,
        *,
        name: str = MISSING,
        name_localizations: Mapping[Locale, str] = MISSING,
        description: str = MISSING,
        description_localizations: Mapping[Locale, str] = MISSING,
        icon: bytes = MISSING,
        secure: bool = MISSING,
        secret: bool = MISSING,
    ) -> None:
        """|coro|

        Edits the achievement.

        All parameters are optional.

        Parameters
        -----------
        name: :class:`str`
            The achievement's name.
        name_localizations: Mapping[:class:`Locale`, :class:`str`]
            The achievement's name localized to other languages.
        description: :class:`str`
            The achievement's description.
        description_localizations: Mapping[:class:`Locale`, :class:`str`]
            The achievement's description localized to other languages.
        icon: :class:`bytes`
            A :term:`py:bytes-like object` representing the new icon.
        secure: :class:`bool`
            Whether the achievement is secure.
        secret: :class:`bool`
            Whether the achievement is secret.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the achievement.
        HTTPException
            Editing the achievement failed.
        """
        payload = {}
        if secure is not MISSING:
            payload['secure'] = secure
        if secret is not MISSING:
            payload['secret'] = secret
        if icon is not MISSING:
            payload['icon'] = utils._bytes_to_base64_data(icon)

        if name is not MISSING or name_localizations is not MISSING:
            localizations = (name_localizations or {}) if name_localizations is not MISSING else self.name_localizations
            payload['name'] = {'default': name or self.name, 'localizations': {str(k): v for k, v in localizations.items()}}
        if description is not MISSING or description_localizations is not MISSING:
            localizations = (
                (name_localizations or {}) if description_localizations is not MISSING else self.description_localizations
            )
            payload['description'] = {
                'default': description or self.description,
                'localizations': {str(k): v for k, v in localizations.items()},
            }

        data = await self._state.http.edit_achievement(self.application_id, self.id, payload)
        self._update(data)

    async def update(self, user: Snowflake, percent_complete: int) -> None:
        """|coro|

        Updates the achievement progress for a specific user.

        Parameters
        -----------
        user: :class:`User`
            The user to update the achievement for.
        percent_complete: :class:`int`
            The percent complete for the achievement.

        Raises
        -------
        Forbidden
            You do not have permissions to update the achievement.
        HTTPException
            Updating the achievement failed.
        """
        await self._state.http.update_user_achievement(self.application_id, self.id, user.id, percent_complete)

    async def delete(self):
        """|coro|

        Deletes the achievement.

        Raises
        -------
        Forbidden
            You do not have permissions to delete the achievement.
        HTTPException
            Deleting the achievement failed.
        """
        await self._state.http.delete_achievement(self.application_id, self.id)


class ThirdPartySKU:
    """Represents an application's primary SKU on third-party platforms.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: Union[:class:`PartialApplication`, :class:`IntegrationApplication`]
        The application that the SKU belongs to.
    distributor: :class:`Distributor`
        The distributor of the SKU.
    id: Optional[:class:`str`]
        The product ID.
    sku_id: Optional[:class:`str`]
        The SKU ID.
    """

    __slots__ = ('application', 'distributor', 'id', 'sku_id')

    def __init__(self, *, data: ThirdPartySKUPayload, application: Union[PartialApplication, IntegrationApplication]):
        self.application = application
        self.distributor: Distributor = try_enum(Distributor, data['distributor'])
        self.id: Optional[str] = data.get('id') or None
        self.sku_id: Optional[str] = data.get('sku_id') or None

    def __repr__(self) -> str:
        return f'<ThirdPartySKU distributor={self.distributor!r} id={self.id!r} sku_id={self.sku_id!r}>'

    @property
    def _id(self) -> str:
        return self.id or self.sku_id or ''

    @property
    def url(self) -> Optional[str]:
        """:class:`str`: Returns the URL of the SKU, if available.

        .. versionadded:: 2.1
        """
        if not self._id:
            return

        if self.distributor == Distributor.discord:
            return f'https://discord.com/store/skus/{self._id}'
        elif self.distributor == Distributor.steam:
            return f'https://store.steampowered.com/app/{self._id}'
        elif self.distributor == Distributor.epic_games:
            return f'https://store.epicgames.com/en-US/p/{self.application.name.replace(" ", "-")}'
        elif self.distributor == Distributor.google_play:
            return f'https://play.google.com/store/apps/details?id={self._id}'


class EmbeddedActivityPlatformConfig:
    """Represents an application's embedded activity configuration for a specific platform.

    .. versionadded:: 2.1

    Attributes
    -----------
    platform: :class:`EmbeddedActivityPlatform`
        The platform that the configuration is for.
    label_type: :class:`EmbeddedActivityLabelType`
        The current label shown on the activity.
    label_until: Optional[:class:`datetime.datetime`]
        When the current label expires.
    release_phase: :class:`EmbeddedActivityReleasePhase`
        The current release phase of the activity.
    """

    __slots__ = ('platform', 'label_type', 'label_until', 'release_phase')

    def __init__(
        self,
        platform: EmbeddedActivityPlatform,
        *,
        label_type: EmbeddedActivityLabelType = EmbeddedActivityLabelType.none,
        label_until: Optional[datetime] = None,
        release_phase: EmbeddedActivityReleasePhase = EmbeddedActivityReleasePhase.global_launch,
    ):
        self.platform = platform
        self.label_type = label_type
        self.label_until = label_until
        self.release_phase = release_phase

    @classmethod
    def from_data(cls, *, data: EmbeddedActivityPlatformConfigPayload, platform: EmbeddedActivityPlatformValues) -> Self:
        return cls(
            try_enum(EmbeddedActivityPlatform, platform),
            label_type=try_enum(EmbeddedActivityLabelType, data.get('label_type', 0)),
            label_until=utils.parse_time(data.get('label_until')),
            release_phase=try_enum(EmbeddedActivityReleasePhase, data.get('release_phase', 'global_launch')),
        )

    def __repr__(self) -> str:
        return (
            f'<EmbeddedActivityPlatformConfig platform={self.platform!r} label_type={self.label_type!r} '
            f'label_until={self.label_until!r} release_phase={self.release_phase!r}>'
        )

    def to_dict(self) -> EmbeddedActivityPlatformConfigPayload:
        return {
            'label_type': self.label_type.value,
            'label_until': self.label_until.isoformat() if self.label_until else None,
            'release_phase': self.release_phase.value,
        }


class EmbeddedActivityConfig:
    """Represents an application's embedded activity configuration.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: :class:`PartialApplication`
        The application that the configuration is for.
    supported_platforms: List[:class:`EmbeddedActivityPlatform`]
        A list of platforms that the activity supports.
    platform_configs: List[:class:`EmbeddedActivityPlatformConfig`]
        A list of configurations for each supported activity platform.

        .. versionadded:: 2.1
    orientation_lock_state: :class:`EmbeddedActivityOrientation`
        The mobile orientation lock state of the activity.
    tablet_orientation_lock_state: :class:`EmbeddedActivityOrientation`
        The mobile orientation lock state of the activity on tablets.
    premium_tier_requirement: :class:`int`
        The guild premium tier required to use the activity.
    requires_age_gate: :class:`bool`
        Whether the activity should be blocked from underage users.
    shelf_rank: :class:`int`
        The sorting rank of the activity in the activity shelf.
    free_period_starts_at: Optional[:class:`datetime.datetime`]
        When the activity's free availability period starts.
    free_period_ends_at: Optional[:class:`datetime.datetime`]
        When the activity's free availability period ends.
    """

    __slots__ = (
        'application',
        'supported_platforms',
        'platform_configs',
        'orientation_lock_state',
        'tablet_orientation_lock_state',
        'premium_tier_requirement',
        'requires_age_gate',
        'shelf_rank',
        'free_period_starts_at',
        'free_period_ends_at',
        '_preview_video_asset_id',
    )

    def __init__(self, *, data: EmbeddedActivityConfigPayload, application: PartialApplication) -> None:
        self.application: PartialApplication = application
        self._update(data)

    def __repr__(self) -> str:
        return f'<EmbeddedActivityConfig supported_platforms={self.supported_platforms!r} orientation_lock_state={self.orientation_lock_state!r} tablet_orientation_lock_state={self.tablet_orientation_lock_state!r} premium_tier_requirement={self.premium_tier_requirement!r} requires_age_gate={self.requires_age_gate!r}>'

    def _update(self, data: EmbeddedActivityConfigPayload) -> None:
        self.supported_platforms: List[EmbeddedActivityPlatform] = [
            try_enum(EmbeddedActivityPlatform, platform) for platform in data.get('supported_platforms', [])
        ]
        self.platform_configs: List[EmbeddedActivityPlatformConfig] = [
            EmbeddedActivityPlatformConfig.from_data(platform=platform, data=config)
            for platform, config in data.get('client_platform_config', {}).items()
        ]
        self.orientation_lock_state: EmbeddedActivityOrientation = try_enum(
            EmbeddedActivityOrientation, data.get('default_orientation_lock_state', 0)
        )
        self.tablet_orientation_lock_state: EmbeddedActivityOrientation = try_enum(
            EmbeddedActivityOrientation, data.get('tablet_default_orientation_lock_state', 0)
        )
        self.premium_tier_requirement: int = data.get('premium_tier_requirement') or 0
        self.requires_age_gate: bool = data.get('requires_age_gate', False)
        self.shelf_rank: int = data.get('shelf_rank', 0)
        self.free_period_starts_at: Optional[datetime] = utils.parse_time(data.get('free_period_starts_at'))
        self.free_period_ends_at: Optional[datetime] = utils.parse_time(data.get('free_period_ends_at'))
        self._preview_video_asset_id = utils._get_as_snowflake(data, 'preview_video_asset_id')

    @property
    def preview_video_asset(self) -> Optional[ApplicationAsset]:
        """Optional[:class:`ApplicationAsset`]: The preview video asset of the activity, if available."""
        if self._preview_video_asset_id is None:
            return None
        return ApplicationAsset._from_embedded_activity_config(self.application, self._preview_video_asset_id)

    async def edit(
        self,
        *,
        supported_platforms: Collection[EmbeddedActivityPlatform] = MISSING,
        platform_configs: Collection[EmbeddedActivityPlatformConfig] = MISSING,
        orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        tablet_orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        requires_age_gate: bool = MISSING,
        shelf_rank: int = MISSING,
        free_period_starts_at: Optional[datetime] = MISSING,
        free_period_ends_at: Optional[datetime] = MISSING,
        preview_video_asset: Optional[Snowflake] = MISSING,
    ) -> None:
        """|coro|

        Edits the application's embedded activity configuration.

        Parameters
        -----------
        supported_platforms: List[:class:`EmbeddedActivityPlatform`]
            A list of platforms that the activity supports.
        platform_configs: List[:class:`EmbeddedActivityPlatformConfig`]
            A list of configurations for each supported activity platform.

            .. versionadded:: 2.1
        orientation_lock_state: :class:`EmbeddedActivityOrientation`
            The mobile orientation lock state of the activity.
        tablet_orientation_lock_state: :class:`EmbeddedActivityOrientation`
            The mobile orientation lock state of the activity on tablets.
        requires_age_gate: :class:`bool`
            Whether the activity should be blocked from underage users.
        shelf_rank: :class:`int`
            The sorting rank of the activity in the activity shelf.
        free_period_starts_at: Optional[:class:`datetime.datetime`]
            When the activity's free availability period starts.
        free_period_ends_at: Optional[:class:`datetime.datetime`]
            When the activity's free availability period ends.
        preview_video_asset: Optional[:class:`ApplicationAsset`]
            The preview video asset of the activity.

        Raises
        -------
        Forbidden
            You are not allowed to edit this application's configuration.
        HTTPException
            Editing the configuration failed.
        """
        data = await self.application._state.http.edit_embedded_activity_config(
            self.application.id,
            supported_platforms=[str(x) for x in (supported_platforms)] if supported_platforms is not MISSING else None,
            platform_config={c.platform.value: c.to_dict() for c in (platform_configs)}
            if platform_configs is not MISSING
            else None,
            orientation_lock_state=int(orientation_lock_state) if orientation_lock_state is not MISSING else None,
            tablet_orientation_lock_state=int(tablet_orientation_lock_state)
            if tablet_orientation_lock_state is not MISSING
            else None,
            requires_age_gate=requires_age_gate if requires_age_gate is not MISSING else None,
            shelf_rank=shelf_rank if shelf_rank is not MISSING else None,
            free_period_starts_at=free_period_starts_at.isoformat() if free_period_starts_at else None,
            free_period_ends_at=free_period_ends_at.isoformat() if free_period_ends_at else None,
            preview_video_asset_id=(preview_video_asset.id if preview_video_asset else None)
            if preview_video_asset is not MISSING
            else MISSING,
        )
        self._update(data)


class ApplicationBot(User):
    """Represents a bot attached to an application.

    .. container:: operations

        .. describe:: x == y

            Checks if two bots are equal.

        .. describe:: x != y

            Checks if two bots are not equal.

        .. describe:: hash(x)

            Return the bot's hash.

        .. describe:: str(x)

            Returns the bot's name with discriminator.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: :class:`Application`
        The application that the bot is attached to.
    """

    __slots__ = ('application',)

    def __init__(self, *, data: PartialUserPayload, state: ConnectionState, application: Application):
        super().__init__(state=state, data=data)
        self.application = application

    def _update(self, data: PartialUserPayload) -> None:
        super()._update(data)

    def __repr__(self) -> str:
        return f'<ApplicationBot id={self.id} name={self.name!r} discriminator={self.discriminator!r} public={self.public} require_code_grant={self.require_code_grant}>'

    @property
    def public(self) -> bool:
        """:class:`bool`: Whether the bot can be invited by anyone or if it is locked to the application owner."""
        return self.application.public

    @property
    def require_code_grant(self) -> bool:
        """:class:`bool`: Whether the bot requires the completion of the full OAuth2 code grant flow to join."""
        return self.application.require_code_grant

    @property
    def disabled(self) -> bool:
        """:class:`bool`: Whether the bot is disabled by Discord.

        .. versionadded:: 2.1
        """
        return self.application.disabled

    @property
    def quarantined(self) -> bool:
        """:class:`bool`: Whether the bot is quarantined by Discord.

        Quarantined bots cannot join more guilds or start new direct messages.

        .. versionadded:: 2.1
        """
        return self.application.quarantined

    @property
    def bio(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the bot's 'about me' section."""
        return self.application.description or None

    @property
    def mfa_enabled(self) -> bool:
        """:class:`bool`: Whether the bot has MFA turned on and working. This follows the bot owner's value."""
        if self.application.owner.public_flags.team_user:
            return True
        return self._state.user.mfa_enabled  # type: ignore # user is always present at this point

    @property
    def verified(self) -> bool:
        """:class:`bool`: Whether the bot's email has been verified. This follows the bot owner's value."""
        # Not possible to have a bot without a verified email
        return True

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[bytes] = MISSING,
        bio: Optional[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
    ) -> None:
        """|coro|

        Edits the bot.

        All parameters are optional.

        Parameters
        -----------
        username: :class:`str`
            The new username you wish to change the bot to.
        avatar: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar.
        bio: Optional[:class:`str`]
            The bot's 'about me' section. This is just the application description.
            Could be ``None`` to represent no 'about me'.
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
        if username is not MISSING:
            payload['username'] = username
        if avatar is not MISSING:
            if avatar is not None:
                payload['avatar'] = _bytes_to_base64_data(avatar)
            else:
                payload['avatar'] = None

        if payload:
            data = await self._state.http.edit_bot(self.application.id, payload)
            self._update(data)
            payload = {}

        if public is not MISSING:
            payload['bot_public'] = public
        if require_code_grant is not MISSING:
            payload['bot_require_code_grant'] = require_code_grant
        if bio is not MISSING:
            payload['description'] = bio

        if payload:
            data = await self._state.http.edit_application(self.application.id, payload)
            self.application._update(data)

    async def token(self) -> str:
        """|coro|

        Gets the bot's token.

        This revokes all previous tokens.

        Raises
        ------
        Forbidden
            You are not allowed to reset the token.
        HTTPException
            Resetting the token failed.

        Returns
        -------
        :class:`str`
            The new token.
        """
        data = await self._state.http.reset_bot_token(self.application.id)
        return data['token']


class ApplicationExecutable:
    """Represents an application executable.

    .. container:: operations

        .. describe:: str(x)

            Returns the executable's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The name of the executable.
    os: :class:`OperatingSystem`
        The operating system the executable is for.

        .. versionchanged:: 2.1

            The type of this attribute has changed to :class:`OperatingSystem`.
    launcher: :class:`bool`
        Whether the executable is a launcher or not.
    application: :class:`PartialApplication`
        The application that the executable is for.
    """

    __slots__ = (
        'name',
        'os',
        'launcher',
        'application',
    )

    def __init__(self, *, data: ApplicationExecutablePayload, application: PartialApplication):
        self.name: str = data['name']
        self.os: OperatingSystem = OperatingSystem.from_string(data['os'])
        self.launcher: bool = data['is_launcher']
        self.application = application

    def __repr__(self) -> str:
        return f'<ApplicationExecutable name={self.name!r} os={self.os!r} launcher={self.launcher!r}>'

    def __str__(self) -> str:
        return self.name


class ApplicationInstallParams:
    """Represents an application's authorization parameters.

    .. container:: operations

        .. describe:: str(x)

            Returns the authorization URL.

    .. versionadded:: 2.0

    Attributes
    ----------
    application_id: :class:`int`
        The ID of the application to be authorized.
    scopes: List[:class:`str`]
        The list of :ddocs:`OAuth2 scopes <topics/oauth2#shared-resources-oauth2-scopes>` to add the application with.
    permissions: :class:`Permissions`
        The permissions to grant to the added bot.
    """

    __slots__ = ('application_id', 'scopes', 'permissions')

    def __init__(
        self, application_id: int, *, scopes: Optional[Collection[str]] = None, permissions: Optional[Permissions] = None
    ):
        self.application_id: int = application_id
        self.scopes: List[str] = [scope for scope in scopes] if scopes else ['bot', 'applications.commands']
        self.permissions: Permissions = permissions or Permissions(0)

    @classmethod
    def from_application(cls, application: Snowflake, data: ApplicationInstallParamsPayload) -> ApplicationInstallParams:
        return cls(
            application.id,
            scopes=data.get('scopes', []),
            permissions=Permissions(int(data.get('permissions', 0))),
        )

    def __repr__(self) -> str:
        return f'<ApplicationInstallParams application_id={self.application_id} scopes={self.scopes!r} permissions={self.permissions!r}>'

    def __str__(self) -> str:
        return self.url

    @property
    def url(self) -> str:
        """:class:`str`: The URL to add the application with the parameters."""
        return utils.oauth_url(self.application_id, permissions=self.permissions, scopes=self.scopes)

    def to_dict(self) -> dict:
        return {
            'scopes': self.scopes,
            'permissions': self.permissions.value,
        }


class ApplicationAsset(AssetMixin, Hashable):
    """Represents an application asset.

    .. container:: operations

        .. describe:: x == y

            Checks if two assets are equal.

        .. describe:: x != y

            Checks if two assets are not equal.

        .. describe:: hash(x)

            Return the asset's hash.

        .. describe:: str(x)

            Returns the asset's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: Union[:class:`PartialApplication`, :class:`IntegrationApplication`]
        The application that the asset is for.
    id: :class:`int`
        The asset's ID.
    name: :class:`str`
        The asset's name.
    """

    __slots__ = ('_state', 'id', 'name', 'type', 'application')

    def __init__(self, *, data: AssetPayload, application: Union[PartialApplication, IntegrationApplication]) -> None:
        self._state: ConnectionState = application._state
        self.application = application
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.type: ApplicationAssetType = try_enum(ApplicationAssetType, data.get('type', 1))

    def __repr__(self) -> str:
        return f'<ApplicationAsset id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @classmethod
    def _from_embedded_activity_config(
        cls, application: Union[PartialApplication, IntegrationApplication], id: int
    ) -> ApplicationAsset:
        return cls(data={'id': id, 'name': '', 'type': 1}, application=application)

    @property
    def animated(self) -> bool:
        """:class:`bool`: Indicates if the asset is animated. Here for compatibility purposes."""
        return False

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the asset."""
        return f'{Asset.BASE}/app-assets/{self.application.id}/{self.id}.png'

    async def delete(self) -> None:
        """|coro|

        Deletes the asset.

        Raises
        ------
        Forbidden
            You are not allowed to delete this asset.
        HTTPException
            Deleting the asset failed.
        """
        await self._state.http.delete_asset(self.application.id, self.id)


class ApplicationActivityStatistics:
    """Represents an application's activity usage statistics for a particular user.

    .. versionadded:: 2.0

    Attributes
    -----------
    application_id: :class:`int`
        The ID of the application.
    user_id: :class:`int`
        The ID of the user.
    duration: :class:`int`
        How long the user has ever played the game in seconds.
    sku_duration: :class:`int`
        How long the user has ever played the game on Discord in seconds.
    updated_at: :class:`datetime.datetime`
        When the user last played the game.
    """

    __slots__ = ('application_id', 'user_id', 'duration', 'sku_duration', 'updated_at', '_state')

    def __init__(
        self,
        *,
        data: Union[ActivityStatisticsPayload, GlobalActivityStatisticsPayload],
        state: ConnectionState,
        application_id: Optional[int] = None,
    ) -> None:
        self._state = state
        self.application_id = application_id or int(data['application_id'])  # type: ignore
        self.user_id: int = int(data['user_id']) if 'user_id' in data else state.self_id  # type: ignore
        self.duration: int = data.get('total_duration', data.get('duration', 0))
        self.sku_duration: int = data.get('total_discord_sku_duration', 0)
        self.updated_at: datetime = utils.parse_time(data.get('last_played_at', data.get('updated_at'))) or utils.utcnow()

    def __repr__(self) -> str:
        return f'<ApplicationActivityStatistics user_id={self.user_id} duration={self.duration} last_played_at={self.updated_at!r}>'

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`User`]: Returns the user associated with the statistics, if available."""
        return self._state.get_user(self.user_id)

    async def application(self) -> PartialApplication:
        """|coro|

        Returns the application associated with the statistics.

        Raises
        ------
        HTTPException
            Fetching the application failed.
        """
        state = self._state
        data = await state.http.get_partial_application(self.application_id)
        return PartialApplication(state=state, data=data)


class ManifestLabel(Hashable):
    """Represents an application manifest label.

    .. container:: operations

        .. describe:: x == y

            Checks if two manifest labels are equal.

        .. describe:: x != y

            Checks if two manifest labels are not equal.

        .. describe:: hash(x)

            Return the manifest label's hash.

        .. describe:: str(x)

            Returns the manifest label's name.

    .. versionadded:: 2.0

    Attributes
    ------------
    id: :class:`int`
        The ID of the label.
    application_id: :class:`int`
        The ID of the application the label is for.
    name: :class:`str`
        The name of the label.
    """

    __slots__ = ('id', 'application_id', 'name')

    def __new__(cls, *, data: ManifestLabelPayload, application_id: Optional[int] = None) -> Union[ManifestLabel, int]:
        if data.get('name') is None:
            return int(data['id'])
        if application_id is not None:
            data['application_id'] = application_id
        return super().__new__(cls)

    def __init__(self, *, data: ManifestLabelPayload, **kwargs) -> None:
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.name: Optional[str] = data.get('name')

    def __repr__(self) -> str:
        return f'<ManifestLabel id={self.id} application_id={self.application_id} name={self.name!r}>'


class Manifest(Hashable):
    """Represents an application manifest.

    .. container:: operations

        .. describe:: x == y

            Checks if two manifests are equal.

        .. describe:: x != y

            Checks if two manifests are not equal.

        .. describe:: hash(x)

            Return the manifest's hash.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The ID of the manifest.
    application_id: :class:`int`
        The ID of the application the manifest is for.
    label_id: :class:`int`
        The ID of the manifest's label.
    label: Optional[:class:`ManifestLabel`]
        The manifest's label, if available.
    redistributable_label_ids: List[:class:`int`]
        The label IDs of the manifest's redistributables, if available.
    url: Optional[:class:`str`]
        The URL of the manifest.
    """

    __slots__ = ('id', 'application_id', 'label_id', 'label', 'redistributable_label_ids', 'url', '_state')

    if TYPE_CHECKING:
        label_id: int
        label: Optional[ManifestLabel]

    def __init__(self, *, data: ManifestPayload, state: ConnectionState, application_id: int) -> None:
        self._state = state
        self.id: int = int(data['id'])
        self.application_id = application_id
        self.redistributable_label_ids: List[int] = [int(r) for r in data.get('redistributable_label_ids', [])]
        self.url: Optional[str] = data.get('url')

        label = ManifestLabel(data=data['label'], application_id=application_id)
        if isinstance(label, int):
            self.label_id = label
            self.label = None
        else:
            self.label_id = label.id
            self.label = label

    def __repr__(self) -> str:
        return f'<Manifest id={self.id} application_id={self.application_id} label_id={self.label_id}>'

    async def upload(self, manifest: MetadataObject, /) -> None:
        """|coro|

        Uploads the manifest object to the manifest.

        .. note::

            This should only be used for builds with a status of :attr:`ApplicationBuildStatus.uploading`.

            Additionally, it requires that :attr:`url` is set to the uploadable URL
            (populated on uploadable manifest objects returned from :meth:`ApplicationBranch.create_build`).

        Parameters
        -----------
        manifest: Mapping[:class:`str`, Any]
            A dict-like object representing the manifest to upload.

        Raises
        -------
        ValueError
            Upload URL is not set.
        Forbidden
            Upload URL invalid.
        HTTPException
            Uploading the manifest failed.
        """
        if not self.url:
            raise ValueError('Manifest URL is not set')
        await self._state.http.upload_to_cloud(self.url, utils._to_json(dict(manifest)))


class ApplicationBuild(Hashable):
    """Represents a build of an :class:`ApplicationBranch`.

    .. container:: operations

        .. describe:: x == y

            Checks if two builds are equal.

        .. describe:: x != y

            Checks if two builds are not equal.

        .. describe:: hash(x)

            Return the build's hash.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The build ID.
    application_id: :class:`int`
        The ID of the application the build belongs to.
    branch: :class:`ApplicationBranch`
        The branch the build belongs to.
    created_at: :class:`datetime.datetime`
        When the build was created.
    status: :class:`ApplicationBuildStatus`
        The status of the build.
    source_build_id: Optional[:class:`int`]
        The ID of the source build, if any.
    version: Optional[:class:`str`]
        The version of the build, if any.
    """

    def __init__(self, *, data: BuildPayload, state: ConnectionState, branch: ApplicationBranch) -> None:
        self._state = state
        self.branch = branch
        self._update(data)

    def _update(self, data: BuildPayload) -> None:
        state = self._state

        self.id: int = int(data['id'])
        self.application_id: int = self.branch.application_id
        self.created_at: datetime = (
            utils.parse_time(data['created_at']) if 'created_at' in data else utils.snowflake_time(self.id)
        )
        self.status: ApplicationBuildStatus = try_enum(ApplicationBuildStatus, data['status'])
        self.source_build_id: Optional[int] = utils._get_as_snowflake(data, 'source_build_id')
        self.version: Optional[str] = data.get('version')
        self.manifests: List[Manifest] = [
            Manifest(data=m, state=state, application_id=self.application_id) for m in data.get('manifests', [])
        ]

    def __repr__(self) -> str:
        return f'<ApplicationBuild id={self.id} application_id={self.application_id} status={self.status!r}>'

    @staticmethod
    def format_download_url(
        endpoint: str, application_id, branch_id, build_id, manifest_id, user_id, expires: int, signature: str
    ) -> str:
        return f'{endpoint}/apps/{application_id}/builds/{build_id}/manifests/{manifest_id}/metadata/MANIFEST?branch_id={branch_id}&manifest_id={manifest_id}&user_id={user_id}&expires={expires}&signature={quote(signature)}'

    async def size(self, manifests: Collection[Snowflake] = MISSING) -> float:
        """|coro|

        Retrieves the storage space used by the build.

        Parameters
        -----------
        manifests: List[:class:`Manifest`]
            The manifests to fetch the storage space for.
            Defaults to all the build's manifests.

        Raises
        -------
        HTTPException
            Fetching the storage space failed.

        Returns
        --------
        :class:`float`
            The storage space used by the build in kilobytes.
        """
        data = await self._state.http.get_branch_build_size(
            self.application_id, self.branch.id, self.id, [m.id for m in manifests or self.manifests]
        )
        return float(data['size_kb'])

    async def download_urls(self, manifest_labels: Collection[Snowflake] = MISSING) -> List[str]:
        """|coro|

        Retrieves the download URLs of the build.

        These download URLs are for the manifest metadata, which can be used to download the artifacts.

        .. note::

            The download URLs are signed and valid for roughly 7 days.

        Parameters
        -----------
        manifest_labels: List[:class:`ManifestLabel`]
            The manifest labels to fetch the download URLs for.
            Defaults to all the build's manifest labels.

        Raises
        -------
        NotFound
            The build was not found or you are not entitled to it.
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Fetching the download URLs failed.

        Returns
        --------
        List[:class:`str`]
            The download URLs of the build.
        """
        state = self._state
        app_id, branch_id, build_id, user_id = self.application_id, self.branch.id, self.id, state.self_id
        data = await state.http.get_branch_build_download_signatures(
            app_id,
            branch_id,
            build_id,
            [m.id for m in manifest_labels] if manifest_labels else list({m.label_id for m in self.manifests}),
        )
        return [
            self.format_download_url(v['endpoint'], app_id, branch_id, build_id, k, user_id, v['expires'], v['signature'])
            for k, v in data.items()
        ]

    async def edit(self, status: ApplicationBuildStatus) -> None:
        """|coro|

        Edits the build.

        Parameters
        -----------
        status: :class:`ApplicationBuildStatus`
            The new status of the build.

        Raises
        -------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Editing the build failed.
        """
        await self._state.http.edit_build(self.application_id, self.id, str(status))
        self.status = try_enum(ApplicationBuildStatus, str(status))

    async def upload_files(self, *files: File, hash: bool = True) -> None:
        r"""|coro|

        Uploads files to the build.

        .. note::

            This should only be used for builds with a status of :attr:`ApplicationBuildStatus.uploading`.

        .. warning::

            This does not account for chunking large files.

        Parameters
        -----------
        \*files: :class:`discord.File`
            The files to upload.
        hash: :class:`bool`
            Whether to calculate the MD5 hash of the files before upload.

        Raises
        -------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Uploading the files failed.
        """
        if not files:
            return

        urls = await self._state.http.get_build_upload_urls(self.application_id, self.id, files, hash)
        id_files = {f.filename: f for f in files}
        for url in urls:
            file = id_files.get(url['id'])
            if file:
                await self._state.http.upload_to_cloud(url['url'], file, file.b64_md5 if hash else None)

    async def publish(self) -> None:
        """|coro|

        Publishes the build.

        This can only be done on builds with an :attr:`status` of :attr:`ApplicationBuildStatus.ready`.

        Raises
        -------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Publishing the build failed.
        """
        await self._state.http.publish_build(self.application_id, self.branch.id, self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the build.

        Raises
        -------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Deleting the build failed.
        """
        await self._state.http.delete_build(self.application_id, self.id)


class ApplicationBranch(Hashable):
    """Represents an application branch.

    .. container:: operations

        .. describe:: x == y

            Checks if two branches are equal.

        .. describe:: x != y

            Checks if two branches are not equal.

        .. describe:: hash(x)

            Return the branch's hash.

        .. describe:: str(x)

            Returns the branch's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The branch ID.
    application_id: :class:`int`
        The ID of the application the branch belongs to.
    live_build_id: Optional[:class:`int`]
        The ID of the live build, if it exists and is provided.
    name: :class:`str`
        The branch name, if known.
    """

    __slots__ = ('id', 'live_build_id', 'name', 'application_id', '_created_at', '_state')

    def __init__(self, *, data: BranchPayload, state: ConnectionState, application_id: int) -> None:
        self._state = state
        self.application_id = application_id

        self.id: int = int(data['id'])
        self.name: str = data['name'] if 'name' in data else ('master' if self.id == self.application_id else 'unknown')
        self.live_build_id: Optional[int] = utils._get_as_snowflake(data, 'live_build_id')
        self._created_at = data.get('created_at')

    def __repr__(self) -> str:
        return f'<ApplicationBranch id={self.id} name={self.name!r} live_build_id={self.live_build_id!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the branch's creation time in UTC.

        .. note::

            This may be inaccurate for the master branch if the data is not provided,
            as the ID is shared with the application ID.
        """
        return utils.parse_time(self._created_at) if self._created_at else utils.snowflake_time(self.id)

    def is_master(self) -> bool:
        """:class:`bool`: Indicates if this is the master branch."""
        return self.id == self.application_id

    async def builds(self) -> List[ApplicationBuild]:
        """|coro|

        Retrieves the builds of the branch.

        Raises
        ------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Fetching the builds failed.
        """
        data = await self._state.http.get_branch_builds(self.application_id, self.id)
        return [ApplicationBuild(data=build, state=self._state, branch=self) for build in data]

    async def fetch_build(self, build_id: int, /) -> ApplicationBuild:
        """|coro|

        Retrieves a build of the branch with the given ID.

        Parameters
        -----------
        build_id: :class:`int`
            The ID of the build to fetch.

        Raises
        ------
        NotFound
            The build does not exist.
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Fetching the build failed.
        """
        data = await self._state.http.get_branch_build(self.application_id, self.id, build_id)
        return ApplicationBuild(data=data, state=self._state, branch=self)

    async def fetch_live_build_id(self) -> Optional[int]:
        """|coro|

        Retrieves and caches the ID of the live build of the branch.

        Raises
        ------
        HTTPException
            Fetching the build failed.

        Returns
        --------
        Optional[:class:`int`]
            The ID of the live build, if it exists.
        """
        data = await self._state.http.get_build_ids((self.id,))
        if not data:
            return
        branch = data[0]
        self.live_build_id = build_id = utils._get_as_snowflake(branch, 'live_build_id')
        return build_id

    async def live_build(self, *, locale: Locale = MISSING, platform: str) -> ApplicationBuild:
        """|coro|

        Retrieves the live build of the branch.

        Parameters
        -----------
        locale: :class:`Locale`
            The locale to fetch the build for. Defaults to the current user locale.
        platform: :class:`str`
            The platform to fetch the build for.
            Usually one of ``win32``, ``win64``, ``macos``, or ``linux``.

        Raises
        ------
        NotFound
            The branch does not have a live build.
        HTTPException
            Fetching the build failed.
        """
        state = self._state
        data = await state.http.get_live_branch_build(
            self.application_id, self.id, str(locale) if locale else state.locale, str(platform)
        )
        self.live_build_id = int(data['id'])
        return ApplicationBuild(data=data, state=self._state, branch=self)

    async def latest_build(self) -> ApplicationBuild:
        """|coro|

        Retrieves the latest successful build of the branch.

        Raises
        ------
        NotFound
            The branch does not have a successful build.
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Fetching the build failed.
        """
        data = await self._state.http.get_latest_branch_build(self.application_id, self.id)
        return ApplicationBuild(data=data, state=self._state, branch=self)

    async def create_build(
        self,
        *,
        built_with: str = "DISPATCH",
        manifests: Sequence[MetadataObject],
        source_build: Optional[Snowflake] = None,
    ) -> Tuple[ApplicationBuild, List[Manifest]]:
        """|coro|

        Creates a build for the branch.

        Parameters
        -----------
        manifests: List[Mapping[:class:`str`, Any]]
            A list of dict-like objects representing the manifests.
        source_build: Optional[:class:`ApplicationBuild`]
            The source build of the build, if any.

        Raises
        ------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Creating the build failed.

        Returns
        --------
        Tuple[:class:`ApplicationBuild`, List[:class:`Manifest`]]
            The created build and manifest uploads.
        """
        state = self._state
        app_id = self.application_id
        payload = {'built_with': built_with, 'manifests': [dict(m) for m in manifests]}
        if source_build:
            payload['source_build_id'] = source_build.id

        data = await state.http.create_branch_build(app_id, self.id, payload)
        build = ApplicationBuild(data=data['build'], state=state, branch=self)
        manifest_uploads = [Manifest(data=m, state=state, application_id=app_id) for m in data['manifest_uploads']]
        return build, manifest_uploads

    async def promote(self, branch: Snowflake, /) -> None:
        """|coro|

        Promotes this branch's live build to the given branch.

        Parameters
        -----------
        branch: :class:`ApplicationBranch`
            The target branch to promote the build to.

        Raises
        ------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Promoting the branch failed.
        """
        await self._state.http.promote_build(self.application_id, self.id, branch.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the branch.

        Raises
        ------
        Forbidden
            You are not allowed to manage this application.
        HTTPException
            Deleting the branch failed.
        """
        await self._state.http.delete_app_branch(self.application_id, self.id)


class ApplicationTester(User):
    """Represents a user whitelisted for an application.

    .. container:: operations

        .. describe:: x == y

            Checks if two testers are equal.

        .. describe:: x != y

            Checks if two testers are not equal.

        .. describe:: hash(x)

            Return the tester's hash.

        .. describe:: str(x)

            Returns the tester's name with discriminator.

    .. versionadded:: 2.0

    Attributes
    -------------
    application: :class:`Application`
        The application the tester is whitelisted for.
    state: :class:`ApplicationMembershipState`
        The state of the tester (i.e. invited or accepted)
    """

    __slots__ = ('application', 'state')

    def __init__(self, application: Application, state: ConnectionState, data: WhitelistedUserPayload):
        self.application: Application = application
        self.state: ApplicationMembershipState = try_enum(ApplicationMembershipState, data['state'])
        super().__init__(state=state, data=data['user'])

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'discriminator={self.discriminator!r} state={self.state!r}>'
        )

    async def remove(self) -> None:
        """|coro|

        Removes the user from the whitelist.

        Raises
        -------
        HTTPException
            Removing the user failed.
        """
        await self._state.http.delete_app_whitelist(self.application.id, self.id)


class PartialApplication(Hashable):
    """Represents a partial Application.

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the application's hash.

        .. describe:: str(x)

            Returns the application's name.

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

        .. versionchanged:: 2.1

            The type of this attribute has changed to Optional[List[:class:`str`]].
    verify_key: :class:`str`
        The hex encoded key for verification in interactions and the
        GameSDK's :ddocs:`GetTicket <game-sdk/applications#getticket`.
    terms_of_service_url: Optional[:class:`str`]
        The application's terms of service URL, if set.
    privacy_policy_url: Optional[:class:`str`]
        The application's privacy policy URL, if set.
    deeplink_uri: Optional[:class:`str`]
        The application's deeplink URI, if set.

        .. versionadded:: 2.1
    public: :class:`bool`
        Whether the integration can be invited by anyone or if it is locked
        to the application owner.
    require_code_grant: :class:`bool`
        Whether the integration requires the completion of the full OAuth2 code
        grant flow to join
    max_participants: Optional[:class:`int`]
        The max number of people that can participate in the activity.
        Only available for embedded activities.
    type: Optional[:class:`ApplicationType`]
        The type of application.
    tags: List[:class:`str`]
        A list of tags that describe the application.
    overlay: :class:`bool`
        Whether the application has a Discord overlay or not.
    guild_id: Optional[:class:`int`]
        The ID of the guild the application is attached to, if any.
    primary_sku_id: Optional[:class:`int`]
        The application's primary SKU ID, if any.
        This can be an application's game SKU, subscription SKU, etc.
    store_listing_sku_id: Optional[:class:`int`]
        The application's store listing SKU ID, if any.
        If exists, this SKU ID should be used for checks.
    slug: Optional[:class:`str`]
        The slug for the application's primary SKU, if any.
    eula_id: Optional[:class:`int`]
        The ID of the EULA for the application, if any.
    aliases: List[:class:`str`]
        A list of aliases that can be used to identify the application.
    developers: List[:class:`Company`]
        A list of developers that developed the application.
    publishers: List[:class:`Company`]
        A list of publishers that published the application.
    executables: List[:class:`ApplicationExecutable`]
        A list of executables that are the application's.
    third_party_skus: List[:class:`ThirdPartySKU`]
        A list of third party platforms the SKU is available at.
    custom_install_url: Optional[:class:`str`]
        The custom URL to use for authorizing the application, if specified.
    install_params: Optional[:class:`ApplicationInstallParams`]
        The parameters to use for authorizing the application, if specified.
    embedded_activity_config: Optional[:class:`EmbeddedActivityConfig`]
        The application's embedded activity configuration, if any.
    owner: Optional[:class:`User`]
        The application owner. This may be a team user account.

        .. note::

            In almost all cases, this is not available for partial applications.
    team: Optional[:class:`Team`]
        The team that owns the application.

        .. note::

            In almost all cases, this is not available.
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
        'deeplink_uri',
        '_icon',
        '_flags',
        '_cover_image',
        '_splash',
        'public',
        'require_code_grant',
        'type',
        'hook',
        'tags',
        'max_participants',
        'overlay',
        'overlay_warn',
        'overlay_compatibility_hook',
        'aliases',
        'developers',
        'publishers',
        'executables',
        'third_party_skus',
        'custom_install_url',
        'install_params',
        'embedded_activity_config',
        'guild_id',
        'primary_sku_id',
        'store_listing_sku_id',
        'slug',
        'eula_id',
        'owner',
        'team',
        '_guild',
        '_has_bot',
    )

    if TYPE_CHECKING:
        owner: Optional[User]
        team: Optional[Team]

    def __init__(self, *, state: ConnectionState, data: PartialApplicationPayload):
        self._state: ConnectionState = state
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def _update(self, data: PartialApplicationPayload) -> None:
        state = self._state

        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.rpc_origins: Optional[List[str]] = data.get('rpc_origins')
        self.verify_key: str = data['verify_key']

        self.aliases: List[str] = data.get('aliases', [])
        self.developers: List[Company] = [Company(data=d) for d in data.get('developers', [])]
        self.publishers: List[Company] = [Company(data=d) for d in data.get('publishers', [])]
        self.executables: List[ApplicationExecutable] = [
            ApplicationExecutable(data=e, application=self) for e in data.get('executables', [])
        ]
        self.third_party_skus: List[ThirdPartySKU] = [
            ThirdPartySKU(data=t, application=self) for t in data.get('third_party_skus', [])
        ]

        self._icon: Optional[str] = data.get('icon')
        self._cover_image: Optional[str] = data.get('cover_image')
        self._splash: Optional[str] = data.get('splash')

        self.terms_of_service_url: Optional[str] = data.get('terms_of_service_url')
        self.privacy_policy_url: Optional[str] = data.get('privacy_policy_url')
        self.deeplink_uri: Optional[str] = data.get('deeplink_uri')
        self._flags: int = data.get('flags', 0)
        self.type: Optional[ApplicationType] = try_enum(ApplicationType, data['type']) if data.get('type') else None
        self.hook: bool = data.get('hook', False)
        self.max_participants: Optional[int] = data.get('max_participants')
        self.tags: List[str] = data.get('tags', [])
        self.overlay: bool = data.get('overlay', False)
        self.overlay_warn: bool = data.get('overlay_warn', False)
        self.overlay_compatibility_hook: bool = data.get('overlay_compatibility_hook', False)
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.store_listing_sku_id: Optional[int] = utils._get_as_snowflake(data, 'store_listing_sku_id')
        self.slug: Optional[str] = data.get('slug')
        self.eula_id: Optional[int] = utils._get_as_snowflake(data, 'eula_id')

        params = data.get('install_params')
        self.custom_install_url: Optional[str] = data.get('custom_install_url')
        self.install_params: Optional[ApplicationInstallParams] = (
            ApplicationInstallParams.from_application(self, params) if params else None
        )
        self.embedded_activity_config: Optional[EmbeddedActivityConfig] = (
            EmbeddedActivityConfig(data=data['embedded_activity_config'], application=self)
            if 'embedded_activity_config' in data
            else None
        )

        self.public: bool = data.get('integration_public', data.get('bot_public', True))
        self.require_code_grant: bool = data.get('integration_require_code_grant', data.get('bot_require_code_grant', False))
        self._has_bot: bool = 'bot_public' in data
        self._guild: Optional[Guild] = state.create_guild(data['guild']) if 'guild' in data else None

        # Hacky, but I want these to be persisted

        existing = getattr(self, 'owner', None)
        owner = data.get('owner')
        self.owner = state.create_user(owner) if owner else existing

        existing = getattr(self, 'team', None)
        team = data.get('team')
        if existing and team:
            existing._update(team)
        else:
            self.team = Team(state=state, data=team) if team else existing

        if self.team and not self.owner:
            # We can create a team user from the team data
            team = self.team
            payload: PartialUserPayload = {
                'id': team.id,
                'username': f'team{team.id}',
                'global_name': None,
                'public_flags': UserFlags.team_user.value,
                'discriminator': '0000',
                'avatar': None,
            }
            self.owner = state.create_user(payload)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} description={self.description!r}>'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the application's creation time in UTC.

        .. versionadded:: 2.1
        """
        return utils.snowflake_time(self.id)

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='app')

    @property
    def cover_image(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Retrieves the application's cover image, if any."""
        if self._cover_image is None:
            return None
        return Asset._from_icon(self._state, self.id, self._cover_image, path='app')

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Retrieves the application's splash, if any.

        .. versionadded:: 2.1
        """
        if self._splash is None:
            return None
        return Asset._from_icon(self._state, self.id, self._splash, path='app')

    @property
    def flags(self) -> ApplicationFlags:
        """:class:`ApplicationFlags`: The flags of this application."""
        return ApplicationFlags._from_value(self._flags)

    @property
    def install_url(self) -> Optional[str]:
        """:class:`str`: The URL to install the application."""
        return self.custom_install_url or self.install_params.url if self.install_params else None

    @property
    def primary_sku_url(self) -> Optional[str]:
        """:class:`str`: The URL to the primary SKU of the application, if any."""
        if self.primary_sku_id:
            return f'https://discord.com/store/skus/{self.primary_sku_id}/{self.slug or "unknown"}'

    @property
    def store_listing_sku_url(self) -> Optional[str]:
        """:class:`str`: The URL to the store listing SKU of the application, if any."""
        if self.store_listing_sku_id:
            return f'https://discord.com/store/skus/{self.store_listing_sku_id}/{self.slug or "unknown"}'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild linked to the application, if any and available."""
        return self._state._get_guild(self.guild_id) or self._guild

    def has_bot(self) -> bool:
        """:class:`bool`: Whether the application has an attached bot.

        .. versionadded:: 2.1
        """
        return self._has_bot

    def is_rpc_enabled(self) -> bool:
        """:class:`bool`: Whether the application has the ability to access the client RPC server.

        .. versionadded:: 2.1
        """
        return self.rpc_origins is not None

    async def assets(self) -> List[ApplicationAsset]:
        """|coro|

        Retrieves the assets of this application.

        Raises
        ------
        HTTPException
            Retrieving the assets failed.

        Returns
        -------
        List[:class:`ApplicationAsset`]
            The application's assets.
        """
        data = await self._state.http.get_app_assets(self.id)
        return [ApplicationAsset(data=d, application=self) for d in data]

    async def published_store_listings(self, *, localize: bool = True) -> List[StoreListing]:
        """|coro|

        Retrieves all published store listings for this application.

        Parameters
        ----------
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        HTTPException
            Retrieving the listings failed.

        Returns
        -------
        List[:class:`StoreListing`]
            The store listings.
        """
        state = self._state
        data = await state.http.get_app_store_listings(self.id, country_code=state.country_code or 'US', localize=localize)
        return [StoreListing(state=state, data=d, application=self) for d in data]

    async def primary_store_listing(self, *, localize: bool = True) -> StoreListing:
        """|coro|

        Retrieves the primary store listing of this application.

        This is the public store listing of the primary SKU.

        Parameters
        -----------
        localize: :class:`bool`
            Whether to localize the store listing to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        ------
        NotFound
            The application does not have a primary SKU.
        HTTPException
            Retrieving the store listing failed.

        Returns
        -------
        :class:`StoreListing`
            The application's primary store listing, if any.
        """
        state = self._state
        data = await state.http.get_app_store_listing(self.id, country_code=state.country_code or 'US', localize=localize)
        return StoreListing(state=state, data=data, application=self)

    async def achievements(self, completed: bool = True) -> List[Achievement]:
        """|coro|

        Retrieves the achievements for this application.

        Parameters
        -----------
        completed: :class:`bool`
            Whether to only include achievements the user has completed or can access.
            This means secret achievements that are not yet unlocked will not be included.

            If ``False``, then you require access to the application.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch achievements.
        HTTPException
            Fetching the achievements failed.

        Returns
        --------
        List[:class:`Achievement`]
            The achievements retrieved.
        """
        state = self._state
        data = (await state.http.get_my_achievements(self.id)) if completed else (await state.http.get_achievements(self.id))
        return [Achievement(data=achievement, state=state) for achievement in data]

    async def entitlements(self, *, exclude_consumed: bool = True) -> List[Entitlement]:
        """|coro|

        Retrieves the entitlements this account has granted for this application.

        Parameters
        -----------
        exclude_consumed: :class:`bool`
            Whether to exclude consumed entitlements.

        Raises
        -------
        HTTPException
            Fetching the entitlements failed.

        Returns
        --------
        List[:class:`Entitlement`]
            The entitlements retrieved.
        """
        state = self._state
        data = await state.http.get_user_app_entitlements(self.id, exclude_consumed=exclude_consumed)
        return [Entitlement(data=entitlement, state=state) for entitlement in data]

    async def eula(self) -> Optional[EULA]:
        """|coro|

        Retrieves the EULA for this application.

        Raises
        -------
        HTTPException
            Retrieving the EULA failed.

        Returns
        --------
        Optional[:class:`EULA`]
            The EULA retrieved, if any.
        """
        if self.eula_id is None:
            return None

        state = self._state
        data = await state.http.get_eula(self.eula_id)
        return EULA(data=data)

    async def ticket(self) -> str:
        """|coro|

        Retrieves the license ticket for this application.

        Raises
        -------
        HTTPException
            Retrieving the ticket failed.

        Returns
        --------
        :class:`str`
            The ticket retrieved.
        """
        state = self._state
        data = await state.http.get_app_ticket(self.id)
        return data['ticket']

    async def entitlement_ticket(self) -> str:
        """|coro|

        Retrieves the entitlement ticket for this application.

        Raises
        -------
        HTTPException
            Retrieving the ticket failed.

        Returns
        --------
        :class:`str`
            The ticket retrieved.
        """
        state = self._state
        data = await state.http.get_app_entitlement_ticket(self.id)
        return data['ticket']

    async def activity_statistics(self) -> List[ApplicationActivityStatistics]:
        """|coro|

        Retrieves the activity usage statistics for this application.

        Raises
        -------
        HTTPException
            Retrieving the statistics failed.

        Returns
        --------
        List[:class:`ApplicationActivityStatistics`]
            The statistics retrieved.
        """
        state = self._state
        app_id = self.id
        data = await state.http.get_app_activity_statistics(app_id)
        return [ApplicationActivityStatistics(data=activity, state=state, application_id=app_id) for activity in data]


class Application(PartialApplication):
    """Represents application info for an application you own.

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the application's hash.

        .. describe:: str(x)

            Returns the application's name.

    .. versionadded:: 2.0

    Attributes
    -------------
    owner: :class:`User`
        The application owner. This may be a team user account.
    bot: Optional[:class:`ApplicationBot`]
        The bot attached to the application, if any.
    disabled: :class:`bool`
        Whether the bot attached to this application is disabled by Discord.

        .. versionadded:: 2.1
    quarantined: :class:`bool`
        Whether the bot attached to this application is quarantined by Discord.

        Quarantined bots cannot join more guilds or start new direct messages.

        .. versionadded:: 2.1
    interactions_endpoint_url: Optional[:class:`str`]
        The URL interactions will be sent to, if set.
    interactions_version: :class:`int`
        The interactions version to use. Different versions have different payloads and supported features.

        .. versionadded:: 2.1
    interactions_event_types: List[:class:`str`]
        The interaction event types to subscribe to.
        Requires a valid :attr:`interactions_endpoint_url` and :attr:`interactions_version` 2 or higher.

        .. versionadded:: 2.1
    role_connections_verification_url: Optional[:class:`str`]
        The application's connection verification URL which will render the application as
        a verification method in the guild's role verification configuration.
    redirect_uris: List[:class:`str`]
        A list of redirect URIs authorized for this application.
    verification_state: :class:`ApplicationVerificationState`
        The verification state of the application.
    store_application_state: :class:`StoreApplicationState`
        The approval state of the commerce application.
    rpc_application_state: :class:`RPCApplicationState`
        The approval state of the RPC usage application.
    discoverability_state: :class:`ApplicationDiscoverabilityState`
        The state of the application in the application directory.
    approximate_guild_count: :class:`int`
        The approximate number of guilds this application is in.

        .. versionadded:: 2.1
    """

    __slots__ = (
        'owner',
        'redirect_uris',
        'interactions_endpoint_url',
        'interactions_version',
        'interactions_event_types',
        'role_connections_verification_url',
        'bot',
        'disabled',
        'quarantined',
        'verification_state',
        'store_application_state',
        'rpc_application_state',
        'discoverability_state',
        '_discovery_eligibility_flags',
        'approximate_guild_count',
    )

    if TYPE_CHECKING:
        owner: User

    def __init__(self, *, state: ConnectionState, data: ApplicationPayload, team: Optional[Team] = None):
        self.team = team
        super().__init__(state=state, data=data)

    def _update(self, data: ApplicationPayload) -> None:
        super()._update(data)

        self.disabled: bool = data.get('bot_disabled', False)
        self.quarantined: bool = data.get('bot_quarantined', False)
        self.redirect_uris: List[str] = data.get('redirect_uris', [])
        self.interactions_endpoint_url: Optional[str] = data.get('interactions_endpoint_url')
        self.interactions_version: InteractionsVersion = data.get('interactions_version', 1)
        self.interactions_event_types: List[str] = data.get('interactions_event_types', [])
        self.role_connections_verification_url: Optional[str] = data.get('role_connections_verification_url')

        self.verification_state = try_enum(ApplicationVerificationState, data['verification_state'])
        self.store_application_state = try_enum(StoreApplicationState, data.get('store_application_state', 1))
        self.rpc_application_state = try_enum(RPCApplicationState, data.get('rpc_application_state', 0))
        self.discoverability_state = try_enum(ApplicationDiscoverabilityState, data.get('discoverability_state', 1))
        self._discovery_eligibility_flags = data.get('discovery_eligibility_flags', 0)
        self.approximate_guild_count: int = data.get('approximate_guild_count', 0)

        state = self._state

        # Hacky, but I want these to be persisted
        existing = getattr(self, 'bot', None)
        bot = data.get('bot')
        if existing is not None:
            existing._update(bot)
        else:
            self.bot: Optional[ApplicationBot] = ApplicationBot(data=bot, state=state, application=self) if bot else None

        self.owner = self.owner or state.user

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'description={self.description!r} public={self.public} '
            f'owner={self.owner!r}>'
        )

    @property
    def discovery_eligibility_flags(self) -> ApplicationDiscoveryFlags:
        """:class:`ApplicationDiscoveryFlags`: The directory eligibility flags for this application."""
        return ApplicationDiscoveryFlags._from_value(self._discovery_eligibility_flags)

    def has_bot(self) -> bool:
        """:class:`bool`: Whether the application has an attached bot.

        .. versionadded:: 2.1
        """
        return self.bot is not None

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        icon: Optional[bytes] = MISSING,
        cover_image: Optional[bytes] = MISSING,
        tags: Sequence[str] = MISSING,
        terms_of_service_url: Optional[str] = MISSING,
        privacy_policy_url: Optional[str] = MISSING,
        deeplink_uri: Optional[str] = MISSING,
        interactions_endpoint_url: Optional[str] = MISSING,
        interactions_version: InteractionsVersion = MISSING,
        interactions_event_types: Sequence[str] = MISSING,
        role_connections_verification_url: Optional[str] = MISSING,
        redirect_uris: Sequence[str] = MISSING,
        rpc_origins: Sequence[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
        discoverable: bool = MISSING,
        max_participants: Optional[int] = MISSING,
        flags: ApplicationFlags = MISSING,
        custom_install_url: Optional[str] = MISSING,
        install_params: Optional[ApplicationInstallParams] = MISSING,
        developers: Sequence[Snowflake] = MISSING,
        publishers: Sequence[Snowflake] = MISSING,
        guild: Snowflake = MISSING,
        team: Snowflake = MISSING,
    ) -> None:
        """|coro|

        Edits the application.

        All parameters are optional.

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
        deeplink_uri: Optional[:class:`str`]
            The deeplink URI of the application.

            .. versionadded:: 2.1
        interactions_endpoint_url: Optional[:class:`str`]
            The URL interactions will be sent to, if set.
        interactions_version: :class:`int`
            The interactions version to use. Different versions have different payloads and supported features.

            .. versionadded:: 2.1
        interactions_event_types: List[:class:`str`]
            The interaction event types to subscribe to.
            Requires a valid :attr:`interactions_endpoint_url` and :attr:`interactions_version` 2 or higher.

            .. versionadded:: 2.1
        role_connections_verification_url: Optional[:class:`str`]
            The connection verification URL for the application.

            .. versionadded:: 2.1
        redirect_uris: List[:class:`str`]
            A list of redirect URIs authorized for this application.
        rpc_origins: List[:class:`str`]
            A list of RPC origins authorized for this application.
        public: :class:`bool`
            Whether the application is public or not.
        require_code_grant: :class:`bool`
            Whether the application requires a code grant or not.
        discoverable: :class:`bool`
            Whether the application is listed in the app directory or not.

            .. versionadded:: 2.1
        max_participants: Optional[:class:`int`]
            The max number of people that can participate in the activity.
            Only available for embedded activities.

            .. versionadded:: 2.1
        flags: :class:`ApplicationFlags`
            The flags of the application.
        developers: List[:class:`Company`]
            A list of companies that are the developers of the application.
        publishers: List[:class:`Company`]
            A list of companies that are the publishers of the application.
        guild: :class:`Guild`
            The guild to transfer the application to.
        team: :class:`Team`
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
            payload['tags'] = tags or []
        if terms_of_service_url is not MISSING:
            payload['terms_of_service_url'] = terms_of_service_url or ''
        if privacy_policy_url is not MISSING:
            payload['privacy_policy_url'] = privacy_policy_url or ''
        if deeplink_uri is not MISSING:
            payload['deeplink_uri'] = deeplink_uri or ''
        if interactions_endpoint_url is not MISSING:
            payload['interactions_endpoint_url'] = interactions_endpoint_url or ''
        if interactions_version is not MISSING:
            payload['interactions_version'] = interactions_version
        if interactions_event_types is not MISSING:
            payload['interactions_event_types'] = interactions_event_types or []
        if role_connections_verification_url is not MISSING:
            payload['role_connections_verification_url'] = role_connections_verification_url or ''
        if redirect_uris is not MISSING:
            payload['redirect_uris'] = redirect_uris or []
        if rpc_origins is not MISSING:
            payload['rpc_origins'] = rpc_origins or []
        if public is not MISSING:
            if self.bot:
                payload['bot_public'] = public
            else:
                payload['integration_public'] = public
        if require_code_grant is not MISSING:
            if self.bot:
                payload['bot_require_code_grant'] = require_code_grant
            else:
                payload['integration_require_code_grant'] = require_code_grant
        if discoverable is not MISSING:
            payload['discoverability_state'] = (
                ApplicationDiscoverabilityState.discoverable.value
                if discoverable
                else ApplicationDiscoverabilityState.not_discoverable.value
            )
        if max_participants is not MISSING:
            payload['max_participants'] = max_participants
        if flags is not MISSING:
            payload['flags'] = flags.value
        if custom_install_url is not MISSING:
            payload['custom_install_url'] = custom_install_url or ''
        if install_params is not MISSING:
            payload['install_params'] = install_params.to_dict() if install_params else None
        if developers is not MISSING:
            payload['developer_ids'] = [developer.id for developer in developers or []]
        if publishers is not MISSING:
            payload['publisher_ids'] = [publisher.id for publisher in publishers or []]
        if guild:
            payload['guild_id'] = guild.id

        if team:
            await self._state.http.transfer_application(self.id, team.id)

        data = await self._state.http.edit_application(self.id, payload)
        self._update(data)

    async def fetch_bot(self) -> ApplicationBot:
        """|coro|

        Retrieves the bot attached to this application.

        Raises
        ------
        Forbidden
            You do not have permissions to fetch the bot,
            or the application does not have a bot.
        HTTPException
            Fetching the bot failed.

        Returns
        -------
        :class:`ApplicationBot`
            The bot attached to this application.
        """
        data = await self._state.http.edit_bot(self.id, {})
        if not self.bot:
            self.bot = ApplicationBot(data=data, state=self._state, application=self)
        else:
            self.bot._update(data)

        return self.bot

    async def create_bot(self) -> Optional[str]:
        """|coro|

        Creates a bot attached to this application.

        .. versionchanged:: 2.1

            This now returns the bot token (if applicable)
            instead of implicitly refetching the application
            to return the :class:`ApplicationBot`.

        Raises
        ------
        Forbidden
            You do not have permissions to create bots.
        HTTPException
            Creating the bot failed.

        Returns
        -------
        Optional[:class:`str`]
            The bot's token.
            This is only returned if a bot does not already exist.
        """
        state = self._state
        data = await state.http.botify_app(self.id)
        return data.get('token')

    async def edit_bot(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[bytes] = MISSING,
        bio: Optional[str] = MISSING,
        public: bool = MISSING,
        require_code_grant: bool = MISSING,
    ) -> ApplicationBot:
        """|coro|

        Edits the application's bot.

        All parameters are optional.

        .. versionadded:: 2.1

        Parameters
        -----------
        username: :class:`str`
            The new username you wish to change the bot to.
        avatar: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar.
        bio: Optional[:class:`str`]
            The bot's 'about me' section. This is just the application description.
            Could be ``None`` to represent no 'about me'.
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

        Returns
        --------
        :class:`ApplicationBot`
            The newly edited bot.
        """
        payload = {}
        if username is not MISSING:
            payload['username'] = username
        if avatar is not MISSING:
            if avatar is not None:
                payload['avatar'] = _bytes_to_base64_data(avatar)
            else:
                payload['avatar'] = None

        if payload or not self.bot:  # Ensure we get a bot object
            data = await self._state.http.edit_bot(self.id, payload)
            if not self.bot:
                self.bot = ApplicationBot(data=data, state=self._state, application=self)
            else:
                self.bot._update(data)
            payload = {}

        if public is not MISSING:
            payload['bot_public'] = public
        if require_code_grant is not MISSING:
            payload['bot_require_code_grant'] = require_code_grant
        if bio is not MISSING:
            payload['description'] = bio

        if payload:
            data = await self._state.http.edit_application(self.id, payload)
            self._update(data)

        return self.bot

    async def whitelisted(self) -> List[ApplicationTester]:
        """|coro|

        Retrieves the list of whitelisted users (testers) for this application.

        Raises
        ------
        Forbidden
            You do not have permissions to fetch the testers.
        HTTPException
            Fetching the testers failed.

        Returns
        -------
        List[:class:`ApplicationTester`]
            The testers for this application.
        """
        state = self._state
        data = await state.http.get_app_whitelisted(self.id)
        return [ApplicationTester(self, state, user) for user in data]

    @overload
    async def whitelist(self, user: _UserTag, /) -> ApplicationTester:
        ...

    @overload
    async def whitelist(self, user: str, /) -> ApplicationTester:
        ...

    @overload
    async def whitelist(self, username: str, discriminator: str, /) -> ApplicationTester:
        ...

    async def whitelist(self, *args: Union[_UserTag, str]) -> ApplicationTester:
        """|coro|

        Whitelists a user (adds a tester) for this application.

        This function can be used in multiple ways.

        .. code-block:: python

            # Passing a user object:
            await app.whitelist(user)

            # Passing a username
            await app.whitelist('jake')

            # Passing a legacy user:
            await app.whitelist('Jake#0001')

            # Passing a legacy username and discriminator:
            await app.whitelist('Jake', '0001')

        Parameters
        -----------
        user: Union[:class:`User`, :class:`str`]
            The user to whitelist.
        username: :class:`str`
            The username of the user to whitelist.
        discriminator: :class:`str`
            The discriminator of the user to whitelist.

        Raises
        -------
        HTTPException
            Inviting the user failed.
        TypeError
            More than 2 parameters or less than 1 parameter were passed.

        Returns
        -------
        :class:`ApplicationTester`
            The new whitelisted user.
        """
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, _UserTag):
                user = str(user)
            username, _, discrim = user.partition('#')
        elif len(args) == 2:
            username, discrim = args  # type: ignore
        else:
            raise TypeError(f'whitelist() takes 1 or 2 arguments but {len(args)} were given')

        state = self._state
        data = await state.http.add_app_whitelist(self.id, username, discrim or 0)
        return ApplicationTester(self, state, data)

    async def create_asset(
        self, name: str, image: bytes, *, type: ApplicationAssetType = ApplicationAssetType.one
    ) -> ApplicationAsset:
        """|coro|

        Uploads an asset to this application.

        Parameters
        -----------
        name: :class:`str`
            The name of the asset.
        image: :class:`bytes`
            The image of the asset. Cannot be animated.

        Raises
        -------
        Forbidden
            You do not have permissions to upload assets.
        HTTPException
            Uploading the asset failed.

        Returns
        --------
        :class:`ApplicationAsset`
            The created asset.
        """
        data = await self._state.http.create_asset(self.id, name, int(type), utils._bytes_to_base64_data(image))
        return ApplicationAsset(data=data, application=self)

    async def store_assets(self) -> List[StoreAsset]:
        """|coro|

        Retrieves the store assets for this application.

        Raises
        -------
        Forbidden
            You do not have permissions to store assets.
        HTTPException
            Storing the assets failed.

        Returns
        --------
        List[:class:`StoreAsset`]
            The store assets retrieved.
        """
        state = self._state
        data = await self._state.http.get_store_assets(self.id)
        return [StoreAsset(data=asset, state=state, parent=self) for asset in data]

    async def create_store_asset(self, file: File, /) -> StoreAsset:
        """|coro|

        Uploads a store asset to this application.

        Parameters
        -----------
        file: :class:`File`
            The file to upload. Must be a PNG, JPG, GIF, or MP4.

        Raises
        -------
        Forbidden
            You do not have permissions to upload assets.
        HTTPException
            Uploading the asset failed.

        Returns
        --------
        :class:`StoreAsset`
            The created asset.
        """
        state = self._state
        data = await state.http.create_store_asset(self.id, file)
        return StoreAsset(state=state, data=data, parent=self)

    async def skus(self, *, with_bundled_skus: bool = True, localize: bool = True) -> List[SKU]:
        """|coro|

        Retrieves the SKUs for this application.

        Parameters
        -----------
        with_bundled_skus: :class:`bool`
            Whether to include bundled SKUs in the response.
        localize: :class:`bool`
            Whether to localize the SKU name and description to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch SKUs.
        HTTPException
            Fetching the SKUs failed.

        Returns
        --------
        List[:class:`SKU`]
            The SKUs retrieved.
        """
        state = self._state
        data = await self._state.http.get_app_skus(
            self.id, country_code=state.country_code or 'US', with_bundled_skus=with_bundled_skus, localize=localize
        )
        return [SKU(data=sku, state=state, application=self) for sku in data]

    async def primary_sku(self, *, localize: bool = True) -> Optional[SKU]:
        """|coro|

        Retrieves the primary SKU for this application if it exists.

        Parameters
        -----------
        localize: :class:`bool`
            Whether to localize the SKU name and description to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch SKUs.
        HTTPException
            Fetching the SKUs failed.

        Returns
        --------
        Optional[:class:`SKU`]
            The primary SKU retrieved.
        """
        if not self.primary_sku_id:
            return None

        state = self._state
        data = await self._state.http.get_sku(
            self.primary_sku_id, country_code=state.country_code or 'US', localize=localize
        )
        return SKU(data=data, state=state, application=self)

    async def store_listing_sku(self, *, localize: bool = True) -> Optional[SKU]:
        """|coro|

        Retrieves the store listing SKU for this application if it exists.

        Parameters
        -----------
        localize: :class:`bool`
            Whether to localize the SKU name and description to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch SKUs.
        HTTPException
            Fetching the SKUs failed.

        Returns
        --------
        Optional[:class:`SKU`]
            The store listing SKU retrieved.
        """
        if not self.store_listing_sku_id:
            return None

        state = self._state
        data = await self._state.http.get_sku(
            self.store_listing_sku_id, country_code=state.country_code or 'US', localize=localize
        )
        return SKU(data=data, state=state, application=self)

    async def create_sku(
        self,
        *,
        name: str,
        name_localizations: Optional[Mapping[Locale, str]] = None,
        legal_notice: Optional[str] = None,
        legal_notice_localizations: Optional[Mapping[Locale, str]] = None,
        type: SKUType,
        price_tier: Optional[int] = None,
        price_overrides: Optional[Mapping[str, int]] = None,
        sale_price_tier: Optional[int] = None,
        sale_price_overrides: Optional[Mapping[str, int]] = None,
        dependent_sku: Optional[Snowflake] = None,
        access_level: Optional[SKUAccessLevel] = None,
        features: Optional[Collection[SKUFeature]] = None,
        locales: Optional[Collection[Locale]] = None,
        genres: Optional[Collection[SKUGenre]] = None,
        content_ratings: Optional[Collection[ContentRating]] = None,
        system_requirements: Optional[Collection[SystemRequirements]] = None,
        release_date: Optional[date] = None,
        bundled_skus: Optional[Sequence[Snowflake]] = None,
        manifest_labels: Optional[Sequence[Snowflake]] = None,
    ):
        """|coro|

        Creates a SKU for this application.

        Parameters
        -----------
        name: :class:`str`
            The SKU's name.
        name_localizations: Optional[Mapping[:class:`Locale`, :class:`str`]]
            The SKU's name localized to other languages.
        legal_notice: Optional[:class:`str`]
            The SKU's legal notice.
        legal_notice_localizations: Optional[Mapping[:class:`Locale`, :class:`str`]]
            The SKU's legal notice localized to other languages.
        type: :class:`SKUType`
            The SKU's type.
        price_tier: Optional[:class:`int`]
            The price tier of the SKU.
            This is the base price in USD that other currencies will be calculated from.
        price_overrides: Optional[Mapping[:class:`str`, :class:`int`]]
            A mapping of currency to price. These prices override the base price tier.
        sale_price_tier: Optional[:class:`int`]
            The sale price tier of the SKU.
            This is the base sale price in USD that other currencies will be calculated from.
        sale_price_overrides: Optional[Mapping[:class:`str`, :class:`int`]]
            A mapping of currency to sale price. These prices override the base sale price tier.
        dependent_sku: Optional[:class:`int`]
            The ID of the SKU that this SKU is dependent on.
        access_level: Optional[:class:`SKUAccessLevel`]
            The access level of the SKU.
        features: Optional[List[:class:`SKUFeature`]]
            A list of features of the SKU.
        locales: Optional[List[:class:`Locale`]]
            A list of locales supported by the SKU.
        genres: Optional[List[:class:`SKUGenre`]]
            A list of genres of the SKU.
        content_ratings: Optional[List[:class:`ContentRating`]]
            A list of content ratings of the SKU.
        system_requirements: Optional[List[:class:`SystemRequirements`]]
            A list of system requirements of the SKU.
        release_date: Optional[:class:`datetime.date`]
            The release date of the SKU.
        bundled_skus: Optional[List[:class:`SKU`]]
            A list SKUs that are bundled with this SKU.
        manifest_labels: Optional[List[:class:`ManifestLabel`]]
            A list of manifest labels for the SKU.

        Raises
        -------
        Forbidden
            You do not have permissions to create SKUs.
        HTTPException
            Creating the SKU failed.

        Returns
        --------
        :class:`SKU`
            The SKU created.
        """
        payload = {
            'type': int(type),
            'name': {'default': name, 'localizations': {str(k): v for k, v in (name_localizations or {}).items()}},
            'application_id': self.id,
        }
        if legal_notice or legal_notice_localizations:
            payload['legal_notice'] = {
                'default': legal_notice,
                'localizations': {str(k): v for k, v in (legal_notice_localizations or {}).items()},
            }
        if price_tier is not None:
            payload['price_tier'] = price_tier
        if price_overrides:
            payload['price'] = {str(k): v for k, v in price_overrides.items()}
        if sale_price_tier is not None:
            payload['sale_price_tier'] = sale_price_tier
        if sale_price_overrides:
            payload['sale_price'] = {str(k): v for k, v in sale_price_overrides.items()}
        if dependent_sku is not None:
            payload['dependent_sku_id'] = dependent_sku.id
        if access_level is not None:
            payload['access_level'] = int(access_level)
        if locales:
            payload['locales'] = [str(l) for l in locales]
        if features:
            payload['features'] = [int(f) for f in features]
        if genres:
            payload['genres'] = [int(g) for g in genres]
        if content_ratings:
            payload['content_ratings'] = {
                content_rating.agency: content_rating.to_dict() for content_rating in content_ratings
            }
        if system_requirements:
            payload['system_requirements'] = {
                system_requirement.os: system_requirement.to_dict() for system_requirement in system_requirements
            }
        if release_date is not None:
            payload['release_date'] = release_date.isoformat()
        if bundled_skus:
            payload['bundled_skus'] = [s.id for s in bundled_skus]
        if manifest_labels:
            payload['manifest_labels'] = [m.id for m in manifest_labels]

        state = self._state
        data = await state.http.create_sku(payload)
        return SKU(data=data, state=state, application=self)

    async def fetch_achievement(self, achievement_id: int) -> Achievement:
        """|coro|

        Retrieves an achievement for this application.

        Parameters
        -----------
        achievement_id: :class:`int`
            The ID of the achievement to fetch.

        Raises
        ------
        Forbidden
            You do not have permissions to fetch the achievement.
        HTTPException
            Fetching the achievement failed.

        Returns
        -------
        :class:`Achievement`
            The achievement retrieved.
        """
        data = await self._state.http.get_achievement(self.id, achievement_id)
        return Achievement(data=data, state=self._state)

    async def create_achievement(
        self,
        *,
        name: str,
        name_localizations: Optional[Mapping[Locale, str]] = None,
        description: str,
        description_localizations: Optional[Mapping[Locale, str]] = None,
        icon: bytes,
        secure: bool = False,
        secret: bool = False,
    ) -> Achievement:
        """|coro|

        Creates an achievement for this application.

        Parameters
        -----------
        name: :class:`str`
            The name of the achievement.
        name_localizations: Mapping[:class:`Locale`, :class:`str`]
            The localized names of the achievement.
        description: :class:`str`
            The description of the achievement.
        description_localizations: Mapping[:class:`Locale`, :class:`str`]
            The localized descriptions of the achievement.
        icon: :class:`bytes`
            The icon of the achievement.
        secure: :class:`bool`
            Whether the achievement is secure.
        secret: :class:`bool`
            Whether the achievement is secret.

        Raises
        -------
        Forbidden
            You do not have permissions to create achievements.
        HTTPException
            Creating the achievement failed.

        Returns
        --------
        :class:`Achievement`
            The created achievement.
        """
        state = self._state
        data = await state.http.create_achievement(
            self.id,
            name=name,
            name_localizations={str(k): v for k, v in name_localizations.items()} if name_localizations else None,
            description=description,
            description_localizations={str(k): v for k, v in description_localizations.items()}
            if description_localizations
            else None,
            icon=_bytes_to_base64_data(icon),
            secure=secure,
            secret=secret,
        )
        return Achievement(state=state, data=data)

    async def entitlements(
        self,
        *,
        user: Optional[Snowflake] = None,
        guild: Optional[Snowflake] = None,
        skus: Optional[List[Snowflake]] = None,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        oldest_first: bool = MISSING,
        with_payments: bool = False,
        exclude_ended: bool = False,
    ) -> AsyncIterator[Entitlement]:
        """Returns an :term:`asynchronous iterator` that enables receiving this application's entitlements.

        Examples
        ---------

        Usage ::

            counter = 0
            async for entitlement in application.entitlements(limit=200, user=client.user):
                if entitlement.consumed:
                    counter += 1

        Flattening into a list: ::

            entitlements = [entitlement async for entitlement in application.entitlements(limit=123)]
            # entitlements is now a list of Entitlement...

        All parameters are optional.

        Parameters
        -----------
        user: Optional[:class:`User`]
            The user to retrieve entitlements for.
        guild: Optional[:class:`Guild`]
            The guild to retrieve entitlements for.
        skus: Optional[List[:class:`SKU`]]
            The SKUs to retrieve entitlements for.
        limit: Optional[:class:`int`]
            The number of payments to retrieve.
            If ``None``, retrieves every entitlement the application has. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entitlements before this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entitlements after this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        oldest_first: :class:`bool`
            If set to ``True``, return entitlements in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.
        with_payments: :class:`bool`
            Whether to include partial payment info in the response.
        exclude_ended: :class:`bool`
            Whether to exclude entitlements that have ended.

        Raises
        ------
        HTTPException
            The request to get payments failed.

        Yields
        -------
        :class:`Entitlement`
            The entitlement retrieved.
        """

        _state = self._state

        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await _state.http.get_app_entitlements(
                self.id,
                limit=retrieve,
                after=after_id,
                user_id=user.id if user else None,
                guild_id=guild.id if guild else None,
                sku_ids=[sku.id for sku in skus] if skus else None,
                with_payments=with_payments,
                exclude_ended=exclude_ended,
            )

            if data:
                if limit is not None:
                    limit -= len(data)

                after = Object(id=int(data[0]['id']))

            return data, after, limit

        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await _state.http.get_app_entitlements(
                self.id,
                limit=retrieve,
                before=before_id,
                user_id=user.id if user else None,
                guild_id=guild.id if guild else None,
                sku_ids=[sku.id for sku in skus] if skus else None,
                with_payments=with_payments,
                exclude_ended=exclude_ended,
            )
            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[-1]['id']))

            return data, before, limit

        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))

        if oldest_first in (MISSING, None):
            reverse = after is not None
        else:
            reverse = oldest_first

        after = after or OLDEST_OBJECT
        predicate = None

        if reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda m: int(m['id']) > after.id

        while True:
            retrieve = min(100 if limit is None else limit, 100)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            # Terminate loop on next iteration; there's no data left after this
            if len(data) < 100:
                limit = 0

            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)

            for entitlement in data:
                yield Entitlement(data=entitlement, state=_state)

    async def fetch_entitlement(self, entitlement_id: int, /) -> Entitlement:
        """|coro|

        Retrieves an entitlement from this application.

        Parameters
        -----------
        entitlement_id: :class:`int`
            The ID of the entitlement to fetch.

        Raises
        ------
        HTTPException
            Fetching the entitlement failed.

        Returns
        -------
        :class:`Entitlement`
            The entitlement retrieved.
        """
        state = self._state
        data = await state.http.get_app_entitlement(self.id, entitlement_id)
        return Entitlement(data=data, state=state)

    async def gift_batches(self) -> List[GiftBatch]:
        """|coro|

        Retrieves the gift batches for this application.

        Raises
        ------
        HTTPException
            Fetching the gift batches failed.

        Returns
        -------
        List[:class:`GiftBatch`]
            The gift batches retrieved.
        """
        state = self._state
        app_id = self.id
        data = await state.http.get_gift_batches(app_id)
        return [GiftBatch(data=batch, state=state, application_id=app_id) for batch in data]

    async def create_gift_batch(
        self,
        sku: Snowflake,
        *,
        amount: int,
        description: str,
        entitlement_branches: Optional[List[Snowflake]] = None,
        entitlement_starts_at: Optional[date] = None,
        entitlement_ends_at: Optional[date] = None,
    ) -> GiftBatch:
        """|coro|

        Creates a gift batch for the specified SKU.

        Parameters
        -----------
        sku: :class:`SKU`
            The SKU to create the gift batch for.
        amount: :class:`int`
            The amount of gifts to create in the batch.
        description: :class:`str`
            The description of the gift batch.
        entitlement_branches: List[:class:`ApplicationBranch`]
            The branches to grant in the gifts.
        entitlement_starts_at: :class:`datetime.date`
            When the entitlement is valid from.
        entitlement_ends_at: :class:`datetime.date`
            When the entitlement is valid until.

        Raises
        ------
        Forbidden
            You do not have permissions to create a gift batch.
        HTTPException
            Creating the gift batch failed.

        Returns
        -------
        :class:`GiftBatch`
            The gift batch created.
        """
        state = self._state
        app_id = self.id
        data = await state.http.create_gift_batch(
            app_id,
            sku.id,
            amount,
            description,
            entitlement_branches=[branch.id for branch in entitlement_branches] if entitlement_branches else None,
            entitlement_starts_at=entitlement_starts_at.isoformat() if entitlement_starts_at else None,
            entitlement_ends_at=entitlement_ends_at.isoformat() if entitlement_ends_at else None,
        )
        return GiftBatch(data=data, state=state, application_id=app_id)

    async def branches(self) -> List[ApplicationBranch]:
        """|coro|

        Retrieves the branches for this application.

        Raises
        ------
        HTTPException
            Fetching the branches failed.

        Returns
        -------
        List[:class:`ApplicationBranch`]
            The branches retrieved.
        """
        state = self._state
        app_id = self.id
        data = await state.http.get_app_branches(app_id)
        return [ApplicationBranch(data=branch, state=state, application_id=app_id) for branch in data]

    async def create_branch(self, name: str) -> ApplicationBranch:
        """|coro|

        Creates a branch for this application.

        .. note::

            The first branch created will always be called ``master``
            and share the same ID as the application.

        Parameters
        -----------
        name: :class:`str`
            The name of the branch.

        Raises
        ------
        HTTPException
            Creating the branch failed.

        Returns
        -------
        :class:`ApplicationBranch`
            The branch created.
        """
        state = self._state
        app_id = self.id
        data = await state.http.create_app_branch(app_id, name)
        return ApplicationBranch(data=data, state=state, application_id=app_id)

    async def manifest_labels(self) -> List[ManifestLabel]:
        """|coro|

        Retrieves the manifest labels for this application.

        Raises
        ------
        HTTPException
            Fetching the manifest labels failed.

        Returns
        -------
        List[:class:`ManifestLabel`]
            The manifest labels retrieved.
        """
        state = self._state
        app_id = self.id
        data = await state.http.get_app_manifest_labels(app_id)
        return [ManifestLabel(data=label, application_id=app_id) for label in data]

    async def fetch_discoverability(self) -> Tuple[ApplicationDiscoverabilityState, ApplicationDiscoveryFlags]:
        """|coro|

        Retrieves the discoverability state for this application.

        .. note::

            This method is an API call. For general usage, consider
            :attr:`discoverability_state` and :attr:`discovery_eligibility_flags` instead.

        Raises
        ------
        HTTPException
            Fetching the discoverability failed.

        Returns
        -------
        Tuple[:class:`ApplicationDiscoverabilityState`, :class:`ApplicationDiscoveryFlags`]
            The discoverability retrieved.
        """
        data = await self._state.http.get_app_discoverability(self.id)
        return try_enum(
            ApplicationDiscoverabilityState, data['discoverability_state']
        ), ApplicationDiscoveryFlags._from_value(data['discovery_eligibility_flags'])

    async def fetch_embedded_activity_config(self) -> EmbeddedActivityConfig:
        """|coro|

        Retrieves the embedded activity configuration for this application.

        .. note::

            This method is an API call. For general usage, consider
            :attr:`PartialApplication.embedded_activity_config` instead.

        Raises
        ------
        Forbidden
            You do not have permissions to fetch the embedded activity config.
        HTTPException
            Fetching the embedded activity config failed.

        Returns
        -------
        :class:`EmbeddedActivityConfig`
            The embedded activity config retrieved.
        """
        data = await self._state.http.get_embedded_activity_config(self.id)
        return EmbeddedActivityConfig(data=data, application=self)

    async def edit_embedded_activity_config(
        self,
        *,
        supported_platforms: Collection[EmbeddedActivityPlatform] = MISSING,
        platform_configs: Collection[EmbeddedActivityPlatformConfig] = MISSING,
        orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        tablet_orientation_lock_state: EmbeddedActivityOrientation = MISSING,
        requires_age_gate: bool = MISSING,
        shelf_rank: int = MISSING,
        free_period_starts_at: Optional[datetime] = MISSING,
        free_period_ends_at: Optional[datetime] = MISSING,
        preview_video_asset: Optional[Snowflake] = MISSING,
    ) -> EmbeddedActivityConfig:
        """|coro|

        Edits the application's embedded activity configuration.

        Parameters
        -----------
        supported_platforms: List[:class:`EmbeddedActivityPlatform`]
            A list of platforms that the activity supports.
        platform_configs: List[:class:`EmbeddedActivityPlatformConfig`]
            A list of configurations for each supported activity platform.

            .. versionadded:: 2.1
        orientation_lock_state: :class:`EmbeddedActivityOrientation`
            The mobile orientation lock state of the activity.
        tablet_orientation_lock_state: :class:`EmbeddedActivityOrientation`
            The mobile orientation lock state of the activity on tablets.
        requires_age_gate: :class:`bool`
            Whether the activity should be blocked from underage users.
        shelf_rank: :class:`int`
            The sorting rank of the activity in the activity shelf.
        free_period_starts_at: Optional[:class:`datetime.datetime`]
            When the activity's free availability period starts.
        free_period_ends_at: Optional[:class:`datetime.datetime`]
            When the activity's free availability period ends.
        preview_video_asset: Optional[:class:`ApplicationAsset`]
            The preview video asset of the activity.

        Raises
        -------
        Forbidden
            You are not allowed to edit this application's configuration.
        HTTPException
            Editing the configuration failed.

        Returns
        --------
        :class:`EmbeddedActivityConfig`
            The edited configuration.
        """
        data = await self._state.http.edit_embedded_activity_config(
            self.id,
            supported_platforms=[str(x) for x in (supported_platforms)] if supported_platforms is not MISSING else None,
            platform_config={c.platform.value: c.to_dict() for c in (platform_configs)}
            if platform_configs is not MISSING
            else None,
            orientation_lock_state=int(orientation_lock_state) if orientation_lock_state is not MISSING else None,
            tablet_orientation_lock_state=int(tablet_orientation_lock_state)
            if tablet_orientation_lock_state is not MISSING
            else None,
            requires_age_gate=requires_age_gate if requires_age_gate is not MISSING else None,
            shelf_rank=shelf_rank if shelf_rank is not MISSING else None,
            free_period_starts_at=free_period_starts_at.isoformat() if free_period_starts_at else None,
            free_period_ends_at=free_period_ends_at.isoformat() if free_period_ends_at else None,
            preview_video_asset_id=(preview_video_asset.id if preview_video_asset else None)
            if preview_video_asset is not MISSING
            else MISSING,
        )
        if self.embedded_activity_config is not None:
            self.embedded_activity_config._update(data)
        else:
            self.embedded_activity_config = EmbeddedActivityConfig(data=data, application=self)
        return self.embedded_activity_config

    async def secret(self) -> str:
        """|coro|

        Gets the application's secret.

        This revokes all previous secrets.

        Raises
        ------
        Forbidden
            You do not have permissions to reset the secret.
        HTTPException
            Getting the secret failed.

        Returns
        -------
        :class:`str`
            The new secret.
        """
        data = await self._state.http.reset_secret(self.id)
        return data['secret']


class IntegrationApplication(Hashable):
    """Represents a very partial application received in integration/interaction contexts.

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the application's hash.

        .. describe:: str(x)

            Returns the application's name.

    .. versionadded:: 2.0

    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    bot: Optional[:class:`User`]
        The bot attached to the application, if any.
    description: :class:`str`
        The application description.
    deeplink_uri: Optional[:class:`str`]
        The application's deeplink URI, if set.

        .. versionadded:: 2.1
    type: Optional[:class:`ApplicationType`]
        The type of application.
    primary_sku_id: Optional[:class:`int`]
        The application's primary SKU ID, if any.
        This can be an application's game SKU, subscription SKU, etc.
    role_connections_verification_url: Optional[:class:`str`]
        The application's connection verification URL which will render the application as
        a verification method in the guild's role verification configuration.
    third_party_skus: List[:class:`ThirdPartySKU`]
        A list of third party platforms the SKU is available at.

        .. versionadded:: 2.1
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        'bot',
        'description',
        'deeplink_uri',
        'type',
        'primary_sku_id',
        'role_connections_verification_url',
        'third_party_skus',
        '_icon',
        '_cover_image',
        '_splash',
    )

    def __init__(self, *, state: ConnectionState, data: BaseApplicationPayload):
        self._state: ConnectionState = state
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def _update(self, data: BaseApplicationPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data.get('description') or ''
        self.deeplink_uri: Optional[str] = data.get('deeplink_uri')
        self.type: Optional[ApplicationType] = try_enum(ApplicationType, data['type']) if 'type' in data else None

        self._icon: Optional[str] = data.get('icon')
        self._cover_image: Optional[str] = data.get('cover_image')
        self._splash: Optional[str] = data.get('splash')
        self.bot: Optional[User] = self._state.create_user(data['bot']) if 'bot' in data else None
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self.role_connections_verification_url: Optional[str] = data.get('role_connections_verification_url')
        self.third_party_skus: List[ThirdPartySKU] = [
            ThirdPartySKU(data=t, application=self) for t in data.get('third_party_skus', [])
        ]

    def __repr__(self) -> str:
        return f'<IntegrationApplication id={self.id} name={self.name!r}>'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the application's creation time in UTC.

        .. versionadded:: 2.1
        """
        return utils.snowflake_time(self.id)

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Retrieves the application's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='app')

    @property
    def cover_image(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Retrieves the application's cover image, if any."""
        if self._cover_image is None:
            return None
        return Asset._from_icon(self._state, self.id, self._cover_image, path='app')

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Retrieves the application's splash, if any.

        .. versionadded:: 2.1
        """
        if self._splash is None:
            return None
        return Asset._from_icon(self._state, self.id, self._splash, path='app')

    @property
    def primary_sku_url(self) -> Optional[str]:
        """:class:`str`: The URL to the primary SKU of the application, if any."""
        if self.primary_sku_id:
            return f'https://discord.com/store/skus/{self.primary_sku_id}/unknown'

    async def assets(self) -> List[ApplicationAsset]:
        """|coro|

        Retrieves the assets of this application.

        Raises
        ------
        HTTPException
            Retrieving the assets failed.

        Returns
        -------
        List[:class:`ApplicationAsset`]
            The application's assets.
        """
        data = await self._state.http.get_app_assets(self.id)
        return [ApplicationAsset(data=d, application=self) for d in data]

    async def published_store_listings(self, *, localize: bool = True) -> List[StoreListing]:
        """|coro|

        Retrieves all published store listings for this application.

        Parameters
        -----------
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        HTTPException
            Retrieving the listings failed.

        Returns
        -------
        List[:class:`StoreListing`]
            The store listings.
        """
        state = self._state
        data = await state.http.get_app_store_listings(self.id, country_code=state.country_code or 'US', localize=localize)
        return [StoreListing(state=state, data=d) for d in data]

    async def primary_store_listing(self, *, localize: bool = True) -> StoreListing:
        """|coro|

        Retrieves the primary store listing of this application.

        This is the public store listing of the primary SKU.

        Parameters
        -----------
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        ------
        NotFound
            The application does not have a primary SKU.
        HTTPException
            Retrieving the store listing failed.

        Returns
        -------
        :class:`StoreListing`
            The application's primary store listing, if any.
        """
        state = self._state
        data = await state.http.get_app_store_listing(self.id, country_code=state.country_code or 'US', localize=localize)
        return StoreListing(state=state, data=data)

    async def entitlements(self, *, exclude_consumed: bool = True) -> List[Entitlement]:
        """|coro|

        Retrieves the entitlements this account has granted for this application.

        Parameters
        -----------
        exclude_consumed: :class:`bool`
            Whether to exclude consumed entitlements.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch entitlements.
        HTTPException
            Fetching the entitlements failed.

        Returns
        --------
        List[:class:`Entitlement`]
            The entitlements retrieved.
        """
        state = self._state
        data = await state.http.get_user_app_entitlements(self.id, exclude_consumed=exclude_consumed)
        return [Entitlement(data=entitlement, state=state) for entitlement in data]

    async def ticket(self) -> str:
        """|coro|

        Retrieves the license ticket for this application.

        Raises
        -------
        HTTPException
            Retrieving the ticket failed.

        Returns
        --------
        :class:`str`
            The ticket retrieved.
        """
        state = self._state
        data = await state.http.get_app_ticket(self.id)
        return data['ticket']

    async def entitlement_ticket(self) -> str:
        """|coro|

        Retrieves the entitlement ticket for this application.

        Raises
        -------
        HTTPException
            Retrieving the ticket failed.

        Returns
        --------
        :class:`str`
            The ticket retrieved.
        """
        state = self._state
        data = await state.http.get_app_entitlement_ticket(self.id)
        return data['ticket']

    async def activity_statistics(self) -> List[ApplicationActivityStatistics]:
        """|coro|

        Retrieves the activity usage statistics for this application.

        Raises
        -------
        HTTPException
            Retrieving the statistics failed.

        Returns
        --------
        List[:class:`ApplicationActivityStatistics`]
            The statistics retrieved.
        """
        state = self._state
        app_id = self.id
        data = await state.http.get_app_activity_statistics(app_id)
        return [ApplicationActivityStatistics(data=activity, state=state, application_id=app_id) for activity in data]


class UnverifiedApplication:
    """Represents an unverified application (a game not detected by the Discord client) that has been reported to Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the application's hash.

        .. describe:: str(x)

            Returns the application's name.

    .. versionadded:: 2.1

    Attributes
    -----------
    name: :class:`str`
        The name of the application.
    hash: :class:`str`
        The hash of the application.
    missing_data: List[:class:`str`]
        Data missing from the unverified application report.

        .. note::

            :meth:`Client.report_unverified_application` will automatically
            upload the unverified application's icon, if missing.
    """

    __slots__ = ('name', 'hash', 'missing_data')

    def __init__(self, *, data: UnverifiedApplicationPayload):
        self.name: str = data['name']
        self.hash: str = data['hash']
        self.missing_data: List[str] = data.get('missing_data', [])

    def __repr__(self) -> str:
        return f'<UnverifiedApplication name={self.name!r} hash={self.hash!r}>'

    def __hash__(self) -> int:
        return hash(self.hash)

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, UnverifiedApplication):
            return self.hash == other.hash
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, UnverifiedApplication):
            return self.hash != other.hash
        return NotImplemented
