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
import sys
import traceback
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generator,
    List,
    Optional,
    overload,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import aiohttp

from .user import BaseUser, User, ClientUser, Note
from .invite import Invite
from .template import Template
from .widget import Widget
from .guild import Guild
from .emoji import Emoji
from .channel import _private_channel_factory, _threaded_channel_factory, GroupChannel, PartialMessageable
from .enums import ActivityType, ChannelType, Status, InviteType, try_enum
from .mentions import AllowedMentions
from .errors import *
from .enums import Status
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
from .appinfo import Application, PartialApplication
from .stage_instance import StageInstance
from .threads import Thread
from .sticker import GuildSticker, StandardSticker, StickerPack, _sticker_factory
from .profile import UserProfile
from .connections import Connection
from .team import Team
from .member import _ClientStatus
from .handlers import CaptchaHandler

if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType
    from .guild import GuildChannel
    from .abc import PrivateChannel, GuildChannel, Snowflake
    from .channel import DMChannel
    from .message import Message
    from .member import Member
    from .voice_client import VoiceProtocol
    from .types.snowflake import Snowflake as _Snowflake

# fmt: off
__all__ = (
    'Client',
)
# fmt: on

Coro = TypeVar('Coro', bound=Callable[..., Coroutine[Any, Any, Any]])

_log = logging.getLogger(__name__)


class _LoopSentinel:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        msg = (
            'loop attribute cannot be accessed in non-async contexts. '
            'Consider using either an asynchronous main function and passing it to asyncio.run or '
            'using asynchronous initialisation hooks such as Client.setup_hook'
        )
        raise AttributeError(msg)


_loop: Any = _LoopSentinel()


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
    request_guilds: :class:`bool`
        Whether to request guilds at startup. Defaults to True.

        .. versionadded:: 2.0
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
    sync_presence: :class:`bool`
        Whether to keep presences up-to-date across clients.
        The default behavior is ``True`` (what the client does).

        .. versionadded:: 2.0
    http_trace: :class:`aiohttp.TraceConfig`
        The trace configuration to use for tracking HTTP requests the library does using ``aiohttp``.
        This allows you to check requests the library is using. For more information, check the
        `aiohttp documentation <https://docs.aiohttp.org/en/stable/client_advanced.html#client-tracing>`_.

        .. versionadded:: 2.0
    captcha_handler: Optional[:class:`CaptchaHandler`]
        A class that solves captcha challenges.

        .. versionadded:: 2.0

    Attributes
    -----------
    ws
        The websocket gateway the client is currently connected to. Could be ``None``.
    """

    def __init__(self, **options: Any) -> None:
        self.loop: asyncio.AbstractEventLoop = _loop
        # self.ws is set in the connect method
        self.ws: DiscordWebSocket = None  # type: ignore
        self._listeners: Dict[str, List[Tuple[asyncio.Future, Callable[..., bool]]]] = {}

        proxy: Optional[str] = options.pop('proxy', None)
        proxy_auth: Optional[aiohttp.BasicAuth] = options.pop('proxy_auth', None)
        unsync_clock: bool = options.pop('assume_unsync_clock', True)
        http_trace: Optional[aiohttp.TraceConfig] = options.pop('http_trace', None)
        captcha_handler: Optional[CaptchaHandler] = options.pop('captcha_handler', None)
        if captcha_handler is not None and not isinstance(captcha_handler, CaptchaHandler):
            raise TypeError(f'captcha_handler must derive from CaptchaHandler')
        self.http: HTTPClient = HTTPClient(
            self.loop,
            proxy=proxy,
            proxy_auth=proxy_auth,
            unsync_clock=unsync_clock,
            http_trace=http_trace,
            captcha_handler=captcha_handler,
        )

        self._handlers: Dict[str, Callable[..., None]] = {
            'ready': self._handle_ready,
            'connect': self._handle_connect,
        }

        self._hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {
            'before_identify': self._call_before_identify_hook,
        }

        self._enable_debug_events: bool = options.pop('enable_debug_events', False)
        self._sync_presences: bool = options.pop('sync_presence', True)
        self._connection: ConnectionState = self._get_state(**options)
        self._closed: bool = False
        self._ready: asyncio.Event = MISSING

        self._client_status: _ClientStatus = _ClientStatus()
        self._client_activities: Dict[Optional[str], Tuple[ActivityTypes, ...]] = {
            None: tuple(),
            'this': tuple(),
        }
        self._session_count = 1

        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            _log.warning('PyNaCl is not installed, voice will NOT be supported.')

    async def __aenter__(self) -> Self:
        await self._async_setup_hook()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if not self.is_closed():
            await self.close()

    # Internals

    def _get_state(self, **options: Any) -> ConnectionState:
        return ConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            client=self,
            **options,
        )

    def _handle_ready(self) -> None:
        self._ready.set()

    def _handle_connect(self) -> None:
        state = self._connection
        activities = self.initial_activities
        status = self.initial_status
        if status is None:
            status = getattr(state.settings, 'status', None) or Status.online
        self.loop.create_task(self.change_presence(activities=activities, status=status))  # type: ignore

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

    @property
    def country_code(self) -> Optional[str]:
        """Optional[:class:`str`]: The country code of the client. ``None`` if not connected.

        .. versionadded:: 2.0
        """
        return self._connection.country_code

    @property
    def preferred_voice_regions(self) -> List[str]:
        """List[:class:`str`]: Geo-ordered list of voice regions the connected client can use.

        .. versionadded:: 2.0
        """
        return self._connection.preferred_regions

    def is_ready(self) -> bool:
        """:class:`bool`: Specifies if the client's internal cache is ready for use."""
        return self._ready is not MISSING and self._ready.is_set()

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return self.loop.create_task(wrapped, name=f'discord.py: {event_name}')

    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
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

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        """|coro|

        The default error handler provided by the client.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.

        .. versionchanged:: 2.0

            ``event_method`` parameter is now positional-only.
        """
        print(f'Ignoring exception in {event_method}', file=sys.stderr)
        traceback.print_exc()

    async def on_internal_settings_update(self, old_settings, new_settings):
        if not self._sync_presences:
            return

        if (
            old_settings is not None
            and old_settings._status == new_settings._status
            and old_settings._custom_status == new_settings._custom_status
        ):
            return  # Nothing changed

        status = new_settings.status
        activities = [a for a in self.activities if a.type != ActivityType.custom]
        if (activity := new_settings.custom_activity) is not None:
            activities.append(activity)

        await self.change_presence(status=status, activities=activities, edit_settings=False)  # type: ignore

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

    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        loop = asyncio.get_running_loop()
        self.loop = loop
        self.http.loop = loop
        self._connection.loop = loop
        await self._connection.async_setup()

        self._ready = asyncio.Event()

    async def setup_hook(self) -> None:
        """|coro|

        A coroutine to be called to setup the bot, by default this is blank.

        To perform asynchronous setup after the bot is logged in but before
        it has connected to the Websocket, overwrite this coroutine.

        This is only called once, in :meth:`login`, and will be called before
        any events are dispatched, making it a better solution than doing such
        setup in the :func:`~discord.on_ready` event.

        .. warning::

            Since this is called *before* the websocket connection is made therefore
            anything that waits for the websocket will deadlock, this includes things
            like :meth:`wait_for` and :meth:`wait_until_ready`.

        .. versionadded:: 2.0
        """
        pass

    # Login state management

    async def login(self, token: str) -> None:
        """|coro|

        Logs in the client with the specified credentials and
        calls the :meth:`setup_hook`.

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
        LoginFailure
            The wrong credentials are passed.
        HTTPException
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """

        _log.info('Logging in using static token.')

        await self._async_setup_hook()

        state = self._connection
        data = await state.http.static_login(token.strip())
        state.analytics_token = data.get('analytics_token', '')
        state.user = ClientUser(state=state, data=data)
        await self.setup_hook()

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
        ConnectionClosed
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
                ws_params.update(sequence=self.ws.sequence, resume=e.resume, session=self.ws.session_id)  # type: ignore # These are always present at this point
                continue
            except (
                OSError,
                HTTPException,
                GatewayNotFound,
                ConnectionClosed,
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as exc:

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
                    ws_params.update(sequence=self.ws.sequence, initial=False, resume=True, session=self.ws.session_id)  # type: ignore # These are always present at this point
                    continue

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, etc)
                # Sometimes, Discord sends us 1000 for unknown reasons so we should
                # reconnect regardless and rely on is_closed instead
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
                ws_params.update(sequence=self.ws.sequence, resume=True, session=self.ws.session_id)  # type: ignore # These are always present at this point

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

        if self._ready is not MISSING:
            self._ready.clear()

        self.loop = MISSING

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
                asyncio.run(self.start(*args, **kwargs))
            except KeyboardInterrupt:
                return

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.
        """

        async def runner():
            async with self:
                await self.start(*args, **kwargs)

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            # Nothing to do here
            # `asyncio.run` handles the loop cleanup
            # and `self.start` closes all sockets and the HTTPClient instance
            return

    # Properties

    def is_closed(self) -> bool:
        """:class:`bool`: Indicates if the websocket connection is closed."""
        return self._closed

    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        """Optional[:class:`.VoiceProtocol`]: Returns the :class:`.VoiceProtocol` associated with private calls, if any."""
        return self._connection._get_voice_client(self._connection.self_id)

    @property
    def initial_activity(self) -> Optional[ActivityTypes]:
        """Optional[:class:`.BaseActivity`]: The primary activity set upon logging in.

        .. note::

            The client may be setting multiple activities, these can be accessed under :attr:`initial_activities`.
        """
        state = self._connection
        return create_activity(state._activities[0], state) if state._activities else None

    @initial_activity.setter
    def initial_activity(self, value: Optional[ActivityTypes]) -> None:
        if value is None:
            self._connection._activities = []
        elif isinstance(value, BaseActivity):
            self._connection._activities = [value.to_dict()]
        else:
            raise TypeError('activity must derive from BaseActivity')

    @property
    def initial_activities(self) -> List[ActivityTypes]:
        """List[:class:`.BaseActivity`]: The activities set upon logging in."""
        state = self._connection
        return [create_activity(activity, state) for activity in state._activities]

    @initial_activities.setter
    def initial_activities(self, values: Sequence[ActivityTypes]) -> None:
        if not values:
            self._connection._activities = []
        elif all(isinstance(value, BaseActivity) for value in values):
            self._connection._activities = [value.to_dict() for value in values]
        else:
            raise TypeError('activity must derive from BaseActivity')

    @property
    def initial_status(self):
        """Optional[:class:`.Status`]: The status set upon logging in.

        .. versionadded:: 2.0
        """
        if self._connection._status in {state.value for state in Status}:
            return Status(self._connection._status)
        return

    @initial_status.setter
    def initial_status(self, value: Status):
        if value is Status.offline:
            self._connection._status = 'invisible'
        elif isinstance(value, Status):
            self._connection._status = str(value)
        else:
            raise TypeError('status must derive from Status')

    @property
    def status(self) -> Status:
        """:class:`.Status`: The user's overall status.

        .. versionadded:: 2.0
        """
        status = try_enum(Status, self._client_status._status)
        if status is Status.offline and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status

    @property
    def raw_status(self) -> str:
        """:class:`str`: The user's overall status as a string value.

        .. versionadded:: 2.0
        """
        return str(self.status)

    @status.setter
    def status(self, value: Status) -> None:
        # Internal use only
        self._client_status._status = str(value)

    @property
    def mobile_status(self) -> Status:
        """:class:`.Status`: The user's status on a mobile device, if applicable.

        .. versionadded:: 2.0
        """
        return try_enum(Status, self._client_status.mobile or 'offline')

    @property
    def desktop_status(self) -> Status:
        """:class:`.Status`: The user's status on the desktop client, if applicable.

        .. versionadded:: 2.0
        """
        return try_enum(Status, self._client_status.desktop or 'offline')

    @property
    def web_status(self) -> Status:
        """:class:`.Status`: The user's status on the web client, if applicable.

        .. versionadded:: 2.0
        """
        return try_enum(Status, self._client_status.web or 'offline')

    @property
    def client_status(self) -> Status:
        """:class:`.Status`: The library's status.

        .. versionadded:: 2.0
        """
        status = try_enum(Status, self._client_status._this)
        if status is Status.offline and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if a member is active on a mobile device.

        .. versionadded:: 2.0
        """
        return self._client_status.mobile is not None

    @property
    def activities(self) -> Tuple[ActivityTypes]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the activities
        the client is currently doing.

        .. versionadded:: 2.0

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.
        """
        state = self._connection
        activities = tuple(create_activity(d, state) for d in self._client_activities[None])  # type: ignore
        if activities is None and not self.is_closed():
            activities = getattr(state.settings, 'custom_activity', [])
            activities = [activities] if activities else activities
        return activities

    @property
    def activity(self) -> Optional[ActivityTypes]:
        """Optional[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the primary
        activity the client is currently doing. Could be ``None`` if no activity is being done.

        .. versionadded:: 2.0

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.

        .. note::

            The client may have multiple activities, these can be accessed under :attr:`activities`.
        """
        if activities := self.activities:
            return activities[0]

    @property
    def mobile_activities(self) -> Tuple[ActivityTypes]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the activities
        the client is currently doing on a mobile device, if applicable.

        .. versionadded:: 2.0
        """
        state = self._connection
        return tuple(create_activity(d, state) for d in self._client_activities.get('mobile', []))

    @property
    def desktop_activities(self) -> Tuple[ActivityTypes]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the activities
        the client is currently doing on the desktop client, if applicable.

        .. versionadded:: 2.0
        """
        state = self._connection
        return tuple(create_activity(d, state) for d in self._client_activities.get('desktop', []))

    @property
    def web_activities(self) -> Tuple[ActivityTypes]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the activities
        the client is currently doing on the web client, if applicable.

        .. versionadded:: 2.0
        """
        state = self._connection
        return tuple(create_activity(d, state) for d in self._client_activities.get('web', []))

    @property
    def client_activities(self) -> Tuple[ActivityTypes]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the activities
        the client is currently doing through this library, if applicable.

        .. versionadded:: 2.0
        """
        state = self._connection
        activities = tuple(create_activity(d, state) for d in self._client_activities.get('this', []))
        if activities is None and not self.is_closed():
            activities = getattr(state.settings, 'custom_activity', [])
            activities = [activities] if activities else activities
        return activities

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

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

        Parameters
        -----------
        id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[Union[:class:`.abc.GuildChannel`, :class:`.Thread`, :class:`.abc.PrivateChannel`]]
            The returned channel or ``None`` if not found.
        """
        return self._connection.get_channel(id)  # type: ignore # The cache contains all channel types

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
            The stage instance or ``None`` if not found.
        """
        from .channel import StageChannel

        channel = self._connection.get_channel(id)

        if isinstance(channel, StageChannel):
            return channel.instance

    def get_guild(self, id: int, /) -> Optional[Guild]:
        """Returns a guild with the given ID.

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

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

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

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

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

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

        .. warning::

            Calling this inside :meth:`setup_hook` can lead to a deadlock.
        """
        if self._ready is not MISSING:
            await self._ready.wait()

    def wait_for(
        self,
        event: str,
        /,
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

        .. versionchanged:: 2.0

            ``event`` parameter is now positional-only.


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

    def event(self, coro: Coro, /) -> Coro:
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        ---------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        .. versionchanged:: 2.0

            ``coro`` parameter is now positional-only.

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
        activities: Optional[List[BaseActivity]] = None,
        status: Optional[Status] = None,
        afk: bool = False,
        edit_settings: bool = True,
    ) -> None:
        """|coro|

        Changes the client's presence.

        .. versionchanged:: 2.0
            Edits are no longer in place most of the time.
            Added option to update settings.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

        Example
        ---------

        .. code-block:: python3

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        Parameters
        ----------
        activity: Optional[:class:`.BaseActivity`]
            The activity being done. ``None`` if no activity is done.
        activities: Optional[List[:class:`.BaseActivity`]]
            A list of the activities being done. ``None`` if no activities
            are done. Cannot be sent with ``activity``.
        status: Optional[:class:`.Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`.Status.online` is used.
        afk: :class:`bool`
            Indicates if you are going AFK. This allows the Discord
            client to know how to handle push notifications better
            for you in case you are actually idle and not lying.
        edit_settings: :class:`bool`
            Whether to update the settings with the new status and/or
            custom activity. This will broadcast the change and cause
            all connected (official) clients to change presence as well.
            Defaults to ``True``. Required for setting/editing expires_at
            for custom activities.
            It's not recommended to change this.

        Raises
        ------
        TypeError
            The ``activity`` parameter is not the proper type.
            Both ``activity`` and ``activities`` were passed.
        """
        if activity and activities:
            raise TypeError('Cannot pass both activity and activities')
        activities = activities or activity and [activity]
        if activities is None:
            activities = []

        if status is None:
            status = Status.online
        elif status is Status.offline:
            status = Status.invisible

        await self.ws.change_presence(status=status, activities=activities, afk=afk)

        if edit_settings:
            custom_activity = None

            for activity in activities:
                if getattr(activity, 'type', None) is ActivityType.custom:
                    custom_activity = activity

            payload: Dict[str, Any] = {}
            if status != getattr(self.user.settings, 'status', None):  # type: ignore # user is always present when logged in
                payload['status'] = status
            if custom_activity != getattr(self.user.settings, 'custom_activity', None):  # type: ignore # user is always present when logged in
                payload['custom_activity'] = custom_activity
            if payload:
                await self.user.edit_settings(**payload)  # type: ignore # user is always present when logged in

        status_str = str(status)
        activities_tuple = tuple(a.to_dict() for a in activities)
        self._client_status._this = str(status)
        self._client_activities['this'] = activities_tuple  # type: ignore
        if self._session_count <= 1:
            self._client_status._status = status_str
            self._client_activities[None] = self._client_activities['this'] = activities_tuple  # type: ignore

    async def change_voice_state(
        self,
        *,
        channel: Optional[Snowflake],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
        preferred_region: Optional[str] = MISSING,
    ) -> None:
        """|coro|

        Changes client's private channel voice state.

        .. versionadded:: 1.10

        Parameters
        -----------
        channel: Optional[:class:`~discord.abc.Snowflake`]
            Channel the client wants to join (must be a private channel). Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        self_video: :class:`bool`
            Indicates if the client is using video. Untested & unconfirmed
            (do not use).
        preferred_region: Optional[:class:`str`]
            The preferred region to connect to.

            .. versionchanged:: 2.0
                The type of this parameter has changed to :class:`str`.
        """
        state = self._connection
        ws = self.ws
        channel_id = channel.id if channel else None

        if preferred_region is None or channel_id is None:
            region = None
        else:
            region = str(preferred_region) if preferred_region else state.preferred_region

        await ws.voice_state(None, channel_id, self_mute, self_deaf, self_video, preferred_region=region)

    # Guild stuff

    async def fetch_guilds(self, *, with_counts: bool = True) -> List[Guild]:
        """Retrieves all your your guilds.

        .. note::

            Using this, you will only receive :attr:`.Guild.owner`, :attr:`.Guild.icon`,
            :attr:`.Guild.id`, and :attr:`.Guild.name` per :class:`.Guild`.

        .. note::

            This method is an API call. For general usage, consider :attr:`guilds` instead.

        Parameters
        -----------
        with_counts: :class:`bool`
            Whether to fill :attr:`.Guild.approximate_member_count` and :attr:`.Guild.approximate_presence_count`.
            Defaults to ``True``.

        Raises
        ------
        HTTPException
            Getting the guilds failed.

        Returns
        --------
        List[:class:`.Guild`]
            A list of all your guilds.
        """
        state = self._connection
        guilds = await state.http.get_guilds(with_counts)
        guilds = [Guild(data=data, state=state) for data in guilds]
        for guild in guilds:
            guild._cs_joined = True
        return guilds

    async def fetch_template(self, code: Union[Template, str]) -> Template:
        """|coro|

        Gets a :class:`.Template` from a discord.new URL or code.

        Parameters
        -----------
        code: Union[:class:`.Template`, :class:`str`]
            The Discord Template Code or URL (must be a discord.new URL).

        Raises
        -------
        NotFound
            The template is invalid.
        HTTPException
            Getting the template failed.

        Returns
        --------
        :class:`.Template`
            The template from the URL/code.
        """
        code = utils.resolve_template(code)
        data = await self.http.get_template(code)
        return Template(data=data, state=self._connection)

    async def fetch_guild(self, guild_id: int, /, *, with_counts: bool = True) -> Guild:
        """|coro|

        Retrieves a :class:`.Guild` from an ID.

        .. versionchanged:: 2.0

            ``guild_id`` parameter is now positional-only.

        .. note::

            Using this, you will **not** receive :attr:`.Guild.channels` and :attr:`.Guild.members`.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_guild` instead.

        .. versionchanged:: 2.0

            ``guild_id`` parameter is now positional-only.

        Parameters
        -----------
        guild_id: :class:`int`
            The guild's ID to fetch from.
        with_counts: :class:`bool`
            Whether to include count information in the guild. This fills the
            :attr:`.Guild.approximate_member_count` and :attr:`.Guild.approximate_presence_count`.
            Defaults to ``True``.

            .. versionadded:: 2.0

        Raises
        ------
        Forbidden
            You do not have access to the guild.
        HTTPException
            Getting the guild failed.

        Returns
        --------
        :class:`.Guild`
            The guild from the ID.
        """
        data = await self.http.get_guild(guild_id, with_counts)
        guild = Guild(data=data, state=self._connection)
        guild._cs_joined = True
        return guild

    async def fetch_guild_preview(self, guild_id: int, /) -> Guild:
        """|coro|

        Retrieves a public :class:`.Guild` preview from an ID.

        .. versionadded:: 2.0

        Raises
        ------
        NotFound
            Guild with given ID does not exist/is not public.
        HTTPException
            Retrieving the guild failed.

        Returns
        --------
        :class:`.Guild`
            The guild from the ID.
        """
        data = await self.http.get_guild_preview(guild_id)
        return Guild(data=data, state=self._connection)

    async def create_guild(
        self,
        name: str,
        icon: bytes = MISSING,
        code: str = MISSING,
    ) -> Guild:
        """|coro|

        Creates a :class:`.Guild`.

        .. versionchanged:: 2.0
            ``name`` and ``icon`` parameters are now keyword-only. The ``region`` parameter has been removed.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

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
        HTTPException
            Guild creation failed.
        ValueError
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

        guild = Guild(data=data, state=self._connection)
        guild._cs_joined = True
        return guild

    async def join_guild(self, guild_id: int, /, lurking: bool = False) -> Guild:
        """|coro|

        Joins a discoverable :class:`.Guild`.

        Parameters
        -----------
        guild_id: :class:`int`
            The ID of the guild to join.
        lurking: :class:`bool`
            Whether to lurk the guild.

        Raises
        -------
        NotFound
            Guild with given ID does not exist/have discovery enabled.
        HTTPException
            Joining the guild failed.

        Returns
        --------
        :class:`.Guild`
            The guild that was joined.
        """
        state = self._connection
        data = await state.http.join_guild(guild_id, lurking, state.session_id)
        guild = Guild(data=data, state=state)
        guild._cs_joined = not lurking
        return guild

    async def leave_guild(self, guild: Snowflake, /, lurking: bool = MISSING) -> None:
        """|coro|

        Leaves a guild. Equivalent to :meth:`.Guild.leave`.

        .. versionadded:: 2.0

        Parameters
        -----------
        guild: :class:`~discord.abc.Snowflake`
            The guild to leave.
        lurking: :class:`bool`
            Whether you are lurking the guild.

        Raises
        -------
        HTTPException
            Leaving the guild failed.
        """
        lurking = lurking if lurking is not MISSING else MISSING
        if lurking is MISSING:
            attr = getattr(guild, 'joined', lurking)
            if attr is not MISSING:
                lurking = not attr
            elif (new_guild := self._connection._get_guild(guild.id)) is not None:
                lurking = not new_guild.is_joined()

        await self.http.leave_guild(guild.id, lurking=lurking)

    async def fetch_stage_instance(self, channel_id: int, /) -> StageInstance:
        """|coro|

        Gets a :class:`.StageInstance` for a stage channel ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        channel_id: :class:`int`
            The stage channel ID.

        Raises
        -------
        NotFound
            The stage instance or channel could not be found.
        HTTPException
            Getting the stage instance failed.

        Returns
        --------
        :class:`.StageInstance`
            The stage instance from the stage channel ID.
        """
        data = await self.http.get_stage_instance(channel_id)
        guild = self.get_guild(int(data['guild_id']))
        # Guild can technically be None here but this is being explicitly silenced right now.
        return StageInstance(guild=guild, state=self._connection, data=data)  # type: ignore

    # Invite management

    async def fetch_invite(
        self,
        url: Union[Invite, str],
        /,
        *,
        with_counts: bool = True,
        with_expiration: bool = True,
        scheduled_event_id: Optional[int] = None,
    ) -> Invite:
        """|coro|

        Gets an :class:`.Invite` from a discord.gg URL or ID.

        .. note::

            If the invite is for a guild you have not joined, the guild and channel
            attributes of the returned :class:`.Invite` will be :class:`.PartialInviteGuild` and
            :class:`.PartialInviteChannel` respectively.

        .. versionchanged:: 2.0

            ``url`` parameter is now positional-only.

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
        scheduled_event_id: Optional[:class:`int`]
            The ID of the scheduled event this invite is for.

            .. note::

                It is not possible to provide a url that contains an ``event_id`` parameter
                when using this parameter.

            .. versionadded:: 2.0

        Raises
        -------
        ValueError
            The url contains an ``event_id``, but ``scheduled_event_id`` has also been provided.
        NotFound
            The invite has expired or is invalid.
        HTTPException
            Getting the invite failed.

        Returns
        --------
        :class:`.Invite`
            The invite from the URL/ID.
        """

        resolved = utils.resolve_invite(url)

        if scheduled_event_id and resolved.event:
            raise ValueError('Cannot specify scheduled_event_id and contain an event_id in the url.')

        scheduled_event_id = scheduled_event_id or resolved.event

        data = await self.http.get_invite(
            resolved.code,
            with_counts=with_counts,
            with_expiration=with_expiration,
            guild_scheduled_event_id=scheduled_event_id,
        )
        return Invite.from_incomplete(state=self._connection, data=data)

    async def delete_invite(self, invite: Union[Invite, str], /) -> None:
        """|coro|

        Revokes an :class:`.Invite`, URL, or ID to an invite.

        You must have the :attr:`~.Permissions.manage_channels` permission in
        the associated guild to do this.

        .. versionchanged:: 2.0

            ``invite`` parameter is now positional-only.

        Parameters
        ----------
        invite: Union[:class:`.Invite`, :class:`str`]
            The invite to revoke.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke invites.
        NotFound
            The invite is invalid or expired.
        HTTPException
            Revoking the invite failed.
        """
        resolved = utils.resolve_invite(invite)
        await self.http.delete_invite(resolved.code)

    async def accept_invite(self, invite: Union[Invite, str], /) -> Union[Guild, User, GroupChannel]:
        """|coro|

        Uses an invite.
        Either joins a guild, joins a group DM, or adds a friend.

        .. versionadded:: 1.9

        .. versionchanged:: 2.0

            ``invite`` parameter is now positional-only.

        Parameters
        ----------
        invite: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID, URL (must be a discord.gg URL), or :class:`.Invite`.

        Raises
        ------
        HTTPException
            Using the invite failed.

        Returns
        -------
        :class:`.Guild`
            The guild joined. This is not the same guild that is
            added to cache.
        """
        if not isinstance(invite, Invite):
            invite = await self.fetch_invite(invite, with_counts=False, with_expiration=False)

        state = self._connection
        type = invite.type
        if message := invite._message:
            kwargs = {'message': message}
        else:
            kwargs = {
                'guild_id': getattr(invite.guild, 'id', MISSING),
                'channel_id': getattr(invite.channel, 'id', MISSING),
                'channel_type': getattr(invite.channel, 'type', MISSING),
            }
        data = await state.http.accept_invite(invite.code, type, **kwargs)
        if type is InviteType.guild:
            guild = Guild(data=data['guild'], state=state)
            guild._cs_joined = True
            return guild
        elif type is InviteType.group_dm:
            return GroupChannel(data=data['channel'], state=state, me=state.user)  # type: ignore
        else:
            return User(data=data['inviter'], state=state)

    # Miscellaneous stuff

    async def fetch_widget(self, guild_id: int, /) -> Widget:
        """|coro|

        Gets a :class:`.Widget` from a guild ID.

        .. note::

            The guild must have the widget enabled to get this information.

        .. versionchanged:: 2.0

            ``guild_id`` parameter is now positional-only.

        Parameters
        -----------
        guild_id: :class:`int`
            The ID of the guild.

        Raises
        -------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
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

        Retrieves a :class:`discord.User` based on their ID.
        You do not have to share any guilds with the user to get
        this information, however many operations do require that you do.

        .. note::

            This method is an API call. If you have member cache enabled, consider :meth:`get_user` instead.

        .. warning::

            This API route is not used by the Discord client and may increase your chances at getting detected.
            Consider :meth:`fetch_user_profile` if you share a guild/relationship with the user.

        .. versionchanged:: 2.0

            ``user_id`` parameter is now positional-only.

        Parameters
        -----------
        user_id: :class:`int`
            The user's ID to fetch from.

        Raises
        -------
        NotFound
            A user with this ID does not exist.
        HTTPException
            Fetching the user failed.

        Returns
        --------
        :class:`discord.User`
            The user you requested.
        """
        data = await self.http.get_user(user_id)
        return User(state=self._connection, data=data)

    async def fetch_user_profile(
        self, user_id: int, /, *, with_mutuals: bool = True, fetch_note: bool = True
    ) -> UserProfile:
        """|coro|

        Gets an arbitrary user's profile.

        You must share a guild or be friends with this user to
        get this information (unless the user is a bot).

        .. versionchanged:: 2.0

            ``user_id`` parameter is now positional-only.

        Parameters
        ------------
        user_id: :class:`int`
            The ID of the user to fetch their profile for.
        with_mutuals: :class:`bool`
            Whether to fetch mutual guilds and friends.
            This fills in :attr:`.UserProfile.mutual_guilds` & :attr:`.UserProfile.mutual_friends`.
        fetch_note: :class:`bool`
            Whether to pre-fetch the user's note.

        Raises
        -------
        NotFound
            A user with this ID does not exist.
        Forbidden
            Not allowed to fetch this profile.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`.UserProfile`
            The profile of the user.
        """
        state = self._connection
        data = await state.http.get_user_profile(user_id, with_mutual_guilds=with_mutuals)

        if with_mutuals:
            if not data['user'].get('bot', False):
                data['mutual_friends'] = await state.http.get_mutual_friends(user_id)
            else:
                data['mutual_friends'] = []
        profile = UserProfile(state=state, data=data)

        if fetch_note:
            await profile.note.fetch()

        return profile

    async def fetch_channel(self, channel_id: int, /) -> Union[GuildChannel, PrivateChannel, Thread]:
        """|coro|

        Retrieves a :class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`, or :class:`.Thread` with the specified ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_channel` instead.

        .. versionadded:: 1.2

        .. versionchanged:: 2.0

            ``channel_id`` parameter is now positional-only.

        Raises
        -------
        InvalidData
            An unknown channel type was received from Discord.
        HTTPException
            Retrieving the channel failed.
        NotFound
            Invalid Channel ID.
        Forbidden
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
            # The factory will be a DMChannel or GroupChannel here
            channel = factory(me=self.user, data=data, state=self._connection)  # type: ignore
        else:
            # The factory can't be a DMChannel or GroupChannel here
            guild_id = int(data['guild_id'])  # type: ignore
            guild = self.get_guild(guild_id) or Object(id=guild_id)
            # GuildChannels expect a Guild, we may be passing an Object
            channel = factory(guild=guild, state=self._connection, data=data)  # type: ignore

        return channel

    async def fetch_webhook(self, webhook_id: int, /) -> Webhook:
        """|coro|

        Retrieves a :class:`.Webhook` with the specified ID.

        .. versionchanged:: 2.0

            ``webhook_id`` parameter is now positional-only.

        Raises
        --------
        HTTPException
            Retrieving the webhook failed.
        NotFound
            Invalid webhook ID.
        Forbidden
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
        HTTPException
            Retrieving the sticker failed.
        NotFound
            Invalid sticker ID.

        Returns
        --------
        Union[:class:`.StandardSticker`, :class:`.GuildSticker`]
            The sticker you requested.
        """
        data = await self.http.get_sticker(sticker_id)
        cls, _ = _sticker_factory(data['type'])
        return cls(state=self._connection, data=data)  # type: ignore

    async def fetch_sticker_packs(self) -> List[StickerPack]:
        """|coro|

        Retrieves all available default sticker packs.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the sticker packs failed.

        Returns
        ---------
        List[:class:`.StickerPack`]
            All available sticker packs.
        """
        data = await self.http.list_premium_sticker_packs()
        return [StickerPack(state=self._connection, data=pack) for pack in data['sticker_packs']]

    async def fetch_sticker_pack(self, pack_id: int, /):
        """|coro|

        Retrieves a sticker pack with the specified ID.

        .. versionadded:: 2.0

        Raises
        -------
        NotFound
            A sticker pack with that ID was not found.
        HTTPException
            Retrieving the sticker packs failed.

        Returns
        -------
        :class:`.StickerPack`
            The sticker pack you requested.
        """
        data = await self.http.get_sticker_pack(pack_id)
        return StickerPack(state=self._connection, data=data)

    async def notes(self) -> List[Note]:
        """|coro|

        Retrieves a list of :class:`.Note` objects representing all your notes.

        .. versionadded:: 1.9

        Raises
        -------
        HTTPException
            Retreiving the notes failed.

        Returns
        --------
        List[:class:`.Note`]
            All your notes.
        """
        state = self._connection
        data = await state.http.get_notes()
        return [Note(state, int(id), note=note) for id, note in data.items()]

    async def fetch_note(self, user_id: int, /) -> Note:
        """|coro|

        Retrieves a :class:`.Note` for the specified user ID.

        .. versionadded:: 1.9

        .. versionchanged:: 2.0

            ``user_id`` parameter is now positional-only.

        Parameters
        -----------
        user_id: :class:`int`
            The ID of the user to fetch the note for.

        Raises
        -------
        HTTPException
            Retreiving the note failed.

        Returns
        --------
        :class:`.Note`
            The note you requested.
        """
        note = Note(self._connection, int(user_id))
        await note.fetch()
        return note

    async def connections(self) -> List[Connection]:
        """|coro|

        Retrieves all of your connections.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retreiving your connections failed.

        Returns
        -------
        List[:class:`.Connection`]
            All your connections.
        """
        state = self._connection
        data = await state.http.get_connections()
        return [Connection(data=d, state=state) for d in data]

    async def fetch_private_channels(self) -> List[PrivateChannel]:
        """|coro|

        Retrieves all your private channels.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retreiving your private channels failed.

        Returns
        --------
        List[:class:`.abc.PrivateChannel`]
            All your private channels.
        """
        state = self._connection
        channels = await state.http.get_private_channels()
        return [_private_channel_factory(data['type'])[0](me=self.user, data=data, state=state) for data in channels]  # type: ignore # user is always present when logged in

    async def fetch_country_code(self) -> str:
        """|coro|

        Retrieves the country code of the client.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the country code failed.

        Returns
        -------
        :class:`str`
            The country code of the client.
        """
        data = await self.http.get_country_code()
        return data['country_code']

    async def fetch_preferred_voice_regions(self) -> List[str]:
        """|coro|

        Retrieves the preferred voice regions of the client.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the preferred voice regions failed.

        Returns
        -------
        List[:class:`str`]
            The preferred voice regions of the client.
        """
        data = await self.http.get_preferred_voice_regions()
        return [v['region'] for v in data]

    async def create_dm(self, user: Snowflake, /) -> DMChannel:
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

    async def create_group(self, *recipients: Snowflake) -> GroupChannel:
        r"""|coro|

        Creates a group direct message with the recipients
        provided. These recipients must be have a relationship
        of type :attr:`.RelationshipType.friend`.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*recipients: :class:`~discord.abc.Snowflake`
            An argument :class:`list` of :class:`discord.User` to have in
            your group.

        Raises
        -------
        HTTPException
            Failed to create the group direct message.

        Returns
        -------
        :class:`.GroupChannel`
            The new group channel.
        """
        users: List[_Snowflake] = [u.id for u in recipients]
        state = self._connection
        data = await state.http.start_group(users)
        return GroupChannel(me=self.user, data=data, state=state)  # type: ignore # user is always present when logged in

    @overload
    async def send_friend_request(self, user: BaseUser, /) -> None:
        ...

    @overload
    async def send_friend_request(self, user: str, /) -> None:
        ...

    @overload
    async def send_friend_request(self, username: str, discriminator: str, /) -> None:
        ...

    async def send_friend_request(self, *args: Union[BaseUser, str]) -> None:
        """|coro|

        Sends a friend request to another user.

        This function can be used in multiple ways.

        .. versionadded:: 2.0

        .. code-block:: python

            # Passing a user object:
            await client.send_friend_request(user)

            # Passing a stringified user:
            await client.send_friend_request('Jake#0001')

            # Passing a username and discriminator:
            await client.send_friend_request('Jake', '0001')


        Parameters
        -----------
        user: Union[:class:`discord.User`, :class:`str`]
            The user to send the friend request to.
        username: :class:`str`
            The username of the user to send the friend request to.
        discriminator: :class:`str`
            The discriminator of the user to send the friend request to.

        Raises
        -------
        Forbidden
            Not allowed to send a friend request to this user.
        HTTPException
            Sending the friend request failed.
        TypeError
            More than 2 parameters or less than 1 parameter was passed.
        """
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, BaseUser):
                user = str(user)
            username, discrim = user.split('#')
        elif len(args) == 2:
            username, discrim = args  # type: ignore
        else:
            raise TypeError(f'send_friend_request() takes 1 or 2 arguments but {len(args)} were given')

        state = self._connection
        await state.http.send_friend_request(username, discrim)

    async def applications(self, *, with_team_applications: bool = True) -> List[Application]:
        """|coro|

        Retrieves all applications owned by you.

        .. versionadded:: 2.0

        Parameters
        -----------
        with_team_applications: :class:`bool`
            Whether to include applications owned by teams you're a part of.
            Defaults to ``True``.

        Raises
        -------
        HTTPException
            Retrieving the applications failed.

        Returns
        -------
        List[:class:`.Application`]
            The applications you own.
        """
        state = self._connection
        data = await state.http.get_my_applications(with_team_applications=with_team_applications)
        return [Application(state=state, data=d) for d in data]

    async def detectable_applications(self) -> List[PartialApplication]:
        """|coro|

        Retrieves the list of applications detectable by the Discord client.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the applications failed.

        Returns
        -------
        List[:class:`.PartialApplication`]
            The applications detectable by the Discord client.
        """
        state = self._connection
        data = await state.http.get_detectable_applications()
        return [PartialApplication(state=state, data=d) for d in data]

    async def fetch_application(self, app_id: int, /) -> Application:
        """|coro|

        Retrieves the application with the given ID.

        The application must be owned by you.

        .. versionadded:: 2.0

        Parameters
        -----------
        id: :class:`int`
            The ID of the application to fetch.

        Raises
        -------
        NotFound
            The application was not found.
        Forbidden
            You do not own the application.
        HTTPException
            Retrieving the application failed.

        Returns
        -------
        :class:`.Application`
            The retrieved application.
        """
        state = self._connection
        data = await state.http.get_my_application(app_id)
        return Application(state=state, data=data)

    async def fetch_partial_application(self, app_id: int, /) -> PartialApplication:
        """|coro|

        Retrieves the partial application with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        app_id: :class:`int`
            The ID of the partial application to fetch.

        Raises
        -------
        NotFound
            The partial application was not found.
        HTTPException
            Retrieving the partial application failed.

        Returns
        --------
        :class:`.PartialApplication`
            The retrieved application.
        """
        state = self._connection
        data = await state.http.get_partial_application(app_id)
        return PartialApplication(state=state, data=data)

    async def teams(self) -> List[Team]:
        """|coro|

        Retrieves all the teams you're a part of.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the teams failed.

        Returns
        -------
        List[:class:`.Team`]
            The teams you're a part of.
        """
        state = self._connection
        data = await state.http.get_teams()
        return [Team(state=state, data=d) for d in data]

    async def fetch_team(self, team_id: int, /) -> Team:
        """|coro|

        Retrieves the team with the given ID.

        You must be a part of the team.

        .. versionadded:: 2.0

        Parameters
        -----------
        id: :class:`int`
            The ID of the team to fetch.

        Raises
        -------
        NotFound
            The team was not found.
        Forbidden
            You are not a part of the team.
        HTTPException
            Retrieving the team failed.

        Returns
        -------
        :class:`.Team`
            The retrieved team.
        """
        state = self._connection
        data = await state.http.get_team(team_id)
        return Team(state=state, data=data)

    async def create_application(self, name: str, /):
        """|coro|

        Creates an application.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The name of the application.

        Raises
        -------
        HTTPException
            Failed to create the application.

        Returns
        -------
        :class:`.Application`
            The newly-created application.
        """
        state = self._connection
        data = await state.http.create_app(name)
        return Application(state=state, data=data)

    async def create_team(self, name: str, /):
        """|coro|

        Creates a team.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The name of the team.

        Raises
        -------
        HTTPException
            Failed to create the team.

        Returns
        -------
        :class:`.Team`
            The newly-created team.
        """
        state = self._connection
        data = await state.http.create_team(name)
        return Team(state=state, data=data)
