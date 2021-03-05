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
from . import opus
import wave
import os


class Sink:
    def __init__(self, *, encoding='wave', output_path=''):
        encoding = encoding.lower()

        # Would also like to add opus, but failed in
        # attempts to save the audio data to an opus
        # file without decoding it.
        valid_encodings = ['wave']
        if encoding not in valid_encodings:
            raise ClientException("That's not a valid encoding type.")

        self.encoding = encoding
        self.file_path = output_path
        self.vc = None
        self.ssrc_cache = []

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
        encoding_to_ext = {
            'wave': 'wav'
        }
        ssrc = self.vc.get_ssrc(user)
        file = os.path.join(self.file_path, f'{ssrc}.{encoding_to_ext[self.encoding]}')
        return file

    def format_audio(self):
        if self.vc.recording:
            raise ClientException("Audio may only be formatted after recording is finished.")
        for file in self.recorded_users.values():
            pcm_file = file.split('.')[0] + '.pcm'
            with open(pcm_file, 'rb') as pcm:
                data = pcm.read()
                pcm.close()
            if self.encoding == 'wave':
                with wave.open(file, 'wb') as f:
                    f.setnchannels(self.vc.decoder.CHANNELS)
                    f.setsampwidth(self.vc.decoder.SAMPLE_SIZE)
                    f.setframerate(self.vc.decoder.SAMPLING_RATE / self.vc.decoder.CHANNELS)
                    f.writeframes(data)
                    f.close()
            os.remove(pcm_file)

    @property
    def recorded_users(self):
        encoding_to_ext = {
            'wave': 'wav'
        }
        return {
            self.vc.ws.ssrc_map[ssrc]['user_id']: os.path.join(self.file_path, f'{ssrc}.{encoding_to_ext[self.encoding]}')
            for ssrc in self.ssrc_cache
        }
