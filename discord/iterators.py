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
import datetime

from .errors import NoMoreMessages
from .utils import time_snowflake
from .object import Object

PY35 = sys.version_info >= (3, 5)

class LogsFromIterator:
    """Iterator for receiving logs.

    The messages endpoint has two behaviours we care about here:
    If `before` is specified, the messages endpoint returns the `limit`
    newest messages before `before`, sorted with newest first. For filling over
    100 messages, update the `before` parameter to the oldest message received.
    Messages will be returned in order by time.
    If `after` is specified, it returns the `limit` oldest messages after
    `after`, sorted with newest first. For filling over 100 messages, update the
    `after` parameter to the newest message received. If messages are not
    reversed, they will be out of order (99-0, 199-100, so on)

    A note that if both before and after are specified, before is ignored by the
    messages endpoint.

    Parameters
    -----------
    channel: class:`Channel`
        Channel from which to request logs
    limit : int
        Maximum number of messages to retrieve
    before : :class:`Message` or id-like
        Message before which all messages must be.
    after : :class:`Message` or id-like
        Message after which all messages must be.
    around : :class:`Message` or id-like
        Message around which all messages must be. Limit max 101. Note that if
        limit is an even number, this will return at most limit+1 messages.
    reverse: bool
        If set to true, return messages in oldest->newest order. Recommended
        when using with "after" queries with limit over 100, otherwise messages
        will be out of order.
    """

    def __init__(self, messageable, limit,
                 before=None, after=None, around=None, reverse=None):

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))
        if isinstance(around, datetime.datetime):
            around = Object(id=time_snowflake(around))

        self.messageable = messageable
        self.limit = limit
        self.before = before
        self.after = after
        self.around = around

        if reverse is None:
            self.reverse = after is not None
        else:
            self.reverse = reverse

        self._filter = None  # message dict -> bool

        self.state = self.messageable._state
        self.logs_from = self.state.http.logs_from
        self.messages = asyncio.Queue(loop=self.state.loop)

        if self.around:
            if self.limit > 101:
                raise ValueError("LogsFrom max limit 101 when specifying around parameter")
            elif self.limit == 101:
                self.limit = 100  # Thanks discord
            elif self.limit == 1:
                raise ValueError("Use get_message.")

            self._retrieve_messages = self._retrieve_messages_around_strategy
            if self.before and self.after:
                self._filter = lambda m: self.after.id < int(m['id']) < self.before.id
            elif self.before:
                self._filter = lambda m: int(m['id']) < self.before.id
            elif self.after:
                self._filter = lambda m: self.after.id < int(m['id'])
        elif self.before and self.after:
            if self.reverse:
                self._retrieve_messages = self._retrieve_messages_after_strategy
                self._filter = lambda m: int(m['id']) < self.before.id
            else:
                self._retrieve_messages = self._retrieve_messages_before_strategy
                self._filter = lambda m: int(m['id']) > self.after.id
        elif self.after:
            self._retrieve_messages = self._retrieve_messages_after_strategy
        else:
            self._retrieve_messages = self._retrieve_messages_before_strategy

    @asyncio.coroutine
    def get(self):
        if self.messages.empty():
            yield from self.fill_messages()

        try:
            return self.messages.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreMessages()

    @asyncio.coroutine
    def fill_messages(self):
        if not hasattr(self, 'channel'):
            # do the required set up
            channel = yield from self.messageable._get_channel()
            self.channel = channel

        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100
            data = yield from self._retrieve_messages(retrieve)
            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            channel = self.channel
            for element in data:
                yield from self.messages.put(self.state.create_message(channel=channel, data=element))

    @asyncio.coroutine
    def _retrieve_messages(self, retrieve):
        """Retrieve messages and update next parameters."""
        pass

    @asyncio.coroutine
    def _retrieve_messages_before_strategy(self, retrieve):
        """Retrieve messages using before parameter."""
        data = yield from self.logs_from(self.channel.id, retrieve, before=getattr(self.before, 'id', None))
        if len(data):
            self.limit -= retrieve
            self.before = Object(id=int(data[-1]['id']))
        return data

    @asyncio.coroutine
    def _retrieve_messages_after_strategy(self, retrieve):
        """Retrieve messages using after parameter."""
        data = yield from self.logs_from(self.channel.id, retrieve, after=getattr(self.after, 'id', None))
        if len(data):
            self.limit -= retrieve
            self.after = Object(id=int(data[0]['id']))
        return data

    @asyncio.coroutine
    def _retrieve_messages_around_strategy(self, retrieve):
        """Retrieve messages using around parameter."""
        if self.around:
            data = yield from self.logs_from(self.channel.id, retrieve, around=getattr(self.around, 'id', None))
            self.around = None
            return data
        return []

    if PY35:
        @asyncio.coroutine
        def __aiter__(self):
            return self

        @asyncio.coroutine
        def __anext__(self):
            try:
                msg = yield from self.get()
                return msg
            except NoMoreMessages:
                # if we're still empty at this point...
                # we didn't get any new messages so stop looping
                raise StopAsyncIteration()
