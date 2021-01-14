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

import struct

from .errors import DiscordException

class OggError(DiscordException):
    """An exception that is thrown for Ogg stream parsing errors."""
    pass

# https://tools.ietf.org/html/rfc3533
# https://tools.ietf.org/html/rfc7845

class OggPage:
    _header = struct.Struct('<xBQIIIB')

    def __init__(self, stream):
        try:
            header = stream.read(struct.calcsize(self._header.format))

            self.flag, self.gran_pos, self.serial, \
            self.pagenum, self.crc, self.segnum = self._header.unpack(header)

            self.segtable = stream.read(self.segnum)
            bodylen = sum(struct.unpack('B'*self.segnum, self.segtable))
            self.data = stream.read(bodylen)
        except Exception:
            raise OggError('bad data stream') from None

    def iter_packets(self):
        packetlen = offset = 0
        partial = True

        for seg in self.segtable:
            if seg == 255:
                packetlen += 255
                partial = True
            else:
                packetlen += seg
                yield self.data[offset:offset+packetlen], True
                offset += packetlen
                packetlen = 0
                partial = False

        if partial:
            yield self.data[offset:], False

class OggStream:
    def __init__(self, stream):
        self.stream = stream

    def _next_page(self):
        head = self.stream.read(4)
        if head == b'OggS':
            return OggPage(self.stream)
        elif not head:
            return None
        else:
            raise OggError('invalid header magic')

    def _iter_pages(self):
        page = self._next_page()
        while page:
            yield page
            page = self._next_page()

    def iter_packets(self):
        partial = b''
        for page in self._iter_pages():
            for data, complete in page.iter_packets():
                partial += data
                if complete:
                    yield partial
                    partial = b''
