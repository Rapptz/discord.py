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

from .enums import ReadStateType, try_enum
from .utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Self

    from .abc import MessageableChannel
    from .guild import Guild
    from .state import ConnectionState
    from .user import ClientUser
    from .types.read_state import ReadState as ReadStatePayload

# fmt: off
__all__ = (
    'ReadState',
)
# fmt: on


class ReadState:
    """Represents the read state of a resource.

    This is a purposefuly very low-level object.

    .. container:: operations

        .. describe:: x == y

            Checks if two read states are equal.

        .. describe:: x != y

            Checks if two read states are not equal.

        .. describe:: hash(x)

            Returns the read state's hash.

    .. versionadded:: 2.1

    Attributes
    -----------
    id: :class:`int`
        The ID of the resource.
    type: :class:`ReadStateType`
        The type of the read state.
    last_acked_id: :class:`int`
        The ID of the last acknowledged resource (e.g. message) in the read state.
        It may *not* point to an existing or valid resource.
    acked_pin_timestamp: Optional[:class:`datetime.datetime`]
        When the channel's pins were last acknowledged.
    badge_count: :class:`int`
        The number of badges in the read state (e.g. mentions).
    """

    __slots__ = (
        'id',
        'type',
        'last_acked_id',
        'acked_pin_timestamp',
        'badge_count',
        'last_viewed',
        '_flags',
        '_last_entity_id',
        '_state',
    )

    def __init__(self, *, state: ConnectionState, data: ReadStatePayload):
        self._state = state

        self.id: int = int(data['id'])
        self.type: ReadStateType = try_enum(ReadStateType, data.get('read_state_type', 0))
        self._last_entity_id: Optional[int] = None
        self._update(data)

    def _update(self, data: ReadStatePayload):
        self.last_acked_id: int = int(data.get('last_acked_id', data.get('last_message_id', 0)))
        self.acked_pin_timestamp: Optional[datetime] = parse_time(data.get('last_pin_timestamp'))
        self.badge_count: int = int(data.get('badge_count', data.get('mention_count', 0)))
        self.last_viewed: Optional[datetime] = parse_time(data.get('last_viewed'))
        self._flags: int = data.get('flags') or 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ReadState):
            return other.id == self.id and other.type == self.type
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, ReadState):
            return other.id != self.id or other.type != self.type
        return True

    def __hash__(self) -> int:
        return (self.id * self.type.value) >> 22

    @classmethod
    def default(cls, id: int, type: ReadStateType, *, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.id = id
        self.type = type
        self._last_entity_id = None
        self.last_acked_id = 0
        self.acked_pin_timestamp = None
        self.badge_count = 0
        return self

    @property
    def resource(self) -> Optional[Union[ClientUser, Guild, MessageableChannel]]:
        """Optional[Union[:class:`ClientUser`, :class:`Guild`, :class:`TextChannel`, :class:`StageChannel`, :class:`VoiceChannel`, :class:`Thread`, :class:`DMChannel`, :class:`GroupChannel`, :class:`PartialMessageable`]]: The entity associated with the read state."""
        state = self._state

        if self.type == ReadStateType.channel:
            return state._get_or_create_partial_messageable(self.id)  # type: ignore
        elif self.type in (ReadStateType.scheduled_events, ReadStateType.guild_home, ReadStateType.onboarding):
            return state._get_or_create_unavailable_guild(self.id)
        elif self.type == ReadStateType.notification_center and self.id == state.self_id:
            return state.user

    @property
    def last_entity_id(self) -> int:
        """:class:`int`: The ID of the last resource (e.g. message) in the read state.
        It may *not* point to an existing or valid resource.
        """
        if self._last_entity_id is not None:
            return self._last_entity_id
        resource = self.resource
        if not resource:
            return 0

        if self.type == ReadStateType.channel:
            return resource.last_message_id or 0  # type: ignore
        elif self.type == ReadStateType.scheduled_events:
            return max(resource.scheduled_events, key=lambda e: e.id).id  # type: ignore
        return 0

    @property
    def last_pin_timestamp(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: When the last pinned message was pinned in the channel."""
        if self.resource and hasattr(self.resource, 'last_pin_timestamp'):
            return self.resource.last_pin_timestamp  # type: ignore

    async def delete(self):
        """|coro|

        Deletes the read state.

        Raises
        -------
        HTTPException
            Deleting the read state failed.
        """
        state = self._state
        await state.http.delete_read_state(self.id, self.type.value)
        state.remove_read_state(self)
