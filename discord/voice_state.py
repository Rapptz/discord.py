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

import socket
import asyncio
import logging
import threading

from typing import TYPE_CHECKING, Optional, Dict, List, Callable, Coroutine, Any, Union

from .enums import Enum
from .utils import MISSING, sane_wait_for
from .errors import ConnectionClosed
from .backoff import ExponentialBackoff
from .gateway import DiscordVoiceWebSocket

if TYPE_CHECKING:
    from . import abc
    from .guild import Guild
    from .user import ClientUser
    from .voice_client import VoiceClient

    from .types.voice import (
        GuildVoiceState as GuildVoiceStatePayload,
        VoiceServerUpdate as VoiceServerUpdatePayload,
        # SupportedModes,
    )

    WebsocketHook = Optional[Callable[['VoiceConnectionState', Dict[str, Any]], Coroutine[Any, Any, Any]]]

    from enum import IntEnum as Enum # heck

__all__ = (
    'VoiceConnectionState',
)

_log = logging.getLogger(__name__)

"""
Some documentation to refer to:

- Our main web socket (mWS) sends opcode 4 with a guild ID and channel ID.
- The mWS receives VOICE_STATE_UPDATE and VOICE_SERVER_UPDATE.
- We pull the session_id from VOICE_STATE_UPDATE.
- We pull the token, endpoint and server_id from VOICE_SERVER_UPDATE.
- Then we initiate the voice web socket (vWS) pointing to the endpoint.
- We send opcode 0 with the user_id, server_id, session_id and token using the vWS.
- The vWS sends back opcode 2 with an ssrc, port, modes(array) and heartbeat_interval.
- We send a UDP discovery packet to endpoint:port and receive our IP and our port in LE.
- Then we send our IP and port via vWS with opcode 1.
- When that's all done, we receive opcode 4 from the vWS.
- Finally we can transmit data to endpoint:port.
"""

class ConnectionStage(Enum, comparable=True):
    """Enum representing voice connection flow state as 'what just happened'."""

    disconnected            = 0b0
    set_guild_voice_state   = 0b00_00000001
    got_voice_state_update  = 0b00_00000011
    got_voice_server_update = 0b00_00000101
    got_both_voice_updates  = 0b00_00000111
    websocket_connected     = 0b00_00001000
    got_websocket_ready     = 0b00_00010000
    # we send udp discovery packet and read from the socket
    got_udp_discovery       = 0b00_00100000
    # we send SELECT_PROTOCOL then SPEAKING
    connected               = 0b00_01000000
    resumed                 = 0b00_11000000
    reconnecting            = 0b01_00000000

    if TYPE_CHECKING:
        @classmethod
        def try_value(cls, value: Union[ConnectionStage, int]) -> Union[ConnectionStage, int]:
            ...


class VoiceConnectionState:
    """Represents the internal state of a voice connection."""

    def __init__(self, voice_client: VoiceClient, *, hook: Optional[WebsocketHook]=None) -> None:
        self.voice_client = voice_client
        self.hook = hook

        self.token: str = MISSING
        self.session_id: str = MISSING
        self.endpoint: str = MISSING
        self.endpoint_ip: str = MISSING
        self.server_id: int = MISSING
        self.ip: str = MISSING
        self.port: int = MISSING
        self.voice_port: int = MISSING
        self.secret_key: List[int] = MISSING
        self.ssrc: int = MISSING
        self.mode: str = MISSING

        self.socket = MISSING
        self.ws: DiscordVoiceWebSocket = MISSING

        self._stage: ConnectionStage = ConnectionStage.disconnected

        self._connected = threading.Event()
        self._stage_event = asyncio.Event()
        self._runner: asyncio.Task = MISSING

    @property
    def stage(self) -> ConnectionStage:
        return self._stage

    @stage.setter
    def stage(self, stage: ConnectionStage) -> None:
        self._stage = stage
        _log.debug('Current stage is now: %s', stage.name, stack_info=False)
        self._stage_event.set()
        self._stage_event.clear()

        if stage.value & ConnectionStage.connected.value:
            self._connected.set()
        else:
            self._connected.clear()

    @property
    def guild(self) -> Guild:
        return self.voice_client.guild

    @property
    def user(self) -> ClientUser:
        return self.voice_client.user

    @property
    def supported_modes(self):
        return self.voice_client.supported_modes

    async def voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        session_id = data['session_id']
        channel_id = data['channel_id']

        if channel_id is None:
            await self.disconnect()

        # if we get the event while connecting
        if self.stage in (
            ConnectionStage.set_guild_voice_state,
            ConnectionStage.got_voice_server_update
        ):
            self.session_id = session_id
            self.stage = ConnectionStage(self.stage.value | ConnectionStage.got_voice_state_update.value)
            return

        if session_id != self.session_id:
            # _log.debug('New session id, old: %r, new: %r', self.session_id, session_id)
            self.session_id = session_id

        if self.stage.value & ConnectionStage.reconnecting.value or self.stage.value & ConnectionStage.connected.value:
            self.voice_client.channel = channel_id and self.guild.get_channel(int(channel_id)) # type: ignore

        elif self.stage < ConnectionStage.connected:
            _log.warning('Got unexpected voice_state_update before complete connection')
            # TODO: kill it and start over?

    # this whole function gives me the heebie jeebies
    async def voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        self.token = data['token']
        self.server_id = int(data['guild_id'])
        endpoint = data.get('endpoint')

        if self.token is None or endpoint is None:
            _log.warning(
                'Awaiting endpoint... This requires waiting. '
                'If timeout occurred considering raising the timeout and reconnecting.'
            )
            return

        self.endpoint, _, _ = endpoint.rpartition(':')
        if self.endpoint.startswith('wss://'):
            # Just in case, strip it off since we're going to add it later
            self.endpoint: str = self.endpoint[6:]

        # if we get the event while connecting
        if self.stage in (
            ConnectionStage.set_guild_voice_state,
            ConnectionStage.got_voice_state_update
        ):
            # This gets set after READY
            self.endpoint_ip = MISSING

            self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)

            self.stage = ConnectionStage(self.stage.value | ConnectionStage.got_voice_server_update.value)
        elif self.stage.value & ConnectionStage.connected.value:
            _log.debug('Closing old websocket')
            await self.ws.close(4014)
            # self.stage = ConnectionStage.reconnecting # is this shit even worth using?
            self.stage = ConnectionStage.got_both_voice_updates
        else:
            _log.warning('Got unexpected voice_server_update')
            # TODO: wat do?

    async def connect(
        self,
        *,
        reconnect: bool,
        timeout: float,
        self_deaf: bool,
        self_mute: bool,
        resume: bool
    ) -> None:

        _log.info('Connecting to voice...')
        self.timeout = timeout

        for i in range(5):
            await self._voice_connect(self_deaf=self_deaf, self_mute=self_mute)
            self.stage = ConnectionStage.set_guild_voice_state

            try:
                await self._wait_for_stage(ConnectionStage.got_both_voice_updates, timeout=timeout)
            except asyncio.TimeoutError:
                _log.info('Timed out waiting for voice update events')
                await self.disconnect(force=True)
                raise

            try:
                self.ws = await self._connect_websocket(resume)
                break
            except (ConnectionClosed, asyncio.TimeoutError):
                if reconnect:
                    wait = 1 + i * 2.0
                    _log.exception('Failed to connect to voice... Retrying in %ss...', wait)
                    await asyncio.sleep(wait)
                    await self._voice_disconnect()
                    continue
                else:
                    try:
                        await self._voice_disconnect()
                    except Exception:
                        _log.exception('Error setting voice state after connection failure')
                    raise

        if self._runner is MISSING:
            self._runner = self.voice_client.loop.create_task(self._poll_voice_ws(reconnect), name="Voice websocket poller")

    async def disconnect(self, *, force: bool=False) -> None:
        if not force and not self.is_connected():
            return

        try:
            if self.ws:
                await self.ws.close()

            await self._voice_disconnect()
        finally:
            self.stage = ConnectionStage.disconnected
            if self.socket:
                self.socket.close()

    async def move_to(self, channel: Optional[abc.Snowflake]) -> None:
        if channel is None:
            await self.disconnect()
            return

        await self.voice_client.channel.guild.change_voice_state(channel=channel)

    def wait(self, timeout: Optional[float]=None) -> bool:
        return self._connected.wait(timeout)

    async def wait_async(self, *, timeout: Optional[float]=None) -> bool:
        return await self._wait_for_stage(ConnectionStage.connected, timeout=timeout, exact=False)

    def is_connected(self) -> bool:
        return bool(self.stage.value & ConnectionStage.connected.value)

    def send_packet(self, packet: bytes) -> int:
        if not self.stage.value & ConnectionStage.connected.value:
            _log.info("Not connected but sending packet anyway...")
            # raise RuntimeError('Not connected')

        return self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))

    async def _wait_for_stage(self, stage: ConnectionStage, *, timeout: Optional[float]=None, exact: bool=True):
        while True:
            if exact:
                if self.stage == stage:
                    return True
            else:
                if self.stage.value & stage.value == stage.value:
                    return True
            await sane_wait_for([self._stage_event.wait()], timeout=timeout)

    async def _voice_connect(self, *, self_deaf: bool = False, self_mute: bool = False) -> None:
        channel = self.voice_client.channel
        await channel.guild.change_voice_state(channel=channel, self_deaf=self_deaf, self_mute=self_mute)

    async def _voice_disconnect(self) -> None:
        _log.info('The voice handshake is being terminated for Channel ID %s (Guild ID %s)',
            self.voice_client.channel.id, self.voice_client.guild.id
        )
        self.stage = ConnectionStage.disconnected
        await self.voice_client.channel.guild.change_voice_state(channel=None)

    async def _connect_websocket(self, resume: bool) -> DiscordVoiceWebSocket:
        ws = await DiscordVoiceWebSocket.from_connection_state(self, resume=resume, hook=self.hook)
        self.stage = ConnectionStage.websocket_connected
        while not self.ip:
            await ws.poll_event()
        self.stage = ConnectionStage.got_udp_discovery
        while ws.secret_key is None:
            await ws.poll_event()
        if resume:
            self.stage = ConnectionStage.resumed
        self.stage = ConnectionStage.connected
        return ws

    async def _poll_voice_ws(self, reconnect: bool) -> None:
        backoff = ExponentialBackoff()
        while True:
            try:
                await self.ws.poll_event()
            except (ConnectionClosed, asyncio.TimeoutError) as exc:
                if isinstance(exc, ConnectionClosed):
                    # The following close codes are undocumented so I will document them here.
                    # 1000 - normal closure (obviously)
                    # 4014 - voice channel has been deleted.
                    # 4015 - voice server has crashed
                    if exc.code in (1000, 4015):
                        _log.info('Disconnecting from voice normally, close code %d.', exc.code)
                        await self.disconnect()
                        break

                    if exc.code == 4014:
                        _log.info('Disconnected from voice by force... potentially reconnecting.')
                        successful = await self._potential_reconnect()
                        if not successful:
                            _log.info('Reconnect was unsuccessful, disconnecting from voice normally...')
                            await self.disconnect()
                            break
                        else:
                            continue

                if not reconnect:
                    await self.disconnect(force=True)
                    raise

                retry = backoff.delay()
                _log.exception('Disconnected from voice... Reconnecting in %.2fs.', retry)
                await asyncio.sleep(retry)
                await self._voice_disconnect()
                # self.stage = ConnectionStage.reconnecting
                try:
                    await self.connect(reconnect=reconnect, timeout=self.timeout, self_deaf=False, self_mute=False, resume=False)
                except asyncio.TimeoutError:
                    # at this point we've retried 5 times... let's continue the loop.
                    _log.warning('Could not connect to voice... Retrying...')
                    continue

    async def _potential_reconnect(self) -> bool:
        try:
            await self._wait_for_stage(ConnectionStage.got_voice_server_update, timeout=self.timeout, exact=False)
        except asyncio.TimeoutError:
            await self.disconnect(force=True)
            return False
        try:
            self.ws = await self._connect_websocket(False)
        except (ConnectionClosed, asyncio.TimeoutError):
            return False
        else:
            return True
