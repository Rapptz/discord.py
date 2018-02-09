# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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
import datetime

from .errors import NoMoreItems
from .utils import time_snowflake, maybe_coroutine
from .object import Object
from .audit_logs import AuditLogEntry

PY35 = sys.version_info >= (3, 5)

class _AsyncIterator:
    __slots__ = ()

    def get(self, **attrs):
        def predicate(elem):
            for attr, val in attrs.items():
                nested = attr.split('__')
                obj = elem
                for attribute in nested:
                    obj = getattr(obj, attribute)

                if obj != val:
                    return False
            return True

        return self.find(predicate)

    @asyncio.coroutine
    def find(self, predicate):
        while True:
            try:
                elem = yield from self.next()
            except NoMoreItems:
                return None

            ret = yield from maybe_coroutine(predicate, elem)
            if ret:
                return elem

    def map(self, func):
        return _MappedAsyncIterator(self, func)

    def filter(self, predicate):
        return _FilteredAsyncIterator(self, predicate)

    @asyncio.coroutine
    def flatten(self):
        ret = []
        while True:
            try:
                item = yield from self.next()
            except NoMoreItems:
                return ret
            else:
                ret.append(item)

    if PY35:
        @asyncio.coroutine
        def __aiter__(self):
            return self

        @asyncio.coroutine
        def __anext__(self):
            try:
                msg = yield from self.next()
            except NoMoreItems:
                raise StopAsyncIteration()
            else:
                return msg

def _identity(x):
    return x

class _MappedAsyncIterator(_AsyncIterator):
    def __init__(self, iterator, func):
        self.iterator = iterator
        self.func = func

    @asyncio.coroutine
    def next(self):
        # this raises NoMoreItems and will propagate appropriately
        item = yield from self.iterator.next()
        return (yield from maybe_coroutine(self.func, item))

class _FilteredAsyncIterator(_AsyncIterator):
    def __init__(self, iterator, predicate):
        self.iterator = iterator

        if predicate is None:
            predicate = _identity

        self.predicate = predicate

    @asyncio.coroutine
    def next(self):
        getter = self.iterator.next
        pred = self.predicate
        while True:
            # propagate NoMoreItems similar to _MappedAsyncIterator
            item = yield from getter()
            ret = yield from maybe_coroutine(pred, item)
            if ret:
                return item

class ReactionIterator(_AsyncIterator):
    def __init__(self, message, emoji, limit=100, after=None):
        self.message = message
        self.limit = limit
        self.after = after
        state = message._state
        self.getter = state.http.get_reaction_users
        self.state = state
        self.emoji = emoji
        self.guild = message.guild
        self.channel_id = message.channel.id
        self.users = asyncio.Queue(loop=state.loop)

    @asyncio.coroutine
    def next(self):
        if self.users.empty():
            yield from self.fill_users()

        try:
            return self.users.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    @asyncio.coroutine
    def fill_users(self):
        # this is a hack because >circular imports<
        from .user import User

        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            after = self.after.id if self.after else None
            data = yield from self.getter(self.message.id, self.channel_id, self.emoji, retrieve, after=after)

            if data:
                self.limit -= retrieve
                self.after = Object(id=int(data[0]['id']))

            if self.guild is None:
                for element in reversed(data):
                    yield from self.users.put(User(state=self.state, data=element))
            else:
                for element in reversed(data):
                    member_id = int(element['id'])
                    member = self.guild.get_member(member_id)
                    if member is not None:
                        yield from self.users.put(member)
                    else:
                        yield from self.users.put(User(state=self.state, data=element))

class HistoryIterator(_AsyncIterator):
    """Iterator for receiving a channel's message history.

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
    messageable: :class:`abc.Messageable`
        Messageable class to retrieve message history fro.
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
            if self.limit is None:
                raise ValueError('history does not support around with limit=None')
            if self.limit > 101:
                raise ValueError("history max limit 101 when specifying around parameter")
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
    def next(self):
        if self.messages.empty():
            yield from self.fill_messages()

        try:
            return self.messages.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None:
            r = 100
        elif l <= 100:
            r = l
        else:
            r = 100

        self.retrieve = r
        return r > 0

    @asyncio.coroutine
    def flatten(self):
        # this is similar to fill_messages except it uses a list instead
        # of a queue to place the messages in.
        result = []
        channel = yield from self.messageable._get_channel()
        self.channel = channel
        while self._get_retrieve():
            data = yield from self._retrieve_messages(self.retrieve)
            if len(data) < 100:
                self.limit = 0 # terminate the infinite loop

            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            for element in data:
                result.append(self.state.create_message(channel=channel, data=element))
        return result

    @asyncio.coroutine
    def fill_messages(self):
        if not hasattr(self, 'channel'):
            # do the required set up
            channel = yield from self.messageable._get_channel()
            self.channel = channel

        if self._get_retrieve():
            data = yield from self._retrieve_messages(self.retrieve)
            if self.limit is None and len(data) < 100:
                self.limit = 0 # terminate the infinite loop

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
        before = self.before.id if self.before else None
        data = yield from self.logs_from(self.channel.id, retrieve, before=before)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(data[-1]['id']))
        return data

    @asyncio.coroutine
    def _retrieve_messages_after_strategy(self, retrieve):
        """Retrieve messages using after parameter."""
        after = self.after.id if self.after else None
        data = yield from self.logs_from(self.channel.id, retrieve, after=after)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(data[0]['id']))
        return data

    @asyncio.coroutine
    def _retrieve_messages_around_strategy(self, retrieve):
        """Retrieve messages using around parameter."""
        if self.around:
            around = self.around.id if self.around else None
            data = yield from self.logs_from(self.channel.id, retrieve, around=around)
            self.around = None
            return data
        return []

class AuditLogIterator(_AsyncIterator):
    def __init__(self, guild, limit=None, before=None, after=None, reverse=None, user_id=None, action_type=None):
        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))


        self.guild = guild
        self.loop = guild._state.loop
        self.request = guild._state.http.get_audit_logs
        self.limit = limit
        self.before = before
        self.user_id = user_id
        self.action_type = action_type
        self.after = after
        self._users = {}
        self._state = guild._state

        if reverse is None:
            self.reverse = after is not None
        else:
            self.reverse = reverse

        self._filter = None  # entry dict -> bool

        self.entries = asyncio.Queue(loop=self.loop)

        if self.before and self.after:
            if self.reverse:
                self._strategy = self._after_strategy
                self._filter = lambda m: int(m['id']) < self.before.id
            else:
                self._strategy = self._before_strategy
                self._filter = lambda m: int(m['id']) > self.after.id
        elif self.after:
            self._strategy = self._after_strategy
        else:
            self._strategy = self._before_strategy

    @asyncio.coroutine
    def _before_strategy(self, retrieve):
        before = self.before.id if self.before else None
        data = yield from self.request(self.guild.id, limit=retrieve, user_id=self.user_id,
                                       action_type=self.action_type, before=before)

        entries = data.get('audit_log_entries', [])
        if len(data) and entries:
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(entries[-1]['id']))
        return data.get('users', []), entries

    @asyncio.coroutine
    def _after_strategy(self, retrieve):
        after = self.after.id if self.after else None
        data = yield from self.request(self.guild.id, limit=retrieve, user_id=self.user_id,
                                       action_type=self.action_type, after=after)
        entries = data.get('audit_log_entries', [])
        if len(data) and entries:
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(entries[0]['id']))
        return data.get('users', []), entries

    @asyncio.coroutine
    def next(self):
        if self.entries.empty():
            yield from self._fill()

        try:
            return self.entries.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None:
            r = 100
        elif l <= 100:
            r = l
        else:
            r = 100

        self.retrieve = r
        return r > 0

    @asyncio.coroutine
    def _fill(self):
        from .user import User

        if self._get_retrieve():
            users, data = yield from self._strategy(self.retrieve)
            if self.limit is None and len(data) < 100:
                self.limit = 0 # terminate the infinite loop

            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            for user in users:
                u = User(data=user, state=self._state)
                self._users[u.id] = u

            for element in data:
                # TODO: remove this if statement later
                if element['action_type'] is None:
                    continue

                yield from self.entries.put(AuditLogEntry(data=element, users=self._users, guild=self.guild))
