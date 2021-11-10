"""
The MIT License (MIT)

Copyright (c) 2015-present Who do I put here???

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

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .voice_client import VoiceClient

unpacker = struct.Struct('>xxHII')


class SSRC:
    def __init__(self, ssrc: int, speaking: bool) -> None:
        self._ssrc = ssrc
        self.speaking = speaking

    def __repr__(self) -> str:
        return str(self._ssrc)


class VoicePacket:  # IN-PROGRESS
    def __init__(self, client: VoiceClient, data: bytes):
        self.client = client
        _data = bytearray(data)

        self.data: bytearray = data[12:]
        self.header: bytearray = data[:12]
