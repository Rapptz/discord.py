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
import logging

import aiohttp

from .state import AutoShardedConnectionState
from .client import Client
from .backoff import ExponentialBackoff
from .gateway import *
from .errors import (
    ClientException,
    HTTPException,
    GatewayNotFound,
    ConnectionClosed,
)

from .enums import Status

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional, Tuple, Type, Union

if TYPE_CHECKING:
    from .gateway import DiscordWebSocket
    from .activity import BaseActivity
    from .flags import Intents

__all__ = (
    'ShardedResumeState',
    'AutoShardedClient',
    'ShardInfo',
)

_log = logging.getLogger(__name__)


class ShardedResumeState:
    """This is the sharded version of :class:`ResumeState`.

    See also: :meth:`AutoShardedClient.connect`.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Serializes the resume state to a :class:`str`, containing only
            alphanumerics, ``:`` and ``,``.

    Parameters
    ----------
    data: ::class:`str`
        The data to deserialize.

    Attributes
    ----------
    state: Mapping[:class:`int`, :class:`ResumeState`]
        A mapping of shard IDs to their respective resume states.
    """

    __slots__ = ('states',)

    def __init__(self, data: Union[str, Mapping[int, ResumeState]]) -> None:
        self.states: Mapping[int, ResumeState]
        if isinstance(data, str):
            self.states = {}
            for row in data.split(','):
                try:
                    sid, session_id, seq = row.split(':')
                    shard_id = int(sid)
                    sequence = int(seq)
                    self.states[shard_id] = ResumeState(session_id, sequence)
                except ValueError:
                    # Worst case the client will just have to re-identify, so we can just ignore invalid data
                    pass
        else:
            self.states = dict(data)

    def __str__(self) -> str:
        return ','.join(f'{shard_id}:{resume_state}' for shard_id, resume_state in self.states.items())

    def __repr__(self) -> str:
        return f'ShardedResumeState({self.states!r})'


class EventType:
    close = 0
    reconnect = 1
    resume = 2
    reidentify = 3
    finish = 4
    terminate = 5
    clean_close = 6


class EventItem:
    __slots__ = ('type', 'shard', 'error', 'resume_state')

    def __init__(
        self,
        etype: int,
        shard: Optional['Shard'],
        error: Optional[Exception],
        resume_state: Optional[ResumeState] = None,
    ) -> None:
        self.type: int = etype
        self.shard: Optional['Shard'] = shard
        self.error: Optional[Exception] = error
        self.resume_state: Optional[ResumeState] = resume_state

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EventItem):
            return NotImplemented
        return self.type < other.type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventItem):
            return NotImplemented
        return self.type == other.type

    def __hash__(self) -> int:
        return hash(self.type)


class Shard:
    def __init__(self, ws: DiscordWebSocket, client: AutoShardedClient, queue_put: Callable[[EventItem], None]) -> None:
        self.ws: DiscordWebSocket = ws
        self._client: Client = client
        self._dispatch: Callable[..., None] = client.dispatch
        self._queue_put: Callable[[EventItem], None] = queue_put
        self._disconnect: bool = False
        self._reconnect = client._reconnect
        self._backoff: ExponentialBackoff = ExponentialBackoff()
        self._task: Optional[asyncio.Task] = None
        self._handled_exceptions: Tuple[Type[Exception], ...] = (
            OSError,
            HTTPException,
            GatewayNotFound,
            ConnectionClosed,
            aiohttp.ClientError,
            asyncio.TimeoutError,
        )

    @property
    def id(self) -> int:
        # DiscordWebSocket.shard_id is set in the from_client classmethod
        return self.ws.shard_id  # type: ignore

    def launch(self) -> None:
        self._task = self._client.loop.create_task(self.worker())

    def _cancel_task(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()

    async def close(self, *, resumable: bool = False) -> None:
        self._cancel_task()
        await self.ws.close(code=4000 if resumable else 1000)

    async def disconnect(self) -> None:
        await self.close(resumable=False)
        self._dispatch('shard_disconnect', self.id)

    async def _handle_disconnect(self, exc: Exception) -> None:
        self._dispatch('disconnect')
        self._dispatch('shard_disconnect', self.id)

        resume_state = self.ws.resume_state()

        try:
            self._client._raise_if_fatal(exc, self._reconnect)
        except Exception as exc:
            self._queue_put(EventItem(EventType.terminate, self, exc))
            return

        if not self._reconnect:
            self._queue_put(EventItem(EventType.close, self, exc))
            return

        if self._client.is_closed():
            self._queue_put(EventItem(EventType.finish, self, None, resume_state))
            return

        if self._client._should_delay(exc):
            retry = self._backoff.delay()
            _log.error('Attempting to reconnect Shard ID %s in %.2f seconds', self.id, retry, exc_info=exc)
            await asyncio.sleep(retry)
        else:
            _log.error('Attempting to reconnect Shard ID %s', self.id, exc_info=exc)
        self._queue_put(EventItem(EventType.reconnect, self, exc, resume_state))

    async def worker(self) -> None:
        while not self._client.is_closed():
            try:
                await self.ws.poll_event()
            except ReconnectWebSocket as e:
                self._queue_put(EventItem(EventType.reidentify, self, e))
                break
            except self._handled_exceptions as e:
                await self._handle_disconnect(e)
                break
            except asyncio.CancelledError:
                self._queue_put(EventItem(EventType.finish, self, None, self.ws.resume_state()))
                break
            except Exception as e:
                self._queue_put(EventItem(EventType.terminate, self, e))
                break

    async def reidentify(self, exc: ReconnectWebSocket) -> None:
        self._cancel_task()
        self._dispatch('disconnect')
        self._dispatch('shard_disconnect', self.id)
        _log.info('Gateway requested to reconnect Shard ID %s %s resume', self.id, 'with' if exc.resume_state else 'without')
        await self.reconnect(exc.resume_state)

    async def reconnect(self, resume_state: Optional[ResumeState] = None) -> None:
        self._cancel_task()
        try:
            coro = DiscordWebSocket.from_client(self._client, shard_id=self.id, resume_state=resume_state)
            self.ws = await asyncio.wait_for(coro, timeout=60.0)
        except self._handled_exceptions as e:
            await self._handle_disconnect(e)
        except asyncio.CancelledError:
            return
        except Exception as e:
            self._queue_put(EventItem(EventType.terminate, self, e))
        else:
            self.launch()


class ShardInfo:
    """A class that gives information and control over a specific shard.

    You can retrieve this object via :meth:`AutoShardedClient.get_shard`
    or :attr:`AutoShardedClient.shards`.

    .. versionadded:: 1.4

    Attributes
    ------------
    id: :class:`int`
        The shard ID for this shard.
    shard_count: Optional[:class:`int`]
        The shard count for this cluster. If this is ``None`` then the bot has not started yet.
    """

    __slots__ = ('_parent', 'id', 'shard_count')

    def __init__(self, parent: Shard, shard_count: Optional[int]) -> None:
        self._parent: Shard = parent
        self.id: int = parent.id
        self.shard_count: Optional[int] = shard_count

    def is_closed(self) -> bool:
        """:class:`bool`: Whether the shard connection is currently closed."""
        return not self._parent.ws.open

    async def disconnect(self) -> None:
        """|coro|

        Disconnects a shard. When this is called, the shard connection will no
        longer be open.

        If the shard is already disconnected this does nothing.
        """
        if self.is_closed():
            return

        await self._parent.disconnect()

    async def reconnect(self) -> None:
        """|coro|

        Disconnects and then connects the shard again.
        """
        if not self.is_closed():
            await self._parent.disconnect()
        await self._parent.reconnect()

    async def connect(self) -> None:
        """|coro|

        Connects a shard. If the shard is already connected this does nothing.
        """
        if not self.is_closed():
            return

        await self._parent.reconnect()

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds for this shard."""
        return self._parent.ws.latency

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        .. versionadded:: 1.6
        """
        return self._parent.ws.is_ratelimited()


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

    .. container:: operations

        .. describe:: async with x

            Asynchronously initialises the client and automatically cleans up.

            .. versionadded:: 2.0

    Attributes
    ------------
    shard_ids: Optional[List[:class:`int`]]
        An optional list of shard_ids to launch the shards with.
    """

    if TYPE_CHECKING:
        _connection: AutoShardedConnectionState

    def __init__(self, *args: Any, intents: Intents, **kwargs: Any) -> None:
        kwargs.pop('shard_id', None)
        self.shard_ids: Optional[List[int]] = kwargs.pop('shard_ids', None)
        super().__init__(*args, intents=intents, **kwargs)

        if self.shard_ids is not None:
            if self.shard_count is None:
                raise ClientException('When passing manual shard_ids, you must provide a shard_count.')
            elif not isinstance(self.shard_ids, (list, tuple)):
                raise ClientException('shard_ids parameter must be a list or a tuple.')

        # instead of a single websocket, we have multiple
        # the key is the shard_id
        self.__shards = {}
        self._connection._get_websocket = self._get_websocket
        self._connection._get_client = lambda: self

    def _get_websocket(self, guild_id: Optional[int] = None, *, shard_id: Optional[int] = None) -> DiscordWebSocket:
        if shard_id is None:
            # guild_id won't be None if shard_id is None and shard_count won't be None here
            shard_id = (guild_id >> 22) % self.shard_count  # type: ignore
        return self.__shards[shard_id].ws

    def _get_state(self, **options: Any) -> AutoShardedConnectionState:
        return AutoShardedConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            **options,
        )

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This operates similarly to :meth:`Client.latency` except it uses the average
        latency of every shard's latency. To get a list of shard latency, check the
        :attr:`latencies` property. Returns ``nan`` if there are no shards ready.
        """
        if not self.__shards:
            return float('nan')
        return sum(latency for _, latency in self.latencies) / len(self.__shards)

    @property
    def latencies(self) -> List[Tuple[int, float]]:
        """List[Tuple[:class:`int`, :class:`float`]]: A list of latencies between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This returns a list of tuples with elements ``(shard_id, latency)``.
        """
        return [(shard_id, shard.ws.latency) for shard_id, shard in self.__shards.items()]

    def get_shard(self, shard_id: int, /) -> Optional[ShardInfo]:
        """
        Gets the shard information at a given shard ID or ``None`` if not found.

        .. versionchanged:: 2.0

            ``shard_id`` parameter is now positional-only.

        Returns
        --------
        Optional[:class:`ShardInfo`]
            Information about the shard with given ID. ``None`` if not found.
        """
        try:
            parent = self.__shards[shard_id]
        except KeyError:
            return None
        else:
            return ShardInfo(parent, self.shard_count)

    @property
    def shards(self) -> Dict[int, ShardInfo]:
        """Mapping[int, :class:`ShardInfo`]: Returns a mapping of shard IDs to their respective info object."""
        return {shard_id: ShardInfo(parent, self.shard_count) for shard_id, parent in self.__shards.items()}

    async def launch_shard(
        self, gateway: str, shard_id: int, resume_state: Optional[ResumeState] = None, *, initial: bool = False
    ) -> None:
        try:
            coro = DiscordWebSocket.from_client(
                self, initial=initial, gateway=gateway, shard_id=shard_id, resume_state=resume_state
            )
            ws = await asyncio.wait_for(coro, timeout=180.0)
        except Exception:
            _log.exception('Failed to connect for shard_id: %s. Retrying...', shard_id)
            await asyncio.sleep(5.0)
            return await self.launch_shard(gateway, shard_id, resume_state)

        # keep reading the shard while others connect
        self.__shards[shard_id] = ret = Shard(ws, self, self.__queue.put_nowait)
        ret.launch()

    async def launch_shards(self, resume_state: Optional[ShardedResumeState] = None) -> None:
        if self.shard_count is None:
            self.shard_count: int
            self.shard_count, gateway = await self.http.get_bot_gateway()
        else:
            gateway = await self.http.get_gateway()

        self._connection.shard_count = self.shard_count

        shard_ids = self.shard_ids or range(self.shard_count)
        self._connection.shard_ids = shard_ids

        for shard_id in shard_ids:
            initial = shard_id == shard_ids[0]
            state = resume_state.states.get(shard_id) if resume_state else None
            await self.launch_shard(gateway, shard_id, state, initial=initial)

    async def _async_setup_hook(self) -> None:
        await super()._async_setup_hook()
        self.__queue = asyncio.PriorityQueue()

    async def connect(
        self, *, reconnect: bool = True, resume_state: Optional[ShardedResumeState] = None
    ) -> ShardedResumeState:
        """|coro|
        Creates a websocket connection and lets the websocket listen
        to messages from Discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        -----------
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).
        resume_state: Optional[:class:`ShardedResumeState`]
            If provided, we will attempt to resume WebSocket connections
            using the given states.

            .. versionadded:: 2.0

        Returns
        -------
        :class:`ShardedResumeState`
            Returns the data necessary to resume WebSocket connections,
            except those that were closed in a way that does not allow resuming.

            .. versionadded:: 2.0

        Raises
        -------
        GatewayNotFound
            If the gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        ConnectionClosed
            The websocket connection has been terminated.
        """
        if resume_state is not None and not isinstance(resume_state, ShardedResumeState):
            raise TypeError(f'resume_state must be a ShardedResumeState not {resume_state.__class__!r}')

        self._reconnect = reconnect
        await self.launch_shards(resume_state)

        states = {}

        while True:
            item = await self.__queue.get()
            if item.type == EventType.close:
                await self.close(resumable=True)
            elif item.type == EventType.reidentify:
                await item.shard.reidentify(item.error)
            elif item.type == EventType.reconnect:
                await item.shard.reconnect(item.resume_state)
            elif item.type == EventType.finish:
                if item.resume_state:
                    states[item.shard.id] = item.resume_state
            elif item.type == EventType.terminate:
                await self.close()
                raise item.error
            elif item.type == EventType.clean_close:
                break

        return ShardedResumeState(states)

    async def close(self, *, resumable: bool = False) -> None:
        """|coro|

        Closes the connection to Discord.

        Parameters
        ----------
        resumable: :class:`bool`
            Whether WebSocket connections should be closed in a way that allows resuming them later.

            .. versionadded:: 2.0

            .. seealso:: :class:`ShardedResumeState`
        """
        if self.is_closed():
            return

        try:
            self._closed = True

            for vc in self.voice_clients:
                try:
                    await vc.disconnect(force=True)
                except Exception:
                    pass

            to_close = [
                asyncio.ensure_future(shard.close(resumable=resumable), loop=self.loop) for shard in self.__shards.values()
            ]
            if to_close:
                await asyncio.wait(to_close)

            await self.http.close()
        finally:
            self.__queue.put_nowait(EventItem(EventType.clean_close, None, None))

    async def change_presence(
        self,
        *,
        activity: Optional[BaseActivity] = None,
        status: Optional[Status] = None,
        shard_id: Optional[int] = None,
    ) -> None:
        """|coro|

        Changes the client's presence.

        Example: ::

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        .. versionchanged:: 2.0
            Removed the ``afk`` keyword-only parameter.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

        Parameters
        ----------
        activity: Optional[:class:`BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`Status.online` is used.
        shard_id: Optional[:class:`int`]
            The shard_id to change the presence to. If not specified
            or ``None``, then it will change the presence of every
            shard the bot can see.

        Raises
        ------
        TypeError
            If the ``activity`` parameter is not of proper type.
        """

        if status is None:
            status_value = 'online'
            status_enum = Status.online
        elif status is Status.offline:
            status_value = 'invisible'
            status_enum = Status.offline
        else:
            status_enum = status
            status_value = str(status)

        if shard_id is None:
            for shard in self.__shards.values():
                await shard.ws.change_presence(activity=activity, status=status_value)

            guilds = self._connection.guilds
        else:
            shard = self.__shards[shard_id]
            await shard.ws.change_presence(activity=activity, status=status_value)
            guilds = [g for g in self._connection.guilds if g.shard_id == shard_id]

        activities = () if activity is None else (activity,)
        for guild in guilds:
            me = guild.me
            if me is None:
                continue

            # Member.activities is typehinted as Tuple[ActivityType, ...], we may be setting it as Tuple[BaseActivity, ...]
            me.activities = activities  # type: ignore
            me.status = status_enum

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        This implementation checks if any of the shards are rate limited.
        For more granular control, consider :meth:`ShardInfo.is_ws_ratelimited`.

        .. versionadded:: 1.6
        """
        return any(shard.ws.is_ratelimited() for shard in self.__shards.values())
