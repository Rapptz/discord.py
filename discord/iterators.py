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

from __future__ import annotations

import asyncio
import datetime
from typing import Awaitable, TYPE_CHECKING, TypeVar, Optional, Any, Callable, Union, List, AsyncIterator

from .errors import NoMoreItems
from .utils import snowflake_time, time_snowflake, maybe_coroutine
from .object import Object
from .audit_logs import AuditLogEntry

__all__ = (
    'ReactionIterator',
    'HistoryIterator',
    'AuditLogIterator',
    'GuildIterator',
    'MemberIterator',
)

if TYPE_CHECKING:
    from .types.audit_log import (
        AuditLog as AuditLogPayload,
    )
    from .types.guild import (
        Guild as GuildPayload,
    )
    from .types.message import (
        Message as MessagePayload,
    )
    from .types.user import (
        PartialUser as PartialUserPayload,
    )

    from .types.threads import (
        Thread as ThreadPayload,
    )

    from .member import Member
    from .user import User
    from .message import Message
    from .audit_logs import AuditLogEntry
    from .guild import Guild
    from .threads import Thread
    from .abc import Snowflake

T = TypeVar('T')
OT = TypeVar('OT')
_Func = Callable[[T], Union[OT, Awaitable[OT]]]

OLDEST_OBJECT = Object(id=0)


class _AsyncIterator(AsyncIterator[T]):
    __slots__ = ()

    async def next(self) -> T:
        raise NotImplementedError

    def get(self, **attrs: Any) -> Awaitable[Optional[T]]:
        def predicate(elem: T):
            for attr, val in attrs.items():
                nested = attr.split('__')
                obj = elem
                for attribute in nested:
                    obj = getattr(obj, attribute)

                if obj != val:
                    return False
            return True

        return self.find(predicate)

    async def find(self, predicate: _Func[T, bool]) -> Optional[T]:
        while True:
            try:
                elem = await self.next()
            except NoMoreItems:
                return None

            ret = await maybe_coroutine(predicate, elem)
            if ret:
                return elem

    def chunk(self, max_size: int) -> _ChunkedAsyncIterator[T]:
        if max_size <= 0:
            raise ValueError('async iterator chunk sizes must be greater than 0.')
        return _ChunkedAsyncIterator(self, max_size)

    def map(self, func: _Func[T, OT]) -> _MappedAsyncIterator[OT]:
        return _MappedAsyncIterator(self, func)

    def filter(self, predicate: _Func[T, bool]) -> _FilteredAsyncIterator[T]:
        return _FilteredAsyncIterator(self, predicate)

    async def flatten(self) -> List[T]:
        return [element async for element in self]

    async def __anext__(self) -> T:
        try:
            return await self.next()
        except NoMoreItems:
            raise StopAsyncIteration()


def _identity(x):
    return x


class _ChunkedAsyncIterator(_AsyncIterator[List[T]]):
    def __init__(self, iterator, max_size):
        self.iterator = iterator
        self.max_size = max_size

    async def next(self) -> List[T]:
        ret: List[T] = []
        n = 0
        while n < self.max_size:
            try:
                item = await self.iterator.next()
            except NoMoreItems:
                if ret:
                    return ret
                raise
            else:
                ret.append(item)
                n += 1
        return ret


class _MappedAsyncIterator(_AsyncIterator[T]):
    def __init__(self, iterator, func):
        self.iterator = iterator
        self.func = func

    async def next(self) -> T:
        # this raises NoMoreItems and will propagate appropriately
        item = await self.iterator.next()
        return await maybe_coroutine(self.func, item)


class _FilteredAsyncIterator(_AsyncIterator[T]):
    def __init__(self, iterator, predicate):
        self.iterator = iterator

        if predicate is None:
            predicate = _identity

        self.predicate = predicate

    async def next(self) -> T:
        getter = self.iterator.next
        pred = self.predicate
        while True:
            # propagate NoMoreItems similar to _MappedAsyncIterator
            item = await getter()
            ret = await maybe_coroutine(pred, item)
            if ret:
                return item


class ReactionIterator(_AsyncIterator[Union['User', 'Member']]):
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
        self.users = asyncio.Queue()

    async def next(self) -> Union[User, Member]:
        if self.users.empty():
            await self.fill_users()

        try:
            return self.users.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    async def fill_users(self):
        # this is a hack because >circular imports<
        from .user import User

        if self.limit > 0:
            retrieve = self.limit if self.limit <= 100 else 100

            after = self.after.id if self.after else None
            data: List[PartialUserPayload] = await self.getter(
                self.channel_id, self.message.id, self.emoji, retrieve, after=after
            )

            if data:
                self.limit -= retrieve
                self.after = Object(id=int(data[-1]['id']))

            if self.guild is None or isinstance(self.guild, Object):
                for element in reversed(data):
                    await self.users.put(User(state=self.state, data=element))
            else:
                for element in reversed(data):
                    member_id = int(element['id'])
                    member = self.guild.get_member(member_id)
                    if member is not None:
                        await self.users.put(member)
                    else:
                        await self.users.put(User(state=self.state, data=element))


class HistoryIterator(_AsyncIterator['Message']):
    """Iterator for receiving a channel's message history.

    The messages endpoint has two behaviours we care about here:
    If ``before`` is specified, the messages endpoint returns the `limit`
    newest messages before ``before``, sorted with newest first. For filling over
    100 messages, update the ``before`` parameter to the oldest message received.
    Messages will be returned in order by time.
    If ``after`` is specified, it returns the ``limit`` oldest messages after
    ``after``, sorted with newest first. For filling over 100 messages, update the
    ``after`` parameter to the newest message received. If messages are not
    reversed, they will be out of order (99-0, 199-100, so on)

    A note that if both ``before`` and ``after`` are specified, ``before`` is ignored by the
    messages endpoint.

    Parameters
    -----------
    messageable: :class:`abc.Messageable`
        Messageable class to retrieve message history from.
    limit: :class:`int`
        Maximum number of messages to retrieve
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message before which all messages must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message after which all messages must be.
    around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message around which all messages must be. Limit max 101. Note that if
        limit is an even number, this will return at most limit+1 messages.
    oldest_first: Optional[:class:`bool`]
        If set to ``True``, return messages in oldest->newest order. Defaults to
        ``True`` if `after` is specified, otherwise ``False``.
    """

    def __init__(self, messageable, limit, before=None, after=None, around=None, oldest_first=None):

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))
        if isinstance(around, datetime.datetime):
            around = Object(id=time_snowflake(around))

        if oldest_first is None:
            self.reverse = after is not None
        else:
            self.reverse = oldest_first

        self.messageable = messageable
        self.limit = limit
        self.before = before
        self.after = after or OLDEST_OBJECT
        self.around = around

        self._filter = None  # message dict -> bool

        self.state = self.messageable._state
        self.logs_from = self.state.http.logs_from
        self.messages = asyncio.Queue()

        if self.around:
            if self.limit is None:
                raise ValueError('history does not support around with limit=None')
            if self.limit > 101:
                raise ValueError("history max limit 101 when specifying around parameter")
            elif self.limit == 101:
                self.limit = 100  # Thanks discord

            self._retrieve_messages = self._retrieve_messages_around_strategy  # type: ignore
            if self.before and self.after:
                self._filter = lambda m: self.after.id < int(m['id']) < self.before.id
            elif self.before:
                self._filter = lambda m: int(m['id']) < self.before.id
            elif self.after:
                self._filter = lambda m: self.after.id < int(m['id'])
        else:
            if self.reverse:
                self._retrieve_messages = self._retrieve_messages_after_strategy  # type: ignore
                if self.before:
                    self._filter = lambda m: int(m['id']) < self.before.id
            else:
                self._retrieve_messages = self._retrieve_messages_before_strategy  # type: ignore
                if self.after and self.after != OLDEST_OBJECT:
                    self._filter = lambda m: int(m['id']) > self.after.id

    async def next(self) -> Message:
        if self.messages.empty():
            await self.fill_messages()

        try:
            return self.messages.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def fill_messages(self):
        if not hasattr(self, 'channel'):
            # do the required set up
            channel = await self.messageable._get_channel()
            self.channel = channel

        if self._get_retrieve():
            data = await self._retrieve_messages(self.retrieve)
            if len(data) < 100:
                self.limit = 0  # terminate the infinite loop

            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            channel = self.channel
            for element in data:
                await self.messages.put(self.state.create_message(channel=channel, data=element))

    async def _retrieve_messages(self, retrieve) -> List[Message]:
        """Retrieve messages and update next parameters."""
        raise NotImplementedError

    async def _retrieve_messages_before_strategy(self, retrieve):
        """Retrieve messages using before parameter."""
        before = self.before.id if self.before else None
        data: List[MessagePayload] = await self.logs_from(self.channel.id, retrieve, before=before)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(data[-1]['id']))
        return data

    async def _retrieve_messages_after_strategy(self, retrieve):
        """Retrieve messages using after parameter."""
        after = self.after.id if self.after else None
        data: List[MessagePayload] = await self.logs_from(self.channel.id, retrieve, after=after)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(data[0]['id']))
        return data

    async def _retrieve_messages_around_strategy(self, retrieve):
        """Retrieve messages using around parameter."""
        if self.around:
            around = self.around.id if self.around else None
            data: List[MessagePayload] = await self.logs_from(self.channel.id, retrieve, around=around)
            self.around = None
            return data
        return []


class AuditLogIterator(_AsyncIterator['AuditLogEntry']):
    def __init__(self, guild, limit=None, before=None, after=None, oldest_first=None, user_id=None, action_type=None):
        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        if oldest_first is None:
            self.reverse = after is not None
        else:
            self.reverse = oldest_first

        self.guild = guild
        self.loop = guild._state.loop
        self.request = guild._state.http.get_audit_logs
        self.limit = limit
        self.before = before
        self.user_id = user_id
        self.action_type = action_type
        self.after = OLDEST_OBJECT
        self._users = {}
        self._state = guild._state

        self._filter = None  # entry dict -> bool

        self.entries = asyncio.Queue()

        if self.reverse:
            self._strategy = self._after_strategy
            if self.before:
                self._filter = lambda m: int(m['id']) < self.before.id
        else:
            self._strategy = self._before_strategy
            if self.after and self.after != OLDEST_OBJECT:
                self._filter = lambda m: int(m['id']) > self.after.id

    async def _before_strategy(self, retrieve):
        before = self.before.id if self.before else None
        data: AuditLogPayload = await self.request(
            self.guild.id, limit=retrieve, user_id=self.user_id, action_type=self.action_type, before=before
        )

        entries = data.get('audit_log_entries', [])
        if len(data) and entries:
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(entries[-1]['id']))
        return data.get('users', []), entries

    async def _after_strategy(self, retrieve):
        after = self.after.id if self.after else None
        data: AuditLogPayload = await self.request(
            self.guild.id, limit=retrieve, user_id=self.user_id, action_type=self.action_type, after=after
        )
        entries = data.get('audit_log_entries', [])
        if len(data) and entries:
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(entries[0]['id']))
        return data.get('users', []), entries

    async def next(self) -> AuditLogEntry:
        if self.entries.empty():
            await self._fill()

        try:
            return self.entries.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def _fill(self):
        from .user import User

        if self._get_retrieve():
            users, data = await self._strategy(self.retrieve)
            if len(data) < 100:
                self.limit = 0  # terminate the infinite loop

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

                await self.entries.put(AuditLogEntry(data=element, users=self._users, guild=self.guild))


class GuildIterator(_AsyncIterator['Guild']):
    """Iterator for receiving the client's guilds.

    The guilds endpoint has the same two behaviours as described
    in :class:`HistoryIterator`:
    If ``before`` is specified, the guilds endpoint returns the ``limit``
    newest guilds before ``before``, sorted with newest first. For filling over
    100 guilds, update the ``before`` parameter to the oldest guild received.
    Guilds will be returned in order by time.
    If `after` is specified, it returns the ``limit`` oldest guilds after ``after``,
    sorted with newest first. For filling over 100 guilds, update the ``after``
    parameter to the newest guild received, If guilds are not reversed, they
    will be out of order (99-0, 199-100, so on)

    Not that if both ``before`` and ``after`` are specified, ``before`` is ignored by the
    guilds endpoint.

    Parameters
    -----------
    bot: :class:`discord.Client`
        The client to retrieve the guilds from.
    limit: :class:`int`
        Maximum number of guilds to retrieve.
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object before which all guilds must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object after which all guilds must be.
    """

    def __init__(self, bot, limit, before=None, after=None):

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.bot = bot
        self.limit = limit
        self.before = before
        self.after = after

        self._filter = None

        self.state = self.bot._connection
        self.get_guilds = self.bot.http.get_guilds
        self.guilds = asyncio.Queue()

        if self.before and self.after:
            self._retrieve_guilds = self._retrieve_guilds_before_strategy  # type: ignore
            self._filter = lambda m: int(m['id']) > self.after.id
        elif self.after:
            self._retrieve_guilds = self._retrieve_guilds_after_strategy  # type: ignore
        else:
            self._retrieve_guilds = self._retrieve_guilds_before_strategy  # type: ignore

    async def next(self) -> Guild:
        if self.guilds.empty():
            await self.fill_guilds()

        try:
            return self.guilds.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    def create_guild(self, data):
        from .guild import Guild

        return Guild(state=self.state, data=data)

    async def fill_guilds(self):
        if self._get_retrieve():
            data = await self._retrieve_guilds(self.retrieve)
            if self.limit is None or len(data) < 100:
                self.limit = 0

            if self._filter:
                data = filter(self._filter, data)

            for element in data:
                await self.guilds.put(self.create_guild(element))

    async def _retrieve_guilds(self, retrieve) -> List[Guild]:
        """Retrieve guilds and update next parameters."""
        raise NotImplementedError

    async def _retrieve_guilds_before_strategy(self, retrieve):
        """Retrieve guilds using before parameter."""
        before = self.before.id if self.before else None
        data: List[GuildPayload] = await self.get_guilds(retrieve, before=before)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(data[-1]['id']))
        return data

    async def _retrieve_guilds_after_strategy(self, retrieve):
        """Retrieve guilds using after parameter."""
        after = self.after.id if self.after else None
        data: List[GuildPayload] = await self.get_guilds(retrieve, after=after)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(data[0]['id']))
        return data


class MemberIterator(_AsyncIterator['Member']):
    def __init__(self, guild, limit=1000, after=None):

        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.guild = guild
        self.limit = limit
        self.after = after or OLDEST_OBJECT

        self.state = self.guild._state
        self.get_members = self.state.http.get_members
        self.members = asyncio.Queue()

    async def next(self) -> Member:
        if self.members.empty():
            await self.fill_members()

        try:
            return self.members.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 1000:
            r = 1000
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def fill_members(self):
        if self._get_retrieve():
            after = self.after.id if self.after else None
            data = await self.get_members(self.guild.id, self.retrieve, after)
            if not data:
                # no data, terminate
                return

            if len(data) < 1000:
                self.limit = 0  # terminate loop

            self.after = Object(id=int(data[-1]['user']['id']))

            for element in reversed(data):
                await self.members.put(self.create_member(element))

    def create_member(self, data):
        from .member import Member

        return Member(data=data, guild=self.guild, state=self.state)


class ArchivedThreadIterator(_AsyncIterator['Thread']):
    def __init__(
        self,
        channel_id: int,
        guild: Guild,
        limit: Optional[int],
        joined: bool,
        private: bool,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ):
        self.channel_id = channel_id
        self.guild = guild
        self.limit = limit
        self.joined = joined
        self.private = private
        self.http = guild._state.http

        if joined and not private:
            raise ValueError('Cannot iterate over joined public archived threads')

        self.before: Optional[str]
        if before is None:
            self.before = None
        elif isinstance(before, datetime.datetime):
            if joined:
                self.before = str(time_snowflake(before, high=False))
            else:
                self.before = before.isoformat()
        else:
            if joined:
                self.before = str(before.id)
            else:
                self.before = snowflake_time(before.id).isoformat()

        self.update_before: Callable[[ThreadPayload], str] = self.get_archive_timestamp

        if joined:
            self.endpoint = self.http.get_joined_private_archived_threads
            self.update_before = self.get_thread_id
        elif private:
            self.endpoint = self.http.get_private_archived_threads
        else:
            self.endpoint = self.http.get_public_archived_threads

        self.queue: asyncio.Queue[Thread] = asyncio.Queue()
        self.has_more: bool = True

    async def next(self) -> Thread:
        if self.queue.empty():
            await self.fill_queue()

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    @staticmethod
    def get_archive_timestamp(data: ThreadPayload) -> str:
        return data['thread_metadata']['archive_timestamp']

    @staticmethod
    def get_thread_id(data: ThreadPayload) -> str:
        return data['id']  # type: ignore

    async def fill_queue(self) -> None:
        if not self.has_more:
            raise NoMoreItems()

        limit = 50 if self.limit is None else max(self.limit, 50)
        data = await self.endpoint(self.channel_id, before=self.before, limit=limit)

        # This stuff is obviously WIP because 'members' is always empty
        threads: List[ThreadPayload] = data.get('threads', [])
        for d in reversed(threads):
            self.queue.put_nowait(self.create_thread(d))

        self.has_more = data.get('has_more', False)
        if self.limit is not None:
            self.limit -= len(threads)
            if self.limit <= 0:
                self.has_more = False

        if self.has_more:
            self.before = self.update_before(threads[-1])

    def create_thread(self, data: ThreadPayload) -> Thread:
        from .threads import Thread
        return Thread(guild=self.guild, state=self.guild._state, data=data)
