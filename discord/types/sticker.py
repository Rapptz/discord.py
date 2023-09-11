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

from typing import List, Literal, TypedDict, Union, Optional
from typing_extensions import NotRequired

from .snowflake import Snowflake
from .user import User

StickerFormatType = Literal[1, 2, 3, 4]


class StickerItem(TypedDict):
    id: Snowflake
    name: str
    format_type: StickerFormatType


class BaseSticker(TypedDict):
    id: Snowflake
    name: str
    description: str
    tags: str
    format_type: StickerFormatType


class StandardSticker(BaseSticker):
    type: Literal[1]
    sort_value: int
    pack_id: Snowflake


class GuildSticker(BaseSticker):
    type: Literal[2]
    available: NotRequired[bool]
    guild_id: Snowflake
    user: NotRequired[User]


Sticker = Union[StandardSticker, GuildSticker]


class StickerPack(TypedDict):
    id: Snowflake
    stickers: List[StandardSticker]
    name: str
    sku_id: Snowflake
    cover_sticker_id: Optional[Snowflake]
    description: str
    banner_asset_id: Optional[Snowflake]


class CreateGuildSticker(TypedDict):
    name: str
    tags: str
    description: NotRequired[str]


class ListPremiumStickerPacks(TypedDict):
    sticker_packs: List[StickerPack]
