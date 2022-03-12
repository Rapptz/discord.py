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

from typing import Optional, TYPE_CHECKING

from .utils import MISSING, cached_slot_property, _get_as_snowflake
from .mixins import Hashable
from .enums import PrivacyLevel, try_enum

# fmt: off
__all__ = (
    'StageInstance',
)
# fmt: on

if TYPE_CHECKING:
    from .types.channel import StageInstance as StageInstancePayload
    from .state import ConnectionState
    from .channel import StageChannel
    from .guild import Guild
    from .scheduled_event import ScheduledEvent


class StageInstance(Hashable):
    """Represents a stage instance of a stage channel in a guild.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two stage instances are equal.

        .. describe:: x != y

            Checks if two stage instances are not equal.

        .. describe:: hash(x)

            Returns the stage instance's hash.

    Attributes
    -----------
    id: :class:`int`
        The stage instance's ID.
    guild: :class:`Guild`
        The guild that the stage instance is running in.
    channel_id: :class:`int`
        The ID of the channel that the stage instance is running in.
    topic: :class:`str`
        The topic of the stage instance.
    privacy_level: :class:`PrivacyLevel`
        The privacy level of the stage instance.
    discoverable_disabled: :class:`bool`
        Whether discoverability for the stage instance is disabled.
    scheduled_event_id: Optional[:class:`int`]
        The ID of scheduled event that belongs to the stage instance if any.

        .. versionadded:: 2.0
    """

    __slots__ = (
        '_state',
        'id',
        'guild',
        'channel_id',
        'topic',
        'privacy_level',
        'discoverable_disabled',
        'scheduled_event_id',
        '_cs_channel',
        '_cs_scheduled_event',
    )

    def __init__(self, *, state: ConnectionState, guild: Guild, data: StageInstancePayload) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self._update(data)

    def _update(self, data: StageInstancePayload) -> None:
        self.id: int = int(data['id'])
        self.channel_id: int = int(data['channel_id'])
        self.topic: str = data['topic']
        self.privacy_level: PrivacyLevel = try_enum(PrivacyLevel, data['privacy_level'])
        self.discoverable_disabled: bool = data.get('discoverable_disabled', False)
        self.scheduled_event_id: Optional[int] = _get_as_snowflake(data, 'guild_scheduled_event_id')

    def __repr__(self) -> str:
        return f'<StageInstance id={self.id} guild={self.guild!r} channel_id={self.channel_id} topic={self.topic!r}>'

    @cached_slot_property('_cs_channel')
    def channel(self) -> Optional[StageChannel]:
        """Optional[:class:`StageChannel`]: The channel that stage instance is running in."""
        # the returned channel will always be a StageChannel or None
        return self._state.get_channel(self.channel_id)  # type: ignore

    @cached_slot_property('_cs_scheduled_event')
    def scheduled_event(self) -> Optional[ScheduledEvent]:
        """Optional[:class:`ScheduledEvent`]: The scheduled event that belongs to the stage instance."""
        # Guild.get_scheduled_event() expects an int, we are passing Optional[int]
        return self.guild.get_scheduled_event(self.scheduled_event_id)  # type: ignore

    async def edit(
        self,
        *,
        topic: str = MISSING,
        privacy_level: PrivacyLevel = MISSING,
        reason: Optional[str] = None,
    ) -> None:
        """|coro|

        Edits the stage instance.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        -----------
        topic: :class:`str`
            The stage instance's new topic.
        privacy_level: :class:`PrivacyLevel`
            The stage instance's new privacy level.
        reason: :class:`str`
            The reason the stage instance was edited. Shows up on the audit log.

        Raises
        ------
        TypeError
            If the ``privacy_level`` parameter is not the proper type.
        Forbidden
            You do not have permissions to edit the stage instance.
        HTTPException
            Editing a stage instance failed.
        """

        payload = {}

        if topic is not MISSING:
            payload['topic'] = topic

        if privacy_level is not MISSING:
            if not isinstance(privacy_level, PrivacyLevel):
                raise TypeError('privacy_level field must be of type PrivacyLevel')

            payload['privacy_level'] = privacy_level.value

        if payload:
            await self._state.http.edit_stage_instance(self.channel_id, **payload, reason=reason)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the stage instance.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        -----------
        reason: :class:`str`
            The reason the stage instance was deleted. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to delete the stage instance.
        HTTPException
            Deleting the stage instance failed.
        """
        await self._state.http.delete_stage_instance(self.channel_id, reason=reason)
