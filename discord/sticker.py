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
from typing import TYPE_CHECKING, List, Optional, Tuple, Type
import unicodedata

from .mixins import Hashable
from .utils import cached_slot_property, snowflake_time
from .enums import StickerType, StickerFormatType, try_enum

__all__ = (
    'Sticker',
    'StandardSticker',
    'GuildSticker',
)

if TYPE_CHECKING:
    import datetime
    from .state import ConnectionState
    from .user import User
    from .guild import Guild
    from .types.sticker import (
        Sticker as StickerPayload,
        StandardSticker as StandardStickerPayload,
        GuildSticker as GuildStickerPayload,
    )


class Sticker(Hashable):
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
    format: :class:`StickerType`
        The format for the sticker's image.
    """

    __slots__ = ('_state', 'id', 'name', 'description', 'pack_id', 'format', '_image', 'tags')

    def __init__(self, *, state: ConnectionState, data: StickerPayload) -> None:
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, data: StickerPayload) -> None:
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.format: StickerFormatType = try_enum(StickerFormatType, data['format_type'])

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the sticker's creation time in UTC."""
        return snowflake_time(self.id)


class StandardSticker(Sticker):
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
    pack_id: :class:`int`
        The id of the sticker's pack.
    format: :class:`StickerType`
        The format for the sticker's image.
    tags: List[:class:`str`]
        A list of tags for the sticker.
    sort_value: :class:`int`
        The sticker's sort order within its pack.
    """

    __slots__ = 'sort_value'

    def _from_data(self, data: StandardStickerPayload) -> None:
        super()._from_data(data)
        self.sort_value = data['sort_value']

        try:
            self.tags: List[str] = [tag.strip() for tag in data['tags'].split(',')]
        except KeyError:
            self.tags = []


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
    pack_id: :class:`int`
        The id of the sticker's pack.
    format: :class:`StickerType`
        The format for the sticker's image.
    available: :class:`bool`
        Whether this sticker is available for use.
    guild_id: :class:`int`
        The ID of the guild that this sticker is from.
    creator: :class:`User`
        The user that created this sticker.
    emoji: :class:`str`
        The name of a unicode emoji that represents this sticker
    """

    __slots__ = ('available', 'guild_id', 'creator', '_cs_guild')

    def _from_data(self, data: GuildStickerPayload) -> None:
        super()._from_data(data)
        self.available = data['available']
        self.guild_id = data['guild_id']
        self.creator: User = self._state.store_user(data['user'])  # Union[User, Member]?
        self.emoji: str = data['tags']

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
        description: str = None,
        emoji: str,
        reason: str,
    ) -> None:
        """|coro|

        Creates a :class:`Sticker` for the guild.

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

        if description:
            payload['description'] = description

        try:
            emoji = unicodedata.name(emoji)
        except TypeError:
            pass
        else:
            emoji = emoji.replace(' ', '_')

        payload['tags'] = emoji

        return await self._state.http.modify_guild_sticker(self.guild_id, self.id, payload, reason)


def _sticker_factory(type: StickerType) -> Tuple[Type[Sticker], StickerType]:
    if type == StickerType.standard:
        return StandardSticker, type
    elif type == StickerType.guild:
        return GuildSticker, type
    else:
        return Sticker, type
