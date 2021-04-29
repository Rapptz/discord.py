# -*- coding: utf-8 -*-

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

from .errors import ClientException
import wave
import os
import threading
import time
import subprocess
import sys
import struct


if sys.platform != 'win32':
    CREATE_NO_WINDOW = 0
else:
    CREATE_NO_WINDOW = 0x08000000

default_filters = {
    'time': 0,
    'users': [],
    'max_size': 0,
}


class Filters:
    # TODO: Filter for max size per file; audio can be split into multiple files
    def __init__(self, **kwargs):
        self.filtered_users = kwargs.get('users', default_filters['users'])
        self.seconds = kwargs.get('time', default_filters['time'])
        self.max_size = kwargs.get('max_size', default_filters['max_size'])
        self.finished = False

    @staticmethod
    def filter_decorator(func):  # Contains all filters
        def _filter(self, data, user):
            if not self.filtered_users or user in self.filtered_users:
                return func(self, data, user)
        return _filter

    def init(self):
        if self.seconds != 0:
            thread = threading.Thread(target=self.wait_and_stop)
            thread.start()

    def wait_and_stop(self):
        time.sleep(self.seconds)
        if self.finished:
            return
        self.vc.stop_recording()


class RawData:
    """
    Handles raw data from Discord so that it can be
    decrypted and decoded to be used.
    """
    def __init__(self, data, client):
        self.data = bytearray(data)
        self.client = client

        self.header = data[:12]
        self.data = self.data[12:]

        unpacker = struct.Struct('>xxHII')
        self.sequence, self.timestamp, self.ssrc = unpacker.unpack_from(self.header)
        self.decrypted_data = getattr(self.client, '_decrypt_' + self.client.mode)(self.header, self.data)
        self.decoded_data = None

        self.user_id = None


class AudioData:
    """
    Handles data that's been completely decrypted and decoded
    and is ready to be saved to file.
    """
    def __init__(self, file):
        self.file = open(file, 'ab')
        self.dir_path = os.path.split(file)[0]

        self.finished = False

    def write(self, data):
        if self.finished:
            raise ClientException("This AudioData is already finished writing.")
        self.file.write(data)

    def cleanup(self):
        if self.finished:
            raise ClientException("This AudioData is already finished writing.")
        self.file.close()
        self.file = os.path.join(self.dir_path, self.file.name)
        self.finished = True

    def on_format(self, encoding):
        if not self.finished:
            raise ClientException("This AudioData is still writing.")
        name = os.path.split(self.file)[1]
        name = name.split('.')[0] + f'.{encoding}'
        self.file = os.path.join(self.dir_path, name)


class Sink(Filters):
    valid_encodings = ['wav', 'mp3', 'pcm']

    def __init__(self, *, encoding='wave', output_path='', filters=None):
        """A Sink "stores" all the audio data.

        Parameters
        ----------
        encoding: :class:`string`
            Valid types include wave
        output_path: :class:`string`
            A path to where the audio files should be output

        Raises
        ------
        ClientException
            That's not a valid encoding type.
        """
        if filters is None:
            filters = default_filters
        self.filters = filters
        Filters.__init__(self, **self.filters)

        encoding = encoding.lower()

        # Would also like to add opus but don't
        # know how I would go about it.
        if encoding not in self.valid_encodings:
            raise ClientException("That's not a valid encoding type.")

        self.encoding = encoding
        self.file_path = output_path
        self.vc = None
        self.audio_data = {}

    def init(self, vc):  # called under start_recording
        self.vc = vc
        super().init()

    @Filters.filter_decorator
    def write(self, data, user):
        if user not in self.audio_data:
            ssrc = self.vc.get_ssrc(user)
            file = os.path.join(self.file_path, f'{ssrc}.pcm')
            self.audio_data.update({user: AudioData(file)})

        file = self.audio_data[user]
        file.write(data)

    def cleanup(self):
        self.finished = True
        for file in self.audio_data.values():
            file.cleanup()
            self.format_audio(file)

    def format_audio(self, audio):
        if self.vc.recording:
            raise ClientException("Audio may only be formatted after recording is finished.")
        if self.encoding == 'pcm':
            return
        if self.encoding == 'mp3':
            mp3_file = audio.file.split('.')[0] + '.mp3'
            args = ['ffmpeg', '-f', 's16le', '-ar', '48000', '-ac', '2', '-i', audio.file, mp3_file]
            process = None
            if os.path.exists(mp3_file):
                os.remove(mp3_file)  # process will get stuck asking whether or not to overwrite, if file already exists.
            try:
                process = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
            except FileNotFoundError:
                raise ClientException('ffmpeg was not found.') from None
            except subprocess.SubprocessError as exc:
                raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc
            process.wait()
        elif self.encoding == 'wav':
            with open(audio.file, 'rb') as pcm:
                data = pcm.read()
                pcm.close()

            wav_file = audio.file.split('.')[0] + '.wav'
            with wave.open(wav_file, 'wb') as f:
                f.setnchannels(self.vc.decoder.CHANNELS)
                f.setsampwidth(self.vc.decoder.SAMPLE_SIZE // self.vc.decoder.CHANNELS)
                f.setframerate(self.vc.decoder.SAMPLING_RATE)
                f.writeframes(data)
                f.close()

        os.remove(audio.file)
        audio.on_format(self.encoding)
