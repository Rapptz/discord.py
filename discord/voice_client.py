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

"""Some documentation to refer to:

- Our main web socket (mWS) sends opcode 4 with a guild ID and channel ID.
- The mWS receives VOICE_STATE_UPDATE and VOICE_SERVER_UPDATE.
- We pull the session_id from VOICE_STATE_UPDATE.
- We pull the token, endpoint and server_id from VOICE_SERVER_UPDATE.
- Then we initiate the voice web socket (vWS) pointing to the endpoint.
- We send opcode 0 with the user_id, server_id, session_id and token using the vWS.
- The vWS sends back opcode 2 with an ssrc, port, modes(array) and hearbeat_interval.
- We send a UDP discovery packet to endpoint:port and receive our IP and our port in LE.
- Then we send our IP and port via vWS with opcode 1.
- When that's all done, we receive opcode 4 from the vWS.
- Finally we can transmit data to endpoint:port.
"""

import asyncio
import socket
import logging
import struct
import threading

from . import opus
from .backoff import ExponentialBackoff
from .gateway import *
from .errors import ClientException, ConnectionClosed
from .player import AudioPlayer, AudioSource

try:
    import nacl.secret
    has_nacl = True
except ImportError:
    has_nacl = False

log = logging.getLogger(__name__)

class VoiceClient:
    """Represents a Discord voice connection.

    You do not create these, you typically get them from
    e.g. :meth:`VoiceChannel.connect`.

    Warning
    --------
    In order to use PCM based AudioSources, you must have the opus library
    installed on your system and loaded through :func:`opus.load_opus`.
    Otherwise, your AudioSources must be opus encoded (e.g. using :class:`FFmpegOpusAudio`)
    or the library will not be able to transmit audio.

    Attributes
    -----------
    session_id: :class:`str`
        The voice connection session ID.
    token: :class:`str`
        The voice connection token.
    endpoint: :class:`str`
        The endpoint we are connecting to.
    channel: :class:`abc.Connectable`
        The voice channel connected to.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the voice client is running on.
    """
    def __init__(self, client, timeout, channel):
        if not has_nacl:
            raise RuntimeError("PyNaCl library needed in order to use voice")

        self.channel = channel
        self.__main_ws = None
        self.__timeout = timeout
        self.__ws = None
        self.__socket = None
        self.loop = client.loop
        self.__state = client._connection
        # this will be used in the AudioPlayer thread
        self.__connected = threading.Event()

        self.__handshaking = False
        self.__handshake_check = asyncio.Lock()
        self.__handshake_complete = asyncio.Event()

        self.__mode = None
        self.__connections = 0
        self.__sequence = 0
        self.__timestamp = 0
        self.__runner = None
        self.__player = None
        self.__encoder = None
        self.__lite_nonce = 0

    warn_nacl = not has_nacl
    supported_modes = (
        'xsalsa20_poly1305_lite',
        'xsalsa20_poly1305_suffix',
        'xsalsa20_poly1305',
    )

    @property
    def guild(self):
        """Optional[:class:`Guild`]: The guild we're connected to, if applicable."""
        return getattr(self.channel, 'guild', None)

    @property
    def user(self):
        """:class:`ClientUser`: The user connected to voice (i.e. ourselves)."""
        return self.__state.user

    def __checked_add(self, attr, value, limit):
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)

    # connection related

    async def __start_handshake(self):
        log.info('Starting voice handshake...')

        guild_id, channel_id = self.channel._get_voice_state_pair()
        state = self.__state
        self.__main_ws = ws = state._get_websocket(guild_id)
        self.__connections += 1

        # request joining
        await ws.voice_state(guild_id, channel_id)

        try:
            await asyncio.wait_for(self.__handshake_complete.wait(), timeout=self.__timeout)
        except asyncio.TimeoutError:
            await self.__terminate_handshake(remove=True)
            raise

        log.info('Voice handshake complete. Endpoint found %s (IP: %s)', self.endpoint, self.__endpoint_ip)

    async def __terminate_handshake(self, *, remove=False):
        guild_id, channel_id = self.channel._get_voice_state_pair()
        self.__handshake_complete.clear()
        await self.__main_ws.voice_state(guild_id, None, self_mute=True)

        log.info('The voice handshake is being terminated for Channel ID %s (Guild ID %s)', channel_id, guild_id)
        if remove:
            log.info('The voice client has been removed for Channel ID %s (Guild ID %s)', channel_id, guild_id)
            key_id, _ = self.channel._get_voice_client_key()
            self.__state._remove_voice_client(key_id)

    async def __create_socket(self, server_id, data):
        async with self.__handshake_check:
            if self.__handshaking:
                log.info("Ignoring voice server update while handshake is in progress")
                return
            self.__handshaking = True

        self.__connected.clear()
        self.session_id = self.__main_ws.session_id
        self.__server_id = server_id
        self.token = data.get('token')
        endpoint = data.get('endpoint')

        if endpoint is None or self.token is None:
            log.warning('Awaiting endpoint... This requires waiting. ' \
                        'If timeout occurred considering raising the timeout and reconnecting.')
            return

        self.endpoint = endpoint.replace(':80', '')
        self.__endpoint_ip = socket.gethostbyname(self.endpoint)

        if self.__socket:
            try:
                self.__socket.close()
            except Exception:
                pass

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.setblocking(False)

        if self.__handshake_complete.is_set():
            # terminate the websocket and handle the reconnect loop if necessary.
            self.__handshake_complete.clear()
            await self.__ws.close(4000)
            return

        self.__handshake_complete.set()

    @property
    def latency(self):
        """:class:`float`: Latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This could be referred to as the Discord Voice WebSocket latency and is
        an analogue of user's voice latencies as seen in the Discord client.
        """
        ws = self.__ws
        return float("inf") if not ws else ws.latency

    @property
    def average_latency(self):
        """:class:`float`: Average of most recent 20 HEARTBEAT latencies in seconds."""
        ws = self.__ws
        return float("inf") if not ws else ws.average_latency

    async def connect(self, *, reconnect=True, _tries=0, do_handshake=True):
        log.info('Connecting to voice...')
        try:
            del self.__secret_key
        except AttributeError:
            pass

        if do_handshake:
            await self.__start_handshake()

        try:
            self.__ws = await DiscordVoiceWebSocket.from_client(self)
            self.__handshaking = False
            self.__connected.clear()
            while not hasattr(self, '_VoiceClient__secret_key'):
                await self.__ws.poll_event()
            self.__connected.set()
        except (ConnectionClosed, asyncio.TimeoutError):
            if reconnect and _tries < 5:
                log.exception('Failed to connect to voice... Retrying...')
                await asyncio.sleep(1 + _tries * 2.0)
                await self.__terminate_handshake()
                await self.connect(reconnect=reconnect, _tries=_tries + 1)
            else:
                raise

        if self.__runner is None:
            self.__runner = self.loop.create_task(self.__poll_voice_ws(reconnect))

    async def __poll_voice_ws(self, reconnect):
        backoff = ExponentialBackoff()
        while True:
            try:
                await self.__ws.poll_event()
            except (ConnectionClosed, asyncio.TimeoutError) as exc:
                if isinstance(exc, ConnectionClosed):
                    # The following close codes are undocumented so I will document them here.
                    # 1000 - normal closure (obviously)
                    # 4014 - voice channel has been deleted.
                    # 4015 - voice server has crashed
                    if exc.code in (1000, 4014, 4015):
                        log.info('Disconnecting from voice normally, close code %d.', exc.code)
                        await self.disconnect()
                        break

                if not reconnect:
                    await self.disconnect()
                    raise

                retry = backoff.delay()
                log.exception('Disconnected from voice... Reconnecting in %.2fs.', retry)
                self.__connected.clear()
                await asyncio.sleep(retry)
                await self.__terminate_handshake()
                try:
                    await self.connect(reconnect=True)
                except asyncio.TimeoutError:
                    # at this point we've retried 5 times... let's continue the loop.
                    log.warning('Could not connect to voice... Retrying...')
                    continue

    async def disconnect(self, *, force=False):
        """|coro|

        Disconnects this voice client from voice.
        """
        if not force and not self.is_connected():
            return

        self.stop()
        self.__connected.clear()

        try:
            if self.__ws:
                await self.__ws.close()

            await self.__terminate_handshake(remove=True)
        finally:
            if self.__socket:
                self.__socket.close()

    async def move_to(self, channel):
        """|coro|

        Moves you to a different voice channel.

        Parameters
        -----------
        channel: :class:`abc.Snowflake`
            The channel to move to. Must be a voice channel.
        """
        guild_id, _ = self.channel._get_voice_state_pair()
        await self.__main_ws.voice_state(guild_id, channel.id)

    def is_connected(self):
        """Indicates if the voice client is connected to voice."""
        return self.__connected.is_set()

    # audio related

    def __get_voice_packet(self, data):
        header = bytearray(12)

        # Formulate rtp header
        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into('>H', header, 2, self.__sequence)
        struct.pack_into('>I', header, 4, self.__timestamp)
        struct.pack_into('>I', header, 8, self.__ssrc)

        encrypt_packet = getattr(self, '_VoiceClient__encrypt_' + self.__mode)
        return encrypt_packet(header, data)

    def __encrypt_xsalsa20_poly1305(self, header, data):
        box = nacl.secret.SecretBox(bytes(self.__secret_key))
        nonce = bytearray(24)
        nonce[:12] = header

        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext

    def __encrypt_xsalsa20_poly1305_suffix(self, header, data):
        box = nacl.secret.SecretBox(bytes(self.__secret_key))
        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

        return header + box.encrypt(bytes(data), nonce).ciphertext + nonce

    def __encrypt_xsalsa20_poly1305_lite(self, header, data):
        box = nacl.secret.SecretBox(bytes(self.__secret_key))
        nonce = bytearray(24)

        nonce[:4] = struct.pack('>I', self.__lite_nonce)
        self.__checked_add('_VoiceClient__lite_nonce', 1, 4294967295)

        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext + nonce[:4]

    def play(self, source, *, after=None):
        """Plays an :class:`AudioSource`.

        The finalizer, ``after`` is called after the source has been exhausted
        or an error occurred.

        If an error happens while the audio player is running, the exception is
        caught and the audio player is then stopped.  If no after callback is
        passed, any caught exception will be displayed as if it were raised.

        Parameters
        -----------
        source: :class:`AudioSource`
            The audio source we're reading from.
        after: Callable[[:class:`Exception`], Any]
            The finalizer that is called after the stream is exhausted.
            This function must have a single parameter, ``error``, that
            denotes an optional exception that was raised during playing.

        Raises
        -------
        ClientException
            Already playing audio or not connected.
        TypeError
            Source is not a :class:`AudioSource` or after is not a callable.
        OpusNotLoaded
            Source is not opus encoded and opus is not loaded.
        """

        if not self.is_connected():
            raise ClientException('Not connected to voice.')

        if self.is_playing():
            raise ClientException('Already playing audio.')

        if not isinstance(source, AudioSource):
            raise TypeError('source must an AudioSource not {0.__class__.__name__}'.format(source))

        if not self.__encoder and not source.is_opus():
            self.__encoder = opus.Encoder()

        self.__player = AudioPlayer(source, self, after=after)
        self.__player.start()

    def is_playing(self):
        """Indicates if we're currently playing audio."""
        return self.__player is not None and self.__player.is_playing()

    def is_paused(self):
        """Indicates if we're playing audio, but if we're paused."""
        return self.__player is not None and self.__player.is_paused()

    def stop(self):
        """Stops playing audio."""
        if self.__player:
            self.__player.stop()
            self.__player = None

    def pause(self):
        """Pauses the audio playing."""
        if self.__player:
            self.__player.pause()

    def resume(self):
        """Resumes the audio playing."""
        if self.__player:
            self.__player.resume()

    @property
    def source(self):
        """Optional[:class:`AudioSource`]: The audio source being played, if playing.

        This property can also be used to change the audio source currently being played.
        """
        return self.__player.source if self.__player else None

    @source.setter
    def source(self, value):
        if not isinstance(value, AudioSource):
            raise TypeError('expected AudioSource not {0.__class__.__name__}.'.format(value))

        if self.__player is None:
            raise ValueError('Not playing anything.')

        self.__player._set_source(value)

    def send_audio_packet(self, data, *, encode=True):
        """Sends an audio packet composed of the data.

        You must be connected to play audio.

        Parameters
        ----------
        data: :class:`bytes`
            The :term:`py:bytes-like object` denoting PCM or Opus voice data.
        encode: :class:`bool`
            Indicates if ``data`` should be encoded into Opus.

        Raises
        -------
        ClientException
            You are not connected.
        opus.OpusError
            Encoding the data failed.
        """

        self.__checked_add('_VoiceClient__sequence', 1, 65535)
        if encode:
            encoded_data = self.__encoder.encode(data, self.__encoder.SAMPLES_PER_FRAME)
        else:
            encoded_data = data
        packet = self.__get_voice_packet(encoded_data)
        try:
            self.__socket.sendto(packet, (self.__endpoint_ip, self.__voice_port))
        except BlockingIOError:
            log.warning('A packet has been dropped (seq: %s, timestamp: %s)', self.__sequence, self.__timestamp)

        self.__checked_add('_VoiceClient__timestamp', opus.Encoder.SAMPLES_PER_FRAME, 4294967295)
