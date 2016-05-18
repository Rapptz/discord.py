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
    @staticmethod
    def create(client, channel, limit, *, before=None, after=None, reverse=False):
        """Create a proper iterator depending on parameters.

        The messages endpoint has two behaviors:
            If `before` is specified, it returns the `limit` newest messages before `before`, sorted with newest first.
              - Fill strategy - update 'before' to oldest message
            If `after` is specified, it returns the `limit` oldest messages after `after`, sorted with newest first.
              - Fill strategy - update 'after' to newest message
              - If messages are not reversed, they will be out of order (99-0, 199-100, so on)

        A note that if both before and after are specified, before is ignored by the messages endpoint.

        Parameters
        -----------
        client : class:`Client`
        channel : class:`Channel`
            Channel from which to request logs
        limit : int
            Maximum number of messages to retrieve
        before : :class:`Message` or id-like
            Message before which all messages must be.
        after : :class:`Message` or id-like
            Message after which all messages must be.
        reverse : bool
            If set to true, return messages in oldest->newest order. Recommended when using with "after" queries,
            otherwise messages will be out of order. Defaults to False for backwards compatability.
        """
        if before and after:
            if reverse:
                return LogsFromBeforeAfterReversedIterator(client, channel, limit, before, after)
            else:
                return LogsFromBeforeAfterIterator(client, channel, limit, before, after)
        elif after:
            return LogsFromAfterIterator(client, channel, limit, after, reverse=reverse)
        else:
            return LogsFromBeforeIterator(client, channel, limit, before)

    def __init__(self, client, channel, limit):
        self.client = client
        self.channel = channel
        self.limit = limit
        self.messages = asyncio.Queue()

    @asyncio.coroutine
    def iterate(self):
        if self.messages.empty():
            yield from self.fill_messages()

        return self.messages.get_nowait()

    if PY35:
        @asyncio.coroutine
        def __aiter__(self):
            return self

        @asyncio.coroutine
        def __anext__(self):
            try:
                msg = yield from self.iterate()
                return msg
            except asyncio.QueueEmpty:
                # if we're still empty at this point...
                # we didn't get any new messages so stop looping
                raise StopAsyncIteration()

class LogsFromBeforeIterator(LogsFromIterator):
    def __init__(self, client, channel, limit, before):
        super().__init__(client, channel, limit)
        self.before = before

    @asyncio.coroutine
    def fill_messages(self):
        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            data = yield from self.client._logs_from(self.channel, retrieve, before=self.before)
            if len(data):
                self.limit -= retrieve
                self.before = Object(id=data[-1]['id'])
                for element in data:
                    yield from self.messages.put(Message(channel=self.channel, **element))

class LogsFromAfterIterator(LogsFromIterator):
    """Iterator for retrieving "after" style responses.

    Recommended to use with reverse=True - this will return messages oldest to newest.
    With reverse=False, you'll recieve messages 99-0, 199-100, etc."""
    def __init__(self, client, channel, limit, after, *, reverse=False):
        super().__init__(client, channel, limit)
        self.after = after
        self.reverse = reverse

    @asyncio.coroutine
    def fill_messages(self):
        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            data = yield from self.client._logs_from(self.channel, retrieve, after=self.after)
            if len(data):
                self.limit -= retrieve
                self.after = Object(id=data[0]['id'])
                for element in (data if not self.reverse else reversed(data)):
                    yield from self.messages.put(Message(channel=self.channel, **element))

class LogsFromBeforeAfterIterator(LogsFromIterator):
    """Newest -> Oldest."""
    def __init__(self, client, channel, limit, before, after):
        super().__init__(client, channel, limit)
        self.before = before
        self.after = after

    @asyncio.coroutine
    def fill_messages(self):
        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            data = yield from self.client._logs_from(self.channel, retrieve, before=self.before)
            if len(data):
                self.limit -= retrieve
                self.before = Object(id=data[-1]['id'])
                # Only filter if the oldest message is not after our endpoint
                if int(data[-1]['id']) <= int(self.after.id):
                    data = filter(lambda d: int(d['id']) > int(self.after.id), data)
                for element in data:
                        yield from self.messages.put(Message(channel=self.channel, **element))

class LogsFromBeforeAfterReversedIterator(LogsFromIterator):
    """Oldest -> Newest."""
    def __init__(self, client, channel, limit, before, after):
        super().__init__(client, channel, limit)
        self.before = before
        self.after = after

    @asyncio.coroutine
    def fill_messages(self):
        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            data = yield from self.client._logs_from(self.channel, retrieve, after=self.after)
            if len(data):
                self.limit -= retrieve
                self.after = Object(id=data[0]['id'])
                # Only filter if the newest is not before our endpoint
                if int(data[0]['id']) >= int(self.before.id):
                    data = filter(lambda d: int(d['id']) < int(self.before.id), reversed(data))
                else:
                    data = reversed(data)
                for element in data:
                    yield from self.messages.put(Message(channel=self.channel, **element))
