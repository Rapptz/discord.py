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

from .state import AutoShardedConnectionState
from .client import Client
from .gateway import *
from .errors import ClientException, InvalidArgument
from . import compat, utils
from .enums import Status

import asyncio
import logging
import websockets
import itertools

log = logging.getLogger(__name__)

class Shard:
    def __init__(self, ws, client):
        self.ws = ws
        self._client = client
        self.loop = self._client.loop
        self._current = compat.create_future(self.loop)
        self._current.set_result(None) # we just need an already done future
        self._pending = asyncio.Event(loop=self.loop)
        self._pending_task = None

    @property
    def id(self):
        return self.ws.shard_id

    def is_pending(self):
        return not self._pending.is_set()

    def complete_pending_reads(self):
        self._pending.set()

    def _pending_reads(self):
        try:
            while self.is_pending():
                yield from self.poll()
        except asyncio.CancelledError:
            pass

    def launch_pending_reads(self):
        self._pending_task = compat.create_task(self._pending_reads(), loop=self.loop)

    def wait(self):
        return self._pending_task

    @asyncio.coroutine
    def poll(self):
        try:
            yield from self.ws.poll_event()
        except ResumeWebSocket as e:
            log.info('Got a request to RESUME the websocket at Shard ID %s.', self.id)
            coro = DiscordWebSocket.from_client(self._client, resume=True,
                                                              shard_id=self.id,
                                                              session=self.ws.session_id,
                                                              sequence=self.ws.sequence)
            self.ws = yield from asyncio.wait_for(coro, timeout=180.0, loop=self.loop)

    def get_future(self):
        if self._current.done():
            self._current = compat.create_task(self.poll(), loop=self.loop)

        return self._current

@asyncio.coroutine
def _ensure_coroutine_connect(gateway, loop):
    # In 3.5+ websockets.connect does not return a coroutine, but an awaitable.
    # The problem is that in 3.5.0 and in some cases 3.5.1, asyncio.ensure_future and
    # by proxy, asyncio.wait_for, do not accept awaitables, but rather futures or coroutines.
    # By wrapping it up into this function we ensure that it's in a coroutine and not an awaitable
    # even for 3.5.0 users.
    ws = yield from websockets.connect(gateway, loop=loop, klass=DiscordWebSocket)
    return ws

class AutoShardedClient(Client):
    """A client similar to :class:`Client` except it handles the complications
    of sharding for the user into a more manageable and transparent single
    process bot.

    When using this client, you will be able to use it as-if it was a regular
    :class:`Client` with a single shard when implementation wise internally it
    is split up into multiple shards. This allows you to not have to deal with
    IPC or other complicated infrastructure.

    It is recommended to use this client only if you have surpassed at least
    1000 guilds.

    If no :attr:`shard_count` is provided, then the library will use the
    Bot Gateway endpoint call to figure out how many shards to use.

    If a ``shard_ids`` parameter is given, then those shard IDs will be used
    to launch the internal shards. Note that :attr:`shard_count` must be provided
    if this is used. By default, when omitted, the client will launch shards from
    0 to ``shard_count - 1``.

    Attributes
    ------------
    shard_ids: Optional[List[:class:`int`]]
        An optional list of shard_ids to launch the shards with.
    """
    def __init__(self, *args, loop=None, **kwargs):
        kwargs.pop('shard_id', None)
        self.shard_ids = kwargs.pop('shard_ids', None)
        super().__init__(*args, loop=loop, **kwargs)

        if self.shard_ids is not None:
            if self.shard_count is None:
                raise ClientException('When passing manual shard_ids, you must provide a shard_count.')
            elif not isinstance(self.shard_ids, (list, tuple)):
                raise ClientException('shard_ids parameter must be a list or a tuple.')

        self._connection = AutoShardedConnectionState(dispatch=self.dispatch, chunker=self._chunker,
                                                      syncer=self._syncer, http=self.http, loop=self.loop, **kwargs)

        # instead of a single websocket, we have multiple
        # the key is the shard_id
        self.shards = {}

        def _get_websocket(guild_id):
            i = (guild_id >> 22) % self.shard_count
            return self.shards[i].ws

        self._connection._get_websocket = _get_websocket

    @asyncio.coroutine
    def _chunker(self, guild, *, shard_id=None):
        try:
            guild_id = guild.id
            shard_id = shard_id or guild.shard_id
        except AttributeError:
            guild_id = [s.id for s in guild]

        payload = {
            'op': 8,
            'd': {
                'guild_id': guild_id,
                'query': '',
                'limit': 0
            }
        }

        ws = self.shards[shard_id].ws
        yield from ws.send_as_json(payload)

    @property
    def latency(self):
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This operates similarly to :meth:`.Client.latency` except it uses the average
        latency of every shard's latency. To get a list of shard latency, check the
        :attr:`latencies` property. Returns ``nan`` if there are no shards ready.
        """
        if not self.shards:
            return float('nan')
        return sum(latency for _, latency in self.latencies) / len(self.shards)

    @property
    def latencies(self):
        """List[Tuple[:class:`int`, :class:`float`]]: A list of latencies between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This returns a list of tuples with elements ``(shard_id, latency)``.
        """
        return [(shard_id, shard.ws.latency) for shard_id, shard in self.shards.items()]

    @asyncio.coroutine
    def request_offline_members(self, *guilds):
        """|coro|

        Requests previously offline members from the guild to be filled up
        into the :attr:`Guild.members` cache. This function is usually not
        called. It should only be used if you have the ``fetch_offline_members``
        parameter set to ``False``.

        When the client logs on and connects to the websocket, Discord does
        not provide the library with offline members if the number of members
        in the guild is larger than 250. You can check if a guild is large
        if :attr:`Guild.large` is ``True``.

        Parameters
        -----------
        \*guilds
            An argument list of guilds to request offline members for.

        Raises
        -------
        InvalidArgument
            If any guild is unavailable or not large in the collection.
        """
        if any(not g.large or g.unavailable for g in guilds):
            raise InvalidArgument('An unavailable or non-large guild was passed.')

        _guilds = sorted(guilds, key=lambda g: g.shard_id)
        for shard_id, sub_guilds in itertools.groupby(_guilds, key=lambda g: g.shard_id):
            sub_guilds = list(sub_guilds)
            yield from self._connection.request_offline_members(sub_guilds, shard_id=shard_id)

    @asyncio.coroutine
    def launch_shard(self, gateway, shard_id):
        try:
            ws = yield from asyncio.wait_for(_ensure_coroutine_connect(gateway, self.loop), loop=self.loop, timeout=180.0)
        except Exception as e:
            log.info('Failed to connect for shard_id: %s. Retrying...', shard_id)
            yield from asyncio.sleep(5.0, loop=self.loop)
            return (yield from self.launch_shard(gateway, shard_id))

        ws.token = self.http.token
        ws._connection = self._connection
        ws._dispatch = self.dispatch
        ws.gateway = gateway
        ws.shard_id = shard_id
        ws.shard_count = self.shard_count
        ws._max_heartbeat_timeout = self._connection.heartbeat_timeout

        try:
            # OP HELLO
            yield from asyncio.wait_for(ws.poll_event(), loop=self.loop, timeout=180.0)
            yield from asyncio.wait_for(ws.identify(), loop=self.loop, timeout=180.0)
        except asyncio.TimeoutError:
            log.info('Timed out when connecting for shard_id: %s. Retrying...', shard_id)
            yield from asyncio.sleep(5.0, loop=self.loop)
            return (yield from self.launch_shard(gateway, shard_id))

        # keep reading the shard while others connect
        self.shards[shard_id] = ret = Shard(ws, self)
        ret.launch_pending_reads()
        yield from asyncio.sleep(5.0, loop=self.loop)

    @asyncio.coroutine
    def launch_shards(self):
        if self.shard_count is None:
            self.shard_count, gateway = yield from self.http.get_bot_gateway()
        else:
            gateway = yield from self.http.get_gateway()

        self._connection.shard_count = self.shard_count

        shard_ids = self.shard_ids if self.shard_ids else range(self.shard_count)

        for shard_id in shard_ids:
            yield from self.launch_shard(gateway, shard_id)

        shards_to_wait_for = []
        for shard in self.shards.values():
            shard.complete_pending_reads()
            shards_to_wait_for.append(shard.wait())

        # wait for all pending tasks to finish
        yield from utils.sane_wait_for(shards_to_wait_for, timeout=300.0, loop=self.loop)

    @asyncio.coroutine
    def _connect(self):
        yield from self.launch_shards()

        while True:
            pollers = [shard.get_future() for shard in self.shards.values()]
            done, pending = yield from asyncio.wait(pollers, loop=self.loop, return_when=asyncio.FIRST_COMPLETED)
            for f in done:
                # we wanna re-raise to the main Client.connect handler if applicable
                f.result()

    @asyncio.coroutine
    def close(self):
        """|coro|

        Closes the connection to discord.
        """
        if self.is_closed():
            return

        self._closed.set()

        for vc in self.voice_clients:
            try:
                yield from vc.disconnect()
            except:
                pass

        to_close = [shard.ws.close() for shard in self.shards.values()]
        yield from asyncio.wait(to_close, loop=self.loop)
        yield from self.http.close()

    @asyncio.coroutine
    def change_presence(self, *, activity=None, status=None, afk=False, shard_id=None):
        """|coro|

        Changes the client's presence.

        The activity parameter is a :class:`Activity` object (not a string) that represents
        the activity being done currently. This could also be the slimmed down versions,
        :class:`Game` and :class:`Streaming`.

        Example: ::

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        Parameters
        ----------
        activity: Optional[Union[:class:`Game`, :class:`Streaming`, :class:`Activity`]]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`Status`]
            Indicates what status to change to. If None, then
            :attr:`Status.online` is used.
        afk: bool
            Indicates if you are going AFK. This allows the discord
            client to know how to handle push notifications better
            for you in case you are actually idle and not lying.
        shard_id: Optional[int]
            The shard_id to change the presence to. If not specified
            or ``None``, then it will change the presence of every
            shard the bot can see.

        Raises
        ------
        InvalidArgument
            If the ``activity`` parameter is not of proper type.
        """

        if status is None:
            status = 'online'
            status_enum = Status.online
        elif status is Status.offline:
            status = 'invisible'
            status_enum = Status.offline
        else:
            status_enum = status
            status = str(status)

        if shard_id is None:
            for shard in self.shards.values():
                yield from shard.ws.change_presence(activity=activity, status=status, afk=afk)

            guilds = self._connection.guilds
        else:
            shard = self.shards[shard_id]
            yield from shard.ws.change_presence(activity=activity, status=status, afk=afk)
            guilds = [g for g in self._connection.guilds if g.shard_id == shard_id]

        for guild in guilds:
            me = guild.me
            if me is None:
                continue

            me.activity = activity
            me.status = status_enum
