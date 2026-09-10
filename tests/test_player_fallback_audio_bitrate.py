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

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from discord import player


def test_fallback_probe_reads_audio_stream_bitrate(monkeypatch):
    class Process:
        def communicate(self, timeout):
            output = '\n'.join(
                [
                    'Input #0, matroska,webm, from source:',
                    '  Duration: 00:00:01.00, start: 0.000000, bitrate: 2000 kb/s',
                    '    Stream #0:0: Video: h264, 1920x1080, 1800 kb/s',
                    '    Stream #0:1: Audio: opus, 48000 Hz, stereo, fltp, 128 kb/s',
                ]
            )
            return output.encode(), None

    monkeypatch.setattr(player.subprocess, 'Popen', lambda *args, **kwargs: Process())

    assert player.FFmpegOpusAudio._probe_codec_fallback('source') == ('opus', 128)
