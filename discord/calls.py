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

import datetime
from typing import List, Optional, TYPE_CHECKING, Union

from . import utils
from .enums import VoiceRegion, try_enum
from .errors import ClientException
from .utils import MISSING

if TYPE_CHECKING:
    from .abc import PrivateChannel
    from .channel import DMChannel, GroupChannel
    from .member import VoiceState
    from .message import Message
    from .state import ConnectionState
    from .types.snowflake import Snowflake, SnowflakeList
    from .types.voice import GuildVoiceState
    from .user import User
    from .voice_client import VoiceProtocol


def _running_only(func):
    def decorator(self, *args, **kwargs):
        if self._ended:
            raise ClientException('Call is over')
        else:
            return func(self, *args, **kwargs)
    return decorator


class CallMessage:
    """Represents a group call message from Discord.

    This is only received in cases where the message type is equivalent to
    :attr:`MessageType.call`.

    Attributes
    -----------
    ended_timestamp: Optional[:class:`datetime.datetime`]
        A naive UTC datetime object that represents the time that the call has ended.
    participants: List[:class:`User`]
        A list of users that participated in the call.
    message: :class:`Message`
        The message associated with this call message.
    """

    def __init__(
        self, message: Message, *, participants: List[User], ended_timestamp: str
    ) -> None:
        self.message = message
        self.ended_timestamp = utils.parse_time(ended_timestamp)
        self.participants = participants

    @property
    def call_ended(self) -> bool:
        """:class:`bool`: Indicates if the call has ended."""
        return self.ended_timestamp is not None

    @property
    def initiator(self) -> User:
        """:class:`User`: Returns the user that started the call."""
        return self.message.author

    @property
    def channel(self) -> PrivateChannel:
        r""":class:`PrivateChannel`\: The private channel associated with this message."""
        return self.message.channel

    @property
    def duration(self) -> datetime.timedelta:
        """Queries the duration of the call.

        If the call has not ended then the current duration will
        be returned.

        Returns
        ---------
        :class:`datetime.timedelta`
            The timedelta object representing the duration.
        """
        if self.ended_timestamp is None:
            return datetime.datetime.utcnow() - self.message.created_at
        else:
            return self.ended_timestamp - self.message.created_at


class PrivateCall:
    """Represents the actual group call from Discord.

    This is accompanied with a :class:`CallMessage` denoting the information.

    Attributes
    -----------
    channel: :class:`DMChannel`
        The channel the call is in.
    message: Optional[:class:`Message`]
        The message associated with this call (if available).
    unavailable: :class:`bool`
        Denotes if this call is unavailable.
    ringing: List[:class:`User`]
        A list of users that are currently being rung to join the call.
    region: :class:`VoiceRegion`
        The region the call is being hosted at.
    """

    if TYPE_CHECKING:
        channel: DMChannel
        ringing: List[User]
        region: VoiceRegion

    def __init__(
        self,
        state: ConnectionState,
        *,
        message_id: Snowflake,
        channel_id: Snowflake,
        message: Message = None,
        channel: PrivateChannel,
        unavailable: bool,
        voice_states: List[GuildVoiceState] = [],
        **kwargs,
    ) -> None:
        self._state = state
        self._message_id: int = int(message_id)
        self._channel_id: int = int(channel_id)
        self.message: Optional[Message] = message
        self.channel = channel  # type: ignore
        self.unavailable: bool = unavailable
        self._ended: bool = False

        for vs in voice_states:
            state._update_voice_state(vs)

        self._update(**kwargs)

    def _deleteup(self) -> None:
        self.ringing = []
        self._ended = True

    def _update(
        self, *, ringing: SnowflakeList = {}, region: VoiceRegion = MISSING
    ) -> None:
        if region is not MISSING:
            self.region = try_enum(VoiceRegion, region)
        channel = self.channel
        recipients = {channel.me, channel.recipient}
        lookup = {u.id: u for u in recipients}
        self.ringing = list(filter(None, map(lookup.get, ringing)))

    @property
    def initiator(self) -> Optional[User]:
        """Optional[:class:`User`]: Returns the user that started the call. The call message must be available to obtain this information."""
        if self.message:
            return self.message.author

    @property
    def connected(self) -> bool:
        """:class:`bool`: Returns whether you're in the call (this does not mean you're in the call through the lib)."""
        return self.voice_state_for(self.channel.me).channel.id == self._channel_id

    @property
    def members(self) -> List[User]:
        """List[:class:`User`]: Returns all users that are currently in this call."""
        channel = self.channel
        recipients = {channel.me, channel.recipient}
        ret = [u for u in recipients if self.voice_state_for(u).channel.id == self._channel_id]

        return ret

    @property
    def voice_states(self)  -> List[VoiceState]:
        """Mapping[:class:`int`, :class:`VoiceState`]: Returns a mapping of user IDs who have voice states in this call."""
        return set(self._voice_states)

    async def fetch_message(self) -> Optional[Message]:
        message = await self.channel.fetch_message(self._message_id)
        if message is not None and self.message is None:
            self.message = message
        return message

    @_running_only
    async def change_region(self, region) -> None:
        """|coro|

        Changes the channel's voice region.

        Parameters
        -----------
        region: :class:`VoiceRegion`
            A :class:`VoiceRegion` to change the voice region to.

        Raises
        -------
        HTTPException
            Failed to change the channel's voice region.
        """
        await self._state.http.change_call_voice_region(self.channel.id, str(region))

    @_running_only
    async def ring(self) -> None:
        channel = self.channel
        await self._state.http.ring(channel.id, channel.recipient.id)

    @_running_only
    async def stop_ringing(self) -> None:
        channel = self.channel
        await self._state.http.stop_ringing(channel.id, channel.recipient.id)

    @_running_only
    async def join(self, **kwargs) -> VoiceProtocol:
        return await self.channel._connect(**kwargs)

    connect = join

    @_running_only
    async def leave(self, **kwargs) -> None:
        state = self._state
        if not (client := state._get_voice_client(self.channel.me.id)):
            return

        return await client.disconnect(**kwargs)

    disconnect = leave

    def voice_state_for(self, user) -> Optional[VoiceState]:
        """Retrieves the :class:`VoiceState` for a specified :class:`User`.

        If the :class:`User` has no voice state then this function returns
        ``None``.

        Parameters
        ------------
        user: :class:`User`
            The user to retrieve the voice state for.

        Returns
        --------
        Optional[:class:`VoiceState`]
            The voice state associated with this user.
        """
        return self._state._voice_state_for(user.id)


class GroupCall(PrivateCall):
    """Represents a Discord group call.

    This is accompanied with a :class:`CallMessage` denoting the information.

    Attributes
    -----------
    channel: :class:`GroupChannel`
        The channel the group call is in.
    message: Optional[:class:`Message`]
        The message associated with this group call (if available).
    unavailable: :class:`bool`
        Denotes if this group call is unavailable.
    ringing: List[:class:`User`]
        A list of users that are currently being rung to join the call.
    region: :class:`VoiceRegion`
        The region the group call is being hosted in.
    """

    if TYPE_CHECKING:
        channel: GroupChannel

    def _update(
        self, *, ringing: SnowflakeList = [], region: VoiceRegion = MISSING
    ) -> None:
        if region is not MISSING:
            self.region = try_enum(VoiceRegion, region)
        lookup = {u.id: u for u in self.channel.recipients}
        me = self.channel.me
        lookup[me.id] = me
        self.ringing = list(filter(None, map(lookup.get, ringing)))

    @property
    def members(self) -> List[User]:
        """List[:class:`User`]: Returns all users that are currently in this call."""
        ret = [u for u in self.channel.recipients if self.voice_state_for(u).channel.id == self._channel_id]
        me = self.channel.me
        if self.voice_state_for(me).channel.id == self._channel_id:
            ret.append(me)

        return ret

    @_running_only
    async def ring(self, *recipients) -> None:
        await self._state.http.ring(self._channel_id, *{r.id for r in recipients})

    @_running_only
    async def stop_ringing(self, *recipients) -> None:
        await self._state.http.stop_ringing(self._channel_id, *{r.id for r in recipients})


Call = Union[PrivateCall, GroupCall]
