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

import sys
import asyncio
import aiohttp
from .message import Message
from .object import Object

PY35 = sys.version_info >= (3, 5)

class LogsFromIterator:
    def __init__(self, client, channel, limit, before, after):
        self.client = client
        self.channel = channel
        self.limit = limit
        self.before = before
        self.after = after
        self.messages = asyncio.Queue()

    @asyncio.coroutine
    def fill_messages(self):
        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100
            data = yield from self.client._logs_from(self.channel, retrieve, self.before, self.after)
            if len(data):
                self.limit -= retrieve
                self.before = Object(id=data[-1]['id'])
                for element in data:
                    yield from self.messages.put(Message(channel=self.channel, **element))

    if PY35:
        @asyncio.coroutine
        def __aiter__(self):
            return self

        @asyncio.coroutine
        def __anext__(self):
            if self.messages.empty():
                yield from self.fill_messages()

            try:
                msg = self.messages.get_nowait()
                return msg
            except asyncio.QueueEmpty:
                # if we're still empty at this point...
                # we didn't get any new messages so stop looping
                raise StopAsyncIteration()
