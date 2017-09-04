# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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
import heapq
import time

log = logging.getLogger(__name__)

try:
    import nacl.secret
    has_nacl = True
except ImportError:
    has_nacl = False

from . import opus
from .backoff import ExponentialBackoff
from .gateway import *
from .errors import ClientException, ConnectionClosed,  InvalidVoicePacket
from .player import AudioPlayer, AudioSource

class VoicePacket:
    """Represents a packet of voice data.

    You should not construct these yourself, they will be constructed from
    incoming UDP packets on the socket used for voice data.

    Attributes
    ----------
    sequence : int
        The sequence id for the packet. Must be between 0 and 65535. Each
        packet has a value of 1 greater than the previous packet from the
        same source. After the sequence reaches the maximum value (65535),
        the next packet has a sequence value of 0.
    timestamp : int
        The timestamp for the packet.
    ssrc : int
        The id of the user (or source) of this voice packet.
    buff : bytes
        The Opus packet (as bytes).
    user : Optional[:class:`abc.User`]
        The user who the packet belongs to
    pcm : Optional[bytes]
        The decoded PCM data.
    """
    # Struct format of the packet metadata
    _FORMAT = '>HHII'
    # Packets should start with b'\x80\x78' (32888 as a big endian ushort)
    _CHECK = 32888
    # Some packets will start with b'\x90\x78' (36984)
    _CHECK2 = 36984

    def __init__(self, sequence=None, timestamp=None, ssrc=None, buff=None, user=None):
        self.sequence = sequence
        self.timestamp = timestamp
        self.ssrc = ssrc
        self.buff = buff
        self.user = user

    @classmethod
    def unpack(cls, packet, voice_client):
        if len(packet) < 13:
            raise InvalidVoicePacket('packet is too small: {}'.format(packet))

        # Unpack header
        check, seq, ts, ssrc = struct.unpack_from(cls._FORMAT, packet)
        header = packet[:12]
        buff = packet[12:]

        # Check the packet is valid
        if check != cls._CHECK and check != cls._CHECK2:
            fmt = 'packet has invalid check bytes: {}'
            raise InvalidVoicePacket(fmt.format(packet))

        # Decrypt data
        nonce = bytearray(24)
        nonce[:12] = header
        box = nacl.secret.SecretBox(bytes(voice_client.secret_key))
        buff = box.decrypt(bytes(buff), bytes(nonce))

        # Packets starting with b'\x90' need the first 8 bytes ignored
        if check == cls._CHECK2:
            buff = buff[8:]

        # Lookup the SSRC and then get the user
        user_id = 0
        if voice_client.channel.id in voice_client._ssrc_lookup:
            if ssrc in voice_client._ssrc_lookup[voice_client.channel.id]:
                user_id = int(voice_client._ssrc_lookup[voice_client.channel.id][ssrc])
        user = voice_client._state.get_user(user_id)

        # Create a `VoicePacket` instance and return it.
        return cls(seq, ts, ssrc, buff, user)

    def __str__(self):
        fmt = '<VoicePacket sequence={0.sequence}, timestamp={0.timestamp}, ssrc={0.ssrc}, buff=bytes({1})>'
        return fmt.format(self, len(self.buff))

    def __repr__(self):
        return str(self)

class VoiceClient:
    """Represents a Discord voice connection.

    You do not create these, you typically get them from
    e.g. :meth:`VoiceChannel.connect`.

    Warning
    --------
    In order to play or receive audio, you must have loaded the opus
    library through :func:`opus.load_opus`.

    If you don't do this then the library will not be able to
    transmit or receive audio.

    Attributes
    -----------
    session_id: str
        The voice connection session ID.
    token: str
        The voice connection token.
    endpoint: str
        The endpoint we are connecting to.
    channel: :class:`abc.Connectable`
        The voice channel connected to.
    loop
        The event loop that the voice client is running on.
    """
    def __init__(self, state, timeout, channel):
        if not has_nacl:
            raise RuntimeError("PyNaCl library needed in order to use voice")

        self.channel = channel
        self.main_ws = None
        self.timeout = timeout
        self.ws = None
        self.socket = None
        self.loop = state.loop
        self._state = state
        # this will be used in the AudioPlayer thread
        self._connected = threading.Event()
        self._handshake_complete = asyncio.Event(loop=self.loop)

        self._connections = 0
        self.sequence = 0
        self.timestamp = 0
        self._runner = None
        self._player = None
        self.encoder = opus.Encoder()
        self.decoders = {}
        self._ssrc_lookup = {}
        self._voice_receiver = None

        self._pcm_listeners = []
        self._speaking_listeners = []

    warn_nacl = not has_nacl

    @property
    def guild(self):
        """Optional[:class:`Guild`]: The guild we're connected to, if applicable."""
        return getattr(self.channel, 'guild', None)

    @property
    def user(self):
        """:class:`ClientUser`: The user connected to voice (i.e. ourselves)."""
        return self._state.user

    def checked_add(self, attr, value, limit):
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)

    # connection related

    @asyncio.coroutine
    def start_handshake(self):
        log.info('Starting voice handshake...')

        key_id, key_name = self.channel._get_voice_client_key()
        guild_id, channel_id = self.channel._get_voice_state_pair()
        state = self._state
        self.main_ws = ws = state._get_websocket(guild_id)
        self._connections += 1

        # request joining
        yield from ws.voice_state(guild_id, channel_id)

        try:
            yield from asyncio.wait_for(self._handshake_complete.wait(), timeout=self.timeout, loop=self.loop)
        except asyncio.TimeoutError as e:
            yield from self.terminate_handshake(remove=True)
            raise e

        log.info('Voice handshake complete. Endpoint found %s (IP: %s)', self.endpoint, self.endpoint_ip)

    @asyncio.coroutine
    def terminate_handshake(self, *, remove=False):
        guild_id, channel_id = self.channel._get_voice_state_pair()
        self._handshake_complete.clear()
        yield from self.main_ws.voice_state(guild_id, None, self_mute=True)

        log.info('The voice handshake is being terminated for Channel ID %s (Guild ID %s)', channel_id, guild_id)
        if remove:
            log.info('The voice client has been removed for Channel ID %s (Guild ID %s)', channel_id, guild_id)
            key_id, _ = self.channel._get_voice_client_key()
            self._state._remove_voice_client(key_id)

    @asyncio.coroutine
    def _create_socket(self, server_id, data):
        self._connected.clear()
        self.session_id = self.main_ws.session_id
        self.server_id = server_id
        self.token = data.get('token')
        endpoint = data.get('endpoint')

        if endpoint is None or self.token is None:
            log.warning('Awaiting endpoint... This requires waiting. ' \
                        'If timeout occurred considering raising the timeout and reconnecting.')
            return

        self.endpoint = endpoint.replace(':80', '')
        self.endpoint_ip = socket.gethostbyname(self.endpoint)

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        if self._handshake_complete.is_set():
            # terminate the websocket and handle the reconnect loop if necessary.
            self._handshake_complete.clear()
            yield from self.ws.close(1006)
            return

        self._handshake_complete.set()

    @asyncio.coroutine
    def connect(self, *, reconnect=True, _tries=0, do_handshake=True):
        log.info('Connecting to voice...')
        try:
            del self.secret_key
        except AttributeError:
            pass

        if do_handshake:
            yield from self.start_handshake()

        try:
            self.ws = yield from DiscordVoiceWebSocket.from_client(self)
            self._connected.clear()
            while not hasattr(self, 'secret_key'):
                yield from self.ws.poll_event()
            self._connected.set()

            self._voice_receiver = self.loop.create_task(self._voice_receive_loop())
            #receive_thread = threading.Thread(target=self._voice_receive_loop)
            #receive_thread.deamon = True
            #receive_thread.start()
        except (ConnectionClosed, asyncio.TimeoutError):
            if reconnect and _tries < 5:
                log.exception('Failed to connect to voice... Retrying...')
                yield from asyncio.sleep(1 + _tries * 2.0, loop=self.loop)
                yield from self.terminate_handshake()
                yield from self.connect(reconnect=reconnect, _tries=_tries + 1)
            else:
                raise

        if self._runner is None:
            self._runner = self.loop.create_task(self.poll_voice_ws(reconnect))

    @asyncio.coroutine
    def poll_voice_ws(self, reconnect):
        backoff = ExponentialBackoff()
        while True:
            try:
                yield from self.ws.poll_event()
            except (ConnectionClosed, asyncio.TimeoutError) as e:
                if isinstance(e, ConnectionClosed):
                    if e.code == 1000:
                        yield from self.disconnect()
                        break

                if not reconnect:
                    yield from self.disconnect()
                    raise e

                retry = backoff.delay()
                log.exception('Disconnected from voice... Reconnecting in %.2fs.', retry)
                self._connected.clear()
                yield from asyncio.sleep(retry, loop=self.loop)
                yield from self.terminate_handshake()
                try:
                    yield from self.connect(reconnect=True)
                except asyncio.TimeoutError:
                    # at this point we've retried 5 times... let's continue the loop.
                    log.warning('Could not connect to voice... Retrying...')
                    continue

    @asyncio.coroutine
    def disconnect(self, *, force=False):
        """|coro|

        Disconnects all connections to the voice client.
        """
        if not force and not self._connected.is_set():
            return

        self.stop()

        if self._voice_receiver is not None:
            self._voice_receiver.cancel()
            self._voice_receiver = None
        self.decoders.clear()
        self._pcm_listeners = []

        self._connected.clear()

        try:
            if self.ws:
                yield from self.ws.close()

            yield from self.terminate_handshake(remove=True)
        finally:
            if self.socket:
                self.socket.close()

    @asyncio.coroutine
    def move_to(self, channel):
        """|coro|

        Moves you to a different voice channel.

        Parameters
        -----------
        channel: :class:`abc.Snowflake`
            The channel to move to. Must be a voice channel.
        """
        guild_id, _ = self.channel._get_voice_state_pair()
        yield from self.main_ws.voice_state(guild_id, channel.id)

    def is_connected(self):
        """bool: Indicates if the voice client is connected to voice."""
        return self._connected.is_set()

    # audio related

    @asyncio.coroutine
    def get_voice_data(self, user, timeout=0.4):
        """|coro|

        Receive voice data from a user until they are silent for
        `timeout` s.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to listen for audio from.
        timeout: Optional[float]
            The time in ms of silence after which to stop listening.

        Returns
        -----------
        `bytearray`
            The received voice data from the user.

        Note
        -----------
        The returned data is stereo 48kHz audio in raw PCM. You will have to
        add your own headers if you want to save it as a `.wav` file.
        """
        buffer = []
        last_packet = 0
        user_id = user.id

        def listener(vc, vp):
            nonlocal buffer, user_id, last_packet
            if user_id == (None if vp.user is None else vp.user.id):
                last_packet = time.time()
                heapq.heappush(buffer, (vp.timestamp, vp))

        self._pcm_listeners.append(listener)

        while time.time() - last_packet < timeout or last_packet == 0:
            yield from asyncio.sleep(0.1)  # Continue to fill up the buffer.
        self._pcm_listeners.remove(listener)

        buffer.sort()
        data = bytearray()
        current_timestamp = 0
        for key, value in buffer:
            if current_timestamp == 0:
                delta = 0
            else:
                delta = (key - current_timestamp) - 960
                delta = max(delta, 0)  # Just to be safe

            padding = bytearray([0] * delta * 4)
            data += padding
            data += value.pcm

            current_timestamp = key

        return data

    @asyncio.coroutine
    def pipe_voice_into_file(self, user, file_object, buffer_size=0.2):
        """|coro|

        Constantly receive data from a user and pipe it into a file-like
        object. Packets will be reordered and any silence or missed packets
        will be accounted for.

        Parameters
        -----------
        user: :class:`abc.User`
            The user to listen for audio from.
        file_object: File-like
            The file-like object to pipe the voice data into. This object just
            has to have a `.write` method that takes bytes.
        buffer_size: Optional[float]
            The number of seconds to bufffer the audio for before writing to
            the `file_object`. The larger this value, the less likely you are
            to miss a packet, but the longer you have to wait before the data
            is in the `file_object`.

        Note
        -----------
        This function, although a co-routine, is not blocking.

        Note
        -----------
        The returned data is stereo 48kHz audio in raw PCM. You will have to
        add your own headers if you want to save it as a `.wav` file.
        """

        # Convert buffer_size from seconds to packets.
        buffer_size = int(round((buffer_size * 1000) / 20))

        SAMPLE_RATE = 48000
        SAMPLE_SIZE = 2

        last_packet = 0
        user_id = user.id
        voice_buffer = []
        last_speaking = 0

        def listener(vc, vp):
            nonlocal voice_buffer, user_id, last_packet
            if user_id == (None if vp.user is None else vp.user.id):
                last_packet = vp.timestamp
                heapq.heappush(voice_buffer, (vp.timestamp, vp))

                if len(voice_buffer) > buffer_size:
                    packet = heapq.heappop(voice_buffer)[1]

                    if last_packet == 0:
                        delta = 0
                    else:
                        delta = (packet.timestamp - last_packet) - 960

                    if delta > 0:  # Ignore skipped packets
                        data = bytearray([0] * delta * 4)
                        data += packet.pcm

                        file_object.write(data)

                        last_packet = packet.timestamp

        def speaking_listener(user, speaking):
            nonlocal last_speaking, user_id
            if user.id == user_id:
                if speaking:
                    if last_speaking != 0:
                        delta = time.time() - last_speaking
                        padding = bytearray([0] * int(delta * SAMPLE_RATE) * SAMPLE_SIZE)
                        file_object.write(padding)

                        last_speaking = 0
                else:
                    last_speaking = time.time()

        self._pcm_listeners.append(listener)
        self._speaking_listeners.append(speaking_listener)

    @asyncio.coroutine
    def _voice_receive_loop(self):
        """
        Listener loop.
        This loop will receive data from `self.socket` then it will create a
        `VoicePckaet` object that handles the decryption and decoding then
        dispatch two client events so the user can tap into the data.
        """

        try:
            while self.is_connected():
                packet = yield from self.loop.sock_recv(self.socket, 65536)
                log.debug('Received Voice Packet of {} bytes'.format(len(packet)))

                vp = VoicePacket.unpack(packet, self)
                log.debug('Decoded Voice Packet: {}'.format(vp))

                if vp.ssrc not in self.decoders:
                    self.decoders[vp.ssrc] = opus.Decoder()

                # Dispatch event
                self._state.dispatch('receive_opus', self, vp)

                # TODO: re-order packets

                pcm = self.decoders[vp.ssrc].decode(vp.buff)
                log.debug('Opus decoded {} bytes of pcm data'.format(len(pcm)))

                vp.pcm = pcm
                self._state.dispatch('receive_pcm', self, vp)

                # Send PCM data to `get_voice_data`(s):
                for f in self._pcm_listeners:
                    f(self, vp)
        except asyncio.CancelledError:
            pass

    def play(self, source, *, after=None):
        """Plays an :class:`AudioSource`.

        The finalizer, ``after`` is called after the source has been exhausted
        or an error occurred.

        If an error happens while the audio player is running, the exception is
        caught and the audio player is then stopped.

        Parameters
        -----------
        source: :class:`AudioSource`
            The audio source we're reading from.
        after
            The finalizer that is called after the stream is exhausted.
            All exceptions it throws are silently discarded. This function
            must have a single parameter, ``error``, that denotes an
            optional exception that was raised during playing.

        Raises
        -------
        ClientException
            Already playing audio or not connected.
        TypeError
            source is not a :class:`AudioSource` or after is not a callable.
        """

        if not self._connected:
            raise ClientException('Not connected to voice.')

        if self.is_playing():
            raise ClientException('Already playing audio.')

        if not isinstance(source, AudioSource):
            raise TypeError('source must an AudioSource not {0.__class__.__name__}'.format(source))

        self._player = AudioPlayer(source, self, after=after)
        self._player.start()

    def is_playing(self):
        """Indicates if we're currently playing audio."""
        return self._player is not None and self._player.is_playing()

    def is_paused(self):
        """Indicates if we're playing audio, but if we're paused."""
        return self._player is not None and self._player.is_paused()

    def stop(self):
        """Stops playing audio."""
        if self._player:
            self._player.stop()
            self._player = None

    def pause(self):
        """Pauses the audio playing."""
        if self._player:
            self._player.pause()

    def resume(self):
        """Resumes the audio playing."""
        if self._player:
            self._player.resume()

    @property
    def source(self):
        """Optional[:class:`AudioSource`]: The audio source being played, if playing.

        This property can also be used to change the audio source currently being played.
        """
        return self._player.source if self._player else None

    @source.setter
    def source(self, value):
        if not isinstance(value, AudioSource):
            raise TypeError('expected AudioSource not {0.__class__.__name__}.'.format(value))

        if self._player is None:
            raise ValueError('Not playing anything.')

        self._player._set_source(value)

    def send_audio_packet(self, data, *, encode=True):
        """Sends an audio packet composed of the data.

        You must be connected to play audio.

        Parameters
        ----------
        data: bytes
            The *bytes-like object* denoting PCM or Opus voice data.
        encode: bool
            Indicates if ``data`` should be encoded into Opus.

        Raises
        -------
        ClientException
            You are not connected.
        OpusError
            Encoding the data failed.
        """

        self.checked_add('sequence', 1, 65535)
        if encode:
            encoded_data = self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME)
        else:
            encoded_data = data
        packet = self._get_voice_packet(encoded_data)
        try:
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
        except BlockingIOError:
            log.warning('A packet has been dropped (seq: %s, timestamp: %s)', self.sequence, self.timestamp)

        self.checked_add('timestamp', self.encoder.SAMPLES_PER_FRAME, 4294967295)
