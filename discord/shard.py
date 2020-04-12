# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2020 Rapptz

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

import asyncio
import itertools
import logging

import aiohttp

from .state import AutoShardedConnectionState
from .client import Client
from .backoff import ExponentialBackoff
from .gateway import *
from .errors import ClientException, InvalidArgument, HTTPException, GatewayNotFound, ConnectionClosed
from . import utils
from .enums import Status

log = logging.getLogger(__name__)

class EventType:
    close = 0
    reconnect = 1
    resume = 2
    identify = 3

class EventItem:
    __slots__ = ('type', 'shard', 'error')

    def __init__(self, etype, shard, error):
        self.type = etype
        self.shard = shard
        self.error = error

    def __lt__(self, other):
        if not isinstance(other, EventItem):
            return NotImplemented
        return self.type < other.type

    def __eq__(self, other):
        if not isinstance(other, EventItem):
            return NotImplemented
        return self.type == other.type

    def __hash__(self):
        return hash(self.type)

class Shard:
    def __init__(self, ws, client):
        self.ws = ws
        self._client = client
        self._dispatch = client.dispatch
        self._queue = client._queue
        self.loop = self._client.loop
        self._disconnect = False
        self._reconnect = client._reconnect
        self._backoff = ExponentialBackoff()
        self._task = None
        self._handled_exceptions = (
            OSError,
            HTTPException,
            GatewayNotFound,
            ConnectionClosed,
            aiohttp.ClientError,
            asyncio.TimeoutError,
        )

    @property
    def id(self):
        return self.ws.shard_id

    def launch(self):
        self._task = self.loop.create_task(self.worker())

    def _cancel_task(self):
        if self._task is not None and not self._task.done():
            self._task.cancel()

    async def close(self):
        self._cancel_task()
        await self.ws.close(code=1000)

    async def _handle_disconnect(self, e):
        self._dispatch('disconnect')
        self._dispatch('shard_disconnect', self.id)
        if not self._reconnect:
            self._queue.put_nowait(EventItem(EventType.close, self, e))
            return

        if self._client.is_closed():
            return

        if isinstance(e, ConnectionClosed):
            if e.code != 1000:
                self._queue.put_nowait(EventItem(EventType.close, self, e))
                return

        retry = self._backoff.delay()
        log.error('Attempting a reconnect for shard ID %s in %.2fs', self.id, retry, exc_info=e)
        await asyncio.sleep(retry)
        self._queue.put_nowait(EventItem(EventType.reconnect, self, e))

    async def worker(self):
        while not self._client.is_closed():
            try:
                await self.ws.poll_event()
            except ReconnectWebSocket as e:
                etype = EventType.resume if e.resume else EventType.identify
                self._queue.put_nowait(EventItem(etype, self, e))
                break
            except self._handled_exceptions as e:
                await self._handle_disconnect(e)
                break

    async def reidentify(self, exc):
        self._cancel_task()
        self._dispatch('disconnect')
        self._dispatch('shard_disconnect', self.id)
        log.info('Got a request to %s the websocket at Shard ID %s.', exc.op, self.id)
        try:
            coro = DiscordWebSocket.from_client(self._client, resume=exc.resume, shard_id=self.id,
                                                session=self.ws.session_id, sequence=self.ws.sequence)
            self.ws = await asyncio.wait_for(coro, timeout=180.0)
        except self._handled_exceptions as e:
            await self._handle_disconnect(e)
        else:
            self.launch()

    async def reconnect(self):
        self._cancel_task()
        try:
            coro = DiscordWebSocket.from_client(self._client, shard_id=self.id)
            self.ws = await asyncio.wait_for(coro, timeout=180.0)
        except self._handled_exceptions as e:
            await self._handle_disconnect(e)
        else:
            self.launch()

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

    If no :attr:`.shard_count` is provided, then the library will use the
    Bot Gateway endpoint call to figure out how many shards to use.

    If a ``shard_ids`` parameter is given, then those shard IDs will be used
    to launch the internal shards. Note that :attr:`.shard_count` must be provided
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

        self._connection = AutoShardedConnectionState(dispatch=self.dispatch,
                                                      handlers=self._handlers, syncer=self._syncer,
                                                      hooks=self._hooks, http=self.http, loop=self.loop, **kwargs)

        # instead of a single websocket, we have multiple
        # the key is the shard_id
        self.shards = {}
        self._connection._get_websocket = self._get_websocket
        self._queue = asyncio.PriorityQueue()

    def _get_websocket(self, guild_id=None, *, shard_id=None):
        if shard_id is None:
            shard_id = (guild_id >> 22) % self.shard_count
        return self.shards[shard_id].ws

    @property
    def latency(self):
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This operates similarly to :meth:`Client.latency` except it uses the average
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

    async def request_offline_members(self, *guilds):
        r"""|coro|

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
        \*guilds: :class:`Guild`
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
            await self._connection.request_offline_members(sub_guilds, shard_id=shard_id)

    async def launch_shard(self, gateway, shard_id, *, initial=False):
        try:
            coro = DiscordWebSocket.from_client(self, initial=initial, gateway=gateway, shard_id=shard_id)
            ws = await asyncio.wait_for(coro, timeout=180.0)
        except Exception:
            log.exception('Failed to connect for shard_id: %s. Retrying...', shard_id)
            await asyncio.sleep(5.0)
            return await self.launch_shard(gateway, shard_id)

        # keep reading the shard while others connect
        self.shards[shard_id] = ret = Shard(ws, self)
        ret.launch()

    async def launch_shards(self):
        if self.shard_count is None:
            self.shard_count, gateway = await self.http.get_bot_gateway()
        else:
            gateway = await self.http.get_gateway()

        self._connection.shard_count = self.shard_count

        shard_ids = self.shard_ids if self.shard_ids else range(self.shard_count)
        self._connection.shard_ids = shard_ids

        for shard_id in shard_ids:
            initial = shard_id == shard_ids[0]
            await self.launch_shard(gateway, shard_id, initial=initial)

        self._connection.shards_launched.set()

    async def connect(self, *, reconnect=True):
        self._reconnect = reconnect
        await self.launch_shards()

        while not self.is_closed():
            item = await self._queue.get()
            if item.type == EventType.close:
                await self.close()
                if isinstance(item.error, ConnectionClosed) and item.error.code != 1000:
                    raise item.error
                return
            elif item.type in (EventType.identify, EventType.resume):
                await item.shard.reidentify(item.error)
            elif item.type == EventType.reconnect:
                await item.shard.reconnect()

    async def close(self):
        """|coro|

        Closes the connection to Discord.
        """
        if self.is_closed():
            return

        self._closed = True

        for vc in self.voice_clients:
            try:
                await vc.disconnect()
            except Exception:
                pass

        to_close = [asyncio.ensure_future(shard.close(), loop=self.loop) for shard in self.shards.values()]
        if to_close:
            await asyncio.wait(to_close)

        await self.http.close()

    async def change_presence(self, *, activity=None, status=None, afk=False, shard_id=None):
        """|coro|

        Changes the client's presence.

        Example: ::

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        Parameters
        ----------
        activity: Optional[:class:`BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`Status.online` is used.
        afk: :class:`bool`
            Indicates if you are going AFK. This allows the discord
            client to know how to handle push notifications better
            for you in case you are actually idle and not lying.
        shard_id: Optional[:class:`int`]
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
                await shard.ws.change_presence(activity=activity, status=status, afk=afk)

            guilds = self._connection.guilds
        else:
            shard = self.shards[shard_id]
            await shard.ws.change_presence(activity=activity, status=status, afk=afk)
            guilds = [g for g in self._connection.guilds if g.shard_id == shard_id]

        activities = () if activity is None else (activity,)
        for guild in guilds:
            me = guild.me
            if me is None:
                continue

            me.activities = activities
            me.status = status_enum
