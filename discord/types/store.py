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

from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

from .application import PartialApplication, StoreAsset
from .entitlements import Entitlement
from .guild import PartialGuild
from .library import LibraryApplication
from .snowflake import Snowflake
from .user import PartialUser

LOCALIZED_STR = Union[str, Dict[str, str]]


class StoreNote(TypedDict):
    content: str
    user: Optional[PartialUser]


class SystemRequirement(TypedDict, total=False):
    ram: int
    disk: int
    operating_system_version: LOCALIZED_STR
    cpu: LOCALIZED_STR
    gpu: LOCALIZED_STR
    sound_card: LOCALIZED_STR
    directx: LOCALIZED_STR
    network: LOCALIZED_STR
    notes: LOCALIZED_STR


class SystemRequirements(TypedDict, total=False):
    minimum: SystemRequirement
    recommended: SystemRequirement


class CarouselItem(TypedDict, total=False):
    asset_id: Snowflake
    youtube_video_id: str


class StoreListing(TypedDict):
    id: Snowflake
    summary: NotRequired[LOCALIZED_STR]
    description: NotRequired[LOCALIZED_STR]
    tagline: NotRequired[LOCALIZED_STR]
    flavor_text: NotRequired[str]
    published: NotRequired[bool]
    entitlement_branch_id: NotRequired[Snowflake]
    staff_notes: NotRequired[StoreNote]
    guild: NotRequired[PartialGuild]
    assets: NotRequired[List[StoreAsset]]
    carousel_items: NotRequired[List[CarouselItem]]
    preview_video: NotRequired[StoreAsset]
    header_background: NotRequired[StoreAsset]
    hero_background: NotRequired[StoreAsset]
    hero_video: NotRequired[StoreAsset]
    box_art: NotRequired[StoreAsset]
    thumbnail: NotRequired[StoreAsset]
    header_logo_light_theme: NotRequired[StoreAsset]
    header_logo_dark_theme: NotRequired[StoreAsset]
    sku: SKU
    child_skus: NotRequired[List[SKU]]
    alternative_skus: NotRequired[List[SKU]]


class SKUPrice(TypedDict):
    currency: str
    amount: int
    sale_amount: NotRequired[Optional[int]]
    sale_percentage: NotRequired[int]
    premium: NotRequired[bool]


class ContentRating(TypedDict):
    rating: int
    descriptors: List[int]


class PartialSKU(TypedDict):
    id: Snowflake
    type: Literal[1, 2, 3, 4, 5, 6]
    premium: bool
    preorder_release_date: Optional[str]
    preorder_released_at: Optional[str]


class SKU(PartialSKU):
    id: Snowflake
    type: Literal[1, 2, 3, 4, 5, 6]
    name: LOCALIZED_STR
    summary: NotRequired[LOCALIZED_STR]
    legal_notice: NotRequired[LOCALIZED_STR]
    slug: str
    dependent_sku_id: Optional[Snowflake]
    application_id: Snowflake
    application: NotRequired[PartialApplication]
    flags: int
    price_tier: NotRequired[int]
    price: NotRequired[Union[SKUPrice, Dict[str, int]]]
    sale_price_tier: NotRequired[int]
    sale_price: NotRequired[Dict[str, int]]
    access_level: Literal[1, 2, 3]
    features: List[int]
    locales: NotRequired[List[str]]
    genres: NotRequired[List[int]]
    available_regions: NotRequired[List[str]]
    content_rating_agency: NotRequired[Literal[1, 2]]
    content_rating: NotRequired[ContentRating]
    content_ratings: NotRequired[Dict[Literal[1, 2], ContentRating]]
    system_requirements: NotRequired[Dict[Literal[1, 2, 3], SystemRequirements]]
    release_date: Optional[str]
    preorder_release_date: NotRequired[Optional[str]]
    preorder_released_at: NotRequired[Optional[str]]
    external_purchase_url: NotRequired[str]
    premium: NotRequired[bool]
    restricted: NotRequired[bool]
    exclusive: NotRequired[bool]
    show_age_gate: bool
    bundled_skus: NotRequired[List[SKU]]
    manifest_labels: Optional[List[Snowflake]]


class SKUPurchase(TypedDict):
    entitlements: List[Entitlement]
    library_applications: NotRequired[List[LibraryApplication]]
    gift_code: NotRequired[str]
