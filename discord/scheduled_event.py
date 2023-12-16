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
    "ScheduledEventExceptionCount"
)
# fmt: on


class ScheduledEventExceptionCount:
    """Represents the exception counts in a Scheduled Event.
    
    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two Exception Counts are equal.
    """

    def __init__(self, data: GuildScheduledEventExceptionCountsPayload) -> None:
        self.count: int = int(data.get('guild_scheduled_event_count'))

        self._exception_snowflakes: Dict[Union[str, int], int] = data.get('guild_scheduled_event_exception_counts')

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.exception_ids == other.exception_ids
        return NotImplemented

    @property
    def exception_ids(self) -> List[int]:
        """List[:class:`int`]: A list containing all the exception event IDs"""
        return [int(id) for id in self._exception_snowflakes.keys()]
    
    @property
    def exceptions(self) -> Dict[int, int]:
        """Dict[:class:`int`, :class:`int`]: A dictionary containing all the
        event IDs as keys and their respective exception counts as value.
        """

        return {int(snowflake): count for snowflake, count in self._exception_snowflakes.items()}


class ScheduledEventRecurrence:
    """Represents a Scheduled Event Recurrence
    
    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two Scheduled Event Recurrences are equal

    Parameters
    ----------
    start: :class:`datetime.datetime`
        When the first event of this series is started.
    end: Optional[:class:`datetime.datetime`]
        When the events of this series will stop. If it is `None`, it will repeat forever.
    weekday: :class:`int`
        An integer representing the weekday this event will repeat in. Monday is 0
        and Sunday is 6.
    n_weekday: Tuple[:class:`int`, :class:`int`]
        A tuple that contain the N weekday this event will repeat in.

        For example, if you want for this event to repeat the 1st Monday of the month,
        then this param should have a value of `(1, 0)`. Where ``1`` represents the
        'first' and ``0`` the weekday, in this case, Monday.
    month: :class:`int`
        An integer representing the month this event will repeat in.
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
        start: datetime,
        *,
        weekdays: List[Literal[0, 1, 2, 3, 4, 5, 6]],
        end: Optional[datetime] = ...,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        start: datetime,
        *,
        n_weekday: Tuple[Literal[1, 2, 3, 4], int],
        end: Optional[datetime] = ...,
    ) -> None:
        ...
    
    @overload
    def __init__(
        self,
        start: datetime,
        *,
        month: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        month_days: List[int],
        end: Optional[datetime] = ...,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        start: datetime,
        *,
        year_days: List[int],
        end: Optional[datetime] = ...,
    ) -> None:
        ...

    def __init__(
        self,
        start: datetime,
        *,
        weekdays: List[Literal[0, 1, 2, 3, 4, 5, 6]] = MISSING,
        n_weekday: Tuple[Literal[1, 2, 3, 4], int] = MISSING,
        month: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] = MISSING,
        month_days: List[int] = MISSING,
        year_days: List[int] = MISSING,
        end: Optional[datetime] = MISSING,
    ) -> None:
        
        if not start.tzinfo:
            raise ValueError(
                '\'start\' must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
            )
        
        if end not in (MISSING, None):
            if not end.tzinfo:
                raise ValueError(
                    '\'end\' must be an aware datetime. Consider using discord.utils.utcnow() or datetime.datetime.now().astimezone() for local time.'
                )

        self.start: datetime = start
        self.end: Optional[datetime] = end if end is not MISSING else None

        self.weekdays: Optional[List[int]] = weekdays if weekdays is not MISSING else None
        self.n_weekday: Optional[Tuple[int, int]] = n_weekday if n_weekday is not MISSING else None
        self.month: Optional[int] = month if month is not MISSING else None
        self.month_days: Optional[List[int]] = month_days if month_days is not MISSING else None
        self.year_days: Optional[List[int]] = year_days if year_days is not MISSING else None
        self._interval: int = 1

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.start == other.start
            )
        return NotImplemented
    
    def __set_interval(self, value: int) -> None:
        # Inner function to set the interval to the one that we
        # recieved from the API
        self._interval: int = value

    @property
    def frequency(self) -> int:
        """:class:`int`: Returns the frequency of this recurrent scheduled event"""

        # This is now an internal parameter because if it is user-provided this could cause
        # HTTPExceptions when creating or editing events.

        if self.weekdays is not None:
            return 2 if len(self.weekdays) == 1 else 3
        elif self.n_weekday is not None:
            return 1
        elif self.month is not None and self.month_days is not None:
            return 0
        return 0 # In case None of the cases matches (i.e.: year_days) then we return 0
    
    @property
    def interval(self) -> int:
        """:class:`int`: Returns the interval of this recurrent scheduled event"""
        return self._interval
    
    def to_dict(self) -> GuildScheduledEventRecurrencePayload:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
            "by_weekday": self.weekdays or [],
            "by_month": [self.month,] if self.month else [],
            "by_month_day": self.month_days or [],
            "by_n_weekday": [self.n_weekday,] if self.n_weekday else [],
            "by_year_day": self.year_days or [],
            "count": None, # There isn't counts, yet
            "frequency": self.frequency,
            "interval": self.interval,
        } # type: ignore
    
    @classmethod
    def from_dict(cls, data: GuildScheduledEventRecurrencePayload) -> ScheduledEventRecurrence:
        self: cls = cls(
            start=datetime.fromisoformat(data.get('start')),
            weekdays=data.get('by_weekday', MISSING),
            n_weekdays=((d['n'], d['day']) for d in data.get('by_n_weekday')) if data.get('by_n_weekday', MISSING) is not MISSING else MISSING,
            month=data.get('by_month')[0] if len(data.get('by_month', [])) > 0 and data.get('by_month', MISSING) is not MISSING else MISSING,
            month_days=data.get('by_month_day', MISSING),
            year_days=data.get('by_year_day', MISSING),
            end=data.get('end', MISSING)
        ) # type: ignore

        self.__set_interval(int(data.get('interval', 1)))

        return self


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
        The recurrence rule this event follows, if any.

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
        self.recurrence: Optional[ScheduledEventRecurrence] = ScheduledEventRecurrence.from_dict(data.get('recurrence_rule')) if data.get('recurrence_rule', None) is not None else None

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
        recurrence: Optional[:class:`ScheduledEventRecurrence`]
            The recurrence rule this event will follow, or `None` to set it to a
            one-time event.

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
            else:
                payload['recurrence_rule'] = None

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

    async def fetch_counts(self, *children: Snowflake) -> ScheduledEventExceptionCount:
        """|coro|
        
        Retrieves all the counts for this Event children, if this event isn't
        recurrent, then this will return `None`.

        This also contains the exceptions of this Scheduled event.

        .. versionadded:: 2.4

        Parameters
        ----------
        *children: :class:`Snowflake`
            The snowflakes of the children to fetcht the counts of.

        Raises
        ------
        HTTPException
            Fetching the counts failed.

        Returns
        -------
        Optional[:class:`ScheduledEventExceptionCount`]
            The counts of this event, or `None` if this event isn't recurrent or
            there isn't any exception.
        """

        if not self.recurrence:
            return None
        
        data = await self._state.http.get_scheduled_event_counts(self.guild_id, self.id, tuple([child.id for child in children]))

        return ScheduledEventExceptionCount(data)

    def _add_user(self, user: User) -> None:
        self._users[user.id] = user

    def _pop_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)
