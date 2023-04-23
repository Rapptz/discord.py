"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

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

import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from . import utils
from .asset import Asset
from .enums import (
    ScheduledEventLocationType,
    ScheduledEventPrivacyLevel,
    ScheduledEventStatus,
    try_enum,
)
from .errors import ValidationError
from .iterators import ScheduledEventSubscribersIterator
from .mixins import Hashable
from .object import Object

__all__ = (
    "ScheduledEvent",
    "ScheduledEventLocation",
)

if TYPE_CHECKING:
    from .abc import Snowflake
    from .guild import Guild
    from .iterators import AsyncIterator
    from .member import Member
    from .state import ConnectionState
    from .types.channel import StageChannel, VoiceChannel
    from .types.scheduled_events import ScheduledEvent as ScheduledEventPayload

MISSING = utils.MISSING


class ScheduledEventLocation:
    """Represents a scheduled event's location.

    Setting the ``value`` to its corresponding type will set the location type automatically:

    +------------------------+---------------------------------------------------+
    |     Type of Input      |                   Location Type                   |
    +========================+===================================================+
    | :class:`StageChannel`: | :attr:`ScheduledEventLocationType.stage_instance` |
    | :class:`VoiceChannel`: | :attr:`ScheduledEventLocationType.voice`          |
    | :class:`str`:          | :attr:`ScheduledEventLocationType.external`       |
    +------------------------+---------------------------------------------------+

    .. versionadded:: 2.0

    Attributes
    ----------
    value: Union[:class:`str`, :class:`StageChannel`, :class:`VoiceChannel`, :class:`Object`]
        The actual location of the scheduled event.
    type: :class:`ScheduledEventLocationType`
        The type of location.
    """

    __slots__ = (
        "_state",
        "value",
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        value: Union[str, int, StageChannel, VoiceChannel],
    ):
        self._state = state
        self.value: Union[str, StageChannel, VoiceChannel, Object]
        if isinstance(value, int):
            self.value = self._state.get_channel(id=int(value)) or Object(id=int(value))
        else:
            self.value = value

    def __repr__(self) -> str:
        return f"<ScheduledEventLocation value={self.value!r} type={self.type}>"

    def __str__(self) -> str:
        return str(self.value)

    @property
    def type(self) -> ScheduledEventLocationType:
        if isinstance(self.value, str):
            return ScheduledEventLocationType.external
        elif self.value.__class__.__name__ == "StageChannel":
            return ScheduledEventLocationType.stage_instance
        elif self.value.__class__.__name__ == "VoiceChannel":
            return ScheduledEventLocationType.voice


class ScheduledEvent(Hashable):
    """Represents a Discord Guild Scheduled Event.

    .. container:: operations

        .. describe:: x == y

            Checks if two scheduled events are equal.

        .. describe:: x != y

            Checks if two scheduled events are not equal.

        .. describe:: hash(x)

            Returns the scheduled event's hash.

        .. describe:: str(x)

            Returns the scheduled event's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    guild: :class:`Guild`
        The guild where the scheduled event is happening.
    name: :class:`str`
        The name of the scheduled event.
    description: Optional[:class:`str`]
        The description of the scheduled event.
    start_time: :class:`datetime.datetime`
        The time when the event will start
    end_time: Optional[:class:`datetime.datetime`]
        The time when the event is supposed to end.
    status: :class:`ScheduledEventStatus`
        The status of the scheduled event.
    location: :class:`ScheduledEventLocation`
        The location of the event.
        See :class:`ScheduledEventLocation` for more information.
    subscriber_count: Optional[:class:`int`]
        The number of users that have marked themselves as interested for the event.
    creator_id: Optional[:class:`int`]
        The ID of the user who created the event.
        It may be ``None`` because events created before October 25th, 2021, haven't
        had their creators tracked.
    creator: Optional[:class:`User`]
        The resolved user object of who created the event.
    privacy_level: :class:`ScheduledEventPrivacyLevel`
        The privacy level of the event. Currently, the only possible value
        is :attr:`ScheduledEventPrivacyLevel.guild_only`, which is default,
        so there is no need to use this attribute.
    """

    __slots__ = (
        "id",
        "name",
        "description",
        "start_time",
        "end_time",
        "status",
        "creator_id",
        "creator",
        "location",
        "guild",
        "_state",
        "_cover",
        "subscriber_count",
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        guild: Guild,
        creator: Optional[Member],
        data: ScheduledEventPayload,
    ):
        self._state: ConnectionState = state

        self.id: int = int(data.get("id"))
        self.guild: Guild = guild
        self.name: str = data.get("name")
        self.description: Optional[str] = data.get("description", None)
        self._cover: Optional[str] = data.get("image", None)
        self.start_time: datetime.datetime = datetime.datetime.fromisoformat(data.get("scheduled_start_time"))
        end_time = data.get("scheduled_end_time", None)
        if end_time != None:
            end_time = datetime.datetime.fromisoformat(end_time)
        self.end_time: Optional[datetime.datetime] = end_time
        self.status: ScheduledEventStatus = try_enum(ScheduledEventStatus, data.get("status"))
        self.subscriber_count: Optional[int] = data.get("user_count", None)
        self.creator_id = data.get("creator_id", None)
        self.creator: Optional[Member] = creator

        entity_metadata = data.get("entity_metadata")
        channel_id = data.get("channel_id", None)
        if channel_id is None:
            self.location = ScheduledEventLocation(state=state, value=entity_metadata["location"])
        else:
            self.location = ScheduledEventLocation(state=state, value=int(channel_id))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"<ScheduledEvent id={self.id} "
            f"name={self.name} "
            f"description={self.description} "
            f"start_time={self.start_time} "
            f"end_time={self.end_time} "
            f"location={self.location!r} "
            f"status={self.status.name} "
            f"subscriber_count={self.subscriber_count} "
            f"creator_id={self.creator_id}>"
        )

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the scheduled event's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def interested(self) -> Optional[int]:
        """An alias to :attr:`.subscriber_count`"""
        return self.subscriber_count

    @property
    def url(self) -> str:
        """:class:`str`: The url to reference the scheduled event."""
        return f"https://discord.com/events/{self.guild.id}/{self.id}"

    @property
    def cover(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the scheduled event cover image asset, if available."""
        if self._cover is None:
            return None
        return Asset._from_scheduled_event_cover(
            self._state,
            self.id,
            self._cover,
        )

    async def edit(
        self,
        *,
        reason: Optional[str] = None,
        name: str = MISSING,
        description: str = MISSING,
        status: Union[int, ScheduledEventStatus] = MISSING,
        location: Union[str, int, VoiceChannel, StageChannel, ScheduledEventLocation] = MISSING,
        start_time: datetime.datetime = MISSING,
        end_time: datetime.datetime = MISSING,
        cover: Optional[bytes] = MISSING,
        privacy_level: ScheduledEventPrivacyLevel = ScheduledEventPrivacyLevel.guild_only,
    ) -> Optional[ScheduledEvent]:
        """|coro|

        Edits the Scheduled Event's data

        All parameters are optional unless ``location.type`` is
        :attr:`ScheduledEventLocationType.external`, then ``end_time``
        is required.

        Will return a new :class:`.ScheduledEvent` object if applicable.

        Parameters
        -----------
        name: :class:`str`
            The new name of the event.
        description: :class:`str`
            The new description of the event.
        location: :class:`.ScheduledEventLocation`
            The location of the event.
        status: :class:`ScheduledEventStatus`
            The status of the event. It is recommended, however,
            to use :meth:`.start`, :meth:`.complete`, and
            :meth:`cancel` to edit statuses instead.
        start_time: :class:`datetime.datetime`
            The new starting time for the event.
        end_time: :class:`datetime.datetime`
            The new ending time of the event.
        privacy_level: :class:`ScheduledEventPrivacyLevel`
            The privacy level of the event. Currently, the only possible value
            is :attr:`ScheduledEventPrivacyLevel.guild_only`, which is default,
            so there is no need to change this parameter.
        reason: Optional[:class:`str`]
            The reason to show in the audit log.
        cover: Optional[:class:`Asset`]
            The cover image of the scheduled event.

        Raises
        -------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.

        Returns
        --------
        Optional[:class:`.ScheduledEvent`]
            The newly updated scheduled event object. This is only returned when certain
            fields are updated.
        """
        payload: Dict[str, Any] = {}

        if name is not MISSING:
            payload["name"] = name

        if description is not MISSING:
            payload["description"] = description

        if status is not MISSING:
            payload["status"] = int(status)

        if privacy_level is not MISSING:
            payload["privacy_level"] = int(privacy_level)

        if cover is not MISSING:
            if cover is None:
                payload["image"]
            else:
                payload["image"] = utils._bytes_to_base64_data(cover)

        if location is not MISSING:
            if not isinstance(location, (ScheduledEventLocation, utils._MissingSentinel)):
                location = ScheduledEventLocation(state=self._state, value=location)

            if location.type is ScheduledEventLocationType.external:
                payload["channel_id"] = None
                payload["entity_metadata"] = {"location": str(location.value)}
            else:
                payload["channel_id"] = location.value.id
                payload["entity_metadata"] = None

        location = location if location is not MISSING else self.location
        if end_time is MISSING and location.type is ScheduledEventLocationType.external:
            end_time = self.end_time
            if end_time is None:
                raise ValidationError("end_time needs to be passed if location type is external.")

        if start_time is not MISSING:
            payload["scheduled_start_time"] = start_time.isoformat()

        if end_time is not MISSING:
            payload["scheduled_end_time"] = end_time.isoformat()

        if payload != {}:
            data = await self._state.http.edit_scheduled_event(self.guild.id, self.id, **payload, reason=reason)
            return ScheduledEvent(data=data, guild=self.guild, creator=self.creator, state=self._state)

    async def delete(self) -> None:
        """|coro|

        Deletes the scheduled event.

        Raises
        -------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.
        """
        await self._state.http.delete_scheduled_event(self.guild.id, self.id)

    async def start(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Starts the scheduled event. Shortcut from :meth:`.edit`.

        .. note::

            This method can only be used if :attr:`.status` is :attr:`ScheduledEventStatus.scheduled`.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason to show in the audit log.

        Raises
        -------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.

        Returns
        --------
        Optional[:class:`.ScheduledEvent`]
            The newly updated scheduled event object.
        """
        return await self.edit(status=ScheduledEventStatus.active, reason=reason)

    async def complete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Ends/completes the scheduled event. Shortcut from :meth:`.edit`.

        .. note::

            This method can only be used if :attr:`.status` is :attr:`ScheduledEventStatus.active`.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason to show in the audit log.

        Raises
        -------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.

        Returns
        --------
        Optional[:class:`.ScheduledEvent`]
            The newly updated scheduled event object.
        """
        return await self.edit(status=ScheduledEventStatus.completed, reason=reason)

    async def cancel(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Cancels the scheduled event. Shortcut from :meth:`.edit`.

        .. note::

            This method can only be used if :attr:`.status` is :attr:`ScheduledEventStatus.scheduled`.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason to show in the audit log.

        Raises
        -------
        Forbidden
            You do not have the Manage Events permission.
        HTTPException
            The operation failed.

        Returns
        --------
        Optional[:class:`.ScheduledEvent`]
            The newly updated scheduled event object.
        """
        return await self.edit(status=ScheduledEventStatus.canceled, reason=reason)

    def subscribers(
        self,
        *,
        limit: int = 100,
        as_member: bool = False,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
        after: Optional[Union[Snowflake, datetime.datetime]] = None,
    ) -> AsyncIterator:
        """Returns an :class:`AsyncIterator` representing the users or members subscribed to the event.

        The ``after`` and ``before`` parameters must represent member
        or user objects and meet the :class:`abc.Snowflake` abc.

        .. note::

            Even is ``as_member`` is set to ``True``, if the user
            is outside the guild, it will be a :class:`User` object.

        Examples
        ---------

        Usage ::

            async for user in event.subscribers(limit=100):
                print(user.name)

        Flattening into a list: ::

            users = await event.subscribers(limit=100).flatten()
            # users is now a list of User...

        Getting members instead of user objects: ::

            async for member in event.subscribers(limit=100, as_member=True):
                print(member.display_name)

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The maximum number of results to return.
        as_member: Optional[:class:`bool`]
            Whether to fetch :class:`Member` objects instead of user objects.
            There may still be :class:`User` objects if the user is outside
            the guild.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieves users before this date or object. If a datetime is provided,
            it is recommended to use a UTC aware datetime. If the datetime is naive,
            it is assumed to be local time.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieves users after this date or object. If a datetime is provided,
            it is recommended to use a UTC aware datetime. If the datetime is naive,
            it is assumed to be local time.

        Raises
        -------
        HTTPException
            Fetching the subscribed users failed.

        Yields
        -------
        Union[:class:`User`, :class:`Member`]
            The subscribed :class:`Member`. If ``as_member`` is set to
            ``False`` or the user is outside the guild, it will be a
            :class:`User` object.
        """
        return ScheduledEventSubscribersIterator(
            event=self, limit=limit, with_member=as_member, before=before, after=after
        )
