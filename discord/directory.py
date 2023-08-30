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

from typing import TYPE_CHECKING, Optional, Union

from .enums import DirectoryCategory, DirectoryEntryType, try_enum
from .scheduled_event import ScheduledEvent
from .utils import MISSING, parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .channel import DirectoryChannel
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .types.directory import (
        DirectoryEntry as DirectoryEntryPayload,
        PartialDirectoryEntry as PartialDirectoryEntryPayload,
    )

__all__ = ('DirectoryEntry',)


class DirectoryEntry:
    """Represents a directory entry for a channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two entries are equal.

        .. describe:: x != y

            Checks if two entries are not equal.

        .. describe:: hash(x)

            Returns the entry's hash.

    .. versionadded:: 2.1

    Attributes
    -----------
    channel: :class:`DirectoryChannel`
        The channel this entry is from.
    type: :class:`DirectoryEntryType`
        The type of this entry.
    category: :class:`DirectoryCategory`
        The primary category of this entry.
    author_id: :class:`int`
        The ID of the user who created this entry.
    created_at: :class:`datetime.datetime`
        When this entry was created.
    description: Optional[:class:`str`]
        The description of the entry's guild.
        Only applicable for entries of type :attr:`DirectoryEntryType.guild`.
    entity_id: :class:`int`
        The ID of the entity this entry represents.
    guild: Optional[:class:`Guild`]
        The guild this entry represents.
        For entries of type :attr:`DirectoryEntryType.scheduled_event`,
        this is the guild the scheduled event is from.
        Not available in all contexts.
    featurable: :class:`bool`
        Whether this entry's guild can be featured in the directory.
        Only applicable for entries of type :attr:`DirectoryEntryType.guild`.
    scheduled_event: Optional[:class:`ScheduledEvent`]
        The scheduled event this entry represents.
        Only applicable for entries of type :attr:`DirectoryEntryType.scheduled_event`.
    rsvp: :class:`bool`
        Whether the current user has RSVP'd to the scheduled event.
        Only applicable for entries of type :attr:`DirectoryEntryType.scheduled_event`.
    """

    def __init__(
        self,
        *,
        data: Union[DirectoryEntryPayload, PartialDirectoryEntryPayload],
        state: ConnectionState,
        channel: DirectoryChannel,
    ):
        self.channel = channel
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<DirectoryEntry channel={self.channel!r} type={self.type!r} category={self.category!r} author_id={self.author_id!r} guild={self.guild!r}>'

    def __hash__(self) -> int:
        return hash((self.channel.id, self.entity_id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DirectoryEntry):
            return self.channel == other.channel and self.entity_id == other.entity_id
        return NotImplemented

    def _update(self, data: Union[DirectoryEntryPayload, PartialDirectoryEntryPayload]):
        state = self._state
        self.type: DirectoryEntryType = try_enum(DirectoryEntryType, data['type'])
        self.category: DirectoryCategory = try_enum(DirectoryCategory, data.get('primary_category_id', 0))
        self.author_id: int = int(data['author_id'])
        self.created_at: datetime = parse_time(data['created_at'])
        self.description: Optional[str] = data.get('description') or None
        self.entity_id: int = int(data['entity_id'])

        guild_data = data.get('guild', data.get('guild_scheduled_event', {}).get('guild'))
        self.guild: Optional[Guild] = state.create_guild(guild_data) if guild_data is not None else None
        self.featurable: bool = guild_data.get('featurable_in_directory', False) if guild_data is not None else False

        event_data = data.get('guild_scheduled_event')
        self.scheduled_event: Optional[ScheduledEvent] = (
            ScheduledEvent(data=event_data, state=state) if event_data is not None else None
        )
        self.rsvp: bool = event_data.get('user_rsvp', False) if event_data is not None else False

    @property
    def author(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member that created this entry."""
        return self.channel.guild.get_member(self.author_id)

    async def edit(self, *, description: Optional[str] = MISSING, category: DirectoryCategory = MISSING) -> None:
        """|coro|

        Edits this directory entry.
        Only entries of type :attr:`DirectoryEntryType.guild` can be edited.

        You must be the author of the entry or have
        :attr:`~Permissions.manage_guild` in the represented guild to edit it.

        Parameters
        -----------
        description: Optional[:class:`str`]
            The new description of the entry's guild.
        category: :class:`DirectoryCategory`
            The new primary category of the entry.

        Raises
        -------
        Forbidden
            You do not have permissions to edit this entry.
        HTTPException
            Editing the entry failed.
        """
        data = await self._state.http.edit_directory_entry(
            self.channel.id,
            self.entity_id,
            description=description,
            primary_category_id=category.value if category is not MISSING else MISSING,
        )
        self._update(data)

    async def delete(self) -> None:
        """|coro|

        Deletes this directory entry.

        You must be the author of the entry or have
        :attr:`~Permissions.manage_guild` in the represented guild to delete it.

        Raises
        -------
        Forbidden
            You do not have permissions to delete this entry.
        HTTPException
            Deleting the entry failed.
        """
        await self._state.http.delete_directory_entry(self.channel.id, self.entity_id)
