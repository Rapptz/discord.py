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


def test_native_probe_preserves_valid_bitrate_and_caps_large_values(monkeypatch):
    outputs = iter(
        [
            b'{"streams": [{"codec_name": "opus", "bit_rate": "128000"}]}',
            b'{"streams": [{"codec_name": "opus", "bit_rate": "1000000"}]}',
            b'{"streams": [{"codec_name": "opus"}]}',
        ]
    )
    monkeypatch.setattr(player.subprocess, 'check_output', lambda *args, **kwargs: next(outputs))

    assert player.FFmpegOpusAudio._probe_codec_native('source') == ('opus', 128)
    assert player.FFmpegOpusAudio._probe_codec_native('source') == ('opus', 512)
    assert player.FFmpegOpusAudio._probe_codec_native('source') == ('opus', None)


def test_fallback_probe_caps_large_bitrate(monkeypatch):
    class Process:
        def communicate(self, timeout):
            return b'    Stream #0:1: Audio: opus, 48000 Hz, stereo, fltp, 1024 kb/s', None

    monkeypatch.setattr(player.subprocess, 'Popen', lambda *args, **kwargs: Process())

    assert player.FFmpegOpusAudio._probe_codec_fallback('source') == ('opus', 512)
