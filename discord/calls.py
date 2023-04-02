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
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

from . import utils
from .errors import ClientException
from .utils import cached_slot_property
from .voice_client import VoiceClient

if TYPE_CHECKING:
    from . import abc
    from .abc import T as ConnectReturn
    from .channel import DMChannel, GroupChannel
    from .client import Client
    from .member import VoiceState
    from .message import Message
    from .state import ConnectionState
    from .user import BaseUser, User

    _PrivateChannel = Union[abc.DMChannel, abc.GroupChannel]

__all__ = (
    'CallMessage',
    'PrivateCall',
    'GroupCall',
)


def _running_only(func: Callable):
    def decorator(self: Call, *args, **kwargs):
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
        An aware UTC datetime object that represents the time that the call has ended.
    participants: List[:class:`User`]
        A list of users that participated in the call.
    message: :class:`Message`
        The message associated with this call message.
    """

    __slots__ = ('message', 'ended_timestamp', 'participants')

    def __init__(self, message: Message, *, participants: List[User], ended_timestamp: Optional[str]) -> None:
        self.message = message
        self.ended_timestamp = utils.parse_time(ended_timestamp)
        self.participants = participants

    @property
    def call_ended(self) -> bool:
        """:class:`bool`: Indicates if the call has ended."""
        return self.ended_timestamp is not None

    @property
    def initiator(self) -> User:
        """:class:`.abc.User`: Returns the user that started the call."""
        return self.message.author  # type: ignore # Cannot be a Member in private messages

    @property
    def channel(self) -> _PrivateChannel:
        """:class:`.abc.PrivateChannel`: The private channel associated with this message."""
        return self.message.channel  # type: ignore # Can only be a private channel here

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
            return utils.utcnow() - self.message.created_at
        else:
            return self.ended_timestamp - self.message.created_at


class PrivateCall:
    """Represents the actual group call from Discord.

    This is accompanied with a :class:`CallMessage` denoting the information.

    .. versionadded:: 1.9

    Attributes
    -----------
    channel: :class:`DMChannel`
        The channel the call is in.
    unavailable: :class:`bool`
        Denotes if this call is unavailable.
    region: :class:`str`
        The region the call is being hosted at.

        .. versionchanged:: 2.0
            The type of this attribute has changed to :class:`str`.
    """

    __slots__ = ('_state', '_ended', 'channel', '_cs_message', '_ringing', '_message_id', 'region', 'unavailable')

    if TYPE_CHECKING:
        channel: DMChannel

    def __init__(
        self,
        *,
        data: dict,
        state: ConnectionState,
        message: Optional[Message],
        channel: abc.PrivateChannel,
    ) -> None:
        self._state = state
        self._cs_message = message
        self.channel = channel  # type: ignore # Will always be a DMChannel here
        self._ended: bool = False

        self._update(data)

    def _delete(self) -> None:
        self._ringing = tuple()
        self._ended = True

    def _get_recipients(self) -> Tuple[BaseUser, ...]:
        channel = self.channel
        return channel.me, channel.recipient

    def _is_participating(self, user: BaseUser) -> bool:
        state = self.voice_state_for(user)
        return bool(state and state.channel and state.channel.id == self.channel.id)

    def _update(self, data) -> None:
        self._message_id = int(data['message_id'])
        self.unavailable = data.get('unavailable', False)
        try:
            self.region: str = data['region']
        except KeyError:
            pass

        channel = self.channel
        recipients = self._get_recipients()
        lookup = {u.id: u for u in recipients}
        self._ringing = tuple(filter(None, map(lookup.get, data.get('ringing', []))))

        for vs in data.get('voice_states', []):
            self._state._update_voice_state(vs, channel.id)

    @property
    def ringing(self) -> List[BaseUser]:
        """List[:class:`.abc.User`]: A list of users that are currently being rung to join the call."""
        return list(self._ringing)

    @property
    def initiator(self) -> Optional[User]:
        """Optional[:class:`.abc.User`]: Returns the user that started the call. Returns ``None`` if the message is not cached."""
        return getattr(self.message, 'author', None)

    @property
    def connected(self) -> bool:
        """:class:`bool`: Returns whether you're in the call (this does not mean you're in the call through the library)."""
        return self._is_participating(self.channel.me)

    @property
    def members(self) -> List[BaseUser]:
        """List[:class:`.abc.User`]: Returns all users that are currently in this call."""
        recipients = self._get_recipients()
        return [u for u in recipients if self._is_participating(u)]

    @property
    def voice_states(self) -> Dict[int, VoiceState]:
        """Mapping[:class:`int`, :class:`VoiceState`]: Returns a mapping of user IDs who have voice states in this call."""
        return {
            k: v for k, v in self._state._voice_states.items() if bool(v and v.channel and v.channel.id == self.channel.id)
        }

    @cached_slot_property('_cs_message')
    def message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: The message associated with this call. Sometimes may not be cached."""
        return self._state._get_message(self._message_id)

    async def fetch_message(self) -> Message:
        """|coro|

        Fetches and caches the message associated with this call.

        Raises
        -------
        HTTPException
            Retrieving the message failed.

        Returns
        -------
        :class:`Message`
            The message associated with this call.
        """
        message = await self.channel.fetch_message(self._message_id)
        state = self._state
        if self.message is None:
            if state._messages is not None:
                state._messages.append(message)
            self._cs_message = message
        return message

    async def change_region(self, region: str) -> None:
        """|coro|

        Changes the channel's voice region.

        Parameters
        -----------
        region: :class:`str`
            A region to change the voice region to.

            .. versionchanged:: 2.0
                The type of this parameter has changed to :class:`str`.

        Raises
        -------
        HTTPException
            Failed to change the channel's voice region.
        """
        await self._state.http.change_call_voice_region(self.channel.id, region)

    @_running_only
    async def ring(self) -> None:
        """|coro|

        Rings the other recipient.

        Raises
        -------
        Forbidden
            Not allowed to ring the other recipient.
        HTTPException
            Ringing failed.
        ClientException
            The call has ended.
        """
        channel = self.channel
        await self._state.http.ring(channel.id)

    @_running_only
    async def stop_ringing(self) -> None:
        """|coro|

        Stops ringing the other recipient.

        Raises
        -------
        HTTPException
            Stopping the ringing failed.
        ClientException
            The call has ended.
        """
        channel = self.channel
        await self._state.http.stop_ringing(channel.id, channel.recipient.id)

    @_running_only
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, abc.VocalChannel], ConnectReturn] = VoiceClient,
    ) -> ConnectReturn:
        """|coro|

        Connects to voice and creates a :class:`~discord.VoiceClient` to establish
        your connection to the voice server.

        There is an alias of this called :attr:`join`.

        Parameters
        -----------
        timeout: :class:`float`
            The timeout in seconds to wait for the voice endpoint.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`~discord.VoiceProtocol`]
            A type that subclasses :class:`~discord.VoiceProtocol` to connect with.
            Defaults to :class:`~discord.VoiceClient`.

        Raises
        -------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~discord.ClientException
            You are already connected to a voice channel.
        ~discord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        --------
        :class:`~discord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """
        return await self.channel.connect(timeout=timeout, reconnect=reconnect, cls=cls, ring=False)

    @_running_only
    async def join(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, abc.VocalChannel], ConnectReturn] = VoiceClient,
    ) -> ConnectReturn:
        """|coro|

        Connects to voice and creates a :class:`~discord.VoiceClient` to establish
        your connection to the voice server.

        This is an alias of :attr:`connect`.

        Parameters
        -----------
        timeout: :class:`float`
            The timeout in seconds to wait for the voice endpoint.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`~discord.VoiceProtocol`]
            A type that subclasses :class:`~discord.VoiceProtocol` to connect with.
            Defaults to :class:`~discord.VoiceClient`.

        Raises
        -------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~discord.ClientException
            You are already connected to a voice channel.
        ~discord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        --------
        :class:`~discord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """
        return await self.connect(timeout=timeout, reconnect=reconnect, cls=cls)

    @_running_only
    async def disconnect(self, force: bool = False) -> None:
        """|coro|

        Disconnects this voice client from voice.

        There is an alias of this called :attr:`leave`.
        """
        state = self._state
        if not (client := state._get_voice_client(self.channel.me.id)):
            return

        return await client.disconnect(force=force)

    @_running_only
    async def leave(self, force: bool = False) -> None:
        """|coro|

        Disconnects this voice client from voice.

        This is an alias of :attr:`disconnect`.
        """
        return await self.disconnect(force=force)

    def voice_state_for(self, user: abc.Snowflake) -> Optional[VoiceState]:
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
    unavailable: :class:`bool`
        Denotes if this group call is unavailable.
    region: :class:`str`
        The region the group call is being hosted in.

        .. versionchanged:: 2.0
            The type of this attribute has changed to :class:`str`.
    """

    __slots__ = ()

    if TYPE_CHECKING:
        channel: GroupChannel

    def _get_recipients(self) -> Tuple[BaseUser, ...]:
        channel = self.channel
        return *channel.recipients, channel.me

    @_running_only
    async def ring(self, *recipients: abc.Snowflake) -> None:
        r"""|coro|

        Rings the specified recipients.

        Parameters
        -----------
        \*recipients: :class:`User`
            The recipients to ring. The default is to ring all recipients.

        Raises
        -------
        HTTPException
            Stopping the ringing failed.
        ClientException
            The call has ended.
        """
        await self._state.http.ring(self.channel.id, *{r.id for r in recipients})

    @_running_only
    async def stop_ringing(self, *recipients: abc.Snowflake) -> None:
        r"""|coro|

        Stops ringing the specified recipients.

        Parameters
        -----------
        \*recipients: :class:`User`
            The recipients to stop ringing.

        Raises
        -------
        HTTPException
            Ringing failed.
        ClientException
            The call has ended.
        """
        channel = self.channel
        await self._state.http.stop_ringing(channel.id, *{r.id for r in recipients or channel.recipients})


Call = Union[PrivateCall, GroupCall]
