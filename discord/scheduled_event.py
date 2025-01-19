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

from datetime import datetime, date
from typing import (
    TYPE_CHECKING,
    AsyncIterator,
    Dict,
    Optional,
    Tuple,
    Union,
    overload,
    Literal,
    List,
)
from functools import partial

from .asset import Asset
from .enums import (
    EventStatus,
    EntityType,
    PrivacyLevel,
    ScheduledEventRecurrenceFrequency,
    ScheduledEventRecurrenceWeekday,
    try_enum,
)
from .mixins import Hashable
from .object import Object, OLDEST_OBJECT
from .utils import parse_time, _get_as_snowflake, _bytes_to_base64_data, MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.scheduled_event import (
        GuildScheduledEvent as BaseGuildScheduledEventPayload,
        GuildScheduledEventWithUserCount as GuildScheduledEventWithUserCountPayload,
        ScheduledEventRecurrenceRule as ScheduledEventRecurrenceRulePayload,
        _NWeekday as NWeekdayPayload,
        EntityMetadata,
    )

    from .abc import Snowflake
    from .guild import Guild
    from .channel import VoiceChannel, StageChannel
    from .state import ConnectionState
    from .user import User

    GuildScheduledEventPayload = Union[BaseGuildScheduledEventPayload, GuildScheduledEventWithUserCountPayload]
    Week = Literal[1, 2, 3, 4, 5]
    NWeekday = Tuple[Week, ScheduledEventRecurrenceWeekday]

# fmt: off
__all__ = (
    "ScheduledEvent",
    "ScheduledEventRecurrenceRule",
)
# fmt: on


class ScheduledEventRecurrenceRule:
    """The recurrence rule for a scheduled event.

    .. versionadded:: 2.5

    Parameters
    ----------
    start: :class:`datetime.datetime`
        The datetime when the recurrence interval starts.
    frequency: :class:`ScheduledEventRecurrenceFrequency`
        How often the event occurs.
    interval: :class:`int`
        The spacing between the events, defined by ``frequency``.

        This must be ``1``, except when ``frequency`` is :attr:`ScheduledEventRecurrenceFrequency.weekly`,
        in which case it can be set to ``2``.
    weekdays: List[:class:`ScheduledEventRecurrenceWeekday`]
        The weekdays the event will recur on.

        Currently this only allows the following sets:

        If ``frequency`` is :attr`ScheduledEventRecurrenceFrequency.daily`:

        - Monday to Friday
        - Tuesday to Saturday
        - Sunday to Thursday
        - Friday & Saturday
        - Saturday & Sunday
        - Sunday & Monday

        If ``frequency`` is :attr:`ScheduledEventRecurrenceFrequency.weekly`:

        The list length can only be up to 1, every day is valid.
    n_weekdays: List[Tuple[:class:`int`, :class:`ScheduledEventRecurrenceWeekday`]]
        A (week, weekday) tuple list of the N weekdays the event will recur on.
    month_days: List[:class:`datetime.date`]
        The months and month days the scheduled event will recur on.

    Examples
    --------

    Creating a recurrence rule that repeats every weekday ::

        recurrence_rule = discord.ScheduledEventRecurrenceRule(
            start=datetime.datetime(...),
            frequency=discord.ScheduledEventRecurrenceFrequency.daily,
            interval=1,
            weekdays=[...],  # Pass any valid set of weekdays in here.
        )

    Creating a recurrence rule that repeats every (other) Wednesday ::

        recurrence_rule = discord.ScheduledEventRecurrenceRule(
            start=datetime.datetime(...),
            frequency=discord.ScheduledEventRecurrenceFrequency.weekly,
            interval=...,  # Here you can either pass 1 or 2, if you pass 1
            # then the recurrence rule is "Every Wednesday", if you pass 2
            # then the recurrence rule is "Every other Wednesday"
            weekdays=[...],  # Only 1 item is allowed as frequency is weekly
        )

    Creating a recurrence rule that repeats monthly on the fourth Wednesday ::

        recurrence_rule = discord.ScheduledEventRecurrenceRule(
            start=datetime.datetime(...),
            frequency=discord.ScheduledEventRecurrenceFrequency.monthly,
            interval=1,
            n_weekdays=[(4, discord.ScheduledEventRecurrenceWeekday.wednesday)],
        )

    Creating a recurrence rule that repeats anually on July 24 ::

        recurrence_rule = discord.ScheduledEventRecurrenceRule(
            start=datetime.datetime(...),
            frequency=discord.ScheduledEventRecurrenceFrequency.yearly,
            interval=1,
            month_days=[
                datetime.date(
                    1900,  # This is a placeholder year, it is ignored so any value is valid
                    7,  # July
                    24,  # 24th
                )
            ]
        )
    """

    __slots__ = (
        # Attributes user can set:
        'start',
        'frequency',
        'interval',
        '_weekdays',
        '_n_weekdays',
        '_month_days',
        # Attributes that are returned by API only:
        '_count',
        '_end',
        '_year_days',
    )

    @overload
    def __init__(
        self,
        /,
        start: datetime,
        frequency: Literal[
            ScheduledEventRecurrenceFrequency.daily,
            ScheduledEventRecurrenceFrequency.weekly,
        ],
        interval: int,
        *,
        weekdays: List[ScheduledEventRecurrenceWeekday],
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        /,
        start: datetime,
        frequency: Literal[ScheduledEventRecurrenceFrequency.monthly],
        interval: int,
        *,
        n_weekdays: List[NWeekday],
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        /,
        start: datetime,
        frequency: Literal[ScheduledEventRecurrenceFrequency.yearly],
        interval: int,
        *,
        month_days: List[date],
    ) -> None:
        ...

    def __init__(
        self,
        /,
        start: datetime,
        frequency: ScheduledEventRecurrenceFrequency,
        interval: int,
        *,
        weekdays: List[ScheduledEventRecurrenceWeekday] = MISSING,
        n_weekdays: List[NWeekday] = MISSING,
        month_days: List[date] = MISSING,
    ) -> None:
        self.start: datetime = start
        self.frequency: ScheduledEventRecurrenceFrequency = frequency
        self.interval: int = interval
        self._count: Optional[int] = None
        self._end: Optional[datetime] = None
        self._year_days: Optional[List[int]] = None
        # We will be keeping the MISSING values for future use in _to_dict()
        self._weekdays: Optional[List[ScheduledEventRecurrenceWeekday]] = weekdays
        self._n_weekdays: Optional[List[NWeekday]] = n_weekdays
        self._month_days: Optional[List[date]] = month_days

    def __repr__(self) -> str:
        return f'<ScheduledEventRecurrenceRule start={self.start!r} frequency={self.frequency} interval={self.interval!r}>'

    @property
    def weekdays(self) -> Optional[List[ScheduledEventRecurrenceWeekday]]:
        """Optional[List[:class:`ScheduledEventRecurrenceWeekday`]]: Returns a read-only list of the
        weekdays this event recurs on, or ``None``.
        """
        if self._weekdays in (MISSING, None):
            return None
        return self._weekdays.copy()

    @weekdays.setter
    def weekdays(self, new: Optional[List[ScheduledEventRecurrenceWeekday]]) -> None:
        self._weekdays = new

    @property
    def n_weekdays(self) -> Optional[List[NWeekday]]:
        """Optional[List[Tuple[:class:`int`, :class:`ScheduledEventRecurrenceWeekday`]]]: Returns a
        read-only list of the N weekdays this event recurs on, or ``None``.
        """
        if self._n_weekdays in (MISSING, None):
            return None
        return self._n_weekdays.copy()

    @n_weekdays.setter
    def n_weekdays(self, new: Optional[List[NWeekday]]) -> None:
        self._n_weekdays = new

    @property
    def month_days(self) -> Optional[List[date]]:
        """Optional[List[:class:`datetime.date`]]: Returns a read-only list of the month days this
        event recurs on, or ``None``.
        """
        if self._month_days in (MISSING, None):
            return None
        return self._month_days.copy()

    @month_days.setter
    def month_days(self, new: Optional[List[date]]) -> None:
        self._month_days = new

    @property
    def end(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: The ending time of the recurrence interval,
        or ``None``.
        """
        return self._end

    @property
    def count(self) -> Optional[int]:
        """Optional[:class:`int`]: The amount of times the event will recur before stopping,
        or ``None`` if it recurs forever.
        """
        return self._count

    @property
    def year_days(self) -> Optional[List[int]]:
        """Optional[List[:class:`int`]]: Returns a read-only list of the year days this
        event recurs on, or ``None``.
        """
        if self._year_days is None:
            return None
        return self._year_days.copy()

    def replace(
        self,
        *,
        weekdays: Optional[List[ScheduledEventRecurrenceWeekday]] = MISSING,
        n_weekdays: Optional[List[NWeekday]] = MISSING,
        month_days: Optional[List[date]] = MISSING,
    ) -> Self:
        """Replaces and returns the recurrence rule with the same values except for the
        ones that are changed.

        Parameters
        ----------
        weekdays: Optional[List[:class:`ScheduledEventRecurrenceWeekday`]]
            The new weekdays for the event to recur on.
        n_weekdays: Optional[List[Tuple[:class:`int`, :class:`ScheduledEventRecurrenceWeekday`]]]
            The new set of specific days within a week for the event to recur on.
        month_days: Optional[List[:class:`datetime.date`]]
            The new set of month and month days for the event to recur on.

        Returns
        -------
        :class:`ScheduledEventRecurrenceRule`
            The recurrence rule with the replaced values.
        """

        if weekdays is not MISSING:
            self._weekdays = weekdays

        if n_weekdays is not MISSING:
            self._n_weekdays = n_weekdays

        if month_days is not MISSING:
            self._month_days = month_days

        return self

    def _to_dict(self) -> ScheduledEventRecurrenceRulePayload:

        by_weekday: Optional[List[int]] = None
        by_n_weekday: Optional[List[NWeekdayPayload]] = None
        by_month: Optional[List[int]] = None
        by_month_day: Optional[List[int]] = None
        by_year_day: Optional[List[int]] = None

        if self._weekdays not in (MISSING, None):
            by_weekday = [w.value for w in self._weekdays]

        if self._n_weekdays not in (MISSING, None):
            by_n_weekday = [{'n': n, 'day': day} for n, day in self._n_weekdays]  # type: ignore

        if self._month_days not in (MISSING, None):
            by_month = []
            by_month_day = []

            for dt in self._month_days:
                by_month.append(dt.month)
                by_month_day.append(dt.day)

        if self.year_days is not None:
            by_year_day = self.year_days

        return {
            'start': self.start.isoformat(),
            'end': self._end.isoformat() if self._end is not None else None,
            'frequency': self.frequency.value,
            'interval': self.interval,
            'by_weekday': by_weekday,
            'by_n_weekday': by_n_weekday,
            'by_month': by_month,
            'by_month_day': by_month_day,
            'by_year_day': by_year_day,
            'count': self.count,
        }

    @classmethod
    def _from_data(cls, data: ScheduledEventRecurrenceRulePayload, /) -> Self:
        self = cls(
            start=parse_time(data['start']),
            frequency=try_enum(ScheduledEventRecurrenceFrequency, data['frequency']),
            interval=data['interval'],
        )  # type: ignore
        self._count = data.get('count')
        self._year_days = data.get('by_year_day')

        end = data.get('end')
        if end is not None:
            self._end = parse_time(end)

        wd_conv = partial(try_enum, ScheduledEventRecurrenceWeekday)

        raw_weekdays = data.get('by_weekday')
        if raw_weekdays is not None:
            self._weekdays = list(map(wd_conv, raw_weekdays))

        raw_n_weekdays = data.get('by_n_weekday')
        if raw_n_weekdays is not None:
            self._n_weekdays = [(n['n'], wd_conv(n['day'])) for n in raw_n_weekdays]

        raw_months = data.get('by_month')
        raw_month_days = data.get('by_month_day')

        if raw_months is not None and raw_month_days is not None:
            self._month_days = [
                date(
                    1900,  # Using this as a placeholder year, ignored anyways
                    month,
                    day,
                )
                for month, day in zip(raw_months, raw_month_days)
            ]

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
    recurrence_rule: Optional[:class:`.ScheduledEventRecurrenceRule`]
        The recurrence rule for this event, or ``None``.

        .. versionadded:: 2.5
    sku_ids: List[:class:`Object`]
        A list of objects that represent the related SKUs of this event.

        .. versionadded:: 2.5
    exceptions: List[:class:`Object`]
        A list of objects that represent the events on the recurrence rule of this event that
        were cancelled.

        .. versionadded:: 2.5
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
        'recurrence_rule',
        'sku_ids',
        'exceptions',
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

        recurrence_rule = data.get('recurrence_rule')
        self.recurrence_rule = ScheduledEventRecurrenceRule._from_data(recurrence_rule) if recurrence_rule else None

        sku_ids = data.get('sku_ids', [])
        self.sku_ids: List[Object] = list(map(Object, sku_ids))

        exceptions = data.get('guild_scheduled_events_exceptions', [])
        self.exceptions: List[Object] = list(map(Object, exceptions))

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
        recurrence_rule: Optional[ScheduledEventRecurrenceRule] = ...,
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
        recurrence_rule: Optional[ScheduledEventRecurrenceRule] = ...,
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
        recurrence_rule: Optional[ScheduledEventRecurrenceRule] = ...,
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
        recurrence_rule: Optional[ScheduledEventRecurrenceRule] = ...,
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
        recurrence_rule: Optional[ScheduledEventRecurrenceRule] = ...,
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
        recurrence_rule: Optional[ScheduledEventRecurrenceRule] = MISSING,
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
        recurrence_rule: Optional[:class:`.ScheduledEventRecurrenceRule`]
            The recurrence rule this event will follow, or ``None`` to set it to a
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

        if recurrence_rule is not MISSING:
            if recurrence_rule is not None:
                payload['recurrence_rule'] = recurrence_rule._to_dict()
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
        """Returns an :term:`asynchronous iterator` representing the users that have subscribed to
        this event.

        This requires :attr:`Intents.members` to get information about members
        other than yourself.

        Raises
        -------
        HTTPException
            Retrieving the members failed.

        Yields
        ------
        :class:`User`
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

    def _add_user(self, user: User) -> None:
        self._users[user.id] = user

    def _pop_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)
