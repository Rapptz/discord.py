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

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING, overload

from .utils import find, parse_time
from .errors import InvalidArgument, InvalidData

__all__ = (
    'DiscoveryCategory',
    'DiscoveryMetadata',
)

if TYPE_CHECKING:
    from .types.discovery import (
        DiscoveryCategory as DiscoveryCategoryPayload,
        DiscoveryMetadata as DiscoveryMetadataPayload,
    )
    from .state import ConnectionState
    from .guild import Guild


class DiscoveryCategory:
    """The category that a discoverable guild can fall under.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The category's ID.
    name: :class:`str`
        The category's default name.
    localizations: Dict[:class:`str`, :class:`str`]
        The localizations of the category name.
    primary: :class:`bool`
        Whether this category can be set as a guild's
        primary category.
    """

    __slots__ = (
        'id',
        'name',
        'localizations',
        'primary',
    )

    def __init__(self, *, data: DiscoveryCategoryPayload) -> None:
        self.id: int = data['id']
        names = data['name']
        self.name: str = names['default']
        self.localizations: Dict[str, str] = names.get('localizations', {})
        self.primary: bool = data['is_primary']


class DiscoveryMetadata:
    """Represents a guild's discovery settings.

    .. versionadded:: 2.0

    Attributes
    -----------
    guild: :class:`Guild`
        The guild of these discovery settings.
    primary_category_id: :class:`int`
        The ID of the primary category set for this guild.
    keywords: List[:class:`str`]
        The keywords used for discovery search
        results.
    emoji_discoverability_enabled: :class:`bool`
        Whether a guild preview is shown when custom
        emojis are clicked in the Discord client.
    partner_actioned_timestamp: Optional[:class:`datetime.datetime`]
        When the guild's partner application was accepted
        or denied, for applications via Server Settings.
    partner_application_timestamp: Optional[:class:`datetime.datetime`]
        When the guild applied for partnership, if it has
        a pending appplication.
    category_ids: List[:class:`int`]
        IDs of up to 5 discovery subcategories set for this guild.
    """

    __slots__ = (
        'guild',
        'primary_category_id',
        'keywords',
        'emoji_discoverability_enabled',
        'subcategory_ids',
        'partner_actioned_timestamp',
        'partner_application_timestamp',
    )

    def __init__(self, *, state: ConnectionState, data: DiscoveryMetadataPayload, guild: Guild):
        self._state = state

        self.guild: Guild = guild
        self._update(data)

    def _update(self, data: DiscoveryMetadataPayload) -> None:
        self.primary_category_id: int = data['primary_category_id']
        self.keywords: List[str] = data.get('keywords', []) or []
        self.emoji_discoverability_enabled: bool = data['emoji_discoverability_enabled']
        self.subcategory_ids: List[int] = data['category_ids']

        self.partner_actioned_timestamp: Optional[datetime] = parse_time(data['partner_actioned_timestamp'])

        self.partner_application_timestamp: Optional[datetime] = parse_time(data['partner_application_timestamp'])

    @overload
    async def edit(
        self,
        *,
        primary_category: DiscoveryCategory = ...,
        keywords: List[str] = ...,
        emoji_discoverability_enabled: bool = ...,
    ) -> None:
        ...

    @overload
    async def edit(self) -> None:
        ...

    async def edit(self, **fields) -> None:
        """|coro|

        Edit the guild's discovery metadata.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Parameters
        -----------
        primary_category: :class:`DiscoveryCategory`
            The primary category that the guild will be discovered
            under.
        keywords: List[:class:`str`]
            The keywords to use for discovery search
            results.
        emoji_discoverability_enabled: :class:`boolean`
            Whether a guild preview is shown when custom
            emojis are clicked in the Discord client.

        Raises
        -------
        Forbidden
            You do not have permission to edit the discovery metadata.
        HTTPException
            Editing the discovery metadata failed.
        """
        try:
            primary_category = fields.pop('primary_category')
        except KeyError:
            pass
        else:
            if not isinstance(primary_category, DiscoveryCategory):
                raise InvalidArgument('')

            fields['primary_category_id'] = primary_category.id

        try:
            fields['keywords']
        except KeyError:
            fields['keywords'] = self.keywords

        try:
            fields['emoji_discoverability_enabled']
        except KeyError:
            fields['emoji_discoverability_enabled'] = self.emoji_discoverability_enabled

        data = await self._state.http.edit_guild_discovery_metadata(self.guild.id, **fields)
        self._update(data)

    async def primary_category(self) -> DiscoveryCategory:
        """|coro|

        Get the primary category of the guild.

        Raises
        -------
        InvalidData
            The category ID could not be recognised.
        HTTPException
            Fetching the primary category failed.

        Returns
        --------
        :class:`DiscoveryCategory`
            The primary discovery category.
        """
        data = await self._state.http.get_discovery_categories()

        category = find(lambda d: d['id'] == self.primary_category_id, data)

        if category is None:
            raise InvalidData(f'unknown primary category ID {self.primary_category_id}.')

        return DiscoveryCategory(data=category)

    async def subcategories(self) -> List[DiscoveryCategory]:
        """|coro|

        Get the subcategories of the guild.

        Raises
        -------
        HTTPException
            Fetching the subcategories failed.

        Returns
        --------
        List[:class:`DiscoveryCategory`]
            The subcategories of the guild.
        """
        data = await self._state.http.get_discovery_categories()

        relevant_categories = filter(lambda d: d['id'] in self.subcategory_ids, data)

        return [DiscoveryCategory(data=d) for d in relevant_categories]

    async def add_subcategory(self, category: DiscoveryCategory) -> None:
        """|coro|

        Add a discovery subcategory to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Raises
        -------
        Forbidden
            You do not have permission to add the subcategory.
        HTTPException
            Adding the subcategory failed.
        """
        await self._state.http.add_guild_discovery_subcategory(self.guild.id, category.id)

    async def remove_subcategory(self, category: DiscoveryCategory) -> None:
        """|coro|

        Remove a discovery subcategory to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Raises
        -------
        Forbidden
            You do not have permission to remove the subcategory.
        HTTPException
            Removing the subcategory failed.
        """
        await self._state.http.remove_guild_discovery_subcategory(self.guild.id, category.id)
