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

from ws4py.client import WebSocketBaseClient
import socket
import json, time
import logging
import struct
import threading
import subprocess
import shlex
import pipes
import time

import sys
import traceback

log = logging.getLogger(__name__)

from . import utils
from .errors import ClientException, InvalidArgument
from .opus import Encoder as OpusEncoder

class VoiceWebSocket(WebSocketBaseClient):
    def __init__(self, url, endpoint_ip):
        WebSocketBaseClient.__init__(self, url)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.endpoint_ip = endpoint_ip
        self._connected = False
        self.keep_alive = None
    
    def keep_alive_join(self):
        self.keep_alive.join()

    def opened(self):
        pass

    def closed(self, code, reason=None):
        self._connected = False
        if self.keep_alive is not None:
            self.keep_alive.join()

    def handshake_ok(self):
        pass

    def send(self, payload):
        WebSocketBaseClient.send(self, payload)

    def received_message(self, msg):
        msg = json.loads(msg.data)
        log.debug('Voice websocket frame received: {}'.format(msg))
        op = msg.get('op')
        data = msg.get('d')
        
        def keep_alive_handler(self,delay):
            try:
                while self._connected==True:
                    payload = {
                        'op': 3,
                        'd': int(time.time())
                    }

                    msg = 'Keeping voice websocket alive with timestamp {}'
                    log.debug(msg.format(payload['d']))
                    self.send(utils.to_json(payload))
                    time.sleep(delay)
                exit()
            except Exception as e:
                pass
        
        def initial_connection(self,data):
            self.ssrc = data.get('ssrc')
            self.voice_port = data.get('port')
            packet = bytearray(70)
            struct.pack_into('>I', packet, 0, self.ssrc)
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
            recv = None
            while recv == None:
                try:
                    recv = self.socket.recv(70)
                except:
                    pass
            log.debug('received packet in initial_connection: {}'.format(recv))

            # the ip is ascii starting at the 4th byte and ending at the first null
            ip_start = 4
            ip_end = recv.index("\x00",ip_start)
            self.ip = recv[ip_start:ip_end].decode('ascii')

            # the port is a little endian unsigned short in the last two bytes
            # yes, this is different endianness from everything else
            self.port = struct.unpack_from('<H', recv, len(recv) - 2)[0]

            log.debug('detected ip: {} port: {}'.format(self.ip, self.port))
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

            self.send(utils.to_json(payload))
            log.debug('sent {} to initialize voice connection'.format(payload))
            log.info('initial voice connection is done')
        
        def connection_ready(self, data):
            log.info('voice connection is now ready')
            speaking = {
                'op': 5,
                'd': {
                    'speaking': True,
                    'delay': 0
                }
            }

            self.send(utils.to_json(speaking))
            self._connected = True
        
        
        if op == 2:
            delay = (data['heartbeat_interval'] / 100.0) - 5
            self.keep_alive = threading.Thread(None,keep_alive_handler,None,(self,delay,))
            self.keep_alive.start()
            initial_connection(self,data)
        elif op == 4:
            connection_ready(self,data)

        
        
        #return(msg)

class StreamPlayer(threading.Thread):
    def __init__(self, stream, encoder, connected, player, after, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.buff = stream
        self.frame_size = encoder.frame_size
        self.player = player
        self._end = False
        self._paused = False
        self._connected = connected
        self.after = after
        self.delay = encoder.frame_length / 1000.0

    def run(self):
        self.loops = 0
        self._start = time.time()
        while not self._end==True:
            if self._paused==True:
                continue

            while not self._connected==True:
                time.sleep(.01)

            self.loops += 1
            data = self.buff.read(self.frame_size)
            if len(data) != self.frame_size:
                self.stop()
                break

            self.player(data)
            next_time = self._start + self.delay * self.loops
            delay = max(0, self.delay + (next_time - time.time()))
            time.sleep(delay)

    def stop(self):
        self._end = True
        if callable(self.after):
            try:
                self.after()
            except:
                pass

    def pause(self):
        self._paused = True

    def resume(self):
        self.loops = 0
        self._start = time.time()
        self._paused=False

    def is_playing(self):
        return not self._paused==True and not self.is_done()

    def is_done(self):
        return not self._connected==True or self._end==True

class ProcessPlayer(StreamPlayer):
    def __init__(self, process, client, after, **kwargs):
        super(ProcessPlayer, self).__init__(process.stdout, client.encoder,
                         client.ws._connected, client.play_audio, after, **kwargs)
        self.process = process

    def stop(self):
        self.process.terminate()
        super(ProcessPlayer, self).stop()

class VoiceClient:
    """Represents a Discord voice connection.

    This client is created solely through :meth:`Client.join_voice_channel`
    and its only purpose is to transmit voice.

    Warning
    --------
    In order to play audio, you must have loaded the opus library
    through :func:`opus.load_opus`.

    If you don't do this then the library will not be able to
    transmit audio.

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
    loop
        The event loop that the voice client is running on.
    """
    def __init__(self, user, main_ws, session_id, channel, data):
        self.user = user
        self.main_ws = main_ws
        self.vws_thread = None
        self.disconnect_called = False
        self.current_player = None
        self.channel = channel
        self.session_id = session_id
        self._connected = None
        self.token = data.get('token')
        self.guild_id = data.get('guild_id')
        self.endpoint = data.get('endpoint')
        self.sequence = 0
        self.timestamp = 0
        self.encoder = OpusEncoder(48000, 2)
        log.info('created opus encoder with {0.__dict__}'.format(self.encoder))

    def run_ws(self):
        while not self.disconnect_called==True:
            #if self.ws._connected == True:
            try:
                self.ws.run()
            except Exception as e:
                exit()
            time.sleep(.01)
        exit()

    def checked_add(self, attr, value, limit):
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)


    # connection related

    def connect(self):
        log.info('voice connection is connecting...')
        self.endpoint = self.endpoint.replace(':80', '')
        self.endpoint_ip = socket.gethostbyname(self.endpoint)
        

        log.info('Voice endpoint found {0.endpoint} (IP: {0.endpoint_ip})'.format(self))
        self.ws = VoiceWebSocket('wss://' + self.endpoint, self.endpoint_ip)
        self.ws.max_size = None
        self.ws.connect()
        self._connected = self.ws._connected
        self.vws_thread = threading.Thread(None,self.run_ws,None,())
        self.vws_thread.start()

        payload = {
            'op': 0,
            'd': {
                'server_id': self.guild_id,
                'user_id': self.user.id,
                'session_id': self.session_id,
                'token': self.token
            }
        }

        self.ws.send(utils.to_json(payload))

        # while not self.ws._connected == True:
            # msg = self.ws.received_message()
            # if msg is None:
                # self.disconnect()
                # raise ClientException('Unexpected websocket close on voice websocket')
            # self.ws.received_message(json.loads(msg))

    def disconnect(self):
        """

        Disconnects all connections to the voice client.

        In order to reconnect, you must create another voice client
        using :meth:`Client.join_voice_channel`.
        """
        self._connected = self.ws._connected
        if not self.ws._connected:
            return
        
        payload = {
            'op': 4,
            'd': {
                'guild_id': None,
                'channel_id': None,
                'self_mute': True,
                'self_deaf': False
            }
        }
        self.main_ws.send(utils.to_json(payload))
        self.disconnect_called = True
        time.sleep(0.2)
        def manager_thread(self):
            if not self.current_player == None:
                self.current_player.stop()
            self.ws.keep_alive_join()
            self.ws.close()
            self.vws_thread.join()
        threading.Thread(None,manager_thread,None,(self,)).start()

        self.ws.socket.close()
        self.ws._connected = False

    def is_connected(self):
        """bool : Indicates if the voice client is connected to voice."""
        return self.ws._connected

    # audio related

    def _get_voice_packet(self, data):
        buff = bytearray(len(data) + 12)
        buff[0] = chr(0x80)
        buff[1] = chr(0x78)

        for i in range(0, len(data)):
            buff[i + 12] = data[i]

        struct.pack_into('>H', buff, 2, self.sequence)
        struct.pack_into('>I', buff, 4, self.timestamp)
        struct.pack_into('>I', buff, 8, self.ws.ssrc)
        return buff

    def create_ffmpeg_player(self, filename, use_avconv=False, pipe=False, options=None, after=None):
        """Creates a stream player for ffmpeg that launches in a separate thread to play
        audio.

        The ffmpeg player launches a subprocess of ``ffmpeg`` to a specific
        filename and then plays that file.

        You must have the ffmpeg or avconv executable in your path environment variable
        in order for this to work.

        The operations that can be done on the player are the same as those in
        :meth:`create_stream_player`.

        Examples
        ----------

        Basic usage: ::

            voice = yield from client.join_voice_channel(channel)
            player = voice.create_ffmpeg_player('cool.mp3')
            player.start()

        Parameters
        -----------
        filename
            The filename that ffmpeg will take and convert to PCM bytes.
            If ``pipe`` is True then this is a file-like object that is
            passed to the stdin of ``ffmpeg``.
        use_avconv: bool
            Use ``avconv`` instead of ``ffmpeg``.
        pipe : bool
            If true, denotes that ``filename`` parameter will be passed
            to the stdin of ffmpeg.
        options: str
            Extra command line flags to pass to ``ffmpeg``.
        after : callable
            The finalizer that is called after the stream is done being
            played. All exceptions the finalizer throws are silently discarded.

        Raises
        -------
        ClientException
            Popen failed to due to an error in ``ffmpeg`` or ``avconv``.

        Returns
        --------
        StreamPlayer
            A stream player with specific operations.
            See :meth:`create_stream_player`.
        """
        command = 'ffmpeg' if not use_avconv else 'avconv'
        input_name = '-' if pipe else pipes.quote(filename)
        cmd = command + ' -i {} -f s16le -ar {} -ac {} -loglevel quiet'
        cmd = cmd.format(input_name, self.encoder.sampling_rate, self.encoder.channels)

        if isinstance(options, str):
            cmd = cmd + ' ' + options

        cmd += ' pipe:1'

        stdin = None if not pipe else filename
        args = shlex.split(cmd)
        try:
            p = subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE, stderr=None)
            self.current_player = ProcessPlayer(p, self, after)
            return(self.current_player)
        except Exception as e:
            raise e


    def create_ytdl_player(self, url, options=None, use_avconv=False, after=None):
        """Creates a stream player for youtube or other services that launches
        in a separate thread to play the audio.

        The player uses the ``youtube_dl`` python library to get the information
        required to get audio from the URL. Since this uses an external library,
        you must install it yourself. You can do so by calling
        ``pip install youtube_dl``.

        You must have the ffmpeg or avconv executable in your path environment
        variable in order for this to work.

        The operations that can be done on the player are the same as those in
        :meth:`create_stream_player`.

        .. _ytdl: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L117-L265

        Examples
        ----------

        Basic usage: ::

            voice = yield from client.join_voice_channel(channel)
            player = voice.create_ytdl_player('https://www.youtube.com/watch?v=d62TYemN6MQ')
            player.start()

        Parameters
        -----------
        url : str
            The URL that ``youtube_dl`` will take and download audio to pass
            to ``ffmpeg`` or ``avconv`` to convert to PCM bytes.
        options : dict
            A dictionary of options to pass into the ``YoutubeDL`` instance.
            See `the documentation <ydl>`_ for more details.
        use_avconv: bool
            Use ``avconv`` instead of ``ffmpeg``. Passes the appropriate
            flags to ``youtube-dl`` as well.
        after : callable
            The finalizer that is called after the stream is done being
            played. All exceptions the finalizer throws are silently discarded.

        Raises
        -------
        ClientException
            Popen failure from either ``ffmpeg``/``avconv``.

        Returns
        --------
        StreamPlayer
            A stream player with specific operations.
            See :meth:`create_stream_player`.
        """
        import youtube_dl

        opts = {
            'format': 'webm[abr>0]' if 'youtube' in url else 'best',
            'prefer_ffmpeg': not use_avconv
        }

        if options is not None and isinstance(options, dict):
            opts.update(options)

        ydl = youtube_dl.YoutubeDL(opts)
        info = ydl.extract_info(url, download=False)
        log.info('playing URL {}'.format(url))
        return self.create_ffmpeg_player(info['url'], use_avconv=use_avconv, after=after)

    def encoder_options(self, sample_rate, channels=2):
        """Sets the encoder options for the OpusEncoder.

        Calling this after you create a stream player
        via :meth:`create_ffmpeg_player` or :meth:`create_stream_player`
        has no effect.

        Parameters
        ----------
        sample_rate : int
            Sets the sample rate of the OpusEncoder.
        channels : int
            Sets the number of channels for the OpusEncoder.
            2 for stereo, 1 for mono.

        Raises
        -------
        InvalidArgument
            The values provided are invalid.
        """
        if sample_rate not in (8000, 12000, 16000, 24000, 48000):
            raise InvalidArgument('Sample rate out of range. Valid: [8000, 12000, 16000, 24000, 48000]')
        if channels not in (1, 2):
            raise InvalidArgument('Channels must be either 1 or 2.')

        self.encoder = OpusEncoder(sample_rate, channels)
        log.info('created opus encoder with {0.__dict__}'.format(self.encoder))

    def create_stream_player(self, stream, after=None):
        """Creates a stream player that launches in a separate thread to
        play audio.

        The stream player assumes that ``stream.read`` is a valid function
        that returns a *bytes-like* object.

        The finalizer, ``after`` is called after the stream has been exhausted.

        The following operations are valid on the ``StreamPlayer`` object:

        +---------------------+-----------------------------------------------------+
        |      Operation      |                     Description                     |
        +=====================+=====================================================+
        | player.start()      | Starts the audio stream.                            |
        +---------------------+-----------------------------------------------------+
        | player.stop()       | Stops the audio stream.                             |
        +---------------------+-----------------------------------------------------+
        | player.is_done()    | Returns a bool indicating if the stream is done.    |
        +---------------------+-----------------------------------------------------+
        | player.is_playing() | Returns a bool indicating if the stream is playing. |
        +---------------------+-----------------------------------------------------+
        | player.pause()      | Pauses the audio stream.                            |
        +---------------------+-----------------------------------------------------+
        | player.resume()     | Resumes the audio stream.                           |
        +---------------------+-----------------------------------------------------+

        The stream must have the same sampling rate as the encoder and the same
        number of channels. The defaults are 48000 Mhz and 2 channels. You
        could change the encoder options by using :meth:`encoder_options`
        but this must be called **before** this function.

        Parameters
        -----------
        stream
            The stream object to read from.
        after:
            The finalizer that is called after the stream is exhausted.
            All exceptions it throws are silently discarded. It is called
            without parameters.

        Returns
        --------
        StreamPlayer
            A stream player with the operations noted above.
        """
        return StreamPlayer(stream, self.encoder, self.ws, self.play_audio, after)

    def play_audio(self, data):
        """Sends an audio packet composed of the data.

        You must be connected to play audio.

        Parameters
        ----------
        data
            The *bytes-like object* denoting PCM voice data.

        Raises
        -------
        ClientException
            You are not connected.
        OpusError
            Encoding the data failed.
        """

        self.checked_add('sequence', 1, 65535)
        encoded_data = self.encoder.encode(data, self.encoder.samples_per_frame)
        packet = self._get_voice_packet(encoded_data)
        sent = self.ws.socket.sendto(packet, (self.endpoint_ip, self.ws.voice_port))
        self.checked_add('timestamp', self.encoder.samples_per_frame, 4294967295)

