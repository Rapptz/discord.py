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
    def __init__(self, **kwargs):
        self.filtered_users = kwargs.get('users', default_filters['users'])
        self.seconds = kwargs.get('time', default_filters['time'])
        self.max_size = kwargs.get('max_size', default_filters['max_size'])

        if self.seconds != 0:
            thread = threading.Thread(target=self.wait_and_stop)
            thread.start()

    @staticmethod
    def filter_decorator(func):  # Contains all filters
        def _filter(self, data, user):
            if not self.filtered_users or user in self.filtered_users:
                return func(self, data, user)
        return _filter

    def wait_and_stop(self):
        time.sleep(self.seconds)
        self.vc.stop_recording()


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

        encoding = encoding.lower()

        # Would also like to add opus, but don't
        # know how I would go about it.
        if encoding not in self.valid_encodings:
            raise ClientException("That's not a valid encoding type.")

        self.encoding = encoding
        self.file_path = output_path
        self.vc = None
        self.ssrc_cache = []

    def init(self):  # called under start_recording
        Filters.__init__(self, **self.filters)

    @Filters.filter_decorator
    def write(self, data, user):
        ssrc = self.vc.get_ssrc(user)
        file = os.path.join(self.file_path, f'{ssrc}.pcm')
        if ssrc not in self.ssrc_cache:
            self.ssrc_cache.append(ssrc)
            open_type = 'wb'
        else:
            open_type = 'ab'

        with open(file, open_type) as f:
            f.write(data)
            f.close()

    def get_user_audio(self, user):
        ssrc = self.vc.get_ssrc(user)
        file = os.path.join(self.file_path, f'{ssrc}.{self.encoding}')
        return file

    def format_audio(self):
        if self.vc.recording:
            raise ClientException("Audio may only be formatted after recording is finished.")
        if self.encoding == 'pcm':
            return
        for file in self.recorded_users.values():
            pcm_file = file.split('.')[0] + '.pcm'
            with open(pcm_file, 'rb') as pcm:
                data = pcm.read()
                pcm.close()
            if self.encoding == 'wav':
                with wave.open(file, 'wb') as f:
                    f.setnchannels(self.vc.decoder.CHANNELS)
                    f.setsampwidth(self.vc.decoder.SAMPLE_SIZE)
                    f.setframerate(self.vc.decoder.SAMPLING_RATE / self.vc.decoder.CHANNELS)
                    f.writeframes(data)
                    f.close()
            elif self.encoding == 'mp3':
                args = ['ffmpeg', '-f', 's16le', '-ar', '48000', '-ac', '2', '-i', pcm_file, file]
                process = None
                if os.path.exists(file):
                    os.remove(file)  # process will get stuck asking whether or not to overwrite, if file already exists.
                try:
                    process = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
                except FileNotFoundError:
                    raise ClientException('ffmpeg was not found.') from None
                except subprocess.SubprocessError as exc:
                    raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc
                process.wait()

            os.remove(pcm_file)

    @property
    def recorded_users(self):
        return {
            self.vc.ws.ssrc_map[ssrc]['user_id']: os.path.join(self.file_path, f'{ssrc}.{self.encoding}')
            for ssrc in self.ssrc_cache
        }
