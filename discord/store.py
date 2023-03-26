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

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Collection, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .asset import Asset, AssetMixin
from .enums import (
    ContentRatingAgency,
    ESRBContentDescriptor,
    ESRBRating,
    GiftStyle,
    Locale,
    OperatingSystem,
    PEGIContentDescriptor,
    PEGIRating,
    PremiumType,
    SKUAccessLevel,
    SKUFeature,
    SKUGenre,
    SKUType,
    SubscriptionInterval,
    SubscriptionPlanPurchaseType,
    try_enum,
)
from .flags import SKUFlags
from .mixins import Hashable
from .utils import (
    MISSING,
    _get_as_snowflake,
    _get_extension_for_mime_type,
    _parse_localizations,
    get,
    parse_date,
    parse_time,
    utcnow,
)

if TYPE_CHECKING:
    from datetime import date
    from typing_extensions import Self

    from .abc import Snowflake
    from .application import Application, PartialApplication
    from .entitlements import Entitlement, Gift, GiftBatch
    from .guild import Guild
    from .library import LibraryApplication
    from .state import ConnectionState
    from .types.application import StoreAsset as StoreAssetPayload
    from .types.entitlements import Gift as GiftPayload
    from .types.snowflake import Snowflake as SnowflakeType
    from .types.store import (
        SKU as SKUPayload,
        CarouselItem as CarouselItemPayload,
        ContentRating as ContentRatingPayload,
        SKUPrice as SKUPricePayload,
        StoreListing as StoreListingPayload,
        StoreNote as StoreNotePayload,
        SystemRequirements as SystemRequirementsPayload,
    )
    from .types.subscriptions import (
        PartialSubscriptionPlan as PartialSubscriptionPlanPayload,
        SubscriptionPlan as SubscriptionPlanPayload,
        SubscriptionPrice as SubscriptionPricePayload,
        SubscriptionPrices as SubscriptionPricesPayload,
    )
    from .user import User

__all__ = (
    'StoreAsset',
    'StoreNote',
    'SystemRequirements',
    'StoreListing',
    'SKUPrice',
    'ContentRating',
    'SKU',
    'SubscriptionPlanPrices',
    'SubscriptionPlan',
)

THE_GAME_AWARDS_WINNERS = (500428425362931713, 451550535720501248, 471376328319303681, 466696214818193408)


class StoreAsset(AssetMixin, Hashable):
    """Represents an application store asset.

    .. container:: operations

        .. describe:: x == y

            Checks if two assets are equal.

        .. describe:: x != y

            Checks if two assets are not equal.

        .. describe:: hash(x)

            Returns the asset's hash.

    .. versionadded:: 2.0

    Attributes
    -----------
    parent: Union[:class:`StoreListing`, :class:`Application`]
        The store listing or application that this asset belongs to.
    id: Union[:class:`int`, :class:`str`]
        The asset's ID or YouTube video ID.
    size: :class:`int`
        The asset's size in bytes, or 0 if it's a YouTube video.
    height: :class:`int`
        The asset's height in pixels, or 0 if it's a YouTube video.
    width: :class:`int`
        The asset's width in pixels, or 0 if it's a YouTube video.
    mime_type: :class:`str`
        The asset's mime type, or "video/youtube" if it is a YouTube video.
    """

    __slots__ = ('_state', 'parent', 'id', 'size', 'height', 'width', 'mime_type')

    def __init__(self, *, data: StoreAssetPayload, state: ConnectionState, parent: Union[StoreListing, Application]) -> None:
        self._state: ConnectionState = state
        self.parent = parent
        self.size: int = data['size']
        self.height: int = data['height']
        self.width: int = data['width']
        self.mime_type: str = data['mime_type']

        self.id: SnowflakeType
        try:
            self.id = int(data['id'])
        except ValueError:
            self.id = data['id']

    @classmethod
    def _from_id(
        cls, *, id: SnowflakeType, mime_type: str = '', state: ConnectionState, parent: Union[StoreListing, Application]
    ) -> StoreAsset:
        data: StoreAssetPayload = {'id': id, 'size': 0, 'height': 0, 'width': 0, 'mime_type': mime_type}
        return cls(data=data, state=state, parent=parent)

    @classmethod
    def _from_carousel_item(
        cls, *, data: CarouselItemPayload, state: ConnectionState, store_listing: StoreListing
    ) -> StoreAsset:
        asset_id = _get_as_snowflake(data, 'asset_id')
        if asset_id:
            return get(store_listing.assets, id=asset_id) or StoreAsset._from_id(
                id=asset_id, state=state, parent=store_listing
            )
        else:
            # One or the other must be present
            return cls._from_id(id=data['youtube_video_id'], mime_type='video/youtube', state=state, parent=store_listing)  # type: ignore

    def __repr__(self) -> str:
        return f'<ApplicationAsset id={self.id} height={self.height} width={self.width}>'

    @property
    def application_id(self) -> int:
        """:class:`int`: Returns the application ID that this asset belongs to."""
        parent = self.parent
        return parent.sku.application_id if hasattr(parent, 'sku') else parent.id  # type: ignore # Type checker doesn't understand

    @property
    def animated(self) -> bool:
        """:class:`bool`: Indicates if the store asset is animated."""
        return self.mime_type in {'video/youtube', 'image/gif', 'video/mp4'}

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the store asset."""
        if self.is_youtube_video():
            return f'https://youtube.com/watch?v={self.id}'
        return (
            f'{Asset.BASE}/app-assets/{self.application_id}/store/{self.id}.{_get_extension_for_mime_type(self.mime_type)}'
        )

    def is_youtube_video(self) -> bool:
        """:class:`bool`: Indicates if the asset is a YouTube video."""
        return self.mime_type == 'video/youtube'

    def to_carousel_item(self) -> dict:
        if self.is_youtube_video():
            return {'youtube_video_id': self.id}
        return {'asset_id': self.id}

    async def read(self) -> bytes:
        """|coro|

        Retrieves the content of this asset as a :class:`bytes` object.

        Raises
        ------
        ValueError
            The asset is a YouTube video.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        -------
        :class:`bytes`
            The content of the asset.
        """
        if self.is_youtube_video():
            raise ValueError('StoreAsset is not a real asset')

        return await super().read()

    async def delete(self) -> None:
        """|coro|

        Deletes the asset.

        Raises
        ------
        ValueError
            The asset is a YouTube video.
        Forbidden
            You are not allowed to delete this asset.
        HTTPException
            Deleting the asset failed.
        """
        if self.is_youtube_video():
            raise ValueError('StoreAsset is not a real asset')

        await self._state.http.delete_store_asset(self.application_id, self.id)


class StoreNote:
    """Represents a note for a store listing.

    .. container:: operations

        .. describe:: str(x)

            Returns the note's content.

    .. versionadded:: 2.0

    Attributes
    -----------
    user: Optional[:class:`User`]
        The user who wrote the note.
    content: :class:`str`
        The note content.
    """

    __slots__ = ('user', 'content')

    def __init__(self, *, data: StoreNotePayload, state: ConnectionState) -> None:
        self.user: Optional[User] = state.create_user(data['user']) if data.get('user') else None  # type: ignore
        self.content: str = data['content']

    def __repr__(self) -> str:
        return f'<StoreNote user={self.user!r} content={self.content!r}>'

    def __str__(self) -> str:
        return self.content


class SystemRequirements:
    """Represents system requirements.

    .. versionadded:: 2.0

    Attributes
    -----------
    os: :class:`OperatingSystem`
        The operating system these requirements apply to.
    minimum_os_version: :class:`str`
        The minimum operating system version required.
    recommended_os_version: :class:`str`
        The recommended operating system version.
    minimum_cpu: :class:`str`
        The minimum CPU specifications required.
    recommended_cpu: :class:`str`
        The recommended CPU specifications.
    minimum_gpu: :class:`str`
        The minimum GPU specifications required.
    recommended_gpu: :class:`str`
        The recommended GPU specifications.
    minimum_ram: :class:`int`
        The minimum RAM size in megabytes.
    recommended_ram: :class:`int`
        The recommended RAM size in megabytes.
    minimum_disk: :class:`int`
        The minimum free storage space in megabytes.
    recommended_disk: :class:`int`
        The recommended free storage space in megabytes.
    minimum_sound_card: Optional[:class:`str`]
        The minimum sound card specifications required, if any.
    recommended_sound_card: Optional[:class:`str`]
        The recommended sound card specifications, if any.
    minimum_directx: Optional[:class:`str`]
        The minimum DirectX version required, if any.
    recommended_directx: Optional[:class:`str`]
        The recommended DirectX version, if any.
    minimum_network: Optional[:class:`str`]
        The minimum network specifications required, if any.
    recommended_network: Optional[:class:`str`]
        The recommended network specifications, if any.
    minimum_notes: Optional[:class:`str`]
        Any extra notes on minimum requirements.
    recommended_notes: Optional[:class:`str`]
        Any extra notes on recommended requirements.
    """

    if TYPE_CHECKING:
        os: OperatingSystem
        minimum_ram: Optional[int]
        recommended_ram: Optional[int]
        minimum_disk: Optional[int]
        recommended_disk: Optional[int]
        minimum_os_version: Optional[str]
        minimum_os_version_localizations: Dict[Locale, str]
        recommended_os_version: Optional[str]
        recommended_os_version_localizations: Dict[Locale, str]
        minimum_cpu: Optional[str]
        minimum_cpu_localizations: Dict[Locale, str]
        recommended_cpu: Optional[str]
        recommended_cpu_localizations: Dict[Locale, str]
        minimum_gpu: Optional[str]
        minimum_gpu_localizations: Dict[Locale, str]
        recommended_gpu: Optional[str]
        recommended_gpu_localizations: Dict[Locale, str]
        minimum_sound_card: Optional[str]
        minimum_sound_card_localizations: Dict[Locale, str]
        recommended_sound_card: Optional[str]
        recommended_sound_card_localizations: Dict[Locale, str]
        minimum_directx: Optional[str]
        minimum_directx_localizations: Dict[Locale, str]
        recommended_directx: Optional[str]
        recommended_directx_localizations: Dict[Locale, str]
        minimum_network: Optional[str]
        minimum_network_localizations: Dict[Locale, str]
        recommended_network: Optional[str]
        recommended_network_localizations: Dict[Locale, str]
        minimum_notes: Optional[str]
        minimum_notes_localizations: Dict[Locale, str]
        recommended_notes: Optional[str]
        recommended_notes_localizations: Dict[Locale, str]

    __slots__ = (
        'os',
        'minimum_ram',
        'recommended_ram',
        'minimum_disk',
        'recommended_disk',
        'minimum_os_version',
        'minimum_os_version_localizations',
        'recommended_os_version',
        'recommended_os_version_localizations',
        'minimum_cpu',
        'minimum_cpu_localizations',
        'recommended_cpu',
        'recommended_cpu_localizations',
        'minimum_gpu',
        'minimum_gpu_localizations',
        'recommended_gpu',
        'recommended_gpu_localizations',
        'minimum_sound_card',
        'minimum_sound_card_localizations',
        'recommended_sound_card',
        'recommended_sound_card_localizations',
        'minimum_directx',
        'minimum_directx_localizations',
        'recommended_directx',
        'recommended_directx_localizations',
        'minimum_network',
        'minimum_network_localizations',
        'recommended_network',
        'recommended_network_localizations',
        'minimum_notes',
        'minimum_notes_localizations',
        'recommended_notes',
        'recommended_notes_localizations',
    )

    def __init__(
        self,
        os: OperatingSystem,
        *,
        minimum_ram: Optional[int] = None,
        recommended_ram: Optional[int] = None,
        minimum_disk: Optional[int] = None,
        recommended_disk: Optional[int] = None,
        minimum_os_version: Optional[str] = None,
        minimum_os_version_localizations: Optional[Dict[Locale, str]] = None,
        recommended_os_version: Optional[str] = None,
        recommended_os_version_localizations: Optional[Dict[Locale, str]] = None,
        minimum_cpu: Optional[str] = None,
        minimum_cpu_localizations: Optional[Dict[Locale, str]] = None,
        recommended_cpu: Optional[str] = None,
        recommended_cpu_localizations: Optional[Dict[Locale, str]] = None,
        minimum_gpu: Optional[str] = None,
        minimum_gpu_localizations: Optional[Dict[Locale, str]] = None,
        recommended_gpu: Optional[str] = None,
        recommended_gpu_localizations: Optional[Dict[Locale, str]] = None,
        minimum_sound_card: Optional[str] = None,
        minimum_sound_card_localizations: Optional[Dict[Locale, str]] = None,
        recommended_sound_card: Optional[str] = None,
        recommended_sound_card_localizations: Optional[Dict[Locale, str]] = None,
        minimum_directx: Optional[str] = None,
        minimum_directx_localizations: Optional[Dict[Locale, str]] = None,
        recommended_directx: Optional[str] = None,
        recommended_directx_localizations: Optional[Dict[Locale, str]] = None,
        minimum_network: Optional[str] = None,
        minimum_network_localizations: Optional[Dict[Locale, str]] = None,
        recommended_network: Optional[str] = None,
        recommended_network_localizations: Optional[Dict[Locale, str]] = None,
        minimum_notes: Optional[str] = None,
        minimum_notes_localizations: Optional[Dict[Locale, str]] = None,
        recommended_notes: Optional[str] = None,
        recommended_notes_localizations: Optional[Dict[Locale, str]] = None,
    ) -> None:
        self.os = os
        self.minimum_ram = minimum_ram
        self.recommended_ram = recommended_ram
        self.minimum_disk = minimum_disk
        self.recommended_disk = recommended_disk
        self.minimum_os_version = minimum_os_version
        self.minimum_os_version_localizations = minimum_os_version_localizations or {}
        self.recommended_os_version = recommended_os_version
        self.recommended_os_version_localizations = recommended_os_version_localizations or {}
        self.minimum_cpu = minimum_cpu
        self.minimum_cpu_localizations = minimum_cpu_localizations or {}
        self.recommended_cpu = recommended_cpu
        self.recommended_cpu_localizations = recommended_cpu_localizations or {}
        self.minimum_gpu = minimum_gpu
        self.minimum_gpu_localizations = minimum_gpu_localizations or {}
        self.recommended_gpu = recommended_gpu
        self.recommended_gpu_localizations = recommended_gpu_localizations or {}
        self.minimum_sound_card = minimum_sound_card
        self.minimum_sound_card_localizations = minimum_sound_card_localizations or {}
        self.recommended_sound_card = recommended_sound_card
        self.recommended_sound_card_localizations = recommended_sound_card_localizations or {}
        self.minimum_directx = minimum_directx
        self.minimum_directx_localizations = minimum_directx_localizations or {}
        self.recommended_directx = recommended_directx
        self.recommended_directx_localizations = recommended_directx_localizations or {}
        self.minimum_network = minimum_network
        self.minimum_network_localizations = minimum_network_localizations or {}
        self.recommended_network = recommended_network
        self.recommended_network_localizations = recommended_network_localizations or {}
        self.minimum_notes = minimum_notes
        self.minimum_notes_localizations = minimum_notes_localizations or {}
        self.recommended_notes = recommended_notes
        self.recommended_notes_localizations = recommended_notes_localizations or {}

    @classmethod
    def from_dict(cls, os: OperatingSystem, data: SystemRequirementsPayload) -> Self:
        minimum = data.get('minimum', {})
        recommended = data.get('recommended', {})

        minimum_os_version, minimum_os_version_localizations = _parse_localizations(minimum, 'operating_system_version')
        recommended_os_version, recommended_os_version_localizations = _parse_localizations(
            recommended, 'operating_system_version'
        )
        minimum_cpu, minimum_cpu_localizations = _parse_localizations(minimum, 'cpu')
        recommended_cpu, recommended_cpu_localizations = _parse_localizations(recommended, 'cpu')
        minimum_gpu, minimum_gpu_localizations = _parse_localizations(minimum, 'gpu')
        recommended_gpu, recommended_gpu_localizations = _parse_localizations(recommended, 'gpu')
        minimum_sound_card, minimum_sound_card_localizations = _parse_localizations(minimum, 'sound_card')
        recommended_sound_card, recommended_sound_card_localizations = _parse_localizations(recommended, 'sound_card')
        minimum_directx, minimum_directx_localizations = _parse_localizations(minimum, 'directx')
        recommended_directx, recommended_directx_localizations = _parse_localizations(recommended, 'directx')
        minimum_network, minimum_network_localizations = _parse_localizations(minimum, 'network')
        recommended_network, recommended_network_localizations = _parse_localizations(recommended, 'network')
        minimum_notes, minimum_notes_localizations = _parse_localizations(minimum, 'notes')
        recommended_notes, recommended_notes_localizations = _parse_localizations(recommended, 'notes')

        return cls(
            os,
            minimum_ram=minimum.get('ram'),
            recommended_ram=recommended.get('ram'),
            minimum_disk=minimum.get('disk'),
            recommended_disk=recommended.get('disk'),
            minimum_os_version=minimum_os_version,
            minimum_os_version_localizations=minimum_os_version_localizations,
            recommended_os_version=recommended_os_version,
            recommended_os_version_localizations=recommended_os_version_localizations,
            minimum_cpu=minimum_cpu,
            minimum_cpu_localizations=minimum_cpu_localizations,
            recommended_cpu=recommended_cpu,
            recommended_cpu_localizations=recommended_cpu_localizations,
            minimum_gpu=minimum_gpu,
            minimum_gpu_localizations=minimum_gpu_localizations,
            recommended_gpu=recommended_gpu,
            recommended_gpu_localizations=recommended_gpu_localizations,
            minimum_sound_card=minimum_sound_card,
            minimum_sound_card_localizations=minimum_sound_card_localizations,
            recommended_sound_card=recommended_sound_card,
            recommended_sound_card_localizations=recommended_sound_card_localizations,
            minimum_directx=minimum_directx,
            minimum_directx_localizations=minimum_directx_localizations,
            recommended_directx=recommended_directx,
            recommended_directx_localizations=recommended_directx_localizations,
            minimum_network=minimum_network,
            minimum_network_localizations=minimum_network_localizations,
            recommended_network=recommended_network,
            recommended_network_localizations=recommended_network_localizations,
            minimum_notes=minimum_notes,
            minimum_notes_localizations=minimum_notes_localizations,
            recommended_notes=recommended_notes,
            recommended_notes_localizations=recommended_notes_localizations,
        )

    def __repr__(self) -> str:
        return f'<SystemRequirements os={self.os!r}>'

    def to_dict(self) -> dict:
        minimum = {}
        recommended = {}
        for key in self.__slots__:
            if key.endswith('_localizations'):
                continue

            value = getattr(self, key)
            localizations = getattr(self, f'{key}_localizations', None)
            if value or localizations:
                data = (
                    value
                    if localizations is None
                    else {'default': value, 'localizations': {str(k): v for k, v in localizations.items()}}
                )
                if key.startswith('minimum_'):
                    minimum[key[8:]] = data
                elif key.startswith('recommended_'):
                    recommended[key[12:]] = data

        return {'minimum': minimum, 'recommended': recommended}


class StoreListing(Hashable):
    """Represents a store listing.

    .. container:: operations

        .. describe:: x == y

            Checks if two listings are equal.

        .. describe:: x != y

            Checks if two listings are not equal.

        .. describe:: hash(x)

            Returns the listing's hash.

        .. describe:: str(x)

            Returns the listing's summary.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The listing's ID.
    summary: Optional[:class:`str`]
        The listing's summary.
    summary_localizations: Dict[:class:`Locale`, :class:`str`]
        The listing's summary localized to different languages.
    description: Optional[:class:`str`]
        The listing's description.
    description_localizations: Dict[:class:`Locale`, :class:`str`]
        The listing's description localized to different languages.
    tagline: Optional[:class:`str`]
        The listing's tagline.
    tagline_localizations: Dict[:class:`Locale`, :class:`str`]
        The listing's tagline localized to different languages.
    flavor: Optional[:class:`str`]
        The listing's flavor text.
    sku: :class:`SKU`
        The SKU attached to this listing.
    child_skus: List[:class:`SKU`]
        The child SKUs attached to this listing.
    alternative_skus: List[:class:`SKU`]
        Alternative SKUs to the one attached to this listing.
    guild: Optional[:class:`Guild`]
        The guild tied to this listing, if any.
    published: :class:`bool`
        Whether the listing is published and publicly visible.
    staff_note: Optional[:class:`StoreNote`]
        The staff note attached to this listing.
    assets: List[:class:`StoreAsset`]
        A list of assets used in this listing.
    carousel_items: List[:class:`StoreAsset`]
        A list of assets and YouTube videos displayed in the carousel.
    preview_video: Optional[:class:`StoreAsset`]
        The preview video of the store listing.
    header_background: Optional[:class:`StoreAsset`]
        The header background image.
    hero_background: Optional[:class:`StoreAsset`]
        The hero background image.
    box_art: Optional[:class:`StoreAsset`]
        The box art of the product.
    thumbnail: Optional[:class:`StoreAsset`]
        The listing's thumbnail.
    header_logo_light: Optional[:class:`StoreAsset`]
        The header logo image for light backgrounds.
    header_logo_dark: Optional[:class:`StoreAsset`]
        The header logo image for dark backgrounds.
    """

    __slots__ = (
        '_state',
        'id',
        'summary',
        'summary_localizations',
        'description',
        'description_localizations',
        'tagline',
        'tagline_localizations',
        'flavor',
        'sku',
        'child_skus',
        'alternative_skus',
        'entitlement_branch_id',
        'guild',
        'published',
        'staff_note',
        'assets',
        'carousel_items',
        'preview_video',
        'header_background',
        'hero_background',
        'hero_video',
        'box_art',
        'thumbnail',
        'header_logo_light',
        'header_logo_dark',
    )

    if TYPE_CHECKING:
        summary: Optional[str]
        summary_localizations: Dict[Locale, str]
        description: Optional[str]
        description_localizations: Dict[Locale, str]
        tagline: Optional[str]
        tagline_localizations: Dict[Locale, str]

    def __init__(
        self, *, data: StoreListingPayload, state: ConnectionState, application: Optional[PartialApplication] = None
    ) -> None:
        self._state = state
        self._update(data, application=application)

    def __str__(self) -> str:
        return self.summary or ''

    def __repr__(self) -> str:
        return f'<StoreListing id={self.id} summary={self.summary!r} sku={self.sku!r}>'

    def _update(self, data: StoreListingPayload, application: Optional[PartialApplication] = None) -> None:
        from .guild import Guild

        state = self._state

        self.summary, self.summary_localizations = _parse_localizations(data, 'summary')
        self.description, self.description_localizations = _parse_localizations(data, 'description')
        self.tagline, self.tagline_localizations = _parse_localizations(data, 'tagline')

        self.id: int = int(data['id'])
        self.flavor: Optional[str] = data.get('flavor_text')
        self.sku: SKU = SKU(data=data['sku'], state=state, application=application)
        self.child_skus: List[SKU] = [SKU(data=sku, state=state) for sku in data.get('child_skus', [])]
        self.alternative_skus: List[SKU] = [SKU(data=sku, state=state) for sku in data.get('alternative_skus', [])]
        self.entitlement_branch_id: Optional[int] = _get_as_snowflake(data, 'entitlement_branch_id')
        self.guild: Optional[Guild] = Guild(data=data['guild'], state=state) if 'guild' in data else None
        self.published: bool = data.get('published', True)
        self.staff_note: Optional[StoreNote] = (
            StoreNote(data=data['staff_notes'], state=state) if 'staff_notes' in data else None
        )

        self.assets: List[StoreAsset] = [
            StoreAsset(data=asset, state=state, parent=self) for asset in data.get('assets', [])
        ]
        self.carousel_items: List[StoreAsset] = [
            StoreAsset._from_carousel_item(data=asset, state=state, store_listing=self)
            for asset in data.get('carousel_items', [])
        ]
        self.preview_video: Optional[StoreAsset] = (
            StoreAsset(data=data['preview_video'], state=state, parent=self) if 'preview_video' in data else None
        )
        self.header_background: Optional[StoreAsset] = (
            StoreAsset(data=data['header_background'], state=state, parent=self) if 'header_background' in data else None
        )
        self.hero_background: Optional[StoreAsset] = (
            StoreAsset(data=data['hero_background'], state=state, parent=self) if 'hero_background' in data else None
        )
        self.hero_video: Optional[StoreAsset] = (
            StoreAsset(data=data['hero_video'], state=state, parent=self) if 'hero_video' in data else None
        )
        self.box_art: Optional[StoreAsset] = (
            StoreAsset(data=data['box_art'], state=state, parent=self) if 'box_art' in data else None
        )
        self.thumbnail: Optional[StoreAsset] = (
            StoreAsset(data=data['thumbnail'], state=state, parent=self) if 'thumbnail' in data else None
        )
        self.header_logo_light: Optional[StoreAsset] = (
            StoreAsset(data=data['header_logo_light_theme'], state=state, parent=self)
            if 'header_logo_light_theme' in data
            else None
        )
        self.header_logo_dark: Optional[StoreAsset] = (
            StoreAsset(data=data['header_logo_dark_theme'], state=state, parent=self)
            if 'header_logo_dark_theme' in data
            else None
        )

    async def edit(
        self,
        *,
        summary: Optional[str] = MISSING,
        summary_localizations: Mapping[Locale, str] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Mapping[Locale, str] = MISSING,
        tagline: Optional[str] = MISSING,
        tagline_localizations: Mapping[Locale, str] = MISSING,
        child_skus: Sequence[Snowflake] = MISSING,
        guild: Optional[Snowflake] = MISSING,
        published: bool = MISSING,
        carousel_items: Sequence[Union[StoreAsset, str]] = MISSING,
        preview_video: Optional[Snowflake] = MISSING,
        header_background: Optional[Snowflake] = MISSING,
        hero_background: Optional[Snowflake] = MISSING,
        hero_video: Optional[Snowflake] = MISSING,
        box_art: Optional[Snowflake] = MISSING,
        thumbnail: Optional[Snowflake] = MISSING,
        header_logo_light: Optional[Snowflake] = MISSING,
        header_logo_dark: Optional[Snowflake] = MISSING,
    ):
        """|coro|

        Edits the store listing.

        All parameters are optional.

        Parameters
        ----------
        summary: Optional[:class:`str`]
            The summary of the store listing.
        summary_localizations: Dict[:class:`Locale`, :class:`str`]
            The summary of the store listing localized to different languages.
        description: Optional[:class:`str`]
            The description of the store listing.
        description_localizations: Dict[:class:`Locale`, :class:`str`]
            The description of the store listing localized to different languages.
        tagline: Optional[:class:`str`]
            The tagline of the store listing.
        tagline_localizations: Dict[:class:`Locale`, :class:`str`]
            The tagline of the store listing localized to different languages.
        child_skus: List[:class:`SKU`]
            The child SKUs of the store listing.
        guild: Optional[:class:`Guild`]
            The guild that the store listing is for.
        published: :class:`bool`
            Whether the store listing is published.
        carousel_items: List[Union[:class:`StoreAsset`, :class:`str`]]
            A list of carousel items to add to the store listing. These can be store assets or YouTube video IDs.
        preview_video: Optional[:class:`StoreAsset`]
            The preview video of the store listing.
        header_background: Optional[:class:`StoreAsset`]
            The header background of the store listing.
        hero_background: Optional[:class:`StoreAsset`]
            The hero background of the store listing.
        hero_video: Optional[:class:`StoreAsset`]
            The hero video of the store listing.
        box_art: Optional[:class:`StoreAsset`]
            The box art of the store listing.
        thumbnail: Optional[:class:`StoreAsset`]
            The thumbnail of the store listing.
        header_logo_light: Optional[:class:`StoreAsset`]
            The header logo image for light backgrounds.
        header_logo_dark: Optional[:class:`StoreAsset`]
            The header logo image for dark backgrounds.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the store listing.
        HTTPException
            Editing the store listing failed.
        """
        payload = {}

        if summary is not MISSING or summary_localizations is not MISSING:
            localizations = (
                (summary_localizations or {}) if summary_localizations is not MISSING else self.summary_localizations
            )
            payload['name'] = {
                'default': (summary if summary is not MISSING else self.summary) or '',
                'localizations': {str(k): v for k, v in localizations.items()},
            }
        if description is not MISSING or description_localizations is not MISSING:
            localizations = (
                (description_localizations or {})
                if description_localizations is not MISSING
                else self.description_localizations
            )
            payload['description'] = {
                'default': (description if description is not MISSING else self.description) or '',
                'localizations': {str(k): v for k, v in localizations.items()},
            }
        if tagline is not MISSING or tagline_localizations is not MISSING:
            localizations = (
                (tagline_localizations or {}) if tagline_localizations is not MISSING else self.tagline_localizations
            )
            payload['tagline'] = {
                'default': (tagline if tagline is not MISSING else self.tagline) or '',
                'localizations': {str(k): v for k, v in localizations.items()},
            }

        if child_skus is not MISSING:
            payload['child_sku_ids'] = [sku.id for sku in child_skus] if child_skus else []
        if guild is not MISSING:
            payload['guild_id'] = guild.id if guild else None
        if published is not MISSING:
            payload['published'] = published
        if carousel_items is not MISSING:
            payload['carousel_items'] = (
                [
                    item.to_carousel_item() if isinstance(item, StoreAsset) else {'youtube_video_id': item}
                    for item in carousel_items
                ]
                if carousel_items
                else []
            )
        if preview_video is not MISSING:
            payload['preview_video_asset_id'] = preview_video.id if preview_video else None
        if header_background is not MISSING:
            payload['header_background_asset_id'] = header_background.id if header_background else None
        if hero_background is not MISSING:
            payload['hero_background_asset_id'] = hero_background.id if hero_background else None
        if hero_video is not MISSING:
            payload['hero_video_asset_id'] = hero_video.id if hero_video else None
        if box_art is not MISSING:
            payload['box_art_asset_id'] = box_art.id if box_art else None
        if thumbnail is not MISSING:
            payload['thumbnail_asset_id'] = thumbnail.id if thumbnail else None
        if header_logo_light is not MISSING:
            payload['header_logo_light_theme_asset_id'] = header_logo_light.id if header_logo_light else None
        if header_logo_dark is not MISSING:
            payload['header_logo_dark_theme_asset_id'] = header_logo_dark.id if header_logo_dark else None

        data = await self._state.http.edit_store_listing(self.id, payload)
        self._update(data, application=self.sku.application)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the store listing. This is the URL of the primary SKU."""
        return self.sku.url


class SKUPrice:
    """Represents a SKU's price.

    .. container:: operations

        .. describe:: bool(x)

            Checks if a SKU costs anything.

        .. describe:: int(x)

            Returns the price of the SKU.

    .. versionadded:: 2.0

    Attributes
    -----------
    currency: :class:`str`
        The currency of the price.
    amount: :class:`int`
        The price of the SKU.
    sale_amount: Optional[:class:`int`]
        The price of the SKU with discounts applied, if any.
    sale_percentage: :class:`int`
        The percentage of the price discounted, if any.
    """

    __slots__ = ('currency', 'amount', 'sale_amount', 'sale_percentage', 'premium', 'exponent')

    def __init__(self, data: Union[SKUPricePayload, SubscriptionPricePayload]) -> None:
        self.currency: str = data.get('currency', 'usd')
        self.amount: int = data.get('amount', 0)
        self.sale_amount: Optional[int] = data.get('sale_amount')
        self.sale_percentage: int = data.get('sale_percentage', 0)
        self.premium = data.get('premium')
        self.exponent: Optional[int] = data.get('exponent')

    @classmethod
    def from_private(cls, data: SKUPayload) -> SKUPrice:
        payload: SKUPricePayload = {
            'currency': 'usd',
            'amount': data.get('price_tier') or 0,
            'sale_amount': data.get('sale_price_tier'),
        }
        if payload['sale_amount'] is not None:
            payload['sale_percentage'] = int((1 - (payload['sale_amount'] / payload['amount'])) * 100)
        return cls(payload)

    def __repr__(self) -> str:
        return f'<SKUPrice amount={self.amount} currency={self.currency!r}>'

    def __bool__(self) -> bool:
        return self.amount > 0

    def __int__(self) -> int:
        return self.amount

    def is_discounted(self) -> bool:
        """:class:`bool`: Checks whether the SKU is discounted."""
        return self.sale_percentage > 0

    def is_free(self) -> bool:
        """:class:`bool`: Checks whether the SKU is free."""
        return self.amount == 0

    @property
    def discounts(self) -> int:
        """:class:`int`: Returns the amount of discounts applied to the SKU price."""
        return self.amount - (self.sale_amount or self.amount)


class ContentRating:
    """Represents a SKU's content rating.

    .. versionadded:: 2.0

    Attributes
    -----------
    agency: :class:`ContentRatingAgency`
        The agency that rated the content.
    rating: Union[:class:`ESRBRating`, :class:`PEGIRating`]
        The rating of the content.
    descriptors: Union[List[:class:`ESRBContentDescriptor`], List[:class:`PEGIContentDescriptor`]
        Extra descriptors for the content rating.
    """

    _AGENCY_MAP = {
        ContentRatingAgency.esrb: (ESRBRating, ESRBContentDescriptor),
        ContentRatingAgency.pegi: (PEGIRating, PEGIContentDescriptor),
    }

    __slots__ = ('agency', 'rating', 'descriptors')

    def __init__(
        self,
        *,
        agency: ContentRatingAgency,
        rating: Union[ESRBRating, PEGIRating],
        descriptors: Union[Collection[ESRBContentDescriptor], Collection[PEGIContentDescriptor]],
    ) -> None:
        self.agency = agency

        ratingcls, descriptorcls = self._AGENCY_MAP[agency]
        self.rating: Union[ESRBRating, PEGIRating] = try_enum(ratingcls, int(rating))
        self.descriptors: Union[List[ESRBContentDescriptor], List[PEGIContentDescriptor]] = [
            try_enum(descriptorcls, int(descriptor)) for descriptor in descriptors
        ]

    @classmethod
    def from_dict(cls, data: ContentRatingPayload, agency: int) -> ContentRating:
        return cls(
            agency=try_enum(ContentRatingAgency, agency),
            rating=data.get('rating', 1),  # type: ignore # Faked
            descriptors=data.get('descriptors', []),  # type: ignore # Faked
        )

    @classmethod
    def from_dicts(cls, datas: Optional[dict]) -> List[ContentRating]:
        if not datas:
            return []
        return [cls.from_dict(data, int(agency)) for agency, data in datas.items()]

    def __repr__(self) -> str:
        return f'<ContentRating agency={self.agency!r} rating={self.rating}>'

    def to_dict(self) -> dict:
        return {'rating': int(self.rating), 'descriptors': [int(descriptor) for descriptor in self.descriptors]}


class SKU(Hashable):
    """Represents a store SKU.

    .. container:: operations

        .. describe:: x == y

            Checks if two SKUs are equal.

        .. describe:: x != y

            Checks if two SKUs are not equal.

        .. describe:: hash(x)

            Returns the SKU's hash.

        .. describe:: str(x)

            Returns the SKU's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The SKU's ID.
    name: :class:`str`
        The name of the SKU.
    name_localizations: Dict[:class:`Locale`, :class:`str`]
        The name of the SKU localized to different languages.
    summary: Optional[:class:`str`]
        The SKU's summary, if any.
    summary_localizations: Dict[:class:`Locale`, :class:`str`]
        The summary of the SKU localized to different languages.
    legal_notice: Optional[:class:`str`]
        The SKU's legal notice, if any.
    legal_notice_localizations: Dict[:class:`Locale`, :class:`str`]
        The legal notice of the SKU localized to different languages.
    type: :class:`SKUType`
        The type of the SKU.
    slug: :class:`str`
        The URL slug of the SKU.
    dependent_sku_id: Optional[:class:`int`]
        The ID of the SKU that this SKU is dependent on, if any.
    application_id: :class:`int`
        The ID of the application that owns this SKU.
    application: Optional[:class:`PartialApplication`]
        The application that owns this SKU, if available.
    price_tier: Optional[:class:`int`]
        The price tier of the SKU. This is the base price in USD.
        Not available for public SKUs.
    price_overrides: Dict[:class:`str`, :class:`int`]
        Price overrides for specific currencies. These override the base price tier.
        Not available for public SKUs.
    sale_price_tier: Optional[:class:`int`]
        The sale price tier of the SKU. This is the base sale price in USD.
        Not available for public SKUs.
    sale_price_overrides: Dict[:class:`str`, :class:`int`]
        Sale price overrides for specific currencies. These override the base sale price tier.
    price: :class:`SKUPrice`
        The price of the SKU.
    access_level: :class:`SKUAccessLevel`
        The access level of the SKU.
    features: List[:class:`SKUFeature`]
        A list of features that this SKU has.
    locales: List[:class:`Locale`]
        The locales that this SKU is available in.
    genres: List[:class:`SKUGenre`]
        The genres that apply to this SKU.
    available_regions: Optional[List[:class:`str`]]
        The regions that this SKU is available in.
        If this is ``None``, then the SKU is available everywhere.
    content_ratings: List[:class:`ContentRating`]
        The content ratings of the SKU, if any.
        For public SKUs, only the rating of your region is returned.
    system_requirements: List[:class:`SystemRequirements`]
        The system requirements of the SKU by operating system, if any.
    release_date: Optional[:class:`datetime.date`]
        The date that the SKU will released, if any.
    preorder_release_date: Optional[:class:`datetime.date`]
        The approximate date that the SKU will released for pre-order, if any.
    preorder_released_at: Optional[:class:`datetime.datetime`]
        The date that the SKU was released for pre-order, if any.
    external_purchase_url: Optional[:class:`str`]
        An external URL to purchase the SKU at, if applicable.
    premium: :class:`bool`
        Whether this SKU is provided for free to premium users.
    restricted: :class:`bool`
        Whether this SKU is restricted.
    exclusive: :class:`bool`
        Whether this SKU is exclusive to Discord.
    show_age_gate: :class:`bool`
        Whether the client should prompt the user to verify their age.
    bundled_skus: List[:class:`SKU`]
        A list of SKUs bundled with this SKU.
        These are SKUs that the user will be entitled to after purchasing this parent SKU.
    manifest_label_ids: List[:class:`int`]
        A list of manifest label IDs that this SKU is associated with.
    """

    __slots__ = (
        'id',
        'name',
        'name_localizations',
        'summary',
        'summary_localizations',
        'legal_notice',
        'legal_notice_localizations',
        'type',
        'slug',
        'price_tier',
        'price_overrides',
        'sale_price_tier',
        'sale_price_overrides',
        'price',
        'dependent_sku_id',
        'application_id',
        'application',
        'access_level',
        'features',
        'locales',
        'genres',
        'available_regions',
        'content_ratings',
        'system_requirements',
        'release_date',
        'preorder_release_date',
        'preorder_released_at',
        'external_purchase_url',
        'premium',
        'restricted',
        'exclusive',
        'show_age_gate',
        'bundled_skus',
        'manifests',
        'manifest_label_ids',
        '_flags',
        '_state',
    )

    if TYPE_CHECKING:
        name: str
        name_localizations: Dict[Locale, str]
        summary: Optional[str]
        summary_localizations: Dict[Locale, str]
        legal_notice: Optional[str]
        legal_notice_localizations: Dict[Locale, str]

    def __init__(
        self, *, data: SKUPayload, state: ConnectionState, application: Optional[PartialApplication] = None
    ) -> None:
        self._state = state
        self.application = application
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<SKU id={self.id} name={self.name!r} type={self.type!r}>'

    def _update(self, data: SKUPayload) -> None:
        from .application import PartialApplication

        state = self._state

        self.name, self.name_localizations = _parse_localizations(data, 'name')
        self.summary, self.summary_localizations = _parse_localizations(data, 'summary')
        self.legal_notice, self.legal_notice_localizations = _parse_localizations(data, 'legal_notice')

        self.id: int = int(data['id'])
        self.type: SKUType = try_enum(SKUType, data['type'])
        self.slug: str = data['slug']
        self.dependent_sku_id: Optional[int] = _get_as_snowflake(data, 'dependent_sku_id')
        self.application_id: int = int(data['application_id'])
        self.application: Optional[PartialApplication] = (
            PartialApplication(data=data['application'], state=state)
            if 'application' in data
            else (
                state.premium_subscriptions_application
                if self.application_id == state.premium_subscriptions_application.id
                else self.application
            )
        )
        self._flags: int = data.get('flags', 0)

        # This hurts me, but we have two cases here:
        # - The SKU is public and we get our local price/sale in the `price` field (an object in its entirety)
        # - The SKU is private and we get the `price`/`sale` (overrides) and `price_tier`/`sale_price_tier` fields
        #   In the above case, we construct a fake price object from the fields given
        # Unfortunately, in both cases, the `price` field may just be missing if there is no price set

        self.price_tier: Optional[int] = data.get('price_tier')
        self.price_overrides: Dict[str, int] = data.get('price') or {}  # type: ignore
        self.sale_price_tier: Optional[int] = data.get('sale_price_tier')
        self.sale_price_overrides: Dict[str, int] = data.get('sale_price') or {}

        if self.price_overrides and any(x in self.price_overrides for x in ('amount', 'currency')):
            self.price: SKUPrice = SKUPrice(data['price'])  # type: ignore
            self.price_overrides = {}
        else:
            self.price = SKUPrice.from_private(data)

        self.access_level: SKUAccessLevel = try_enum(SKUAccessLevel, data.get('access_type', 1))
        self.features: List[SKUFeature] = [try_enum(SKUFeature, feature) for feature in data.get('features', [])]
        self.locales: List[Locale] = [try_enum(Locale, locale) for locale in data.get('locales', ['en-US'])]
        self.genres: List[SKUGenre] = [try_enum(SKUGenre, genre) for genre in data.get('genres', [])]
        self.available_regions: Optional[List[str]] = data.get('available_regions')
        self.content_ratings: List[ContentRating] = (
            [ContentRating.from_dict(data['content_rating'], data['content_rating_agency'])]
            if 'content_rating' in data and 'content_rating_agency' in data
            else ContentRating.from_dicts(data.get('content_ratings'))
        )
        self.system_requirements: List[SystemRequirements] = [
            SystemRequirements.from_dict(try_enum(OperatingSystem, int(os)), reqs)
            for os, reqs in data.get('system_requirements', {}).items()
        ]

        self.release_date: Optional[date] = parse_date(data.get('release_date'))
        self.preorder_release_date: Optional[date] = parse_date(data.get('preorder_approximate_release_date'))
        self.preorder_released_at: Optional[datetime] = parse_time(data.get('preorder_release_at'))
        self.external_purchase_url: Optional[str] = data.get('external_purchase_url')

        self.premium: bool = data.get('premium', False)
        self.restricted: bool = data.get('restricted', False)
        self.exclusive: bool = data.get('exclusive', False)
        self.show_age_gate: bool = data.get('show_age_gate', False)
        self.bundled_skus: List[SKU] = [
            SKU(data=sku, state=state, application=self.application) for sku in data.get('bundled_skus', [])
        ]

        self.manifest_label_ids: List[int] = [int(label) for label in data.get('manifest_labels') or []]

    def is_free(self) -> bool:
        """:class:`bool`: Checks if the SKU is free."""
        return self.price.is_free() and not self.premium

    def is_paid(self) -> bool:
        """:class:`bool`: Checks if the SKU requires payment."""
        return not self.price.is_free() and not self.premium

    def is_preorder(self) -> bool:
        """:class:`bool`: Checks if this SKU is a preorder."""
        return self.preorder_release_date is not None or self.preorder_released_at is not None

    def is_released(self) -> bool:
        """:class:`bool`: Checks if the SKU is released."""
        return self.release_date is not None and self.release_date <= utcnow()

    def is_giftable(self) -> bool:
        """:class:`bool`: Checks if this SKU is giftable."""
        return (
            self.type == SKUType.durable_primary
            and self.flags.available
            and not self.external_purchase_url
            and self.is_paid()
        )

    def is_premium_perk(self) -> bool:
        """:class:`bool`: Checks if the SKU is a perk for premium users."""
        return self.premium and (self.flags.premium_and_distribution or self.flags.premium_purchase)

    def is_premium_subscription(self) -> bool:
        """:class:`bool`: Checks if the SKU is a premium subscription (e.g. Nitro or Server Boosts)."""
        return self.application_id == self._state.premium_subscriptions_application.id

    def is_game_awards_winner(self) -> bool:
        """:class:`bool`: Checks if the SKU is a winner of The Game Awards."""
        return self.id in THE_GAME_AWARDS_WINNERS

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the SKU."""
        return f'https://discord.com/store/skus/{self.id}/{self.slug}'

    @property
    def flags(self) -> SKUFlags:
        """:class:`SKUFlags`: Returns the SKU's flags."""
        return SKUFlags._from_value(self._flags)

    @property
    def supported_operating_systems(self) -> List[OperatingSystem]:
        """List[:class:`OperatingSystem`]: A list of supported operating systems."""
        return [reqs.os for reqs in self.system_requirements] or [OperatingSystem.windows]

    async def edit(
        self,
        name: str = MISSING,
        name_localizations: Mapping[Locale, str] = MISSING,
        legal_notice: Optional[str] = MISSING,
        legal_notice_localizations: Mapping[Locale, str] = MISSING,
        price_tier: Optional[int] = MISSING,
        price_overrides: Mapping[str, int] = MISSING,
        sale_price_tier: Optional[int] = MISSING,
        sale_price_overrides: Mapping[str, int] = MISSING,
        dependent_sku: Optional[Snowflake] = MISSING,
        flags: SKUFlags = MISSING,
        access_level: SKUAccessLevel = MISSING,
        features: Collection[SKUFeature] = MISSING,
        locales: Collection[Locale] = MISSING,
        genres: Collection[SKUGenre] = MISSING,
        content_ratings: Collection[ContentRating] = MISSING,
        system_requirements: Collection[SystemRequirements] = MISSING,
        release_date: Optional[date] = MISSING,
        bundled_skus: Sequence[Snowflake] = MISSING,
        manifest_labels: Sequence[Snowflake] = MISSING,
    ) -> None:
        """|coro|

        Edits the SKU.

        All parameters are optional.

        Parameters
        -----------
        name: :class:`str`
            The SKU's name.
        name_localizations: Dict[:class:`Locale`, :class:`str`]
            The SKU's name localized to other languages.
        legal_notice: Optional[:class:`str`]
            The SKU's legal notice.
        legal_notice_localizations: Dict[:class:`Locale`, :class:`str`]
            The SKU's legal notice localized to other languages.
        price_tier: Optional[:class:`int`]
            The price tier of the SKU.
            This is the base price in USD that other currencies will be calculated from.
        price_overrides: Dict[:class:`str`, :class:`int`]
            A mapping of currency to price. These prices override the base price tier.
        sale_price_tier: Optional[:class:`int`]
            The sale price tier of the SKU.
            This is the base sale price in USD that other currencies will be calculated from.
        sale_price_overrides: Dict[:class:`str`, :class:`int`]
            A mapping of currency to sale price. These prices override the base sale price tier.
        dependent_sku: Optional[:class:`SKU`]
            The ID of the SKU that this SKU is dependent on.
        flags: :class:`SKUFlags`
            The SKU's flags.
        access_level: :class:`SKUAccessLevel`
            The access level of the SKU.
        features: List[:class:`SKUFeature`]
            A list of features of the SKU.
        locales: List[:class:`Locale`]
            A list of locales supported by the SKU.
        genres: List[:class:`SKUGenre`]
            A list of genres of the SKU.
        content_ratings: List[:class:`ContentRating`]
            A list of content ratings of the SKU.
        system_requirements: List[:class:`SystemRequirements`]
            A list of system requirements of the SKU.
        release_date: Optional[:class:`datetime.date`]
            The release date of the SKU.
        bundled_skus: List[:class:`SKU`]
            A list SKUs that are bundled with this SKU.
        manifest_labels: List[:class:`ManifestLabel`]
            A list of manifest labels for the SKU.

        Raises
        ------
        Forbidden
            You do not have access to edit the SKU.
        HTTPException
            Editing the SKU failed.
        """
        payload = {}
        if name is not MISSING or name_localizations is not MISSING:
            payload['name'] = {
                'default': name or self.name,
                'localizations': {
                    str(k): v
                    for k, v in (
                        (name_localizations or {}) if name_localizations is not MISSING else self.name_localizations
                    ).items()
                },
            }
        if legal_notice or legal_notice_localizations:
            payload['legal_notice'] = {
                'default': legal_notice,
                'localizations': {
                    str(k): v
                    for k, v in (
                        (legal_notice_localizations or {})
                        if legal_notice_localizations is not MISSING
                        else self.legal_notice_localizations
                    ).items()
                },
            }
        if price_tier is not MISSING:
            payload['price_tier'] = price_tier
        if price_overrides is not MISSING:
            payload['price'] = {str(k): v for k, v in price_overrides.items()}
        if sale_price_tier is not MISSING:
            payload['sale_price_tier'] = sale_price_tier
        if sale_price_overrides is not MISSING:
            payload['sale_price'] = {str(k): v for k, v in (sale_price_overrides or {}).items()}
        if dependent_sku is not MISSING:
            payload['dependent_sku_id'] = dependent_sku.id if dependent_sku else None
        if flags is not MISSING:
            payload['flags'] = flags.value if flags else 0
        if access_level is not MISSING:
            payload['access_level'] = int(access_level)
        if locales is not MISSING:
            payload['locales'] = [str(l) for l in locales] if locales else []
        if features is not MISSING:
            payload['features'] = [int(f) for f in features] if features else []
        if genres is not MISSING:
            payload['genres'] = [int(g) for g in genres] if genres else []
        if content_ratings is not MISSING:
            payload['content_ratings'] = (
                {content_rating.agency: content_rating.to_dict() for content_rating in content_ratings}
                if content_ratings
                else {}
            )
        if system_requirements is not MISSING:
            payload['system_requirements'] = (
                {system_requirement.os: system_requirement.to_dict() for system_requirement in system_requirements}
                if system_requirements
                else {}
            )
        if release_date is not MISSING:
            payload['release_date'] = release_date.isoformat() if release_date else None
        if bundled_skus is not MISSING:
            payload['bundled_skus'] = [s.id for s in bundled_skus] if bundled_skus else []
        if manifest_labels is not MISSING:
            payload['manifest_labels'] = [m.id for m in manifest_labels] if manifest_labels else []

        data = await self._state.http.edit_sku(self.id, **payload)
        self._update(data)

    async def subscription_plans(
        self,
        *,
        country_code: str = MISSING,
        payment_source: Snowflake = MISSING,
        with_unpublished: bool = False,
    ) -> List[SubscriptionPlan]:
        r"""|coro|

        Returns a list of :class:`SubscriptionPlan`\s for this SKU.

        .. versionadded:: 2.0

        Parameters
        ----------
        country_code: :class:`str`
            The country code to retrieve the subscription plan prices for.
            Defaults to the country code of the current user.
        payment_source: :class:`PaymentSource`
            The specific payment source to retrieve the subscription plan prices for.
            Defaults to all payment sources of the current user.
        with_unpublished: :class:`bool`
            Whether to include unpublished subscription plans.

            If ``True``, then you require access to the application.

        Raises
        ------
        HTTPException
            Retrieving the subscription plans failed.

        Returns
        -------
        List[:class:`.SubscriptionPlan`]
            The subscription plans for this SKU.
        """
        state = self._state
        data = await state.http.get_store_listing_subscription_plans(
            self.id,
            country_code=country_code if country_code is not MISSING else None,
            payment_source_id=payment_source.id if payment_source is not MISSING else None,
            include_unpublished=with_unpublished,
        )
        return [SubscriptionPlan(state=state, data=d) for d in data]

    async def store_listings(self, localize: bool = True) -> List[StoreListing]:
        r"""|coro|

        Returns a list of :class:`StoreListing`\s for this SKU.

        Parameters
        -----------
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        ------
        Forbidden
            You do not have access to fetch store listings.
        HTTPException
            Retrieving the store listings failed.

        Returns
        -------
        List[:class:`StoreListing`]
            The store listings for this SKU.
        """
        data = await self._state.http.get_sku_store_listings(self.id, localize=localize)
        return [StoreListing(data=listing, state=self._state, application=self.application) for listing in data]

    async def create_store_listing(
        self,
        *,
        summary: str,
        summary_localizations: Optional[Mapping[Locale, str]] = None,
        description: str,
        description_localizations: Optional[Mapping[Locale, str]] = None,
        tagline: Optional[str] = None,
        tagline_localizations: Optional[Mapping[Locale, str]] = None,
        child_skus: Optional[Collection[Snowflake]] = None,
        guild: Optional[Snowflake] = None,
        published: bool = False,
        carousel_items: Optional[Collection[Union[StoreAsset, str]]] = None,
        preview_video: Optional[Snowflake] = None,
        header_background: Optional[Snowflake] = None,
        hero_background: Optional[Snowflake] = None,
        hero_video: Optional[Snowflake] = None,
        box_art: Optional[Snowflake] = None,
        thumbnail: Optional[Snowflake] = None,
        header_logo_light: Optional[Snowflake] = None,
        header_logo_dark: Optional[Snowflake] = None,
    ) -> StoreListing:
        """|coro|

        Creates a a store listing for this SKU.

        Parameters
        ----------
        summary: :class:`str`
            The summary of the store listing.
        summary_localizations: Optional[Dict[:class:`Locale`, :class:`str`]]
            The summary of the store listing localized to different languages.
        description: :class:`str`
            The description of the store listing.
        description_localizations: Optional[Dict[:class:`Locale`, :class:`str`]]
            The description of the store listing localized to different languages.
        tagline: Optional[:class:`str`]
            The tagline of the store listing.
        tagline_localizations: Optional[Dict[:class:`Locale`, :class:`str`]]
            The tagline of the store listing localized to different languages.
        child_skus: Optional[List[:class:`SKU`]]
            The child SKUs of the store listing.
        guild: Optional[:class:`Guild`]
            The guild that the store listing is for.
        published: :class:`bool`
            Whether the store listing is published.
        carousel_items: Optional[List[Union[:class:`StoreAsset`, :class:`str`]]]
            A list of carousel items to add to the store listing. These can be store assets or YouTube video IDs.
        preview_video: Optional[:class:`StoreAsset`]
            The preview video of the store listing.
        header_background: Optional[:class:`StoreAsset`]
            The header background of the store listing.
        hero_background: Optional[:class:`StoreAsset`]
            The hero background of the store listing.
        hero_video: Optional[:class:`StoreAsset`]
            The hero video of the store listing.
        box_art: Optional[:class:`StoreAsset`]
            The box art of the store listing.
        thumbnail: Optional[:class:`StoreAsset`]
            The thumbnail of the store listing.
        header_logo_light: Optional[:class:`StoreAsset`]
            The header logo image for light backgrounds.
        header_logo_dark: Optional[:class:`StoreAsset`]
            The header logo image for dark backgrounds.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the store listing.
        HTTPException
            Editing the store listing failed.
        """
        payload: Dict[str, Any] = {
            'summary': {
                'default': summary or '',
                'localizations': {str(k): v for k, v in (summary_localizations or {}).items()},
            },
            'description': {
                'default': description or '',
                'localizations': {str(k): v for k, v in (description_localizations or {}).items()},
            },
        }

        if tagline or tagline_localizations:
            payload['tagline'] = {
                'default': tagline or '',
                'localizations': {str(k): v for k, v in (tagline_localizations or {}).items()},
            }
        if child_skus:
            payload['child_sku_ids'] = [sku.id for sku in child_skus]
        if guild:
            payload['guild_id'] = guild.id
        if published:
            payload['published'] = True
        if carousel_items:
            payload['carousel_items'] = [
                item.to_carousel_item() if isinstance(item, StoreAsset) else {'youtube_video_id': item}
                for item in carousel_items
            ]
        if preview_video:
            payload['preview_video_asset_id'] = preview_video.id
        if header_background:
            payload['header_background_asset_id'] = header_background.id
        if hero_background:
            payload['hero_background_asset_id'] = hero_background.id
        if hero_video:
            payload['hero_video_asset_id'] = hero_video.id
        if box_art:
            payload['box_art_asset_id'] = box_art.id
        if thumbnail:
            payload['thumbnail_asset_id'] = thumbnail.id
        if header_logo_light:
            payload['header_logo_light_theme_asset_id'] = header_logo_light.id
        if header_logo_dark:
            payload['header_logo_dark_theme_asset_id'] = header_logo_dark.id

        data = await self._state.http.create_store_listing(self.application_id, self.id, payload)
        return StoreListing(data=data, state=self._state, application=self.application)

    async def create_discount(self, user: Snowflake, percent_off: int, *, ttl: int = 3600) -> None:
        """|coro|

        Creates a discount for this SKU for a user.

        This discount will be applied to the user's next purchase of this SKU.

        Parameters
        ----------
        user: :class:`User`
            The user to create the discount for.
        percent_off: :class:`int`
            The discount in the form of a percentage off the price to give the user.
        ttl: :class:`int`
            How long the discount should last for in seconds.
            Minimum 60 seconds, maximum 3600 seconds.

        Raises
        ------
        Forbidden
            You do not have permissions to create the discount.
        HTTPException
            Creating the discount failed.
        """
        await self._state.http.create_sku_discount(self.id, user.id, percent_off, ttl)

    async def delete_discount(self, user: Snowflake) -> None:
        """|coro|

        Deletes a discount for this SKU for a user.

        You do not need to call this after a discounted purchase has been made,
        as the discount will be automatically consumed and deleted.

        Parameters
        ----------
        user: :class:`User`
            The user to delete the discount for.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the discount.
        HTTPException
            Deleting the discount failed.
        """
        await self._state.http.delete_sku_discount(self.id, user.id)

    async def create_gift_batch(
        self,
        *,
        amount: int,
        description: str,
        entitlement_branches: Optional[List[Snowflake]] = None,
        entitlement_starts_at: Optional[date] = None,
        entitlement_ends_at: Optional[date] = None,
    ) -> GiftBatch:
        """|coro|

        Creates a gift batch for this SKU.

        Parameters
        -----------
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
        from .entitlements import GiftBatch

        state = self._state
        app_id = self.application_id
        data = await state.http.create_gift_batch(
            app_id,
            self.id,
            amount,
            description,
            entitlement_branches=[branch.id for branch in entitlement_branches] if entitlement_branches else None,
            entitlement_starts_at=entitlement_starts_at.isoformat() if entitlement_starts_at else None,
            entitlement_ends_at=entitlement_ends_at.isoformat() if entitlement_ends_at else None,
        )
        return GiftBatch(data=data, state=state, application_id=app_id)

    async def gifts(self, subscription_plan: Optional[Snowflake] = None) -> List[Gift]:
        """|coro|

        Retrieves the gifts purchased for this SKU.

        Parameters
        ----------
        subscription_plan: Optional[:class:`SubscriptionPlan`]
            The subscription plan to retrieve the gifts for.

        Raises
        ------
        HTTPException
            Retrieving the gifts failed.

        Returns
        -------
        List[:class:`Gift`]
            The gifts that have been purchased for this SKU.
        """
        from .entitlements import Gift

        data = await self._state.http.get_sku_gifts(self.id, subscription_plan.id if subscription_plan else None)
        return [Gift(data=gift, state=self._state) for gift in data]

    async def create_gift(
        self, *, subscription_plan: Optional[Snowflake] = None, gift_style: Optional[GiftStyle] = None
    ) -> Gift:
        """|coro|

        Creates a gift for this SKU.

        You must have a giftable entitlement for this SKU to create a gift.

        Parameters
        -----------
        subscription_plan: Optional[:class:`SubscriptionPlan`]
            The subscription plan to gift.
        gift_style: Optional[:class:`GiftStyle`]
            The style of the gift.

        Raises
        ------
        Forbidden
            You do not have permissions to create a gift.
        HTTPException
            Creating the gift failed.

        Returns
        -------
        :class:`Gift`
            The gift created.
        """
        from .entitlements import Gift

        state = self._state
        data = await state.http.create_gift(
            self.id,
            subscription_plan_id=subscription_plan.id if subscription_plan else None,
            gift_style=int(gift_style) if gift_style else None,
        )
        return Gift(data=data, state=state)

    async def preview_purchase(
        self, payment_source: Snowflake, *, subscription_plan: Optional[Snowflake] = None, test_mode: bool = False
    ) -> SKUPrice:
        """|coro|

        Previews a purchase of this SKU.

        Parameters
        ----------
        payment_source: :class:`PaymentSource`
            The payment source to use for the purchase.
        subscription_plan: Optional[:class:`SubscriptionPlan`]
            The subscription plan being purchased.
        test_mode: :class:`bool`
            Whether to preview the purchase in test mode.

        Raises
        ------
        HTTPException
            Previewing the purchase failed.

        Returns
        -------
        :class:`SKUPrice`
            The previewed purchase price.
        """
        data = await self._state.http.preview_sku_purchase(
            self.id, payment_source.id, subscription_plan.id if subscription_plan else None, test_mode=test_mode
        )
        return SKUPrice(data=data)

    async def purchase(
        self,
        payment_source: Optional[Snowflake] = None,
        *,
        subscription_plan: Optional[Snowflake] = None,
        expected_amount: Optional[int] = None,
        expected_currency: Optional[str] = None,
        gift: bool = False,
        gift_style: Optional[GiftStyle] = None,
        test_mode: bool = False,
        payment_source_token: Optional[str] = None,
        purchase_token: Optional[str] = None,
        return_url: Optional[str] = None,
        gateway_checkout_context: Optional[str] = None,
    ) -> Tuple[List[Entitlement], List[LibraryApplication], Optional[Gift]]:
        """|coro|

        Purchases this SKU.

        Parameters
        ----------
        payment_source: Optional[:class:`PaymentSource`]
            The payment source to use for the purchase.
            Not required for free SKUs.
        subscription_plan: Optional[:class:`SubscriptionPlan`]
            The subscription plan to purchase.
            Can only be used for premium subscription SKUs.
        expected_amount: Optional[:class:`int`]
            The expected amount of the purchase.
            This can be gotten from :attr:`price` or :meth:`preview_purchase`.

            If the value passed here does not match the actual purchase amount,
            the purchase will error.
        expected_currency: Optional[:class:`str`]
            The expected currency of the purchase.
            This can be gotten from :attr:`price` or :meth:`preview_purchase`.

            If the value passed here does not match the actual purchase currency,
            the purchase will error.
        gift: :class:`bool`
            Whether to purchase the SKU as a gift.
            Certain requirements must be met for this to be possible.
        gift_style: Optional[:class:`GiftStyle`]
            The style of the gift. Only applicable if ``gift`` is ``True``.
        test_mode: :class:`bool`
            Whether to purchase the SKU in test mode.
        payment_source_token: Optional[:class:`str`]
            The token used to authorize with the payment source.
        purchase_token: Optional[:class:`str`]
            The purchase token to use.
        return_url: Optional[:class:`str`]
            The URL to return to after the payment is complete.
        gateway_checkout_context: Optional[:class:`str`]
            The current checkout context.

        Raises
        ------
        TypeError
            ``gift_style`` was passed but ``gift`` was not ``True``.
        HTTPException
            Purchasing the SKU failed.

        Returns
        -------
        Tuple[List[:class:`Entitlement`], List[:class:`LibraryApplication`], Optional[:class:`Gift`]]
            The purchased entitlements, the library entries created, and the gift created (if any).
        """
        if not gift and gift_style:
            raise TypeError('gift_style can only be used with gifts')

        state = self._state
        data = await state.http.purchase_sku(
            self.id,
            payment_source.id if payment_source else None,
            subscription_plan_id=subscription_plan.id if subscription_plan else None,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
            gift=gift,
            gift_style=int(gift_style) if gift_style else None,
            test_mode=test_mode,
            payment_source_token=payment_source_token,
            purchase_token=purchase_token,
            return_url=return_url,
            gateway_checkout_context=gateway_checkout_context,
        )

        from .entitlements import Entitlement, Gift
        from .library import LibraryApplication

        entitlements = [Entitlement(state=state, data=entitlement) for entitlement in data.get('entitlements', [])]
        library_applications = [
            LibraryApplication(state=state, data=application) for application in data.get('library_applications', [])
        ]
        gift_code = data.get('gift_code')
        gift_ = None
        if gift_code:
            # We create fake gift data
            gift_data: GiftPayload = {
                'code': gift_code,
                'application_id': self.application_id,
                'subscription_plan_id': subscription_plan.id if subscription_plan else None,
                'sku_id': self.id,
                'gift_style': int(gift_style) if gift_style else None,  # type: ignore # Enum is identical
                'max_uses': 1,
                'uses': 0,
                'user': state.user._to_minimal_user_json(),  # type: ignore
            }
            gift_ = Gift(state=state, data=gift_data)
            if subscription_plan and isinstance(subscription_plan, SubscriptionPlan):
                gift_.subscription_plan = subscription_plan

        return entitlements, library_applications, gift_


class SubscriptionPlanPrices:
    """Represents the different prices for a :class:`SubscriptionPlan`.

    .. versionadded:: 2.0

    Attributes
    ----------
    country_code: :class:`str`
        The country code the country prices are for.
    country_prices: List[:class:`SKUPrice`]
        The prices for the country the plan is being purchased in.
    payment_source_prices: Dict[:class:`int`, List[:class:`SKUPrice`]]
        A mapping of payment source IDs to the prices for that payment source.
    """

    def __init__(self, data: SubscriptionPricesPayload):
        country_prices = data.get('country_prices') or {}
        payment_source_prices = data.get('payment_source_prices') or {}

        self.country_code: str = country_prices.get('country_code', 'US')
        self.country_prices: List[SKUPrice] = [SKUPrice(data=price) for price in country_prices.get('prices', [])]
        self.payment_source_prices: Dict[int, List[SKUPrice]] = {
            int(payment_source_id): [SKUPrice(data=price) for price in prices]
            for payment_source_id, prices in payment_source_prices.items()
        }

    def __repr__(self) -> str:
        return f'<SubscriptionPlanPrice country_code={self.country_code!r}>'


class SubscriptionPlan(Hashable):
    """Represents a subscription plan for a :class:`SKU`.

    .. container:: operations

        .. describe:: x == y

            Checks if two subscription plans are equal.

        .. describe:: x != y

            Checks if two subscription plans are not equal.

        .. describe:: hash(x)

            Returns the subscription plan's hash.

        .. describe:: str(x)

            Returns the subscription plan's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the subscription plan.
    name: :class:`str`
        The name of the subscription plan.
    sku_id: :class:`int`
        The ID of the SKU that this subscription plan is for.
    interval: :class:`SubscriptionInterval`
        The interval of the subscription plan.
    interval_count: :class:`int`
        The number of intervals that make up a subscription period.
    tax_inclusive: :class:`bool`
        Whether the subscription plan price is tax inclusive.
    prices: Dict[:class:`SubscriptionPlanPurchaseType`, :class:`SubscriptionPlanPrices`]
        The different prices of the subscription plan.
        Not available in some contexts.
    currency: Optional[:class:`str`]
        The currency of the subscription plan's price.
        Not available in some contexts.
    price: Optional[:class:`int`]
        The price of the subscription plan.
        Not available in some contexts.
    discount_price: Optional[:class:`int`]
        The discounted price of the subscription plan.
        This price is the one premium subscribers will pay, and is only available for premium subscribers.
    fallback_currency: Optional[:class:`str`]
        The fallback currency of the subscription plan's price.
        This is the currency that will be used for gifting if the user's currency is not giftable.
    fallback_price: Optional[:class:`int`]
        The fallback price of the subscription plan.
        This is the price that will be used for gifting if the user's currency is not giftable.
    fallback_discount_price: Optional[:class:`int`]
        The fallback discounted price of the subscription plan.
        This is the discounted price that will be used for gifting if the user's currency is not giftable.
    """

    _INTERVAL_TABLE = {
        SubscriptionInterval.day: 1,
        SubscriptionInterval.month: 30,
        SubscriptionInterval.year: 365,
    }

    __slots__ = (
        'id',
        'name',
        'sku_id',
        'interval',
        'interval_count',
        'tax_inclusive',
        'prices',
        'currency',
        'price_tier',
        'price',
        'discount_price',
        'fallback_currency',
        'fallback_price',
        'fallback_discount_price',
        '_state',
    )

    def __init__(
        self, *, data: Union[PartialSubscriptionPlanPayload, SubscriptionPlanPayload], state: ConnectionState
    ) -> None:
        self._state = state
        self._update(data)

    def _update(self, data: Union[PartialSubscriptionPlanPayload, SubscriptionPlanPayload]) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.sku_id: int = int(data['sku_id'])
        self.interval: SubscriptionInterval = try_enum(SubscriptionInterval, data['interval'])
        self.interval_count: int = data['interval_count']
        self.tax_inclusive: bool = data['tax_inclusive']

        self.prices: Dict[SubscriptionPlanPurchaseType, SubscriptionPlanPrices] = {
            try_enum(SubscriptionPlanPurchaseType, int(purchase_type)): SubscriptionPlanPrices(data=price_data)
            for purchase_type, price_data in (data.get('prices') or {}).items()
        }
        self.currency: Optional[str] = data.get('currency')
        self.price_tier: Optional[int] = data.get('price_tier')
        self.price: Optional[int] = data.get('price')
        self.discount_price: Optional[int] = data.get('discount_price')
        self.fallback_currency: Optional[str] = data.get('fallback_currency')
        self.fallback_price: Optional[int] = data.get('fallback_price')
        self.fallback_discount_price: Optional[int] = data.get('fallback_discount_price')

    def __repr__(self) -> str:
        return f'<SubscriptionPlan id={self.id} name={self.name!r} sku_id={self.sku_id} interval={self.interval!r} interval_count={self.interval_count}>'

    def __str__(self) -> str:
        return self.name

    @property
    def duration(self) -> timedelta:
        """:class:`datetime.timedelta`: How long the subscription plan lasts."""
        return timedelta(days=self.interval_count * self._INTERVAL_TABLE[self.interval])

    @property
    def premium_type(self) -> Optional[PremiumType]:
        """Optional[:class:`PremiumType`]: The premium type of the subscription plan, if it is a premium subscription."""
        return PremiumType.from_sku_id(self.sku_id)

    async def gifts(self) -> List[Gift]:
        """|coro|

        Retrieves the gifts purchased for this subscription plan.

        Raises
        ------
        HTTPException
            Retrieving the gifts failed.

        Returns
        -------
        List[:class:`Gift`]
            The gifts that have been purchased for this SKU.
        """
        from .entitlements import Gift

        data = await self._state.http.get_sku_gifts(self.sku_id, self.id)
        return [Gift(data=gift, state=self._state) for gift in data]

    async def create_gift(self, *, gift_style: Optional[GiftStyle] = None) -> Gift:
        """|coro|

        Creates a gift for this subscription plan.

        You must have a giftable entitlement for this subscription plan to create a gift.

        Parameters
        -----------
        gift_style: Optional[:class:`GiftStyle`]
            The style of the gift.

        Raises
        ------
        Forbidden
            You do not have permissions to create a gift.
        HTTPException
            Creating the gift failed.

        Returns
        -------
        :class:`Gift`
            The gift created.
        """
        from .entitlements import Gift

        state = self._state
        data = await state.http.create_gift(
            self.sku_id,
            subscription_plan_id=self.id,
            gift_style=int(gift_style) if gift_style else None,
        )
        return Gift(data=data, state=state)

    async def preview_purchase(self, payment_source: Snowflake, *, test_mode: bool = False) -> SKUPrice:
        """|coro|

        Previews a purchase of this subscription plan.

        Parameters
        ----------
        payment_source: :class:`PaymentSource`
            The payment source to use for the purchase.
        test_mode: :class:`bool`
            Whether to preview the purchase in test mode.

        Raises
        ------
        HTTPException
            Previewing the purchase failed.

        Returns
        -------
        :class:`SKUPrice`
            The previewed purchase price.
        """
        data = await self._state.http.preview_sku_purchase(self.id, payment_source.id, self.id, test_mode=test_mode)
        return SKUPrice(data=data)

    async def purchase(
        self,
        payment_source: Optional[Snowflake] = None,
        *,
        expected_amount: Optional[int] = None,
        expected_currency: Optional[str] = None,
        gift: bool = False,
        gift_style: Optional[GiftStyle] = None,
        test_mode: bool = False,
        payment_source_token: Optional[str] = None,
        purchase_token: Optional[str] = None,
        return_url: Optional[str] = None,
        gateway_checkout_context: Optional[str] = None,
    ) -> Tuple[List[Entitlement], List[LibraryApplication], Optional[Gift]]:
        """|coro|

        Purchases this subscription plan.

        This can only be used on premium subscription plans.

        Parameters
        ----------
        payment_source: Optional[:class:`PaymentSource`]
            The payment source to use for the purchase.
            Not required for free subscription plans.
        expected_amount: Optional[:class:`int`]
            The expected amount of the purchase.
            This can be gotten from :attr:`price` or :meth:`preview_purchase`.

            If the value passed here does not match the actual purchase amount,
            the purchase will error.
        expected_currency: Optional[:class:`str`]
            The expected currency of the purchase.
            This can be gotten from :attr:`price` or :meth:`preview_purchase`.

            If the value passed here does not match the actual purchase currency,
            the purchase will error.
        gift: :class:`bool`
            Whether to purchase the subscription plan as a gift.
            Certain requirements must be met for this to be possible.
        gift_style: Optional[:class:`GiftStyle`]
            The style of the gift. Only applicable if ``gift`` is ``True``.
        test_mode: :class:`bool`
            Whether to purchase the subscription plan in test mode.
        payment_source_token: Optional[:class:`str`]
            The token used to authorize with the payment source.
        purchase_token: Optional[:class:`str`]
            The purchase token to use.
        return_url: Optional[:class:`str`]
            The URL to return to after the payment is complete.
        gateway_checkout_context: Optional[:class:`str`]
            The current checkout context.

        Raises
        ------
        TypeError
            ``gift_style`` was passed but ``gift`` was not ``True``.
        HTTPException
            Purchasing the subscription plan failed.

        Returns
        -------
        Tuple[List[:class:`Entitlement`], List[:class:`LibraryApplication`], Optional[:class:`Gift`]]
            The purchased entitlements, the library entries created, and the gift created (if any).
        """
        if not gift and gift_style:
            raise TypeError('gift_style can only be used with gifts')

        state = self._state
        data = await self._state.http.purchase_sku(
            self.sku_id,
            payment_source.id if payment_source else None,
            subscription_plan_id=self.id,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
            gift=gift,
            gift_style=int(gift_style) if gift_style else None,
            test_mode=test_mode,
            payment_source_token=payment_source_token,
            purchase_token=purchase_token,
            return_url=return_url,
            gateway_checkout_context=gateway_checkout_context,
        )

        from .entitlements import Entitlement, Gift
        from .library import LibraryApplication

        entitlements = [Entitlement(state=state, data=entitlement) for entitlement in data.get('entitlements', [])]
        library_applications = [
            LibraryApplication(state=state, data=application) for application in data.get('library_applications', [])
        ]
        gift_code = data.get('gift_code')
        gift_ = None
        if gift_code:
            # We create fake gift data
            gift_data: GiftPayload = {
                'code': gift_code,
                'subscription_plan_id': self.id,
                'sku_id': self.sku_id,
                'gift_style': int(gift_style) if gift_style else None,  # type: ignore # Enum is identical
                'max_uses': 1,
                'uses': 0,
                'user': state.user._to_minimal_user_json(),  # type: ignore
            }
            gift_ = Gift(state=state, data=gift_data)
            gift_.subscription_plan = self

        return entitlements, library_applications, gift_
