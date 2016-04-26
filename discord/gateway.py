# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

import sys
import websockets
import asyncio
import aiohttp
from . import utils, endpoints, compat
from .enums import Status
from .game import Game
from .errors import GatewayNotFound, ConnectionClosed, InvalidArgument
import logging
import zlib, time, json
from collections import namedtuple
import threading

log = logging.getLogger(__name__)

__all__ = [ 'ReconnectWebSocket', 'get_gateway', 'DiscordWebSocket',
            'KeepAliveHandler' ]

class ReconnectWebSocket(Exception):
    """Signals to handle the RECONNECT opcode."""
    pass

EventListener = namedtuple('EventListener', 'predicate event result future')

class KeepAliveHandler(threading.Thread):
    def __init__(self, *args, **kwargs):
        ws = kwargs.pop('ws', None)
        interval = kwargs.pop('interval', None)
        threading.Thread.__init__(self, *args, **kwargs)
        self.ws = ws
        self.interval = interval
        self.daemon = True
        self._stop = threading.Event()

    def run(self):
        while not self._stop.wait(self.interval):
            data = self.get_payload()
            msg = 'Keeping websocket alive with sequence {0[d]}'.format(data)
            log.debug(msg)
            coro = self.ws.send_as_json(data)
            f = compat.run_coroutine_threadsafe(coro, loop=self.ws.loop)
            try:
                # block until sending is complete
                f.result()
            except Exception:
                self.stop()

    def get_payload(self):
        return {
            'op': self.ws.HEARTBEAT,
            'd': self.ws._connection.sequence
        }

    def stop(self):
        self._stop.set()


@asyncio.coroutine
def get_gateway(token, *, loop=None):
    """Returns the gateway URL for connecting to the WebSocket.

    Parameters
    -----------
    token : str
        The discord authentication token.
    loop
        The event loop.

    Raises
    ------
    GatewayNotFound
        When the gateway is not returned gracefully.
    """
    headers = {
        'authorization': token,
        'content-type': 'application/json'
    }

    with aiohttp.ClientSession(loop=loop) as session:
        resp = yield from session.get(endpoints.GATEWAY, headers=headers)
        if resp.status != 200:
            yield from resp.release()
            raise GatewayNotFound()
        data = yield from resp.json()
        return data.get('url')

class DiscordWebSocket(websockets.client.WebSocketClientProtocol):
    """Implements a WebSocket for Discord's gateway v4.

    This is created through :func:`create_main_websocket`. Library
    users should never create this manually.

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
        Send only. Starts a new connection to a voice server.
    VOICE_PING
        Send only. Checks ping time to a voice server, do not use.
    RESUME
        Send only. Resumes an existing connection.
    RECONNECT
        Receive only. Tells the client to reconnect to a new gateway.
    REQUEST_MEMBERS
        Send only. Asks for the full member list of a server.
    INVALIDATE_SESSION
        Receive only. Tells the client to invalidate the session and IDENTIFY
        again.
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_size=None, **kwargs)
        # an empty dispatcher to prevent crashes
        self._dispatch = lambda *args: None
        # generic event listeners
        self._dispatch_listeners = []
        # the keep alive
        self._keep_alive = None

    @classmethod
    @asyncio.coroutine
    def connect(cls, dispatch, *, token=None, connection=None, loop=None):
        """Creates a main websocket for Discord used for the client.

        Parameters
        ----------
        token : str
            The token for Discord authentication.
        connection
            The ConnectionState for the client.
        dispatch
            The function that dispatches events.
        loop
            The event loop to use.

        Returns
        -------
        DiscordWebSocket
            A websocket connected to Discord.
        """

        gateway = yield from get_gateway(token, loop=loop)
        ws = yield from websockets.connect(gateway, loop=loop, klass=cls)

        # dynamically add attributes needed
        ws.token = token
        ws._connection = connection
        ws._dispatch = dispatch
        ws.gateway = gateway

        log.info('Created websocket connected to {}'.format(gateway))
        yield from ws.identify()
        log.info('sent the identify payload to create the websocket')
        return ws

    @classmethod
    def from_client(cls, client):
        """Creates a main websocket for Discord from a :class:`Client`.

        This is for internal use only.
        """
        return cls.connect(client.dispatch, token=client.token,
                                            connection=client.connection,
                                            loop=client.loop)

    def wait_for(self, event, predicate, result):
        """Waits for a DISPATCH'd event that meets the predicate.

        Parameters
        -----------
        event : str
            The event name in all upper case to wait for.
        predicate
            A function that takes a data parameter to check for event
            properties. The data parameter is the 'd' key in the JSON message.
        result
            A function that takes the same data parameter and executes to send
            the result to the future.

        Returns
        --------
        asyncio.Future
            A future to wait for.
        """

        future = asyncio.Future(loop=self.loop)
        entry = EventListener(event=event, predicate=predicate, result=result, future=future)
        self._dispatch_listeners.append(entry)
        return future

    @asyncio.coroutine
    def identify(self):
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
                'v': 3
            }
        }
        yield from self.send_as_json(payload)

    @asyncio.coroutine
    def received_message(self, msg):
        self._dispatch('socket_raw_receive', msg)

        if isinstance(msg, bytes):
            msg = zlib.decompress(msg, 15, 10490000) # This is 10 MiB
            msg = msg.decode('utf-8')

        msg = json.loads(msg)

        log.debug('WebSocket Event: {}'.format(msg))
        self._dispatch('socket_response', msg)

        op = msg.get('op')
        data = msg.get('d')

        if 's' in msg:
            self._connection.sequence = msg['s']

        if op == self.RECONNECT:
            # "reconnect" can only be handled by the Client
            # so we terminate our connection and raise an
            # internal exception signalling to reconnect.
            yield from self.close()
            raise ReconnectWebSocket()

        if op == self.INVALIDATE_SESSION:
            self._connection.sequence = None
            self._connection.session_id = None
            return

        if op != self.DISPATCH:
            log.info('Unhandled op {}'.format(op))
            return

        event = msg.get('t')
        is_ready = event == 'READY'

        if is_ready:
            self._connection.clear()
            self._connection.sequence = msg['s']
            self._connection.session_id = data['session_id']

        if is_ready or event == 'RESUMED':
            interval = data['heartbeat_interval'] / 1000.0
            self._keep_alive = KeepAliveHandler(ws=self, interval=interval)
            self._keep_alive.start()

        parser = 'parse_' + event.lower()

        try:
            func = getattr(self._connection, parser)
        except AttributeError:
            log.info('Unhandled event {}'.format(event))
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

            try:
                valid = entry.predicate(data)
            except Exception as e:
                future.set_exception(e)
                removed.append(index)
            else:
                if valid:
                    future.set_result(entry.result)
                    removed.append(index)

        for index in reversed(removed):
            del self._dispatch_listeners[index]

    @asyncio.coroutine
    def poll_event(self):
        """Polls for a DISPATCH event and handles the general gateway loop.

        Raises
        ------
        ConnectionClosed
            The websocket connection was terminated for unhandled reasons.
        """
        try:
            msg = yield from self.recv()
            yield from self.received_message(msg)
        except websockets.exceptions.ConnectionClosed as e:
            if e.code in (4008, 4009) or e.code in range(1001, 1015):
                raise ReconnectWebSocket() from e
            else:
                raise ConnectionClosed(e) from e

    @asyncio.coroutine
    def send(self, data):
        self._dispatch('socket_raw_send', data)
        yield from super().send(data)

    @asyncio.coroutine
    def send_as_json(self, data):
        yield from super().send(utils.to_json(data))

    @asyncio.coroutine
    def change_presence(self, *, game=None, idle=None):
        if game is not None and not isinstance(game, Game):
            raise InvalidArgument('game must be of Game or None')

        idle_since = None if idle == False else int(time.time() * 1000)
        sent_game = game and {'name': game.name}

        payload = {
            'op': self.PRESENCE,
            'd': {
                'game': sent_game,
                'idle_since': idle_since
            }
        }

        sent = utils.to_json(payload)
        log.debug('Sending "{}" to change status'.format(sent))
        yield from self.send(sent)

        for server in self._connection.servers:
            me = server.me
            if me is None:
                continue

            me.game = game
            status = Status.idle if idle_since else Status.online
            me.status = status

    @asyncio.coroutine
    def close(self, code=1000, reason=''):
        if self._keep_alive:
            self._keep_alive.stop()

        yield from super().close(code, reason)
