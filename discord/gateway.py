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

import asyncio
from collections import namedtuple, deque
import logging
import struct
import time
import threading
import traceback
import zlib

import aiohttp

from . import utils
from .activity import BaseActivity
from .enums import SpeakingState
from .errors import ConnectionClosed, InvalidArgument
from .recorder import SSRC

_log = logging.getLogger(__name__)

__all__ = (
    'DiscordWebSocket',
    'KeepAliveHandler',
    'VoiceKeepAliveHandler',
    'DiscordVoiceWebSocket',
    'ReconnectWebSocket',
)

class ReconnectWebSocket(Exception):
    """Signals to safely reconnect the websocket."""
    def __init__(self, *, resume=True):
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
                _log.warning('Gateway is ratelimited, waiting %.2f seconds.', delta)
                await asyncio.sleep(delta)


class KeepAliveHandler:  # Inspired by enhanced-discord.py/Gnome
    def __init__(self, *, ws, interval=None):
        self.ws = ws
        self.interval = interval
        self.heartbeat_timeout = self.ws._max_heartbeat_timeout

        self.msg = 'Keeping websocket alive.'
        self.block_msg = 'Heartbeat blocked for more than %s seconds.'
        self.behind_msg = 'Can\'t keep up, websocket is %.1fs behind.'
        self.not_responding_msg = 'Gateway has stopped responding. Closing and restarting.'
        self.no_stop_msg = 'An error occurred while stopping the gateway. Ignoring.'

        self._stop = asyncio.Event()
        self._last_send = time.perf_counter()
        self._last_recv = time.perf_counter()
        self._last_ack = time.perf_counter()
        self.latency = float('inf')

    async def run(self):
        while True:
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass
            else:
                return

            if self._last_recv + self.heartbeat_timeout < time.perf_counter():
                _log.warning(self.not_responding_msg)

                try:
                    await self.ws.close(4000)
                except Exception:
                    _log.exception(self.no_stop_msg)
                finally:
                    self.stop()
                    return

            data = self.get_payload()
            _log.debug(self.msg)
            try:
                total = 0
                while True:
                    try:
                        await asyncio.wait_for(self.ws.send_heartbeat(data), timeout=10)
                        break
                    except asyncio.TimeoutError:
                        total += 10

                        stack = ''.join(traceback.format_stack())
                        msg = f'{self.block_msg}\nLoop traceback (most recent call last):\n{stack}'
                        _log.warning(msg, total)

            except Exception:
                self.stop()
            else:
                self._last_send = time.perf_counter()

    def get_payload(self):
        return {
            'op': self.ws.HEARTBEAT,
            'd': self.ws.sequence,
        }

    def start(self):
        self.ws.loop.create_task(self.run())

    def stop(self):
        self._stop.set()

    def tick(self):
        self._last_recv = time.perf_counter()

    def ack(self):
        ack_time = time.perf_counter()
        self._last_ack = ack_time
        self.latency = ack_time - self._last_send
        if self.latency > 10:
            _log.warning(self.behind_msg, self.latency)


class VoiceKeepAliveHandler(KeepAliveHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recent_ack_latencies = deque(maxlen=20)
        self.msg = 'Keeping voice websocket alive.'
        self.block_msg = 'Voice heartbeat blocked for more than %s seconds'
        self.behind_msg = 'High socket latency, heartbeat is %.1fs behind'
        self.not_responding_msg = 'Voice gateway has stopped responding. Closing and restarting.'
        self.no_stop_msg = 'An error occurred while stopping the voice gateway. Ignoring.'

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
        if self.latency > 10:
            _log.warning(self.behind_msg, self.latency)


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
        Send only. Asks for the guild members.
    INVALIDATE_SESSION
        Receive only. Tells the client to optionally invalidate the session
        and IDENTIFY again.
    HELLO
        Receive only. Tells the client the heartbeat interval.
    HEARTBEAT_ACK
        Receive only. Confirms receiving of a heartbeat. Not having it implies
        a connection issue.
    GUILD_SYNC
        Send only. Requests a guild sync. This is unfortunately no longer functional.
    CALL_CONNECT
        Send only. Maybe used for calling? Probably just tracking.
    GUILD_SUBSCRIBE
        Send only. Subscribes you to guilds/guild members. Might respond with GUILD_MEMBER_LIST_UPDATE.
    REQUEST_COMMANDS
        Send only. Requests application commands from a guild. Responds with GUILD_APPLICATION_COMMANDS_UPDATE.
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
    GUILD_SYNC         = 12  # :(
    CALL_CONNECT       = 13
    GUILD_SUBSCRIBE    = 14
    REQUEST_COMMANDS   = 24

    def __init__(self, socket, *, loop):
        self.socket = socket
        self.loop = loop

        # An empty dispatcher to prevent crashes
        self._dispatch = lambda *args: None
        # Generic event listeners
        self._dispatch_listeners = []
        # the keep alive
        self._keep_alive = None
        self.thread_id = threading.get_ident()

        # WS related stuff
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

    def debug_log_receive(self, data, /):
        self._dispatch('socket_raw_receive', data)

    def log_receive(self, _, /):
        pass

    @classmethod
    async def from_client(cls, client, *, initial=False, gateway=None, session=None, sequence=None, resume=False):
        """Creates a main websocket for Discord from a :class:`Client`.

        This is for internal use only.
        """
        gateway = gateway or await client.http.get_gateway()
        socket = await client.http.ws_connect(gateway)
        ws = cls(socket, loop=client.loop)

        # Dynamically add attributes needed
        ws.token = client.http.token
        ws._connection = client._connection
        ws._discord_parsers = client._connection.parsers
        ws._dispatch = client.dispatch
        ws.gateway = gateway
        ws.call_hooks = client._connection.call_hooks
        ws._initial_identify = initial
        ws.session_id = session
        ws.sequence = sequence
        ws._max_heartbeat_timeout = client._connection.heartbeat_timeout
        ws._user_agent = client.http.user_agent
        ws._super_properties = client.http.super_properties
        ws._zlib_enabled = client.http.zlib


        if client._enable_debug_events:
            ws.send = ws.debug_send
            ws.log_receive = ws.debug_log_receive

        client._connection._update_references(ws)

        _log.debug('Connected to %s.', gateway)

        # Poll for Hello
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
            The event to wait for.
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

        event = event.upper()
        future = self.loop.create_future()
        entry = EventListener(event=event, predicate=predicate, result=result, future=future)
        self._dispatch_listeners.append(entry)
        return future

    async def identify(self):
        """Sends the IDENTIFY packet."""
        state = self._connection
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'capabilities': 253,
                'properties': self._super_properties,
                'presence': {
                    'status': 'online',
                    'since': 0,
                    'activities': [],
                    'afk': False
                },
                'compress': False,
                'client_state': {
                    'guild_hashes': {},
                    'highest_last_message_id': '0',
                    'read_state_version': 0,
                    'user_guild_settings_version': -1
                }
            }
        }

        if not self._zlib_enabled:
            payload['d']['compress'] = True

        await self.call_hooks('before_identify', initial=self._initial_identify)
        await self.send_as_json(payload)
        _log.info('Gateway has sent the IDENTIFY payload.')

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
        _log.info('Gateway has sent the RESUME payload.')

    async def received_message(self, msg, /):
        if type(msg) is bytes:
            self._buffer.extend(msg)

            if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                return
            msg = self._zlib.decompress(self._buffer)
            msg = msg.decode('utf-8')
            self._buffer = bytearray()

        self.log_receive(msg)
        msg = utils._from_json(msg)

        _log.debug('Gateway event: %s.', msg)
        event = msg.get('t')
        if event:
            self._dispatch('socket_event_type', event)

        op = msg.get('op')
        data = msg.get('d')
        seq = msg.get('s')
        if seq is not None:
            self.sequence = seq

        if self._keep_alive:
            self._keep_alive.tick()

        if op != self.DISPATCH:
            if op == self.RECONNECT:
                # RECONNECT can only be handled by the Client
                # so we terminate our connection and raise an
                # internal exception signalling to reconnect
                _log.debug('Received RECONNECT opcode.')
                await self.close()
                raise ReconnectWebSocket

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
                self._keep_alive = KeepAliveHandler(ws=self, interval=interval)
                # Send a heartbeat immediately
                await self.send_as_json(self._keep_alive.get_payload())
                self._keep_alive.start()
                return

            if op == self.INVALIDATE_SESSION:
                if data is True:
                    await self.close()
                    raise ReconnectWebSocket

                self.sequence = None
                self.session_id = None
                _log.info('Gateway session has been invalidated.')
                await self.close(code=1000)
                raise ReconnectWebSocket(resume=False)

            _log.warning('Unknown OP code %s.', op)
            return

        if event == 'READY':
            self._trace = trace = data.get('_trace', [])
            self.sequence = msg['s']
            self.session_id = data['session_id']
            _log.info('Connected to Gateway: %s (Session ID: %s).',
                      ', '.join(trace), self.session_id)
            await self.voice_state()  # Initial OP 4

        elif event == 'RESUMED':
            self._trace = trace = data.get('_trace', [])
            _log.info('Gateway has successfully RESUMED session %s under trace %s.',
                      self.session_id, ', '.join(trace))

        try:
            func = self._discord_parsers[event]
        except KeyError:
            _log.debug('Unknown event %s.', event)
        else:
            _log.debug('Parsing event %s.', event)
            func(data)

        # Remove the dispatched listeners
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
                _log.debug('Received %s.', msg)
                raise msg.data
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                _log.debug('Received %s.', msg)
                raise WebSocketClosure
        except (asyncio.TimeoutError, WebSocketClosure) as e:
            # Ensure the keep alive handler is closed
            if self._keep_alive:
                self._keep_alive.stop()
                self._keep_alive = None

            if isinstance(e, asyncio.TimeoutError):
                _log.info('Timed out receiving packet. Attempting a reconnect.')
                raise ReconnectWebSocket from None

            code = self._close_code or self.socket.close_code
            if self._can_handle_close():
                _log.info('Websocket closed with %s, attempting a reconnect.', code)
                raise ReconnectWebSocket from None
            else:
                _log.info('Websocket closed with %s, cannot reconnect.', code)
                raise ConnectionClosed(self.socket, code=code) from None

    async def debug_send(self, data, /):
        await self._rate_limiter.block()
        self._dispatch('socket_raw_send', data)
        await self.socket.send_str(data)

    async def send(self, data, /):
        await self._rate_limiter.block()
        await self.socket.send_str(data)

    async def send_as_json(self, data):
        try:
            await self.send(utils._to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket) from exc

    async def send_heartbeat(self, data):
        # This bypasses the rate limit handling code since it has a higher priority
        try:
            await self.socket.send_str(utils._to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket) from exc

    async def change_presence(self, *, activities=None, status=None, since=0, afk=False):
        if activities is not None:
            if not all(isinstance(activity, BaseActivity) for activity in activities):
                raise InvalidArgument('activity must derive from BaseActivity')
            activities = [activity.to_dict() for activity in activities]
        else:
            activities = []

        if status == 'idle':
            since = int(time.time() * 1000)

        payload = {
            'op': self.PRESENCE,
            'd': {
                'activities': activities,
                'afk': afk,
                'since': since,
                'status': str(status)
            }
        }

        sent = utils._to_json(payload)
        _log.debug('Sending "%s" to change presence.', sent)
        await self.send(sent)

    async def request_lazy_guild(self, guild_id, *, typing=None, threads=None, activities=None, members=None, channels=None, thread_member_lists=None):
        payload = {
            'op': self.GUILD_SUBSCRIBE,
            'd': {
                'guild_id': guild_id,
            }
        }

        data = payload['d']
        if typing is not None:
            data['typing'] = typing
        if threads is not None:
            data['threads'] = threads
        if activities is not None:
            data['activities'] = activities
        if members is not None:
            data['members'] = members
        if channels is not None:
            data['channels'] = channels
        if thread_member_lists is not None:
            data['thread_member_lists'] = thread_member_lists

        await self.send_as_json(payload)

    async def request_chunks(self, guild_ids, query=None, *, limit=None, user_ids=None, presences=True, nonce=None):
        payload = {
            'op': self.REQUEST_MEMBERS,
            'd': {
                'guild_id': guild_ids,
                'query': query,
                'limit': limit,
                'presences': presences,
                'user_ids': user_ids,
            }
        }

        if nonce:
            payload['d']['nonce'] = nonce

        await self.send_as_json(payload)

    async def voice_state(self, guild_id=None, channel_id=None, self_mute=False, self_deaf=False, self_video=False, *, preferred_region=None):
        payload = {
            'op': self.VOICE_STATE,
            'd': {
                'guild_id': guild_id,
                'channel_id': channel_id,
                'self_mute': self_mute,
                'self_deaf': self_deaf,
                'self_video': self_video,
            }
        }

        if preferred_region is not None:
            payload['d']['preferred_region'] = preferred_region

        _log.debug('Updating %s voice state to %s.', guild_id or 'client', payload)
        await self.send_as_json(payload)

    async def access_dm(self, channel_id):
        payload = {
            'op': self.CALL_CONNECT,
            'd': {
                'channel_id': channel_id
            }
        }

        _log.debug('Sending ACCESS_DM for channel %s.', channel_id)
        await self.send_as_json(payload)

    async def request_commands(self, guild_id, type, *, nonce=None, limit=None, applications=None, offset=0, query=None, command_ids=None, application_id=None):
        payload = {
            'op': self.REQUEST_COMMANDS,
            'd': {
                'guild_id': guild_id,
                'type': type,
            }
        }

        if nonce is not None:
            payload['d']['nonce'] = nonce
        if applications is not None:
            payload['d']['applications'] = applications
        if limit is not None and limit != 25:
            payload['d']['limit'] = limit
        if offset:
            payload['d']['offset'] = offset
        if query is not None:
            payload['d']['query'] = query
        if command_ids is not None:
            payload['d']['command_ids'] = command_ids
        if application_id is not None:
            payload['d']['application_id'] = application_id

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
    SELECT_PROTOCOL_ACK
        Receive only. Gives you the secret key required for voice.
    SPEAKING
        Send and receive. Notifies the client if anyone begins speaking.
    HEARTBEAT_ACK
        Receive only. Tells you your heartbeat has been acknowledged.
    RESUME
        Sent only. Tells the client to resume its session.
    HELLO
        Receive only. Tells you that your websocket connection was acknowledged.
    RESUMED
        Sent only. Tells you that your RESUME request has succeeded.
    CLIENT_DISCONNECT
        Receive only. Indicates a user has disconnected from voice.
    """

    IDENTIFY              = 0
    SELECT_PROTOCOL       = 1
    READY                 = 2
    HEARTBEAT             = 3
    SELECT_PROTOCOL_ACK   = 4
    SPEAKING              = 5
    HEARTBEAT_ACK         = 6
    RESUME                = 7
    HELLO                 = 8
    RESUMED               = 9
    VIDEO                 = 12
    CLIENT_DISCONNECT     = 13
    SESSION_UPDATE        = 14
    MEDIA_SINK_WANTS      = 15
    VOICE_BACKEND_VERSION = 16

    def __init__(self, socket, loop, *, hook=None):
        self.ws = socket
        self.loop = loop
        self._keep_alive = None
        self._close_code = None
        self.secret_key = None
        if hook:
            self._hook = hook

    async def _hook(self, *args):
        pass

    async def send_as_json(self, data):
        _log.debug('Voice gateway sending: %s.', data)
        await self.ws.send_str(utils._to_json(data))

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
    async def from_client(cls, client, *, resume=False, hook=None):
        """Creates a voice websocket for the :class:`VoiceClient`."""
        gateway = 'wss://' + client.endpoint + '/?v=4'
        http = client._state.http
        socket = await http.ws_connect(gateway, compress=15, host=client.endpoint)
        ws = cls(socket, loop=client.loop, hook=hook)
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
        _log.debug('Voice gateway event: %s.', msg)
        op = msg['op']
        data = msg.get('d')

        if op == self.READY:
            await self.initial_connection(data)
        elif op == self.HEARTBEAT_ACK:
            self._keep_alive.ack()
        elif op == self.RESUMED:
            _log.info('Voice RESUME succeeded.')
            self.secret_key = self._connection.secret_key
        elif op == self.SELECT_PROTOCOL_ACK:
            self._connection.mode = data['mode']
            await self.load_secret_key(data)
        elif op == self.HELLO:
            interval = data['heartbeat_interval'] / 1000.0
            self._keep_alive = VoiceKeepAliveHandler(ws=self, interval=min(interval, 5.0))
            self._keep_alive.start()
        elif op == self.SPEAKING:
            state = self._connection
            user_id = int(data['user_id'])
            speaking = data['speaking']
            ssrc = state._flip_ssrc(user_id)
            if ssrc is None:
                state._set_ssrc(user_id, SSRC(data['ssrc'], speaking))
            else:
                ssrc.speaking = speaking

            #item = state.guild or state._state
            #item._update_speaking_status(user_id, speaking)

        await self._hook(self, msg)

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
        _log.debug('Received packet in initial_connection: %s.', recv)

        # The IP is ascii starting at the 4th byte and ending at the first null
        ip_start = 4
        ip_end = recv.index(0, ip_start)
        state.ip = recv[ip_start:ip_end].decode('ascii')

        state.port = struct.unpack_from('>H', recv, len(recv) - 2)[0]
        _log.debug('Detected ip: %s, port: %s.', state.ip, state.port)

        # There *should* always be at least one supported mode (xsalsa20_poly1305)
        modes = [mode for mode in data['modes'] if mode in self._connection.supported_modes]
        _log.debug('Received supported encryption modes: %s.', ", ".join(modes))

        mode = modes[0]
        await self.select_protocol(state.ip, state.port, mode)
        _log.info('Selected the voice protocol for use: %s.', mode)

    @property
    def latency(self):
        """:class:`float`: Latency between a HEARTBEAT and its HEARTBEAT_ACK in seconds."""
        heartbeat = self._keep_alive
        return float('inf') if heartbeat is None else heartbeat.latency

    @property
    def average_latency(self):
        """:class:`list`: Average of last 20 HEARTBEAT latencies."""
        heartbeat = self._keep_alive
        if heartbeat is None or not heartbeat.recent_ack_latencies:
            return float('inf')

        return sum(heartbeat.recent_ack_latencies) / len(heartbeat.recent_ack_latencies)

    async def load_secret_key(self, data):
        _log.info('Received secret key for voice connection.')
        self.secret_key = self._connection.secret_key = data.get('secret_key')
        await self.speak()
        await self.speak(False)

    async def poll_event(self):
        # This exception is handled up the chain
        msg = await asyncio.wait_for(self.ws.receive(), timeout=30.0)
        if msg.type is aiohttp.WSMsgType.TEXT:
            await self.received_message(utils._from_json(msg.data))
        elif msg.type is aiohttp.WSMsgType.ERROR:
            _log.debug('Voice received %s.', msg)
            raise ConnectionClosed(self.ws) from msg.data
        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
            _log.debug('Voice received %s.', msg)
            raise ConnectionClosed(self.ws, code=self._close_code)

    async def close(self, code=1000):
        if self._keep_alive is not None:
            self._keep_alive.stop()

        self._close_code = code
        await self.ws.close(code=code)
