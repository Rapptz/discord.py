# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2020 Rapptz

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

import asyncio
from collections import namedtuple, deque
import concurrent.futures
import json
import logging
import struct
import sys
import time
import threading
import traceback
import zlib

import aiohttp

from . import utils
from .activity import BaseActivity
from .enums import SpeakingState
from .errors import ConnectionClosed, InvalidArgument

log = logging.getLogger(__name__)

__all__ = (
    'DiscordWebSocket',
    'KeepAliveHandler',
    'VoiceKeepAliveHandler',
    'DiscordVoiceWebSocket',
    'ReconnectWebSocket',
)

class ReconnectWebSocket(Exception):
    """Signals to safely reconnect the websocket."""
    def __init__(self, shard_id, *, resume=True):
        self.shard_id = shard_id
        self.resume = resume
        self.op = 'RESUME' if resume else 'IDENTIFY'

class WebSocketClosure(Exception):
    """An exception to make up for the fact that aiohttp doesn't signal closure."""
    pass

EventListener = namedtuple('EventListener', 'predicate event result future')

class GatewayRatelimiter:
    def __init__(self, count=110, per=60.0):
        # The default is 110 to give room for at least 10 heartbeats per minute
        self.max = count
        self.remaining = count
        self.window = 0.0
        self.per = per
        self.lock = asyncio.Lock()
        self.shard_id = None

    def is_ratelimited(self):
        current = time.time()
        if current > self.window + self.per:
            return False
        return self.remaining == 0

    def get_delay(self):
        current = time.time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        if self.remaining == 0:
            self.window = current

        return 0.0

    async def block(self):
        async with self.lock:
            delta = self.get_delay()
            if delta:
                log.warning('WebSocket in shard ID %s is ratelimited, waiting %.2f seconds', self.shard_id, delta)
                await asyncio.sleep(delta)


class KeepAliveHandler(threading.Thread):
    def __init__(self, *args, **kwargs):
        ws = kwargs.pop('ws', None)
        interval = kwargs.pop('interval', None)
        shard_id = kwargs.pop('shard_id', None)
        threading.Thread.__init__(self, *args, **kwargs)
        self.ws = ws
        self._main_thread_id = ws.thread_id
        self.interval = interval
        self.daemon = True
        self.shard_id = shard_id
        self.msg = 'Keeping shard ID %s websocket alive with sequence %s.'
        self.block_msg = 'Shard ID %s heartbeat blocked for more than %s seconds.'
        self.behind_msg = 'Can\'t keep up, shard ID %s websocket is %.1fs behind.'
        self._stop_ev = threading.Event()
        self._last_ack = time.perf_counter()
        self._last_send = time.perf_counter()
        self._last_recv = time.perf_counter()
        self.latency = float('inf')
        self.heartbeat_timeout = ws._max_heartbeat_timeout

    def run(self):
        while not self._stop_ev.wait(self.interval):
            if self._last_recv + self.heartbeat_timeout < time.perf_counter():
                log.warning("Shard ID %s has stopped responding to the gateway. Closing and restarting.", self.shard_id)
                coro = self.ws.close(4000)
                f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)

                try:
                    f.result()
                except Exception:
                    log.exception('An error occurred while stopping the gateway. Ignoring.')
                finally:
                    self.stop()
                    return

            data = self.get_payload()
            log.debug(self.msg, self.shard_id, data['d'])
            coro = self.ws.send_heartbeat(data)
            f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)
            try:
                # block until sending is complete
                total = 0
                while True:
                    try:
                        f.result(10)
                        break
                    except concurrent.futures.TimeoutError:
                        total += 10
                        try:
                            frame = sys._current_frames()[self._main_thread_id]
                        except KeyError:
                            msg = self.block_msg
                        else:
                            stack = traceback.format_stack(frame)
                            msg = '%s\nLoop thread traceback (most recent call last):\n%s' % (self.block_msg, ''.join(stack))
                        log.warning(msg, self.shard_id, total)

            except Exception:
                self.stop()
            else:
                self._last_send = time.perf_counter()

    def get_payload(self):
        return {
            'op': self.ws.HEARTBEAT,
            'd': self.ws.sequence
        }

    def stop(self):
        self._stop_ev.set()

    def tick(self):
        self._last_recv = time.perf_counter()

    def ack(self):
        ack_time = time.perf_counter()
        self._last_ack = ack_time
        self.latency = ack_time - self._last_send
        if self.latency > 10:
            log.warning(self.behind_msg, self.shard_id, self.latency)

class VoiceKeepAliveHandler(KeepAliveHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recent_ack_latencies = deque(maxlen=20)
        self.msg = 'Keeping shard ID %s voice websocket alive with timestamp %s.'
        self.block_msg = 'Shard ID %s voice heartbeat blocked for more than %s seconds'
        self.behind_msg = 'High socket latency, shard ID %s heartbeat is %.1fs behind'

    def get_payload(self):
        return {
            'op': self.ws.HEARTBEAT,
            'd': int(time.time() * 1000)
        }

    def ack(self):
        ack_time = time.perf_counter()
        self._last_ack = ack_time
        self._last_recv = ack_time
        self.latency = ack_time - self._last_send
        self.recent_ack_latencies.append(self.latency)

class DiscordClientWebSocketResponse(aiohttp.ClientWebSocketResponse):
    async def close(self, *, code: int = 4000, message: bytes = b'') -> bool:
        return await super().close(code=code, message=message)

class DiscordWebSocket:
    """Implements a WebSocket for Discord's gateway v6.

    Attributes
    -----------
    DISPATCH
        Receive only. Denotes an event to be sent to Discord, such as READY.
    HEARTBEAT
        When received tells Discord to keep the connection alive.
        When sent asks if your connection is currently alive.
    IDENTIFY
        Send only. Starts a new session.
    PRESENCE
        Send only. Updates your presence.
    VOICE_STATE
        Send only. Starts a new connection to a voice guild.
    VOICE_PING
        Send only. Checks ping time to a voice guild, do not use.
    RESUME
        Send only. Resumes an existing connection.
    RECONNECT
        Receive only. Tells the client to reconnect to a new gateway.
    REQUEST_MEMBERS
        Send only. Asks for the full member list of a guild.
    INVALIDATE_SESSION
        Receive only. Tells the client to optionally invalidate the session
        and IDENTIFY again.
    HELLO
        Receive only. Tells the client the heartbeat interval.
    HEARTBEAT_ACK
        Receive only. Confirms receiving of a heartbeat. Not having it implies
        a connection issue.
    GUILD_SYNC
        Send only. Requests a guild sync.
    gateway
        The gateway we are currently connected to.
    token
        The authentication token for discord.
    """

    DISPATCH           = 0
    HEARTBEAT          = 1
    IDENTIFY           = 2
    PRESENCE           = 3
    VOICE_STATE        = 4
    VOICE_PING         = 5
    RESUME             = 6
    RECONNECT          = 7
    REQUEST_MEMBERS    = 8
    INVALIDATE_SESSION = 9
    HELLO              = 10
    HEARTBEAT_ACK      = 11
    GUILD_SYNC         = 12

    def __init__(self, socket, *, loop):
        self.socket = socket
        self.loop = loop

        # an empty dispatcher to prevent crashes
        self._dispatch = lambda *args: None
        # generic event listeners
        self._dispatch_listeners = []
        # the keep alive
        self._keep_alive = None
        self.thread_id = threading.get_ident()

        # ws related stuff
        self.session_id = None
        self.sequence = None
        self._zlib = zlib.decompressobj()
        self._buffer = bytearray()
        self._close_code = None
        self._rate_limiter = GatewayRatelimiter()

    @property
    def open(self):
        return not self.socket.closed

    def is_ratelimited(self):
        return self._rate_limiter.is_ratelimited()

    @classmethod
    async def from_client(cls, client, *, initial=False, gateway=None, shard_id=None, session=None, sequence=None, resume=False):
        """Creates a main websocket for Discord from a :class:`Client`.

        This is for internal use only.
        """
        gateway = gateway or await client.http.get_gateway()
        socket = await client.http.ws_connect(gateway)
        ws = cls(socket, loop=client.loop)

        # dynamically add attributes needed
        ws.token = client.http.token
        ws._connection = client._connection
        ws._discord_parsers = client._connection.parsers
        ws._dispatch = client.dispatch
        ws.gateway = gateway
        ws.call_hooks = client._connection.call_hooks
        ws._initial_identify = initial
        ws.shard_id = shard_id
        ws._rate_limiter.shard_id = shard_id
        ws.shard_count = client._connection.shard_count
        ws.session_id = session
        ws.sequence = sequence
        ws._max_heartbeat_timeout = client._connection.heartbeat_timeout

        client._connection._update_references(ws)

        log.debug('Created websocket connected to %s', gateway)

        # poll event for OP Hello
        await ws.poll_event()

        if not resume:
            await ws.identify()
            return ws

        await ws.resume()
        return ws

    def wait_for(self, event, predicate, result=None):
        """Waits for a DISPATCH'd event that meets the predicate.

        Parameters
        -----------
        event: :class:`str`
            The event name in all upper case to wait for.
        predicate
            A function that takes a data parameter to check for event
            properties. The data parameter is the 'd' key in the JSON message.
        result
            A function that takes the same data parameter and executes to send
            the result to the future. If ``None``, returns the data.

        Returns
        --------
        asyncio.Future
            A future to wait for.
        """

        future = self.loop.create_future()
        entry = EventListener(event=event, predicate=predicate, result=result, future=future)
        self._dispatch_listeners.append(entry)
        return future

    async def identify(self):
        """Sends the IDENTIFY packet."""
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'discord.py',
                    '$device': 'discord.py',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                'compress': True,
                'large_threshold': 250,
                'guild_subscriptions': self._connection.guild_subscriptions,
                'v': 3
            }
        }

        if not self._connection.is_bot:
            payload['d']['synced_guilds'] = []

        if self.shard_id is not None and self.shard_count is not None:
            payload['d']['shard'] = [self.shard_id, self.shard_count]

        state = self._connection
        if state._activity is not None or state._status is not None:
            payload['d']['presence'] = {
                'status': state._status,
                'game': state._activity,
                'since': 0,
                'afk': False
            }

        if state._intents is not None:
            payload['d']['intents'] = state._intents.value

        await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
        await self.send_as_json(payload)
        log.info('Shard ID %s has sent the IDENTIFY payload.', self.shard_id)

    async def resume(self):
        """Sends the RESUME packet."""
        payload = {
            'op': self.RESUME,
            'd': {
                'seq': self.sequence,
                'session_id': self.session_id,
                'token': self.token
            }
        }

        await self.send_as_json(payload)
        log.info('Shard ID %s has sent the RESUME payload.', self.shard_id)

    async def received_message(self, msg):
        self._dispatch('socket_raw_receive', msg)

        if type(msg) is bytes:
            self._buffer.extend(msg)

            if len(msg) >= 4:
                if msg[-4:] == b'\x00\x00\xff\xff':
                    msg = self._zlib.decompress(self._buffer)
                    msg = msg.decode('utf-8')
                    self._buffer = bytearray()
                else:
                    return
            else:
                return

        msg = json.loads(msg)

        log.debug('For Shard ID %s: WebSocket Event: %s', self.shard_id, msg)
        self._dispatch('socket_response', msg)

        op = msg.get('op')
        data = msg.get('d')
        seq = msg.get('s')
        if seq is not None:
            self.sequence = seq

        if self._keep_alive:
            self._keep_alive.tick()

        if op != self.DISPATCH:
            if op == self.RECONNECT:
                # "reconnect" can only be handled by the Client
                # so we terminate our connection and raise an
                # internal exception signalling to reconnect.
                log.debug('Received RECONNECT opcode.')
                await self.close()
                raise ReconnectWebSocket(self.shard_id)

            if op == self.HEARTBEAT_ACK:
                if self._keep_alive:
                    self._keep_alive.ack()
                return

            if op == self.HEARTBEAT:
                if self._keep_alive:
                    beat = self._keep_alive.get_payload()
                    await self.send_as_json(beat)
                return

            if op == self.HELLO:
                interval = data['heartbeat_interval'] / 1000.0
                self._keep_alive = KeepAliveHandler(ws=self, interval=interval, shard_id=self.shard_id)
                # send a heartbeat immediately
                await self.send_as_json(self._keep_alive.get_payload())
                self._keep_alive.start()
                return

            if op == self.INVALIDATE_SESSION:
                if data is True:
                    await self.close()
                    raise ReconnectWebSocket(self.shard_id)

                self.sequence = None
                self.session_id = None
                log.info('Shard ID %s session has been invalidated.', self.shard_id)
                await self.close(code=1000)
                raise ReconnectWebSocket(self.shard_id, resume=False)

            log.warning('Unknown OP code %s.', op)
            return

        event = msg.get('t')

        if event == 'READY':
            self._trace = trace = data.get('_trace', [])
            self.sequence = msg['s']
            self.session_id = data['session_id']
            # pass back shard ID to ready handler
            data['__shard_id__'] = self.shard_id
            log.info('Shard ID %s has connected to Gateway: %s (Session ID: %s).',
                     self.shard_id, ', '.join(trace), self.session_id)

        elif event == 'RESUMED':
            self._trace = trace = data.get('_trace', [])
            # pass back the shard ID to the resumed handler
            data['__shard_id__'] = self.shard_id
            log.info('Shard ID %s has successfully RESUMED session %s under trace %s.',
                     self.shard_id, self.session_id, ', '.join(trace))

        try:
            func = self._discord_parsers[event]
        except KeyError:
            log.debug('Unknown event %s.', event)
        else:
            func(data)

        # remove the dispatched listeners
        removed = []
        for index, entry in enumerate(self._dispatch_listeners):
            if entry.event != event:
                continue

            future = entry.future
            if future.cancelled():
                removed.append(index)
                continue

            try:
                valid = entry.predicate(data)
            except Exception as exc:
                future.set_exception(exc)
                removed.append(index)
            else:
                if valid:
                    ret = data if entry.result is None else entry.result(data)
                    future.set_result(ret)
                    removed.append(index)

        for index in reversed(removed):
            del self._dispatch_listeners[index]

    @property
    def latency(self):
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds."""
        heartbeat = self._keep_alive
        return float('inf') if heartbeat is None else heartbeat.latency

    def _can_handle_close(self):
        code = self._close_code or self.socket.close_code
        return code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014)

    async def poll_event(self):
        """Polls for a DISPATCH event and handles the general gateway loop.

        Raises
        ------
        ConnectionClosed
            The websocket connection was terminated for unhandled reasons.
        """
        try:
            msg = await self.socket.receive(timeout=self._max_heartbeat_timeout)
            if msg.type is aiohttp.WSMsgType.TEXT:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.BINARY:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.ERROR:
                log.debug('Received %s', msg)
                raise msg.data
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                log.debug('Received %s', msg)
                raise WebSocketClosure
        except (asyncio.TimeoutError, WebSocketClosure) as e:
            # Ensure the keep alive handler is closed
            if self._keep_alive:
                self._keep_alive.stop()
                self._keep_alive = None

            if isinstance(e, asyncio.TimeoutError):
                log.info('Timed out receiving packet. Attempting a reconnect.')
                raise ReconnectWebSocket(self.shard_id) from None

            code = self._close_code or self.socket.close_code
            if self._can_handle_close():
                log.info('Websocket closed with %s, attempting a reconnect.', code)
                raise ReconnectWebSocket(self.shard_id) from None
            else:
                log.info('Websocket closed with %s, cannot reconnect.', code)
                raise ConnectionClosed(self.socket, shard_id=self.shard_id, code=code) from None

    async def send(self, data):
        await self._rate_limiter.block()
        self._dispatch('socket_raw_send', data)
        await self.socket.send_str(data)

    async def send_as_json(self, data):
        try:
            await self.send(utils.to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket, shard_id=self.shard_id) from exc

    async def send_heartbeat(self, data):
        # This bypasses the rate limit handling code since it has a higher priority
        try:
            await self.socket.send_str(utils.to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket, shard_id=self.shard_id) from exc

    async def change_presence(self, *, activity=None, status=None, afk=False, since=0.0):
        if activity is not None:
            if not isinstance(activity, BaseActivity):
                raise InvalidArgument('activity must derive from BaseActivity.')
            activity = activity.to_dict()

        if status == 'idle':
            since = int(time.time() * 1000)

        payload = {
            'op': self.PRESENCE,
            'd': {
                'game': activity,
                'afk': afk,
                'since': since,
                'status': status
            }
        }

        sent = utils.to_json(payload)
        log.debug('Sending "%s" to change status', sent)
        await self.send(sent)

    async def request_sync(self, guild_ids):
        payload = {
            'op': self.GUILD_SYNC,
            'd': list(guild_ids)
        }
        await self.send_as_json(payload)

    async def request_chunks(self, guild_id, query=None, *, limit, user_ids=None, nonce=None):
        payload = {
            'op': self.REQUEST_MEMBERS,
            'd': {
                'guild_id': guild_id,
                'limit': limit
            }
        }

        if nonce:
            payload['d']['nonce'] = nonce

        if user_ids:
            payload['d']['user_ids'] = user_ids

        if query is not None:
            payload['d']['query'] = query


        await self.send_as_json(payload)

    async def voice_state(self, guild_id, channel_id, self_mute=False, self_deaf=False):
        payload = {
            'op': self.VOICE_STATE,
            'd': {
                'guild_id': guild_id,
                'channel_id': channel_id,
                'self_mute': self_mute,
                'self_deaf': self_deaf
            }
        }

        log.debug('Updating our voice state to %s.', payload)
        await self.send_as_json(payload)

    async def close(self, code=4000):
        if self._keep_alive:
            self._keep_alive.stop()
            self._keep_alive = None

        self._close_code = code
        await self.socket.close(code=code)

class DiscordVoiceWebSocket:
    """Implements the websocket protocol for handling voice connections.

    Attributes
    -----------
    IDENTIFY
        Send only. Starts a new voice session.
    SELECT_PROTOCOL
        Send only. Tells discord what encryption mode and how to connect for voice.
    READY
        Receive only. Tells the websocket that the initial connection has completed.
    HEARTBEAT
        Send only. Keeps your websocket connection alive.
    SESSION_DESCRIPTION
        Receive only. Gives you the secret key required for voice.
    SPEAKING
        Send only. Notifies the client if you are currently speaking.
    HEARTBEAT_ACK
        Receive only. Tells you your heartbeat has been acknowledged.
    RESUME
        Sent only. Tells the client to resume its session.
    HELLO
        Receive only. Tells you that your websocket connection was acknowledged.
    RESUMED
        Sent only. Tells you that your RESUME request has succeeded.
    CLIENT_CONNECT
        Indicates a user has connected to voice.
    CLIENT_DISCONNECT
        Receive only.  Indicates a user has disconnected from voice.
    """

    IDENTIFY            = 0
    SELECT_PROTOCOL     = 1
    READY               = 2
    HEARTBEAT           = 3
    SESSION_DESCRIPTION = 4
    SPEAKING            = 5
    HEARTBEAT_ACK       = 6
    RESUME              = 7
    HELLO               = 8
    RESUMED             = 9
    CLIENT_CONNECT      = 12
    CLIENT_DISCONNECT   = 13

    def __init__(self, socket, loop):
        self.ws = socket
        self.loop = loop
        self._keep_alive = None
        self._close_code = None
        self.secret_key = None

    async def send_as_json(self, data):
        log.debug('Sending voice websocket frame: %s.', data)
        await self.ws.send_str(utils.to_json(data))

    send_heartbeat = send_as_json

    async def resume(self):
        state = self._connection
        payload = {
            'op': self.RESUME,
            'd': {
                'token': state.token,
                'server_id': str(state.server_id),
                'session_id': state.session_id
            }
        }
        await self.send_as_json(payload)

    async def identify(self):
        state = self._connection
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'server_id': str(state.server_id),
                'user_id': str(state.user.id),
                'session_id': state.session_id,
                'token': state.token
            }
        }
        await self.send_as_json(payload)

    @classmethod
    async def from_client(cls, client, *, resume=False):
        """Creates a voice websocket for the :class:`VoiceClient`."""
        gateway = 'wss://' + client.endpoint + '/?v=4'
        http = client._state.http
        socket = await http.ws_connect(gateway, compress=15)
        ws = cls(socket, loop=client.loop)
        ws.gateway = gateway
        ws._connection = client
        ws._max_heartbeat_timeout = 60.0
        ws.thread_id = threading.get_ident()

        if resume:
            await ws.resume()
        else:
            await ws.identify()

        return ws

    async def select_protocol(self, ip, port, mode):
        payload = {
            'op': self.SELECT_PROTOCOL,
            'd': {
                'protocol': 'udp',
                'data': {
                    'address': ip,
                    'port': port,
                    'mode': mode
                }
            }
        }

        await self.send_as_json(payload)

    async def client_connect(self):
        payload = {
            'op': self.CLIENT_CONNECT,
            'd': {
                'audio_ssrc': self._connection.ssrc
            }
        }

        await self.send_as_json(payload)

    async def speak(self, state=SpeakingState.voice):
        payload = {
            'op': self.SPEAKING,
            'd': {
                'speaking': int(state),
                'delay': 0
            }
        }

        await self.send_as_json(payload)

    async def received_message(self, msg):
        log.debug('Voice websocket frame received: %s', msg)
        op = msg['op']
        data = msg.get('d')

        if op == self.READY:
            await self.initial_connection(data)
        elif op == self.HEARTBEAT_ACK:
            self._keep_alive.ack()
        elif op == self.RESUMED:
            log.info('Voice RESUME succeeded.')
        elif op == self.SESSION_DESCRIPTION:
            self._connection.mode = data['mode']
            await self.load_secret_key(data)
        elif op == self.HELLO:
            interval = data['heartbeat_interval'] / 1000.0
            self._keep_alive = VoiceKeepAliveHandler(ws=self, interval=min(interval, 5.0))
            self._keep_alive.start()

    async def initial_connection(self, data):
        state = self._connection
        state.ssrc = data['ssrc']
        state.voice_port = data['port']
        state.endpoint_ip = data['ip']

        packet = bytearray(70)
        struct.pack_into('>H', packet, 0, 1) # 1 = Send
        struct.pack_into('>H', packet, 2, 70) # 70 = Length
        struct.pack_into('>I', packet, 4, state.ssrc)
        state.socket.sendto(packet, (state.endpoint_ip, state.voice_port))
        recv = await self.loop.sock_recv(state.socket, 70)
        log.debug('received packet in initial_connection: %s', recv)

        # the ip is ascii starting at the 4th byte and ending at the first null
        ip_start = 4
        ip_end = recv.index(0, ip_start)
        state.ip = recv[ip_start:ip_end].decode('ascii')

        state.port = struct.unpack_from('>H', recv, len(recv) - 2)[0]
        log.debug('detected ip: %s port: %s', state.ip, state.port)

        # there *should* always be at least one supported mode (xsalsa20_poly1305)
        modes = [mode for mode in data['modes'] if mode in self._connection.supported_modes]
        log.debug('received supported encryption modes: %s', ", ".join(modes))

        mode = modes[0]
        await self.select_protocol(state.ip, state.port, mode)
        log.info('selected the voice protocol for use (%s)', mode)

    @property
    def latency(self):
        """:class:`float`: Latency between a HEARTBEAT and its HEARTBEAT_ACK in seconds."""
        heartbeat = self._keep_alive
        return float('inf') if heartbeat is None else heartbeat.latency

    @property
    def average_latency(self):
        """:class:`list`: Average of last 20 HEARTBEAT latencies."""
        heartbeat = self._keep_alive
        if heartbeat is None:
            return float('inf')

        return sum(heartbeat.recent_ack_latencies) / len(heartbeat.recent_ack_latencies)

    async def load_secret_key(self, data):
        log.info('received secret key for voice connection')
        self.secret_key = self._connection.secret_key = data.get('secret_key')
        await self.speak()
        await self.speak(False)

    async def poll_event(self):
        # This exception is handled up the chain
        msg = await asyncio.wait_for(self.ws.receive(), timeout=30.0)
        if msg.type is aiohttp.WSMsgType.TEXT:
            await self.received_message(json.loads(msg.data))
        elif msg.type is aiohttp.WSMsgType.ERROR:
            log.debug('Received %s', msg)
            raise ConnectionClosed(self.ws, shard_id=None) from msg.data
        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
            log.debug('Received %s', msg)
            raise ConnectionClosed(self.ws, shard_id=None, code=self._close_code)

    async def close(self, code=1000):
        if self._keep_alive is not None:
            self._keep_alive.stop()

        self._close_code = code
        await self.ws.close(code=code)
