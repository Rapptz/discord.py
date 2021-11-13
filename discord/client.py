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
import signal
import sys
import traceback
from typing import Any, Callable, Coroutine, Dict, Generator, List, Optional, Sequence, TYPE_CHECKING, Tuple, TypeVar, Union

import aiohttp

from .user import User, ClientUser, Profile, Note
from .invite import Invite
from .template import Template
from .widget import Widget
from .guild import Guild
from .emoji import Emoji
from .channel import _private_channel_factory, _threaded_channel_factory, GroupChannel, PartialMessageable
from .enums import ChannelType, Status, VoiceRegion, try_enum
from .mentions import AllowedMentions
from .errors import *
from .gateway import *
from .gateway import ConnectionClosed
from .activity import ActivityTypes, BaseActivity, create_activity
from .voice_client import VoiceClient
from .http import HTTPClient
from .state import ConnectionState
from . import utils
from .utils import MISSING
from .object import Object
from .backoff import ExponentialBackoff
from .webhook import Webhook
from .iterators import GuildIterator
from .appinfo import AppInfo
from .stage_instance import StageInstance
from .threads import Thread
from .sticker import GuildSticker, StandardSticker, StickerPack, _sticker_factory

if TYPE_CHECKING:
    from .abc import SnowflakeTime, PrivateChannel, GuildChannel, Snowflake
    from .channel import DMChannel
    from .message import Message
    from .member import Member
    from .voice_client import VoiceProtocol

__all__ = (
    'Client',
)

Coro = TypeVar('Coro', bound=Callable[..., Coroutine[Any, Any, Any]])


_log = logging.getLogger(__name__)

def _cancel_tasks(loop: asyncio.AbstractEventLoop) -> None:
    tasks = {t for t in asyncio.all_tasks(loop=loop) if not t.done()}

    if not tasks:
        return

    _log.info('Cleaning up after %d tasks.', len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    _log.info('All tasks finished cancelling.')

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during Client.run shutdown.',
                'exception': task.exception(),
                'task': task
            })

def _cleanup_loop(loop: asyncio.AbstractEventLoop) -> None:
    try:
        _cancel_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        _log.info('Closing the event loop.')
        loop.close()

class Client:
    r"""Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client`.

    Parameters
    -----------
    max_messages: Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to ``1000``. Passing in ``None`` disables the message cache.

        .. versionchanged:: 1.3
            Allow disabling the message cache and change the default size to ``1000``.
    loop: Optional[:class:`asyncio.AbstractEventLoop`]
        The :class:`asyncio.AbstractEventLoop` to use for asynchronous operations.
        Defaults to ``None``, in which case the default event loop is used via
        :func:`asyncio.get_event_loop()`.
    connector: Optional[:class:`aiohttp.BaseConnector`]
        The connector to use for connection pooling.
    proxy: Optional[:class:`str`]
        Proxy URL.
    proxy_auth: Optional[:class:`aiohttp.BasicAuth`]
        An object that represents proxy HTTP Basic Authorization.
    member_cache_flags: :class:`MemberCacheFlags`
        Allows for finer control over how the library caches members.
        If not given, defaults to cache as much as possible.

        .. versionadded:: 1.5
    chunk_guilds_at_startup: :class:`bool`
        Indicates if :func:`.on_ready` should be delayed to chunk all guilds
        at start-up if necessary. This operation is incredibly slow for large
        amounts of guilds. The default is ``True``.

        .. versionadded:: 1.5
    guild_subscription_options: :class:`GuildSubscriptionOptions`
        Allows for control over the library's auto-subscribing.
        If not given, defaults to off.

        .. versionadded:: 1.9
    request_guilds: :class:`bool`
        Whether to request guilds at startup (behaves similarly to the old
        guild_subscriptions option). Defaults to True.

        .. versionadded:: 1.10
    status: Optional[:class:`.Status`]
        A status to start your presence with upon logging on to Discord.
    activity: Optional[:class:`.BaseActivity`]
        An activity to start your presence with upon logging on to Discord.
    allowed_mentions: Optional[:class:`AllowedMentions`]
        Control how the client handles mentions by default on every message sent.

        .. versionadded:: 1.4
    heartbeat_timeout: :class:`float`
        The maximum numbers of seconds before timing out and restarting the
        WebSocket in the case of not receiving a HEARTBEAT_ACK. Useful if
        processing the initial packets take too long to the point of disconnecting
        you. The default timeout is 60 seconds.
    assume_unsync_clock: :class:`bool`
        Whether to assume the system clock is unsynced. This applies to the ratelimit handling
        code. If this is set to ``True``, the default, then the library uses the time to reset
        a rate limit bucket given by Discord. If this is ``False`` then your system clock is
        used to calculate how long to sleep for. If this is set to ``False`` it is recommended to
        sync your system clock to Google's NTP server.

        .. versionadded:: 1.3
    enable_debug_events: :class:`bool`
        Whether to enable events that are useful only for debugging gateway related information.

        Right now this involves :func:`on_socket_raw_receive` and :func:`on_socket_raw_send`. If
        this is ``False`` then those events will not be dispatched (due to performance considerations).
        To enable these events, this must be set to ``True``. Defaults to ``False``.

        .. versionadded:: 2.0

    Attributes
    -----------
    ws
        The websocket gateway the client is currently connected to. Could be ``None``.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the client uses for asynchronous operations.
    """
    def __init__(
        self,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        **options: Any,
    ):
        # Set in the connect method
        self.ws: DiscordWebSocket = None  # type: ignore
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
        self._listeners: Dict[str, List[Tuple[asyncio.Future, Callable[..., bool]]]] = {}

        connector: Optional[aiohttp.BaseConnector] = options.pop('connector', None)
        proxy: Optional[str] = options.pop('proxy', None)
        proxy_auth: Optional[aiohttp.BasicAuth] = options.pop('proxy_auth', None)
        unsync_clock: bool = options.pop('assume_unsync_clock', True)
        self.http: HTTPClient = HTTPClient(connector, proxy=proxy, proxy_auth=proxy_auth, unsync_clock=unsync_clock, loop=self.loop)

        self._handlers: Dict[str, Callable] = {
            'ready': self._handle_ready,
            'connect': self._handle_connect
        }

        self._hooks: Dict[str, Callable] = {
            'before_identify': self._call_before_identify_hook
        }

        self._enable_debug_events: bool = options.pop('enable_debug_events', False)
        self._connection: ConnectionState = self._get_state(**options)
        self._closed: bool = False
        self._ready: asyncio.Event = asyncio.Event()

        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            _log.warning('PyNaCl is not installed, voice will NOT be supported.')

    # Internals

    def _get_state(self, **options: Any) -> ConnectionState:
        return ConnectionState(dispatch=self.dispatch, handlers=self._handlers,
                               hooks=self._hooks, http=self.http, loop=self.loop,
                               client=self, **options)

    def _handle_ready(self) -> None:
        self._ready.set()

    def _handle_connect(self) -> None:
        state = self._connection
        activity = create_activity(state._activity)
        status = state._status and try_enum(Status, state._status)
        if status is not None or activity is not None:
            self.loop.create_task(self.change_presence(activity=activity, status=status))

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This could be referred to as the Discord WebSocket protocol latency.
        """
        ws = self.ws
        return float('nan') if not ws else ws.latency

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        .. versionadded:: 1.6
        """
        if self.ws:
            return self.ws.is_ratelimited()
        return False

    @property
    def user(self) -> Optional[ClientUser]:
        """Optional[:class:`.ClientUser`]: Represents the connected client. ``None`` if not logged in."""
        return self._connection.user

    @property
    def guilds(self) -> List[Guild]:
        """List[:class:`.Guild`]: The guilds that the connected client is a member of."""
        return self._connection.guilds

    @property
    def emojis(self) -> List[Emoji]:
        """List[:class:`.Emoji`]: The emojis that the connected client has."""
        return self._connection.emojis

    @property
    def stickers(self) -> List[GuildSticker]:
        """List[:class:`.GuildSticker`]: The stickers that the connected client has.

        .. versionadded:: 2.0
        """
        return self._connection.stickers

    @property
    def cached_messages(self) -> Sequence[Message]:
        """Sequence[:class:`.Message`]: Read-only list of messages the connected client has cached.

        .. versionadded:: 1.1
        """
        return utils.SequenceProxy(self._connection._messages or [])

    @property
    def private_channels(self) -> List[PrivateChannel]:
        """List[:class:`.abc.PrivateChannel`]: The private channels that the connected client is participating on."""
        return self._connection.private_channels

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        """List[:class:`.VoiceProtocol`]: Represents a list of voice connections.

        These are usually :class:`.VoiceClient` instances.
        """
        return self._connection.voice_clients

    def is_ready(self) -> bool:
        """:class:`bool`: Specifies if the client's internal cache is ready for use."""
        return self._ready.is_set()

    async def _run_event(self, coro: Callable[..., Coroutine[Any, Any, Any]], event_name: str, *args: Any, **kwargs: Any) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(self, coro: Callable[..., Coroutine[Any, Any, Any]], event_name: str, *args: Any, **kwargs: Any) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        return asyncio.create_task(wrapped, name=f'discord.py: {event_name}')

    def dispatch(self, event: str, *args: Any, **kwargs: Any) -> None:
        _log.debug('Dispatching event %s.', event)
        method = 'on_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """|coro|

        The default error handler provided by the client.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.
        """
        print(f'Ignoring exception in {event_method}', file=sys.stderr)
        traceback.print_exc()

    # Hooks

    async def _call_before_identify_hook(self, *, initial: bool = False) -> None:
        # This hook is an internal hook that actually calls the public one
        # It allows the library to have its own hook without stepping on the
        # toes of those who need to override their own hook
        await self.before_identify_hook(initial=initial)

    async def before_identify_hook(self, *, initial: bool = False) -> None:
        """|coro|

        A hook that is called before IDENTIFYing a session. This is useful
        if you wish to have more control over the synchronization of multiple
        IDENTIFYing clients.

        The default implementation does nothing.

        .. versionadded:: 1.4

        Parameters
        ------------
        initial: :class:`bool`
            Whether this IDENTIFY is the first initial IDENTIFY.
        """
        pass

    # Login state management

    async def login(self, token: str) -> None:
        """|coro|

        Logs in the client with the specified credentials.

        .. warning::

            Logging on with a user token is unfortunately against the Discord
            `Terms of Service <https://support.discord.com/hc/en-us/articles/115002192352>`_
            and doing so might potentially get your account banned.
            Use this at your own risk.

        Parameters
        -----------
        token: :class:`str`
            The authentication token.

        Raises
        ------
        :exc:`.LoginFailure`
            The wrong credentials are passed.
        :exc:`.HTTPException`
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """

        _log.info('Logging in using static token.')

        state = self._connection
        data = await state.http.static_login(token.strip())
        state.analytics_token = data.get('analytics_token', '')
        self._connection.user = ClientUser(state=state, data=data)

    async def connect(self, *, reconnect: bool = True) -> None:
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
            disconnects that lead to bad state will not be handled
            (such as bad tokens).

        Raises
        -------
        :exc:`.GatewayNotFound`
            If the gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        :exc:`.ConnectionClosed`
            The websocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        ws_params = {
            'initial': True,
        }
        while not self.is_closed():
            try:
                coro = DiscordWebSocket.from_client(self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params['initial'] = False
                while True:
                    await self.ws.poll_event()
            except ReconnectWebSocket as e:
                _log.info('Got a request to %s the websocket.', e.op)
                self.dispatch('disconnect')
                ws_params.update(sequence=self.ws.sequence, resume=e.resume, session=self.ws.session_id)
                continue
            except (OSError,
                    HTTPException,
                    GatewayNotFound,
                    ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError) as exc:

                self.dispatch('disconnect')
                if not reconnect:
                    await self.close()
                    if isinstance(exc, ConnectionClosed) and exc.code == 1000:
                        # Clean close, don't re-raise this
                        return
                    raise

                if self.is_closed():
                    return

                # If we get connection reset by peer then try to RESUME
                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(sequence=self.ws.sequence, initial=False, resume=True, session=self.ws.session_id)
                    continue

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, etc)
                # Sometimes, discord sends us 1000 for unknown reasons so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(exc, ConnectionClosed):
                    if exc.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                _log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                # Always try to RESUME the connection
                # If the connection is not RESUME-able then the gateway will invalidate the session
                # This is apparently what the official Discord client does
                ws_params.update(sequence=self.ws.sequence, resume=True, session=self.ws.session_id)

    async def close(self) -> None:
        """|coro|

        Closes the connection to Discord.
        """
        if self._closed:
            return

        self._closed = True

        for voice in self.voice_clients:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # If an error happens during disconnects, disregard it
                pass

        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)

        await self.http.close()
        self._ready.clear()

    def clear(self) -> None:
        """Clears the internal state of the bot.

        After this, the bot can be considered "re-opened", i.e. :meth:`is_closed`
        and :meth:`is_ready` both return ``False`` along with the bot's internal
        cache cleared.
        """
        self._closed = False
        self._ready.clear()
        self._connection.clear()
        self.http.recreate()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        """
        await self.login(token)
        await self.connect(reconnect=reconnect)

    def run(self, *args: Any, **kwargs: Any) -> None:
        """A blocking call that abstracts away the event loop
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(close())
                # cancel all tasks lingering
            finally:
                loop.close()

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.
        """
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass

        async def runner():
            try:
                await self.start(*args, **kwargs)
            finally:
                if not self.is_closed():
                    await self.close()

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            _log.info('Received signal to terminate bot and event loop.')
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            _log.info('Cleaning up tasks.')
            _cleanup_loop(loop)

        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                # I am unsure why this gets raised here but suppress it anyway
                return None

    # Properties

    def is_closed(self) -> bool:
        """:class:`bool`: Indicates if the websocket connection is closed."""
        return self._closed

    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        """Optional[:class:`VoiceProtocol`]: Returns the :class:`VoiceProtocol` associated with private calls, if any."""
        return self._connection._get_voice_client(self.user.id)

    @property
    def activity(self) -> Optional[ActivityTypes]:
        """Optional[:class:`.BaseActivity`]: The activity being used upon
        logging in.
        """
        return create_activity(self._connection._activity)

    @activity.setter
    def activity(self, value: Optional[ActivityTypes]) -> None:
        if value is None:
            self._connection._activity = None
        elif isinstance(value, BaseActivity):
            # ConnectionState._activity is typehinted as ActivityPayload, we're passing Dict[str, Any]
            self._connection._activity = value.to_dict() # type: ignore
        else:
            raise TypeError('activity must derive from BaseActivity')
    
    @property
    def status(self):
        """:class:`.Status`:
        The status being used upon logging on to Discord.

        .. versionadded: 2.0
        """
        if self._connection._status in set(state.value for state in Status):
            return Status(self._connection._status)
        return Status.online

    @status.setter
    def status(self, value):
        if value is Status.offline:
            self._connection._status = 'invisible'
        elif isinstance(value, Status):
            self._connection._status = str(value)
        else:
            raise TypeError('status must derive from Status')

    @property
    def allowed_mentions(self) -> Optional[AllowedMentions]:
        """Optional[:class:`~discord.AllowedMentions`]: The allowed mention configuration.

        .. versionadded:: 1.4
        """
        return self._connection.allowed_mentions

    @allowed_mentions.setter
    def allowed_mentions(self, value: Optional[AllowedMentions]) -> None:
        if value is None or isinstance(value, AllowedMentions):
            self._connection.allowed_mentions = value
        else:
            raise TypeError(f'allowed_mentions must be AllowedMentions not {value.__class__!r}')

    # Helpers/Getters

    @property
    def users(self) -> List[User]:
        """List[:class:`~discord.User`]: Returns a list of all the users the bot can see."""
        return list(self._connection._users.values())

    def get_channel(self, id: int, /) -> Optional[Union[GuildChannel, Thread, PrivateChannel]]:
        """Returns a channel or thread with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[Union[:class:`.abc.GuildChannel`, :class:`.Thread`, :class:`.abc.PrivateChannel`]]
            The returned channel or ``None`` if not found.
        """
        return self._connection.get_channel(id)

    def get_partial_messageable(self, id: int, *, type: Optional[ChannelType] = None) -> PartialMessageable:
        """Returns a partial messageable with the given channel ID.

        This is useful if you have a channel_id but don't want to do an API call
        to send messages to it.
        
        .. versionadded:: 2.0

        Parameters
        -----------
        id: :class:`int`
            The channel ID to create a partial messageable for.
        type: Optional[:class:`.ChannelType`]
            The underlying channel type for the partial messageable.

        Returns
        --------
        :class:`.PartialMessageable`
            The partial messageable
        """
        return PartialMessageable(state=self._connection, id=id, type=type)

    def get_stage_instance(self, id: int, /) -> Optional[StageInstance]:
        """Returns a stage instance with the given stage channel ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`.StageInstance`]
            The returns stage instance of ``None`` if not found.
        """
        from .channel import StageChannel

        channel = self._connection.get_channel(id)

        if isinstance(channel, StageChannel):
            return channel.instance

    def get_guild(self, id: int, /) -> Optional[Guild]:
        """Returns a guild with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`.Guild`]
            The guild or ``None`` if not found.
        """
        return self._connection._get_guild(id)

    def get_user(self, id: int, /) -> Optional[User]:
        """Returns a user with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`~discord.User`]
            The user or ``None`` if not found.
        """
        return self._connection.get_user(id)

    def get_emoji(self, id: int, /) -> Optional[Emoji]:
        """Returns an emoji with the given ID.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`.Emoji`]
            The custom emoji or ``None`` if not found.
        """
        return self._connection.get_emoji(id)

    def get_sticker(self, id: int, /) -> Optional[GuildSticker]:
        """Returns a guild sticker with the given ID.

        .. versionadded:: 2.0

        .. note::

            To retrieve standard stickers, use :meth:`.fetch_sticker`.
            or :meth:`.fetch_sticker_packs`.

        Returns
        --------
        Optional[:class:`.GuildSticker`]
            The sticker or ``None`` if not found.
        """
        return self._connection.get_sticker(id)

    def get_all_channels(self) -> Generator[GuildChannel, None, None]:
        """A generator that retrieves every :class:`.abc.GuildChannel` the client can 'access'.

        This is equivalent to: ::

            for guild in client.guilds:
                for channel in guild.channels:
                    yield channel

        .. note::

            Just because you receive a :class:`.abc.GuildChannel` does not mean that
            you can communicate in said channel. :meth:`.abc.GuildChannel.permissions_for` should
            be used for that.

        Yields
        ------
        :class:`.abc.GuildChannel`
            A channel the client can 'access'.
        """

        for guild in self.guilds:
            yield from guild.channels

    def get_all_members(self) -> Generator[Member, None, None]:
        """Returns a generator with every :class:`.Member` the client can see.

        This is equivalent to: ::

            for guild in client.guilds:
                for member in guild.members:
                    yield member

        Yields
        ------
        :class:`.Member`
            A member the client can see.
        """
        for guild in self.guilds:
            yield from guild.members

    # Listeners/Waiters

    async def wait_until_ready(self) -> None:
        """|coro|

        Waits until the client's internal cache is all ready.
        """
        await self._ready.wait()

    def wait_for(
        self,
        event: str,
        *,
        check: Optional[Callable[..., bool]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By default,
        it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided for
        ease of use.

        In case the event returns multiple arguments, a :class:`tuple` containing those
        arguments is returned instead. Please check the
        :ref:`documentation <discord-api-events>` for a list of events and their
        parameters.

        This function returns the **first event that meets the requirements**.

        Examples
        ---------

        Waiting for a user reply: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')

                    def check(m):
                        return m.content == 'hello' and m.channel == channel

                    msg = await client.wait_for('message', check=check)
                    await channel.send(f'Hello {msg.author}!')

        Waiting for a thumbs up reaction from the message author: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$thumb'):
                    channel = message.channel
                    await channel.send('Send me that \N{THUMBS UP SIGN} reaction, mate')

                    def check(reaction, user):
                        return user == message.author and str(reaction.emoji) == '\N{THUMBS UP SIGN}'

                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        await channel.send('\N{THUMBS DOWN SIGN}')
                    else:
                        await channel.send('\N{THUMBS UP SIGN}')


        Parameters
        ------------
        event: :class:`str`
            The event name, similar to the :ref:`event reference <discord-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[:class:`float`]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.

        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        --------
        Any
            Returns no arguments, a single argument, or a :class:`tuple` of multiple
            arguments that mirrors the parameters passed in the
            :ref:`event reference <discord-api-events>`.
        """

        future = self.loop.create_future()
        if check is None:
            def _check(*args):
                return True
            check = _check

        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout)

    # Event registration

    def event(self, coro: Coro) -> Coro:
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        ---------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        Raises
        --------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        _log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

    async def change_presence(
        self,
        *,
        activity: Optional[BaseActivity] = None,
        status: Optional[Status] = None,
        afk: bool = False
    ):
        """|coro|

        Changes the client's presence.

        Example
        ---------

        .. code-block:: python3

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        Parameters
        ----------
        activity: Optional[:class:`.BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`.Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`.Status.online` is used.
        afk: Optional[:class:`bool`]
            Indicates if you are going AFK. This allows the Discord
            client to know how to handle push notifications better
            for you in case you are actually idle and not lying.

        Raises
        ------
        :exc:`.InvalidArgument`
            If the ``activity`` parameter is not the proper type.
        """

        if status is None:
            status_str = 'online'
            status = Status.online
        elif status is Status.offline:
            status_str = 'invisible'
            status = Status.offline
        else:
            breakpoint()
            status_str = str(status)

        await self.ws.change_presence(activity=activity, status=status_str, afk=afk)

        # TODO: do the same for custom status and check which comes first
        if status:
            try:
                await self._connection.user.edit_settings(status=status)
            except Exception:  # Not essential to actually changing status...
                pass

        for guild in self._connection.guilds:
            me = guild.me
            if me is None:
                continue

            if activity is not None:
                me.activities = (activity,)
            else:
                me.activities = ()

            me.status = status

    async def change_voice_state(
        self,
        *,
        channel: Optional[PrivateChannel],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
        preferred_region: Optional[VoiceRegion] = MISSING
    ) -> None:
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        -----------
        channel: Optional[:class:`VoiceChannel`]
            Channel the client wants to join. Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        self_video: :class:`bool`
            Indicates if the client is using video. Untested & unconfirmed
            (do not use).
        preferred_region: Optional[:class:`VoiceRegion`]
            The preferred region to connect to.
        """
        state = self._connection
        ws = state._get_websocket(self.id)
        channel_id = channel.id if channel else None

        if preferred_region is None or channel_id is None:
            region = None
        else:
            region = str(preferred_region) if preferred_region else str(state.preferred_region)

        await ws.voice_state(None, channel_id, self_mute, self_deaf, self_video, region)

    # Guild stuff

    def fetch_guilds(
        self,
        *,
        limit: Optional[int] = None,
        before: SnowflakeTime = None,
        after: SnowflakeTime = None
    ) -> GuildIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving your guilds.

        .. note::

            Using this, you will only receive :attr:`.Guild.owner`, :attr:`.Guild.icon`,
            :attr:`.Guild.id`, and :attr:`.Guild.name` per :class:`.Guild`.

        .. note::

            This method is an API call. For general usage, consider :attr:`guilds` instead.

        Examples
        ---------

        Usage ::

            async for guild in client.fetch_guilds():
                print(guild.name)

        Flattening into a list ::

            guilds = await client.fetch_guilds().flatten()
            # guilds is now a list of Guild...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of guilds to retrieve.
            If ``None``, it retrieves every guild you have access to.
            Defaults to ``None``.
        before: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieves guilds before this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve guilds after this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.

        Raises
        ------
        :exc:`.HTTPException`
            Getting the guilds failed.

        Yields
        --------
        :class:`.Guild`
            The guild with the guild data parsed.
        """
        return GuildIterator(self, limit=limit, before=before, after=after)

    async def fetch_template(self, code: Union[Template, str]) -> Template:
        """|coro|

        Gets a :class:`.Template` from a discord.new URL or code.

        Parameters
        -----------
        code: Union[:class:`.Template`, :class:`str`]
            The Discord Template Code or URL (must be a discord.new URL).

        Raises
        -------
        :exc:`.NotFound`
            The template is invalid.
        :exc:`.HTTPException`
            Getting the template failed.

        Returns
        --------
        :class:`.Template`
            The template from the URL/code.
        """
        code = utils.resolve_template(code)
        data = await self.http.get_template(code)
        return Template(data=data, state=self._connection)  # type: ignore

    async def fetch_guild(self, guild_id: int, /) -> Guild:
        """|coro|

        Retrieves a :class:`.Guild` from an ID.

        .. note::

            Using this, you will **not** receive :attr:`.Guild.channels` and :attr:`.Guild.members`.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_guild` instead.

        Parameters
        -----------
        guild_id: :class:`int`
            The guild's ID to fetch from.

        Raises
        ------
        :exc:`.Forbidden`
            You do not have access to the guild.
        :exc:`.HTTPException`
            Getting the guild failed.

        Returns
        --------
        :class:`.Guild`
            The guild from the ID.
        """
        data = await self.http.get_guild(guild_id)
        return Guild(data=data, state=self._connection)

    async def create_guild(
        self,
        *,
        name: str,
        region: Union[VoiceRegion, str] = VoiceRegion.us_west,
        icon: bytes = MISSING,
        code: str = MISSING,
    ) -> Guild:
        """|coro|

        Creates a :class:`.Guild`.

        Parameters
        ----------
        name: :class:`str`
            The name of the guild.
        icon: Optional[:class:`bytes`]
            The :term:`py:bytes-like object` representing the icon. See :meth:`.ClientUser.edit`
            for more details on what is expected.
        code: :class:`str`
            The code for a template to create the guild with.

            .. versionadded:: 1.4

        Raises
        ------
        :exc:`.HTTPException`
            Guild creation failed.
        :exc:`.InvalidArgument`
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`.Guild`
            The guild created. This is not the same guild that is
            added to cache.
        """
        if icon is not MISSING:
            icon_base64 = utils._bytes_to_base64_data(icon)
        else:
            icon_base64 = None

        if code:
            data = await self.http.create_from_template(code, name, icon_base64)
        else:
            data = await self.http.create_guild(name, icon_base64)
        return Guild(data=data, state=self._connection)

    async def fetch_stage_instance(self, channel_id: int, /) -> StageInstance:
        """|coro|

        Gets a :class:`.StageInstance` for a stage channel id.

        .. versionadded:: 2.0

        Parameters
        -----------
        channel_id: :class:`int`
            The stage channel ID.

        Raises
        -------
        :exc:`.NotFound`
            The stage instance or channel could not be found.
        :exc:`.HTTPException`
            Getting the stage instance failed.

        Returns
        --------
        :class:`.StageInstance`
            The stage instance from the stage channel ID.
        """
        data = await self.http.get_stage_instance(channel_id)
        guild = self.get_guild(int(data['guild_id']))
        return StageInstance(guild=guild, state=self._connection, data=data)  # type: ignore

    # Invite management

    async def fetch_invite(self, url: Union[Invite, str], *, with_counts: bool = True, with_expiration: bool = True) -> Invite:
        """|coro|

        Gets an :class:`.Invite` from a discord.gg URL or ID.

        .. note::

            If the invite is for a guild you have not joined, the guild and channel
            attributes of the returned :class:`.Invite` will be :class:`.PartialInviteGuild` and
            :class:`.PartialInviteChannel` respectively.

        Parameters
        -----------
        url: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID or URL (must be a discord.gg URL).
        with_counts: :class:`bool`
            Whether to include count information in the invite. This fills the
            :attr:`.Invite.approximate_member_count` and :attr:`.Invite.approximate_presence_count`
            fields.
        with_expiration: :class:`bool`
            Whether to include the expiration date of the invite. This fills the
            :attr:`.Invite.expires_at` field.

            .. versionadded:: 2.0

        Raises
        -------
        :exc:`.NotFound`
            The invite has expired or is invalid.
        :exc:`.HTTPException`
            Getting the invite failed.

        Returns
        --------
        :class:`.Invite`
            The invite from the URL/ID.
        """

        invite_id = utils.resolve_invite(url)
        data = await self.http.get_invite(invite_id, with_counts=with_counts, with_expiration=with_expiration)
        return Invite.from_incomplete(state=self._connection, data=data)

    async def delete_invite(self, invite: Union[Invite, str]) -> None:
        """|coro|

        Revokes an :class:`.Invite`, URL, or ID to an invite.

        You must have the :attr:`~.Permissions.manage_channels` permission in
        the associated guild to do this.

        Parameters
        ----------
        invite: Union[:class:`.Invite`, :class:`str`]
            The invite to revoke.

        Raises
        -------
        :exc:`.Forbidden`
            You do not have permissions to revoke invites.
        :exc:`.NotFound`
            The invite is invalid or expired.
        :exc:`.HTTPException`
            Revoking the invite failed.
        """

        invite_id = utils.resolve_invite(invite)
        await self.http.delete_invite(invite_id)

    async def accept_invite(self, invite: Union[Invite, str]) -> Guild:
        """|coro|

        Accepts an invite and joins a guild.

        .. versionadded:: 1.9

        Parameters
        ----------
        invite: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID, URL (must be a discord.gg URL), or :class:`.Invite`.

        Raises
        ------
        :exc:`.HTTPException`
            Joining the guild failed.

        Returns
        -------
        :class:`.Guild`
            The guild joined. This is not the same guild that is
            added to cache.
        """

        if not isinstance(invite, Invite):
            invite = await self.fetch_invite(invite, with_counts=False, with_expiration=False)

        data = await self.http.join_guild(invite.code, guild_id=invite.guild.id, channel_id=invite.channel.id, channel_type=invite.channel.type.value)
        return Guild(data=data['guild'], state=self._connection)

    use_invite = accept_invite

    # Miscellaneous stuff

    async def fetch_widget(self, guild_id: int, /) -> Widget:
        """|coro|

        Gets a :class:`.Widget` from a guild ID.

        .. note::

            The guild must have the widget enabled to get this information.

        Parameters
        -----------
        guild_id: :class:`int`
            The ID of the guild.

        Raises
        -------
        :exc:`.Forbidden`
            The widget for this guild is disabled.
        :exc:`.HTTPException`
            Retrieving the widget failed.

        Returns
        --------
        :class:`.Widget`
            The guild's widget.
        """
        data = await self.http.get_widget(guild_id)
        return Widget(state=self._connection, data=data)

    async def fetch_user(self, user_id: int, /) -> User:
        """|coro|

        Retrieves a :class:`~discord.User` based on their ID.
        You do not have to share any guilds with the user to get
        this information, however many operations do require that you do.

        .. note::

            This method is an API call. If you have member cache enabled, consider :meth:`get_user` instead.

        Parameters
        -----------
        user_id: :class:`int`
            The user's ID to fetch from.

        Raises
        -------
        :exc:`.NotFound`
            A user with this ID does not exist.
        :exc:`.HTTPException`
            Fetching the user failed.

        Returns
        --------
        :class:`~discord.User`
            The user you requested.
        """
        data = await self.http.get_user(user_id)
        return User(state=self._connection, data=data)


    async def fetch_user_profile(
        self, user_id: int, *, with_mutuals: bool = True, fetch_note: bool = True
    ) -> Profile:
        """|coro|

        Gets an arbitrary user's profile.

        You must share a guild or be friends with this user to
        get this information.

        Parameters
        ------------
        user_id: :class:`int`
            The ID of the user to fetch their profile for.
        with_mutuals: :class:`bool`
            Whether to fetch mutual guilds and friends.
            This fills in :attr:`mutual_guilds` & :attr:`mutual_friends`.
        fetch_note: :class:`bool`
            Whether to pre-fetch the user's note.

        Raises
        -------
        :exc:`.NotFound`
            A user with this ID does not exist.
        :exc:`.Forbidden`
            Not allowed to fetch this profile.
        :exc:`.HTTPException`
            Fetching the profile failed.

        Returns
        --------
        :class:`.Profile`
            The profile of the user.
        """

        state = self._connection
        data = await self.http.get_user_profile(user_id, with_mutual_guilds=with_mutuals)

        if with_mutuals:
            data['mutual_friends'] = await self.http.get_mutual_friends(user_id)

        profile = Profile(state, data)

        if fetch_note:
            await profile.note.fetch()

        return profile

    fetch_profile = fetch_user_profile

    async def fetch_channel(self, channel_id: int, /) -> Union[GuildChannel, PrivateChannel, Thread]:
        """|coro|

        Retrieves a :class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`, or :class:`.Thread` with the specified ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_channel` instead.

        .. versionadded:: 1.2

        Raises
        -------
        :exc:`.InvalidData`
            An unknown channel type was received from Discord.
        :exc:`.HTTPException`
            Retrieving the channel failed.
        :exc:`.NotFound`
            Invalid Channel ID.
        :exc:`.Forbidden`
            You do not have permission to fetch this channel.

        Returns
        --------
        Union[:class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`, :class:`.Thread`]
            The channel from the ID.
        """
        data = await self.http.get_channel(channel_id)

        factory, ch_type = _threaded_channel_factory(data['type'])
        if factory is None:
            raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(data))

        if ch_type in (ChannelType.group, ChannelType.private):
            # the factory will be a DMChannel or GroupChannel here
            channel = factory(me=self.user, data=data, state=self._connection) # type: ignore
        else:
            # the factory can't be a DMChannel or GroupChannel here
            guild_id = int(data['guild_id']) # type: ignore
            guild = self.get_guild(guild_id) or Object(id=guild_id)
            # GuildChannels expect a Guild, we may be passing an Object
            channel = factory(guild=guild, state=self._connection, data=data) # type: ignore

        return channel

    async def fetch_webhook(self, webhook_id: int, /) -> Webhook:
        """|coro|

        Retrieves a :class:`.Webhook` with the specified ID.

        Raises
        --------
        :exc:`.HTTPException`
            Retrieving the webhook failed.
        :exc:`.NotFound`
            Invalid webhook ID.
        :exc:`.Forbidden`
            You do not have permission to fetch this webhook.

        Returns
        ---------
        :class:`.Webhook`
            The webhook you requested.
        """
        data = await self.http.get_webhook(webhook_id)
        return Webhook.from_state(data, state=self._connection)

    async def fetch_sticker(self, sticker_id: int, /) -> Union[StandardSticker, GuildSticker]:
        """|coro|

        Retrieves a :class:`.Sticker` with the specified ID.

        .. versionadded:: 2.0

        Raises
        --------
        :exc:`.HTTPException`
            Retrieving the sticker failed.
        :exc:`.NotFound`
            Invalid sticker ID.

        Returns
        --------
        Union[:class:`.StandardSticker`, :class:`.GuildSticker`]
            The sticker you requested.
        """
        data = await self.http.get_sticker(sticker_id)
        cls, _ = _sticker_factory(data['type'])  # type: ignore
        return cls(state=self._connection, data=data)  # type: ignore

    async def fetch_sticker_packs(
        self, *, country='US', locale='en-US', payment_source_id: int = MISSING
    ) -> List[StickerPack]:
        """|coro|

        Retrieves all available default sticker packs.

        .. versionadded:: 2.0

        Parameters
        -----------
        country: :class:`str`
            ISO 3166 country code to fetch the sticker packs for.
            Defaults to ``US``.
        locale: :class:`str`
            ISO 639 language code the name and description should be in.
            Defaults to ``en-US``.
        payment_source_id: :class:`int`
            Unknown.

        Raises
        -------
        :exc:`.HTTPException`
            Retrieving the sticker packs failed.

        Returns
        ---------
        List[:class:`.StickerPack`]
            All available premium sticker packs.
        """
        data = await self.http.list_premium_sticker_packs(country, locale, payment_source_id)
        return [StickerPack(state=self._connection, data=pack) for pack in data['sticker_packs']]

    async def fetch_notes(self) -> List[Note]:
        """|coro|

        Retrieves a list of :class:`Note` objects representing all your notes.

        Raises
        -------
        :exc:`.HTTPException`
            Retreiving the notes failed.

        Returns
        --------
        List[:class:`Note`]
            All your notes.
        """
        state = self._connection
        data = await state.http.get_notes()
        return [Note(state, int(id), note=note) for id, note in data.items()]

    async def fetch_note(self, user_id: int) -> Note:
        """|coro|

        Retrieves a :class:`Note` for the specified user ID.

        Parameters
        -----------
        user_id: :class:`int`
            The ID of the user to fetch the note for.

        Raises
        -------
        :exc:`.HTTPException`
            Retreiving the note failed.

        Returns
        --------
        :class:`Note`
            The note you requested.
        """
        note = Note(self._connection, int(user_id))
        await note.fetch()
        return note

    async def fetch_private_channels(self) -> List[PrivateChannel]:
        """|coro|

        Retrieves all your private channels.

        Raises
        -------
        :exc:`.HTTPException`
            Retreiving your private channels failed.

        Returns
        --------
        List[:class:`PrivateChannel`]
            All your private channels.
        """
        state = self._connection
        channels = await state.http.get_private_channels()
        return [_private_channel_factory(data['type'])(me=self.user, data=data, state=state) for data in channels]

    async def create_dm(self, user: Snowflake) -> DMChannel:
        """|coro|

        Creates a :class:`.DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        .. versionadded:: 2.0

        Parameters
        -----------
        user: :class:`~discord.abc.Snowflake`
            The user to create a DM with.

        Returns
        -------
        :class:`.DMChannel`
            The channel that was created.
        """
        state = self._connection
        found = state._get_private_channel_by_user(user.id)
        if found:
            return found

        data = await state.http.start_private_message(user.id)
        return state.add_dm_channel(data)

    async def create_group(self, *recipients) -> GroupChannel:
        r"""|coro|

        Creates a group direct message with the recipients
        provided. These recipients must be have a relationship
        of type :attr:`RelationshipType.friend`.

        Parameters
        -----------
        \*recipients: :class:`User`
            An argument :class:`list` of :class:`User` to have in
            your group.

        Raises
        -------
        :exc:`.HTTPException`
            Failed to create the group direct message.

        Returns
        -------
        :class:`.GroupChannel`
            The new group channel.
        """
        users = [str(u.id) for u in recipients]
        state = self._connection
        data = await state.http.start_group(users)
        return GroupChannel(me=self.user, data=data, state=state)
