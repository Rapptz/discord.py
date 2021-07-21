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
from typing import TYPE_CHECKING, List, Optional, Tuple, Type, Union
import unicodedata

from .mixins import Hashable
from .asset import Asset, AssetMixin
from .utils import cached_slot_property, snowflake_time, get, MISSING
from .enums import StickerType, StickerFormatType, try_enum
from .user import User

__all__ = (
    'StickerPack',
    'StickerItem',
    'Sticker',
    'StandardSticker',
    'GuildSticker',
)

if TYPE_CHECKING:
    import datetime
    from .state import ConnectionState
    from .guild import Guild
    from .types.sticker import (
        StickerPack as StickerPackPayload,
        StickerItem as StickerItemPayload,
        Sticker as StickerPayload,
        StandardSticker as StandardStickerPayload,
        GuildSticker as GuildStickerPayload,
    )


class StickerPack(Hashable):
    """Represents a sticker pack.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker pack.

        .. describe:: x == y

           Checks if the sticker pack is equal to another sticker pack.

        .. describe:: x != y

           Checks if the sticker pack is not equal to another sticker pack.

    Attributes
    -----------
    name: :class:`str`
        The name of the sticker pack.
    description: :class:`str`
        The description of the sticker pack.
    id: :class:`int`
        The id of the sticker pack.
    stickers: List[:class:`StandardSticker`]
        The stickers of this sticker pack.
    sku_id: :class:`int`
        The SKU ID of the sticker pack.
    cover_sticker_id: :class:`int`
         The ID of the sticker used for the cover of the sticker pack.
    cover_sticker: :class:`StandardSticker`
        The sticker used for the cover of the sticker pack.
    banner: :class:`Asset`
        The banner asset of the sticker pack.
    """

    __slots__ = (
        '_state',
        'id',
        'stickers',
        'name',
        'sku_id',
        'cover_sticker_id',
        'cover_sticker',
        'description',
        '_banner',
        'banner',
    )

    def __init__(self, *, state: ConnectionState, data: StickerPackPayload) -> None:
        self._state = state
        self._from_data(data)

    def _from_data(self, data: StickerPackPayload) -> None:
        self.id = int(data['id'])
        stickers = data['stickers']
        self.stickers = [StandardSticker(state=self._state, data=sticker) for sticker in stickers]
        self.name = data['name']
        self.sku_id = int(data['sku_id'])
        self.cover_sticker_id = int(data['cover_sticker_id'])
        self.cover_sticker = get(self.stickers, id=self.cover_sticker_id)
        self.description = data['description']
        self._banner = int(data['banner_asset_id'])
        self.banner = Asset._from_sticker_banner(self._state, self._banner)

    def __repr__(self) -> str:
        return f'<StickerPack id={self.id} name={self.name!r} description={self.description!r}>'

    def __str__(self) -> str:
        return self.name


class _StickerTag(Hashable, AssetMixin):
    __slots__ = ()

    id: int
    format: StickerFormatType

    async def read(self):
        """|coro|

        Retrieves the content of this sticker as a :class:`bytes` object.

        .. note::

            Stickers that use the :attr:`StickerFormatType.lottie` format cannot be read.

        Raises
        ------
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        -------
        :class:`bytes`
            The content of the asset.
        """
        if self.format is StickerFormatType.lottie:
            raise TypeError('Cannot read stickers of format "lottie".')
        return await super().read()


class StickerItem(_StickerTag):
    """Represents a sticker item.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker item.

        .. describe:: x == y

           Checks if the sticker item is equal to another sticker item.

        .. describe:: x != y

           Checks if the sticker item is not equal to another sticker item.

    Attributes
    -----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    format: :class:`StickerFormatType`
        The format for the sticker's image.
    """

    __slots__ = ('_state', 'name', 'id', 'format', 'url')

    def __init__(self, *, state: ConnectionState, data: StickerItemPayload):
        self._state: ConnectionState = state
        self.name = data['name']
        self.id = int(data['id'])
        self.format: StickerFormatType = try_enum(StickerFormatType, data['format_type'])
        self.url = f'{Asset.BASE}/stickers/{self.id}.{self.format.file_extension or self.format.value}'

    def __repr__(self) -> str:
        return f'<StickerItem id={self.id} name={self.name!r} format={self.format}>'

    def __str__(self) -> str:
        return self.name

    async def fetch(self) -> Union[Sticker, StandardSticker, GuildSticker]:
        """|coro|

        Attempts to retrieve the full sticker data of the sticker item.

        Raises
        --------
        :exc:`.HTTPException`
            Retrieving the sticker failed.

        Returns
        --------
        Union[:class:`StandardSticker`, :class:`GuildSticker`]
            The retrieved sticker.
        """
        data: StickerPayload = self._state.http.get_sticker(self.id)
        cls, _ = _sticker_factory(data['type'])  # type: ignore
        return cls(state=self._state, data=data)


class Sticker(_StickerTag):
    """Represents a sticker.

    .. versionadded:: 1.6

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker.

        .. describe:: x == y

           Checks if the sticker is equal to another sticker.

        .. describe:: x != y

           Checks if the sticker is not equal to another sticker.

    Attributes
    ----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    description: :class:`str`
        The description of the sticker.
    pack_id: :class:`int`
        The id of the sticker's pack.
    format: :class:`StickerFormatType`
        The format for the sticker's image.
    url: :class:`str`
        The URL for the sticker's image.
    """

    __slots__ = ('_state', 'id', 'name', 'description', 'format', 'tags')

    def __init__(self, *, state: ConnectionState, data: StickerPayload) -> None:
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, data: StickerPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.format: StickerFormatType = try_enum(StickerFormatType, data['format_type'])
        self.url = f'{Asset.BASE}/stickers/{self.id}.{self.format.file_extension or self.format.value}'

    def __repr__(self) -> str:
        return f'<Sticker id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the sticker's creation time in UTC."""
        return snowflake_time(self.id)


class StandardSticker(Sticker):
    """Represents a sticker that is found in a standard sticker pack.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker.

        .. describe:: x == y

           Checks if the sticker is equal to another sticker.

        .. describe:: x != y

           Checks if the sticker is not equal to another sticker.

    Attributes
    ----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    description: :class:`str`
        The description of the sticker.
    pack_id: :class:`int`
        The id of the sticker's pack.
    format: :class:`StickerFormatType`
        The format for the sticker's image.
    tags: List[:class:`str`]
        A list of tags for the sticker.
    sort_value: :class:`int`
        The sticker's sort order within its pack.
    """

    __slots__ = ('sort_value', 'pack_id', 'type')

    def _from_data(self, data: StandardStickerPayload) -> None:
        super()._from_data(data)
        self.sort_value = data['sort_value']
        self.pack_id = data['pack_id']
        self.type = StickerType.standard

        try:
            self.tags: List[str] = [tag.strip() for tag in data['tags'].split(',')]
        except KeyError:
            self.tags = []

    def __repr__(self) -> str:
        return f'<StandardSticker id={self.id} name={self.name!r} pack_id={self.pack_id}>'


class GuildSticker(Sticker):
    """Represents a sticker that belongs to a guild.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker.

        .. describe:: x == y

           Checks if the sticker is equal to another sticker.

        .. describe:: x != y

           Checks if the sticker is not equal to another sticker.

    Attributes
    ----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    description: :class:`str`
        The description of the sticker.
    format: :class:`StickerFormatType`
        The format for the sticker's image.
    available: :class:`bool`
        Whether this sticker is available for use.
    guild_id: :class:`int`
        The ID of the guild that this sticker is from.
    user: :class:`User`
        The user that created this sticker. This can only be retrieved using :meth:`Guild.fetch_sticker` and
        having the :attr:`~Permissions.manage_emojis_and_stickers` permission.
    emoji: :class:`str`
        The name of a unicode emoji that represents this sticker
    """

    __slots__ = ('available', 'guild_id', 'creator', 'emoji', 'type', '_cs_guild')

    def _from_data(self, data: GuildStickerPayload) -> None:
        super()._from_data(data)
        self.available = data['available']
        self.guild_id = data['guild_id']
        user = data.get('user')
        self.user: Optional[User] = User(state=self._state, data=user) if user else None
        self.emoji: str = data['tags']
        self.type = StickerType.guild

    def __repr__(self) -> str:
        return f'<GuildSticker name={self.name!r} id={self.id} guild_id={self.guild_id} creator={self.creator!r}>'

    @cached_slot_property('_cs_guild')
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild that this sticker is from.
        Could be ``None`` if the bot is not in the guild.

        .. versionadded:: 2.0
        """
        return self._state._get_guild(self.guild_id)

    async def edit(
        self,
        *,
        name: str,
        description: str = MISSING,
        emoji: str,
        reason: str,
    ) -> None:
        """|coro|

        Edits a :class:`Sticker` for the guild.

        Parameters
        -----------
        name: :class:`str`
            The sticker name. Must be at least 2 characters.
        description: Optional[:class:`str`]
            The sticker's description. Can be ``None``.
        emoji: :class:`str`
            The name of a unicode emoji that represents the sticker's expression.
        file: :class:`File`
            The file of the sticker to upload.
        reason: :class:`str`
            The reason for creating this sticker. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to edit stickers.
        HTTPException
            An error occurred creating an sticker.
        """
        payload = {
            'name': name,
        }

        if description is not MISSING:
            payload['description'] = description

        try:
            emoji = unicodedata.name(emoji)
        except TypeError:
            pass
        else:
            emoji = emoji.replace(' ', '_')

        payload['tags'] = emoji

        return await self._state.http.modify_guild_sticker(self.guild_id, self.id, payload, reason)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the custom :class:`Sticker` from the guild.

        You must have :attr:`~Permissions.manage_emojis_and_stickers` permission to
        do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this sticker. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to delete stickers.
        HTTPException
            An error occurred deleting the sticker.
        """
        await self._state.http.delete_guild_sticker(self.guild_id, self.id, reason)


def _sticker_factory(type: StickerType) -> Tuple[Type[Union[StandardSticker, GuildSticker, Sticker]], StickerType]:
    if type == StickerType.standard:
        return StandardSticker, type
    elif type == StickerType.guild:
        return GuildSticker, type
    else:
        return Sticker, type
