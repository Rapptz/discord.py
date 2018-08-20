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

from collections import defaultdict

log = logging.getLogger(__name__)

try:
    import nacl.secret
    has_nacl = True
except ImportError:
    has_nacl = False

from . import opus
from .backoff import ExponentialBackoff
from .gateway import *
from .errors import ClientException, ConnectionClosed, InvalidVoicePacket
from .player import AudioPlayer, AudioSource

class VoicePacket:
    __slots__ = ('sequence', 'timestamp', 'ssrc', 'buff', 'user', 'pcm')

    HEADER_FORMAT = struct.Struct('>HHII')
    RTP_VERSION = 2
    RTC_MAGIC = 36984

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
        rtp_header, seq, ts, ssrc = cls.HEADER_FORMAT.unpack_from(packet)
        header = packet[:12]
        buff = packet[12:]

        # Extract info for the header
        version = rtp_header >> 14
        marker = rtp_header & 2 ** 7 != 0
        p_type = rtp_header & 0b1111111

        if version != cls.RTP_VERSION:
            fmt = 'packet has unsupported rtp version: {}'
            raise InvalidVoicePacket(fmt.format(packet))
        if marker:
            return
        if p_type != 120:
            fmt = 'packet is of unsupported type: {}'
            raise InvalidVoicePacket(fmt.format(packet))

        # Decrypt data
        nonce = bytearray(24)
        nonce[:12] = header

        try:
            box = nacl.secret.SecretBox(bytes(voice_client.secret_key))
            buff = box.decrypt(bytes(buff), bytes(nonce))
        except Exception as e:
            log.debug('VoicePacket.unpack failed with %s', e)
            return None

        if buff[0] == 0xBE and buff[1] == 0xDE:
            # RFC5285 Section 4.2: One-Byte Header
            rtp_header_extension_length = buff[2] << 8 | buff[3]
            index = 4
            for i in range(rtp_header_extension_length):
                byte = buff[index]
                index += 1
                if byte == 0:
                    continue
                l = (byte & 0b1111) + 1
                index += l

            while buff[index] == 0:
                index += 1
            buff = buff[index:]
        elif rtp_header == cls.RTC_MAGIC:
            # Drop the header bytes
            buff = buff[8:]

        # Lookup the SSRC and then get the user
        user = None
        #user_id = 0
        #if voice_client.channel.id in voice_client._ssrc_lookup:
        #    if ssrc in voice_client._ssrc_lookup[voice_client.guild.id]:
        #        user_id = int(voice_client._ssrc_lookup[voice_client.guild.id][ssrc])
        #user = voice_client._state.get_user(user_id)

        # Create a `VoicePacket` instance and return it.
        return cls(seq, ts, ssrc, buff, user)

    def __str__(self):
        fmt = '<VoicePacket sequence={0.sequence}, timestamp={0.timestamp}, ssrc={0.ssrc}, buff=bytes({1})>'
        return fmt.format(self, len(self.buff))

    def __repr__(self):
        return str(self)

class PacketDecoder:
    PACKET_SIZE = 960
    SAMPLE_RATE = 48000
    SAMPLE_SIZE = 2

    def __init__(self, voice_client, buffer_size=2000):
        #self.current_packets = []
        #self.next_packets = []
        #self.start_timestamp = None
        #self.end_timestamp = None
        #self.swap_timestamp = None
        self.last_packet = 0
        self.voice_buffer = []

        # Convert buffer_size from ms to packets.
        self.buffer_size = int(round(buffer_size / 20))
        self.decoder = opus.Decoder()

        # User object
        self.user = None

        # Speaking tracking
        self.stopped_speaking = -1
        self.started_speaking = -1
        self.has_had_pause = False

        # Link to the voice client
        self.voice_client = voice_client
        self.dispatch = self.voice_client._state.dispatch

    def speaking_state(self, speaking):
        self.dispatch('voice_speaking_state',
                      self.voice_client, self.user, speaking)

        if speaking:
            self.started_speaking = time.perf_counter()
            if self.stopped_speaking:
                self.has_had_pause = True
        else:
            while self.voice_buffer:
                # Clear buffer
                self.dispatch_buffered()
            self.stopped_speaking = time.perf_counter()

    def feed(self, rtp_packet):
        try:
            rtp_packet.pcm = self.decoder.decode(rtp_packet.buff)
        except Exception as e:
            return e, None
        log.debug('Opus decoded %d bytes of pcm data', len(rtp_packet.pcm))
        rtp_packet.user = self.user
        return None, self.buffer_packet(rtp_packet)

    def dispatch_buffered(self):
        timestamp, packet = heapq.heappop(self.voice_buffer)

        delta = 0
        if self.last_packet != 0:
            delta = (timestamp - self.last_packet) - self.PACKET_SIZE

        if delta >= 0:
            # Pad dropped packets
            data = b'\x00\x00' * delta * self.SAMPLE_SIZE
            data += packet

            # Pad silence
            if self.has_had_pause:
                if self.voice_client.pad_silence:
                    delta = self.started_speaking - self.stopped_speaking
                    data += b'\x00\x00' * round((delta / 2) * self.SAMPLE_SIZE)
                self.has_had_pause = False

            self.last_packet = timestamp

            self.dispatch('voice_receive', self.voice_client, self.user, data)

    def buffer_packet(self, rtp_packet):
        heapq.heappush(self.voice_buffer,
                       (rtp_packet.timestamp, rtp_packet.pcm))

        if len(self.voice_buffer) > self.buffer_size:
            self.dispatch_buffered()

class VoiceClient:
    """Represents a Discord voice connection.

    You do not create these, you typically get them from
    e.g. :meth:`VoiceChannel.connect`.

    Warning
    --------
    In order to play or receive audio, you must have loaded
    the opus library through :func:`opus.load_opus`.

    If you don't do this then the library will not be able to
    transmit audio.

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
    loop
        The event loop that the voice client is running on.
    """
    def __init__(self, state, timeout, pad_silence, channel):
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
        self._voice_receiver = None
        self.encoder = opus.Encoder()
        self.decoders = defaultdict(lambda:PacketDecoder(self))
        self.pad_silence = pad_silence

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

    async def start_handshake(self):
        log.info('Starting voice handshake...')

        key_id, key_name = self.channel._get_voice_client_key()
        guild_id, channel_id = self.channel._get_voice_state_pair()
        state = self._state
        self.main_ws = ws = state._get_websocket(guild_id)
        self._connections += 1

        # request joining
        await ws.voice_state(guild_id, channel_id)

        try:
            await asyncio.wait_for(self._handshake_complete.wait(), timeout=self.timeout, loop=self.loop)
        except asyncio.TimeoutError as e:
            await self.terminate_handshake(remove=True)
            raise e

        log.info('Voice handshake complete. Endpoint found %s (IP: %s)', self.endpoint, self.endpoint_ip)

    async def terminate_handshake(self, *, remove=False):
        guild_id, channel_id = self.channel._get_voice_state_pair()
        self._handshake_complete.clear()
        await self.main_ws.voice_state(guild_id, None, self_mute=True)

        log.info('The voice handshake is being terminated for Channel ID %s (Guild ID %s)', channel_id, guild_id)
        if remove:
            log.info('The voice client has been removed for Channel ID %s (Guild ID %s)', channel_id, guild_id)
            key_id, _ = self.channel._get_voice_client_key()
            self._state._remove_voice_client(key_id)

    async def _create_socket(self, server_id, data):
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
            await self.ws.close(4000)
            return

        self._handshake_complete.set()

    async def connect(self, *, reconnect=True, _tries=0, do_handshake=True):
        log.info('Connecting to voice...')
        try:
            del self.secret_key
        except AttributeError:
            pass

        if do_handshake:
            await self.start_handshake()

        try:
            self.ws = await DiscordVoiceWebSocket.from_client(self)
            self._connected.clear()
            while not hasattr(self, 'secret_key'):
                await self.ws.poll_event()
            self._connected.set()

            self._voice_receiver = self.loop.create_task(self._voice_receive_loop())
        except (ConnectionClosed, asyncio.TimeoutError):
            if reconnect and _tries < 5:
                log.exception('Failed to connect to voice... Retrying...')
                await asyncio.sleep(1 + _tries * 2.0, loop=self.loop)
                await self.terminate_handshake()
                await self.connect(reconnect=reconnect, _tries=_tries + 1)
            else:
                raise

        if self._runner is None:
            self._runner = self.loop.create_task(self.poll_voice_ws(reconnect))

    async def poll_voice_ws(self, reconnect):
        backoff = ExponentialBackoff()
        while True:
            try:
                await self.ws.poll_event()
            except (ConnectionClosed, asyncio.TimeoutError) as e:
                if isinstance(e, ConnectionClosed):
                    if e.code == 1000:
                        await self.disconnect()
                        break

                if not reconnect:
                    await self.disconnect()
                    raise e

                retry = backoff.delay()
                log.exception('Disconnected from voice... Reconnecting in %.2fs.', retry)
                self._connected.clear()
                await asyncio.sleep(retry, loop=self.loop)
                await self.terminate_handshake()
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
        if not force and not self._connected.is_set():
            return

        self.stop()
        self._connected.clear()

        try:
            if self.ws:
                await self.ws.close()

            await self.terminate_handshake(remove=True)
        finally:
            if self.socket:
                self.socket.close()

    async def move_to(self, channel):
        """|coro|

        Moves you to a different voice channel.

        Parameters
        -----------
        channel: :class:`abc.Snowflake`
            The channel to move to. Must be a voice channel.
        """
        guild_id, _ = self.channel._get_voice_state_pair()
        await self.main_ws.voice_state(guild_id, channel.id)

    def is_connected(self):
        """:class:`bool`: Indicates if the voice client is connected to voice."""
        return self._connected.is_set()

    # audio related

    def _get_voice_packet(self, data):
        header = bytearray(12)
        nonce = bytearray(24)
        box = nacl.secret.SecretBox(bytes(self.secret_key))

        # Formulate header
        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into('>H', header, 2, self.sequence)
        struct.pack_into('>I', header, 4, self.timestamp)
        struct.pack_into('>I', header, 8, self.ssrc)

        # Copy header to nonce's first 12 bytes
        nonce[:12] = header

        # Encrypt and return the data
        return header + box.encrypt(bytes(data), bytes(nonce)).ciphertext

    @asyncio.coroutine
    def _voice_receive_loop(self):
        """
        Socket listener loop.
        This loop will poll `self.socket`, attempt to decode the packets it
        receives and then feeds them to a decoder in `self.decoders` which
        handles re-ordering the packets and dispatching ordered events.
        """
        try:
            while self.is_connected():
                packet = yield from self.loop.sock_recv(self.socket, 65536)
                log.debug('Received Voice Packet of %d bytes', len(packet))

                try:
                    rtp_packet = VoicePacket.unpack(packet, self)
                except InvalidVoicePacket as e:
                    log.warning(e)
                    continue

                if rtp_packet is None:
                    log.debug('Voice packet failed to decode.')
                    continue
                log.debug('Decoded Voice Packet: %s', rtp_packet)

                # Decode packet and assign `user` attribute
                decoder = self.decoders[rtp_packet.ssrc]
                error, new_packet = decoder.feed(rtp_packet)

                # Fire events
                self._state.dispatch('raw_voice_receive', self, rtp_packet)
                if error is not None:
                    log.debug('Opus decode failed with %s', error)
                else:
                    self._state.dispatch('pcm_data_receive', self, rtp_packet)
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
