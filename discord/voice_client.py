# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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

"""Some documentation to refer to:

- Our main web socket (mWS) sends opcode 4 with a server ID and channel ID.
- The mWS receives VOICE_STATE_UPDATE and VOICE_SERVER_UPDATE.
- We pull the session_id from VOICE_STATE_UPDATE.
- We pull the token, endpoint and guild_id from VOICE_SERVER_UPDATE.
- Then we initiate the voice web socket (vWS) pointing to the endpoint.
- We send opcode 0 with the user_id, guild_id, session_id and token using the vWS.
- The vWS sends back opcode 2 with an ssrc, port, modes(array) and hearbeat_interval.
- We send a UDP discovery packet to endpoint:port and receive our IP and our port in LE.
- Then we send our IP and port via vWS with opcode 1.
- When that's all done, we receive opcode 4 from the vWS.
- Finally we can transmit data to endpoint:port.
"""

import asyncio
import websockets
import socket
import json, time
import logging
import struct

log = logging.getLogger(__name__)

from . import utils
from .errors import ClientException

class VoiceClient:
    """Represents a Discord voice connection.

    This client is created solely through :meth:`Client.join_voice_channel`
    and its only purpose is to transmit voice.

    Attributes
    -----------
    session_id : str
        The voice connection session ID.
    token : str
        The voice connection token.
    user : :class:`User`
        The user connected to voice.
    endpoint : str
        The endpoint we are connecting to.
    channel : :class:`Channel`
        The voice channel connected to.
    """
    def __init__(self, user, connected, session_id, channel, data, loop):
        self.user = user
        self._connected = connected
        self.channel = channel
        self.session_id = session_id
        self.loop = loop
        self.token = data.get('token')
        self.guild_id = data.get('guild_id')
        self.endpoint = data.get('endpoint')

    @asyncio.coroutine
    def keep_alive_handler(self, delay):
        while True:
            payload = {
                'op': 3,
                'd': int(time.time())
            }

            msg = 'Keeping voice websocket alive with timestamp {}'
            log.debug(msg.format(payload['d']))
            yield from self.ws.send(utils.to_json(payload))
            yield from asyncio.sleep(delay)

    @asyncio.coroutine
    def received_message(self, msg):
        log.debug('Voice websocket frame received: {}'.format(msg))
        op = msg.get('op')
        data = msg.get('d')

        if op == 2:
            delay = (data['heartbeat_interval'] / 100.0) - 5
            self.keep_alive = utils.create_task(self.keep_alive_handler(delay), loop=self.loop)
            yield from self.initial_connection(data)
        elif op == 4:
            yield from self.connection_ready(data)

    @asyncio.coroutine
    def initial_connection(self, data):
        self.ssrc = data.get('ssrc')
        self.voice_port = data.get('port')
        packet = bytearray(70)
        struct.pack_into('>I', packet, 0, self.ssrc)
        self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
        recv = yield from self.loop.sock_recv(self.socket, 70)
        self.ip = []

        for x in range(4, len(recv)):
            val = recv[x]
            if val == 0:
                break
            self.ip.append(str(val))

        self.ip = '.'.join(self.ip)
        self.port = recv[len(recv) - 2] << 0 | recv[len(recv) - 1] << 1

        payload = {
            'op': 1,
            'd': {
                'protocol': 'udp',
                'data': {
                    'address': self.ip,
                    'port': self.port,
                    'mode': 'plain'
                }
            }
        }

        yield from self.ws.send(utils.to_json(payload))
        log.debug('sent {} to initialize voice connection'.format(payload))
        log.info('initial voice connection is done')

    @asyncio.coroutine
    def connection_ready(self, data):
        log.info('voice connection is now ready')
        speaking = {
            'op': 5,
            'd': {
                'speaking': True,
                'delay': 0
            }
        }

        yield from self.ws.send(utils.to_json(speaking))
        self._connected.set()

    @asyncio.coroutine
    def connect(self):
        log.info('voice connection is connecting...')
        self.endpoint = self.endpoint.replace(':80', '')
        self.endpoint_ip = socket.gethostbyname(self.endpoint)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        log.info('Voice endpoint found {0.endpoint} (IP: {0.endpoint_ip})'.format(self))
        self.ws = yield from websockets.connect('wss://' + self.endpoint, loop=self.loop)
        self.ws.max_size = None

        payload = {
            'op': 0,
            'd': {
                'server_id': self.guild_id,
                'user_id': self.user.id,
                'session_id': self.session_id,
                'token': self.token
            }
        }

        yield from self.ws.send(utils.to_json(payload))

        while not self._connected.is_set():
            msg = yield from self.ws.recv()
            if msg is None:
                yield from self.disconnect()
                raise ClientException('Unexpected websocket close on voice websocket')

            yield from self.received_message(json.loads(msg))

    @asyncio.coroutine
    def disconnect(self):
        """|coro|

        Disconnects all connections to the voice client.

        In order to reconnect, you must create another voice client
        using :meth:`Client.join_voice_channel`.
        """
        if not self._connected.is_set():
            return

        self.keep_alive.cancel()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self._connected.clear()
        yield from self.ws.close()
