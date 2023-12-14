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
from typing import TYPE_CHECKING, AsyncIterator, Dict, Optional, Union, overload, Literal, List, Tuple

from .asset import Asset
from .enums import EventStatus, EntityType, PrivacyLevel, try_enum
from .mixins import Hashable
from .object import Object, OLDEST_OBJECT
from .utils import parse_time, _get_as_snowflake, _bytes_to_base64_data, MISSING

if TYPE_CHECKING:
    from .types.scheduled_event import (
        GuildScheduledEvent as BaseGuildScheduledEventPayload,
        GuildScheduledEventWithUserCount as GuildScheduledEventWithUserCountPayload,
        GuildScheduledEventRecurrence as GuildScheduledEventRecurrencePayload,
        GuildScheduledEventRecurrence as GuildScheduledEventRecurrencePayload,
        GuildScheduledEventExceptionCounts as GuildScheduledEventExceptionCountsPayload,
        EntityMetadata,
    )

    from .abc import Snowflake
    from .guild import Guild
    from .channel import VoiceChannel, StageChannel
    from .state import ConnectionState
    from .user import User

    GuildScheduledEventPayload = Union[BaseGuildScheduledEventPayload, GuildScheduledEventWithUserCountPayload]

# fmt: off
__all__ = (
    "ScheduledEvent",
    "ScheduledEventRecurrence",
    "ScheduledEventExceptionCount",
)
# fmt: on


class ScheduledEventRecurrence:
    """Represents a Scheduled Event Recurrence.

    .. container:: operations

        .. descibre:: x == y

            Checks if to Scheduled Event Recurrences are equal.

    Parameters
    ----------
    start: :class:`datetime.datetime`
        When the first event of this series is started.
    end: Optional[:class:`datetime.datetime`]
        When the events of this series will stop. If none, it will repeat forever.
    frequency: :class:`int`
        The frequency the recurrence of this event will be.
    interval: :class:`int`
        The interval between events.
    count: :class:`int`
        ...
    weekdays: List[:class:`int`]
        A list of integers representing the weekdays this event will repeat in.
    n_weekdays: List[Tuple[:class:`int`, :class:`int`]]
        A list of tuples that contain the N weekday this event will repeat in.
    months: List[:class:`int`]
        A list of integers representing the months this event will repeat in.
    month_days: List[:class:`int`]
        A list of integers representing the month days this event will repeat in.

        This marks the days of the month this event will repeat in, for example, if it
        is set to `1`, this event will repeat the first day of every month.
    year_days: List[:class:`int`]
        A list of integers representing the year days this event will repeat in.

        This marks the days of the year this event will repeat in, for example, if it
        is set to `1`, this event will repeat the first day of every year.
    """

    @overload
    def __init__(
        self,
        *,
        start: datetime,
        end: Optional[datetime] = ...,
        frequency: int,
        interval: Literal[1, 2],
        count: int,
        weekdays: List[Literal[0, 1, 2, 3, 4, 5, 6]]
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        start: datetime,
        end: Optional[datetime] = ...,
        frequency: int,
        interval: Literal[1, 2],
        count: int,
        n_weekdays: List[Tuple[int, int]]
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        start: datetime,
        end: Optional[datetime] = ...,
        frequency: int,
        interval: Literal[1, 2],
        count: int,
        months: List[Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
    ) -> None:
        ...
    
    @overload
    def __init__(
        self,
        *,
        start: datetime,
        end: Optional[datetime] = ...,
        frequency: int,
        interval: Literal[1, 2],
        count: int,
        month_days: List[int]
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        start: datetime,
        end: Optional[datetime] = ...,
        frequency: int,
        interval: Literal[1, 2],
        count: int,
        year_days: List[int]
    ) -> None:
        ...

    def __init__(
        self, 
        *,
        start: datetime, 
        end: Optional[datetime] = MISSING,
        frequency: int, 
        interval: Literal[1, 2],
        count: int,
        weekdays: List[Literal[0, 1, 2, 3, 4, 5, 6]] = MISSING,
        n_weekdays: List[Tuple[int, int]] = MISSING,
        months: List[Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]] = MISSING,
        month_days: List[int] = MISSING,
        year_days: List[int] = MISSING, 
    ) -> None:
        
        if not start.tzinfo:
            raise ValueError('\'start\' must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.')
            
        if end is not MISSING:
            if end is not None:
                if not end.tzinfo:
                    raise ValueError('\'end\' must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.')

        self.start: datetime = start
        self.end: Optional[datetime] = end
        self.frequency: int = frequency
        self.interval: int = interval
        self.weekdays: List[Literal[0, 1, 2, 3, 4, 5, 6]] = weekdays
        self.n_weekdays: List[Tuple[int, int]] = n_weekdays
        self.months: List[Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]] = months
        self.month_days: List[int] = month_days
        self.year_days: List[int] = year_days
        self.count: int = count

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.start == other.start and
                self.frequency == other.frequency and
                self.interval == other.interval
            )
        return NotImplemented

    def to_dict(self) -> GuildScheduledEventRecurrencePayload:
        payload: GuildScheduledEventRecurrencePayload = {
            "start": self.start.isoformat(),
            "frequency": self.frequency,
            "interval": self.interval,
            "by_weekday": self.weekdays,
            "by_n_weekday": [{"n": n, "day": day} for n, day in self.n_weekdays], # type: ignore # Supressed error because it says int isnt compatible with int literal
            "by_month": self.months,
            "by_month_day": self.month_days,
            "by_year_day": self.year_days,
            "count": self.count
        }

        if self.end:
            payload['end'] = self.end.isoformat()
        else:
            payload['end'] = None

        return payload

    @classmethod
    def from_dict(cls, data: GuildScheduledEventRecurrencePayload) -> ScheduledEventRecurrence:
        """Creates a new instance of this class using raw data"""
        
        end: Optional[datetime] = parse_time(data['end']) if data.get('end') is not None else None
        n_weekdays: List = data.get('by_n_weekday', [])

        return cls(
            start=parse_time(data['start']),
            end=end,
            frequency=int(data['frequency']),
            interval=int(data['interval']),
            weekdays=data.get('by_weekday', []),
            n_weekdays=[(payload['n'], payload['day']) for payload in n_weekdays],
            months=data.get('by_month', []),
            month_days=data.get('by_month_day', []),
            year_days=data.get('by_year_day', []),
            count=int(data['count']) if data.get('count') is not None else 0, # type: ignore # This ensures the value is an int, and type checker complains about it
        )


class ScheduledEventExceptionCount:
    """Represents the Exception Counts in a Scheduled Event
    
    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two exceptions are equal.

        .. descibre:: x != y
            
            Checks if two exceptions are not equal.
    """

    def __init__(self, data: GuildScheduledEventExceptionCountsPayload) -> None:
        self.count: int = int(data.get('guild_scheduled_event_count'))

        self._exception_snowflakes: Dict[Union[str, int], int] = data.get('guild_scheduled_event_exception_counts', {})

    @property
    def exceptions_ids(self) -> List[int]:
        """List[:class:`int`]: A list containing all exception event IDs"""

        return [int(snowflake) for snowflake in self._exception_snowflakes.keys()]
    
    @property
    def exceptions(self) -> Dict[int, int]:
        """Dict[:class:`int`, :class:`int`]: A dict containing all the event IDs as keys
        and their exception count as value.
        """

        return {int(snowflake): count for snowflake, count in self._exception_snowflakes.items()}


class ScheduledEvent(Hashable):
    """Represents a scheduled event in a guild.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two scheduled events are equal.

        .. describe:: x != y

            Checks if two scheduled events are not equal.

        .. describe:: hash(x)

            Returns the scheduled event's hash.

    Attributes
    ----------
    id: :class:`int`
        The scheduled event's ID.
    name: :class:`str`
        The name of the scheduled event.
    description: Optional[:class:`str`]
        The description of the scheduled event.
    entity_type: :class:`EntityType`
        The type of entity this event is for.
    entity_id: Optional[:class:`int`]
        The ID of the entity this event is for if available.
    start_time: :class:`datetime.datetime`
        The time that the scheduled event will start in UTC.
    end_time: Optional[:class:`datetime.datetime`]
        The time that the scheduled event will end in UTC.
    privacy_level: :class:`PrivacyLevel`
        The privacy level of the scheduled event.
    status: :class:`EventStatus`
        The status of the scheduled event.
    user_count: :class:`int`
        The number of users subscribed to the scheduled event.
    creator: Optional[:class:`User`]
        The user that created the scheduled event.
    creator_id: Optional[:class:`int`]
        The ID of the user that created the scheduled event.

        .. versionadded:: 2.2
    location: Optional[:class:`str`]
        The location of the scheduled event.
    recurrence: Optional[:class:`ScheduledEventRecurrence`]
        The recurrence this event follows, if any.

        .. versionadded:: 2.4
    """

    __slots__ = (
        '_state',
        '_users',
        'id',
        'guild_id',
        'name',
        'description',
        'entity_type',
        'entity_id',
        'start_time',
        'end_time',
        'privacy_level',
        'status',
        '_cover_image',
        'user_count',
        'creator',
        'channel_id',
        'creator_id',
        'location',
        'recurrence',
    )

    def __init__(self, *, state: ConnectionState, data: GuildScheduledEventPayload) -> None:
        self._state = state
        self._users: Dict[int, User] = {}
        self._update(data)

    def _update(self, data: GuildScheduledEventPayload) -> None:
        self.id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.name: str = data['name']
        self.description: Optional[str] = data.get('description')
        self.entity_type: EntityType = try_enum(EntityType, data['entity_type'])
        self.entity_id: Optional[int] = _get_as_snowflake(data, 'entity_id')
        self.start_time: datetime = parse_time(data['scheduled_start_time'])
        self.privacy_level: PrivacyLevel = try_enum(PrivacyLevel, data['status'])
        self.status: EventStatus = try_enum(EventStatus, data['status'])
        self._cover_image: Optional[str] = data.get('image', None)
        self.user_count: int = data.get('user_count', 0)
        self.creator_id: Optional[int] = _get_as_snowflake(data, 'creator_id')
        self.recurrence: Optional[ScheduledEventRecurrence] = ScheduledEventRecurrence.from_dict(data['recurrence_rule']) if data.get('recurrence_rule', None) is not None else None # type: ignore
        # Checker complains that 'recurrence_rule' may be None and that ScheduledEventRecurrence.from_dict doesn't accepts None
        creator = data.get('creator')
        self.creator: Optional[User] = self._state.store_user(creator) if creator else None

        if self.creator_id is not None and self.creator is None:
            self.creator = self._state.get_user(self.creator_id)

        self.end_time: Optional[datetime] = parse_time(data.get('scheduled_end_time'))
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')

        metadata = data.get('entity_metadata')
        self._unroll_metadata(metadata)

    def _unroll_metadata(self, data: Optional[EntityMetadata]):
        self.location: Optional[str] = data.get('location') if data else None

    def __repr__(self) -> str:
        return f'<GuildScheduledEvent id={self.id} name={self.name!r} guild_id={self.guild_id!r} creator={self.creator!r}>'

    @property
    def cover_image(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: The scheduled event's cover image."""
        if self._cover_image is None:
            return None
        return Asset._from_scheduled_event_cover_image(self._state, self.id, self._cover_image)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this scheduled event is in."""
        return self._state._get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[Union[VoiceChannel, StageChannel]]:
        """Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]]: The channel this scheduled event is in."""
        return self.guild.get_channel(self.channel_id)  # type: ignore

    @property
    def url(self) -> str:
        """:class:`str`: The url for the scheduled event."""
        return f'https://discord.com/events/{self.guild_id}/{self.id}'

    async def __modify_status(self, status: EventStatus, reason: Optional[str], /) -> ScheduledEvent:
        payload = {'status': status.value}
        data = await self._state.http.edit_scheduled_event(self.guild_id, self.id, **payload, reason=reason)
        s = ScheduledEvent(state=self._state, data=data)
        s._users = self._users
        return s

    async def start(self, *, reason: Optional[str] = None) -> ScheduledEvent:
        """|coro|

        Starts the scheduled event.

        Shorthand for:

        .. code-block:: python3

            await event.edit(status=EventStatus.active)

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for starting the scheduled event.

        Raises
        ------
        ValueError
            The scheduled event has already started or has ended.
        Forbidden
            You do not have the proper permissions to start the scheduled event.
        HTTPException
            The scheduled event could not be started.

        Returns
        -------
        :class:`ScheduledEvent`
            The scheduled event that was started.
        """
        if self.status is not EventStatus.scheduled:
            raise ValueError('This scheduled event is already running.')

        return await self.__modify_status(EventStatus.active, reason)

    async def end(self, *, reason: Optional[str] = None) -> ScheduledEvent:
        """|coro|

        Ends the scheduled event.

        Shorthand for:

        .. code-block:: python3

            await event.edit(status=EventStatus.completed)

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for ending the scheduled event.

        Raises
        ------
        ValueError
            The scheduled event is not active or has already ended.
        Forbidden
            You do not have the proper permissions to end the scheduled event.
        HTTPException
            The scheduled event could not be ended.

        Returns
        -------
        :class:`ScheduledEvent`
            The scheduled event that was ended.
        """
        if self.status is not EventStatus.active:
            raise ValueError('This scheduled event is not active.')

        return await self.__modify_status(EventStatus.ended, reason)

    async def cancel(self, *, reason: Optional[str] = None) -> ScheduledEvent:
        """|coro|

        Cancels the scheduled event.

        Shorthand for:

        .. code-block:: python3

            await event.edit(status=EventStatus.cancelled)

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for cancelling the scheduled event.

        Raises
        ------
        ValueError
            The scheduled event is already running.
        Forbidden
            You do not have the proper permissions to cancel the scheduled event.
        HTTPException
            The scheduled event could not be cancelled.

        Returns
        -------
        :class:`ScheduledEvent`
            The scheduled event that was cancelled.
        """
        if self.status is not EventStatus.scheduled:
            raise ValueError('This scheduled event is already running.')

        return await self.__modify_status(EventStatus.cancelled, reason)

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        start_time: datetime = ...,
        end_time: Optional[datetime] = ...,
        privacy_level: PrivacyLevel = ...,
        status: EventStatus = ...,
        image: bytes = ...,
        reason: Optional[str] = ...,
        recurrence: Optional[ScheduledEventRecurrence] = ...,
    ) -> ScheduledEvent:
        ...

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        channel: Snowflake,
        start_time: datetime = ...,
        end_time: Optional[datetime] = ...,
        privacy_level: PrivacyLevel = ...,
        entity_type: Literal[EntityType.voice, EntityType.stage_instance],
        status: EventStatus = ...,
        image: bytes = ...,
        reason: Optional[str] = ...,
        recurrence: Optional[ScheduledEventRecurrence] = ...,
    ) -> ScheduledEvent:
        ...

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        start_time: datetime = ...,
        end_time: datetime = ...,
        privacy_level: PrivacyLevel = ...,
        entity_type: Literal[EntityType.external],
        status: EventStatus = ...,
        image: bytes = ...,
        location: str,
        reason: Optional[str] = ...,
        recurrence: Optional[ScheduledEventRecurrence] = ...,
    ) -> ScheduledEvent:
        ...

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        channel: Union[VoiceChannel, StageChannel],
        start_time: datetime = ...,
        end_time: Optional[datetime] = ...,
        privacy_level: PrivacyLevel = ...,
        status: EventStatus = ...,
        image: bytes = ...,
        reason: Optional[str] = ...,
        recurrence: Optional[ScheduledEventRecurrence] = ...,
    ) -> ScheduledEvent:
        ...

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        description: str = ...,
        start_time: datetime = ...,
        end_time: datetime = ...,
        privacy_level: PrivacyLevel = ...,
        status: EventStatus = ...,
        image: bytes = ...,
        location: str,
        reason: Optional[str] = ...,
        recurrence: Optional[ScheduledEventRecurrence] = ...,
    ) -> ScheduledEvent:
        ...

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        channel: Optional[Snowflake] = MISSING,
        start_time: datetime = MISSING,
        end_time: Optional[datetime] = MISSING,
        privacy_level: PrivacyLevel = MISSING,
        entity_type: EntityType = MISSING,
        status: EventStatus = MISSING,
        image: bytes = MISSING,
        location: str = MISSING,
        reason: Optional[str] = None,
        recurrence: Optional[ScheduledEventRecurrence] = MISSING,
    ) -> ScheduledEvent:
        r"""|coro|

        Edits the scheduled event.

        You must have :attr:`~Permissions.manage_events` to do this.

        Parameters
        -----------
        name: :class:`str`
            The name of the scheduled event.
        description: :class:`str`
            The description of the scheduled event.
        channel: Optional[:class:`~discord.abc.Snowflake`]
            The channel to put the scheduled event in. If the channel is
            a :class:`StageInstance` or :class:`VoiceChannel` then
            it automatically sets the entity type.

            Required if the entity type is either :attr:`EntityType.voice` or
            :attr:`EntityType.stage_instance`.
        start_time: :class:`datetime.datetime`
            The time that the scheduled event will start. This must be a timezone-aware
            datetime object. Consider using :func:`utils.utcnow`.
        end_time: Optional[:class:`datetime.datetime`]
            The time that the scheduled event will end. This must be a timezone-aware
            datetime object. Consider using :func:`utils.utcnow`.

            If the entity type is either :attr:`EntityType.voice` or
            :attr:`EntityType.stage_instance`, the end_time can be cleared by
            passing ``None``.

            Required if the entity type is :attr:`EntityType.external`.
        privacy_level: :class:`PrivacyLevel`
            The privacy level of the scheduled event.
        entity_type: :class:`EntityType`
            The new entity type. If the channel is a :class:`StageInstance`
            or :class:`VoiceChannel` then this is automatically set to the
            appropriate entity type.
        status: :class:`EventStatus`
            The new status of the scheduled event.
        image: Optional[:class:`bytes`]
            The new image of the scheduled event or ``None`` to remove the image.
        location: :class:`str`
            The new location of the scheduled event.

            Required if the entity type is :attr:`EntityType.external`.
        reason: Optional[:class:`str`]
            The reason for editing the scheduled event. Shows up on the audit log.

        Raises
        -------
        TypeError
            ``image`` was not a :term:`py:bytes-like object`, or ``privacy_level``
            was not a :class:`PrivacyLevel`, or ``entity_type`` was not an
            :class:`EntityType`, ``status`` was not an :class:`EventStatus`, or
            an argument was provided that was incompatible with the scheduled event's
            entity type.
        ValueError
            ``start_time`` or ``end_time`` was not a timezone-aware datetime object.
        Forbidden
            You do not have permissions to edit the scheduled event.
        HTTPException
            Editing the scheduled event failed.

        Returns
        --------
        :class:`ScheduledEvent`
            The edited scheduled event.
        """
        payload = {}
        metadata = {}

        if name is not MISSING:
            payload['name'] = name

        if start_time is not MISSING:
            if start_time.tzinfo is None:
                raise ValueError(
                    'start_time must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                )
            payload['scheduled_start_time'] = start_time.isoformat()

        if description is not MISSING:
            payload['description'] = description

        if privacy_level is not MISSING:
            if not isinstance(privacy_level, PrivacyLevel):
                raise TypeError('privacy_level must be of type PrivacyLevel.')

            payload['privacy_level'] = privacy_level.value

        if status is not MISSING:
            if not isinstance(status, EventStatus):
                raise TypeError('status must be of type EventStatus')

            payload['status'] = status.value

        if image is not MISSING:
            image_as_str: Optional[str] = _bytes_to_base64_data(image) if image is not None else image
            payload['image'] = image_as_str

        entity_type = entity_type or getattr(channel, '_scheduled_event_entity_type', MISSING)
        if entity_type is MISSING:
            if channel and isinstance(channel, Object):
                if channel.type is VoiceChannel:
                    entity_type = EntityType.voice
                elif channel.type is StageChannel:
                    entity_type = EntityType.stage_instance
            elif location not in (MISSING, None):
                entity_type = EntityType.external
        else:
            if not isinstance(entity_type, EntityType):
                raise TypeError('entity_type must be of type EntityType')

            payload['entity_type'] = entity_type.value

        if entity_type is None:
            raise TypeError(
                f'invalid GuildChannel type passed, must be VoiceChannel or StageChannel not {channel.__class__.__name__}'
            )

        _entity_type = entity_type or self.entity_type
        _entity_type_changed = _entity_type is not self.entity_type

        if _entity_type in (EntityType.stage_instance, EntityType.voice):
            if channel is MISSING or channel is None:
                if _entity_type_changed:
                    raise TypeError('channel must be set when entity_type is voice or stage_instance')
            else:
                payload['channel_id'] = channel.id

            if location not in (MISSING, None):
                raise TypeError('location cannot be set when entity_type is voice or stage_instance')
            payload['entity_metadata'] = None
        else:
            if channel not in (MISSING, None):
                raise TypeError('channel cannot be set when entity_type is external')
            payload['channel_id'] = None

            if location is MISSING or location is None:
                if _entity_type_changed:
                    raise TypeError('location must be set when entity_type is external')
            else:
                metadata['location'] = location

            if not self.end_time and (end_time is MISSING or end_time is None):
                raise TypeError('end_time must be set when entity_type is external')

        if end_time is not MISSING:
            if end_time is not None:
                if end_time.tzinfo is None:
                    raise ValueError(
                        'end_time must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                    )
                payload['scheduled_end_time'] = end_time.isoformat()
            else:
                payload['scheduled_end_time'] = end_time

        if recurrence is not MISSING:
            if recurrence is not None:
                payload['recurrence_rule'] = recurrence.to_dict()

        if metadata:
            payload['entity_metadata'] = metadata

        data = await self._state.http.edit_scheduled_event(self.guild_id, self.id, **payload, reason=reason)
        s = ScheduledEvent(state=self._state, data=data)
        s._users = self._users
        return s

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the scheduled event.

        You must have :attr:`~Permissions.manage_events` to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting the scheduled event. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the scheduled event.
        HTTPException
            Deleting the scheduled event failed.
        """
        await self._state.http.delete_scheduled_event(self.guild_id, self.id, reason=reason)

    async def users(
        self,
        *,
        limit: Optional[int] = None,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        oldest_first: bool = MISSING,
    ) -> AsyncIterator[User]:
        """|coro|

        Retrieves all :class:`User` that are subscribed to this event.

        This requires :attr:`Intents.members` to get information about members
        other than yourself.

        Raises
        -------
        HTTPException
            Retrieving the members failed.

        Returns
        --------
        List[:class:`User`]
            All subscribed users of this event.
        """

        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            users = await self._state.http.get_scheduled_event_users(
                self.guild_id, self.id, limit=retrieve, with_member=False, before=before_id
            )

            if users:
                if limit is not None:
                    limit -= len(users)

                before = Object(id=users[-1]['user']['id'])

            return users, before, limit

        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            users = await self._state.http.get_scheduled_event_users(
                self.guild_id, self.id, limit=retrieve, with_member=False, after=after_id
            )

            if users:
                if limit is not None:
                    limit -= len(users)

                after = Object(id=users[0]['user']['id'])

            return users, after, limit

        if limit is None:
            limit = self.user_count or None

        if oldest_first is MISSING:
            reverse = after is not None
        else:
            reverse = oldest_first

        predicate = None

        if reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda u: u['user']['id'] < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda u: u['user']['id'] > after.id

        while True:
            retrieve = 100 if limit is None else min(limit, 100)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)

            users = (self._state.store_user(raw_user['user']) for raw_user in data)
            count = 0

            for count, user in enumerate(users, 1):
                yield user

            if count < 100:
                # There's no data left after this
                break

    async def fetch_counts(self, *ids: int) -> Optional[ScheduledEventExceptionCount]:
        """|coro|
        
        Retrieves all the counts for this Event children, if this event isn't
        recurrent, then this will return ``None``.

        This also contains the exceptions of this Scheduled event.

        .. versionadded:: 2.4

        Parameters
        ----------
        *ids: Tuple[:class:`int`]
            All the event IDs to fetch the counts of.
            These must be children of this event.

        Raises
        ------
        HTTPException
            Fetching the count failed.

        Returns
        -------
        Optional[:class:`ScheduledEventExceptionCount`]
            The counts of this event, or ``None`` if this event isn't recurrent or there
            isn't any exception.
        """

        if not self.recurrence:
            return None

        data = await self._state.http.get_scheduled_event_counts(self.guild_id, self.id, ids)
        return ScheduledEventExceptionCount(data)

    def _add_user(self, user: User) -> None:
        self._users[user.id] = user

    def _pop_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)
