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
from datetime import datetime
import logging
from typing import (
    Any,
    AsyncIterator,
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

from .user import _UserTag, User, ClientUser, Note
from .invite import Invite
from .template import Template
from .widget import Widget
from .guild import Guild, UserGuild
from .emoji import Emoji
from .channel import _private_channel_factory, _threaded_channel_factory, GroupChannel, PartialMessageable
from .enums import ActivityType, ChannelType, ClientType, ConnectionType, EntitlementType, Status
from .mentions import AllowedMentions
from .errors import *
from .enums import RelationshipType, Status
from .gateway import *
from .gateway import ConnectionClosed
from .activity import ActivityTypes, BaseActivity, Session, Spotify, create_activity
from .voice_client import VoiceClient
from .http import HTTPClient
from .state import ConnectionState
from . import utils
from .utils import MISSING
from .object import Object, OLDEST_OBJECT
from .backoff import ExponentialBackoff
from .webhook import Webhook
from .application import Application, ApplicationActivityStatistics, Company, EULA, PartialApplication
from .stage_instance import StageInstance
from .threads import Thread
from .sticker import GuildSticker, StandardSticker, StickerPack, _sticker_factory
from .profile import UserProfile
from .connections import Connection
from .team import Team
from .handlers import CaptchaHandler
from .billing import PaymentSource, PremiumUsage
from .subscriptions import Subscription, SubscriptionItem, SubscriptionInvoice
from .payments import Payment
from .promotions import PricingPromotion, Promotion, TrialOffer
from .entitlements import Entitlement, Gift
from .store import SKU, StoreListing, SubscriptionPlan
from .guild_premium import *
from .library import LibraryApplication
from .relationship import Relationship
from .settings import UserSettings, LegacyUserSettings, TrackingSettings, EmailSettings
from .affinity import *

if TYPE_CHECKING:
    from typing_extensions import Self
    from types import TracebackType
    from .guild import GuildChannel
    from .abc import Snowflake, SnowflakeTime
    from .channel import DMChannel
    from .message import Message
    from .member import Member
    from .voice_client import VoiceProtocol
    from .settings import GuildSettings
    from .billing import BillingAddress
    from .enums import PaymentGateway, RequiredActionType
    from .metadata import MetadataObject
    from .types.snowflake import Snowflake as _Snowflake

    PrivateChannel = Union[DMChannel, GroupChannel]

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

    .. container:: operations

        .. describe:: async with x

            Asynchronously initialises the client and automatically cleans up.

            .. versionadded:: 2.0

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
    max_ratelimit_timeout: Optional[:class:`float`]
        The maximum number of seconds to wait when a non-global rate limit is encountered.
        If a request requires sleeping for more than the seconds passed in, then
        :exc:`~discord.RateLimited` will be raised. By default, there is no timeout limit.
        In order to prevent misuse and unnecessary bans, the minimum value this can be
        set to is ``30.0`` seconds.

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
        max_ratelimit_timeout: Optional[float] = options.pop('max_ratelimit_timeout', None)
        self.http: HTTPClient = HTTPClient(
            self.loop,
            proxy=proxy,
            proxy_auth=proxy_auth,
            unsync_clock=unsync_clock,
            http_trace=http_trace,
            captcha_handler=captcha_handler,
            max_ratelimit_timeout=max_ratelimit_timeout,
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
        if status or activities:
            if status is None:
                status = getattr(state.settings, 'status', None) or Status.unknown
            self.loop.create_task(self.change_presence(activities=activities, status=status))

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
    def required_action(self) -> Optional[RequiredActionType]:
        """Optional[:class:`.RequiredActionType`]: The required action for the current user.
        A required action is something Discord requires you to do to continue using your account.

        .. versionadded:: 2.0
        """
        return self._connection.required_action

    @property
    def guilds(self) -> Sequence[Guild]:
        """Sequence[:class:`.Guild`]: The guilds that the connected client is a member of."""
        return self._connection.guilds

    @property
    def emojis(self) -> Sequence[Emoji]:
        """Sequence[:class:`.Emoji`]: The emojis that the connected client has."""
        return self._connection.emojis

    @property
    def stickers(self) -> Sequence[GuildSticker]:
        """Sequence[:class:`.GuildSticker`]: The stickers that the connected client has.

        .. versionadded:: 2.0
        """
        return self._connection.stickers

    @property
    def sessions(self) -> Sequence[Session]:
        """Sequence[:class:`.Session`]: The gateway sessions that the current user is connected in with.

        When connected, this includes a representation of the library's session and an "all" session representing the user's overall presence.

        .. versionadded:: 2.0
        """
        return utils.SequenceProxy(self._connection._sessions.values())

    @property
    def cached_messages(self) -> Sequence[Message]:
        """Sequence[:class:`.Message`]: Read-only list of messages the connected client has cached.

        .. versionadded:: 1.1
        """
        return utils.SequenceProxy(self._connection._messages or [])

    @property
    def connections(self) -> Sequence[Connection]:
        """Sequence[:class:`.Connection`]: The connections that the connected client has.

        These connections don't have the :attr:`.Connection.metadata` attribute populated.

        .. versionadded:: 2.0

        .. note::
            Due to a Discord limitation, removed connections may not be removed from this cache.

        """
        return utils.SequenceProxy(self._connection.connections.values())

    @property
    def private_channels(self) -> Sequence[PrivateChannel]:
        """Sequence[:class:`.abc.PrivateChannel`]: The private channels that the connected client is participating on."""
        return self._connection.private_channels

    @property
    def relationships(self) -> Sequence[Relationship]:
        """Sequence[:class:`.Relationship`]: Returns all the relationships that the connected client has.

        .. versionadded:: 2.0
        """
        return utils.SequenceProxy(self._connection._relationships.values())

    @property
    def friends(self) -> List[Relationship]:
        r"""List[:class:`.Relationship`]: Returns all the users that the connected client is friends with.

        .. versionadded:: 2.0
        """
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.friend]

    @property
    def blocked(self) -> List[Relationship]:
        r"""List[:class:`.Relationship`]: Returns all the users that the connected client has blocked.

        .. versionadded:: 2.0
        """
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.blocked]

    def get_relationship(self, user_id: int, /) -> Optional[Relationship]:
        """Retrieves the :class:`.Relationship`, if applicable.

        .. versionadded:: 2.0

        Parameters
        -----------
        user_id: :class:`int`
            The user ID to check if we have a relationship with them.

        Returns
        --------
        Optional[:class:`.Relationship`]
            The relationship, if available.
        """
        return self._connection._relationships.get(user_id)

    @property
    def settings(self) -> Optional[UserSettings]:
        """Optional[:class:`.UserSettings`]: Returns the user's settings.

        .. versionadded:: 2.0
        """
        return self._connection.settings

    @property
    def tracking_settings(self) -> Optional[TrackingSettings]:
        """Optional[:class:`.TrackingSettings`]: Returns your tracking consents, if available.

        .. versionadded:: 2.0
        """
        return self._connection.consents

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

    @property
    def pending_payments(self) -> Sequence[Payment]:
        """Sequence[:class:`.Payment`]: The pending payments that the connected client has.

        .. versionadded:: 2.0
        """
        return utils.SequenceProxy(self._connection.pending_payments.values())

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

        By default this logs to the library logger however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.

        .. versionchanged:: 2.0

            ``event_method`` parameter is now positional-only
            and instead of writing to ``sys.stderr`` it logs instead.
        """
        _log.exception('Ignoring exception in %s', event_method)

    async def on_internal_settings_update(self, old_settings: UserSettings, new_settings: UserSettings):
        if not self._sync_presences:
            return

        if (
            old_settings is not None
            and old_settings.status == new_settings.status
            and old_settings.custom_activity == new_settings.custom_activity
        ):
            return  # Nothing changed

        status = new_settings.status
        activities = [a for a in self.activities if a.type != ActivityType.custom]
        if new_settings.custom_activity is not None:
            activities.append(new_settings.custom_activity)

        await self.change_presence(status=status, activities=activities, edit_settings=False)

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

        A coroutine to be called to setup the client, by default this is blank.

        To perform asynchronous setup after the user is logged in but before
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

        if self.loop is _loop:
            await self._async_setup_hook()

        if not isinstance(token, str):
            raise TypeError(f'expected token to be a str, received {token.__class__!r} instead')

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
        GatewayNotFound
            If the gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        ConnectionClosed
            The websocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        ws_params: Dict[str, Any] = {
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
                _log.debug('Got a request to %s the websocket.', e.op)
                self.dispatch('disconnect')
                ws_params.update(sequence=self.ws.sequence, resume=e.resume, session=self.ws.session_id)
                if e.resume:
                    ws_params['gateway'] = self.ws.gateway
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
                    ws_params.update(
                        sequence=self.ws.sequence,
                        gateway=self.ws.gateway,
                        initial=False,
                        resume=True,
                        session=self.ws.session_id,
                    )
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
                ws_params.update(
                    sequence=self.ws.sequence,
                    gateway=self.ws.gateway,
                    resume=True,
                    session=self.ws.session_id,
                )

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

        After this, the client can be considered "re-opened", i.e. :meth:`is_closed`
        and :meth:`is_ready` both return ``False`` along with the bot's internal
        cache cleared.
        """
        self._closed = False
        self._ready.clear()
        self._connection.clear()
        self.http.clear()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.

        Parameters
        -----------
        token: :class:`str`
            The authentication token.
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as bad tokens).

        Raises
        -------
        TypeError
            An unexpected keyword argument was received.
        """
        await self.login(token)
        await self.connect(reconnect=reconnect)

    def run(
        self,
        token: str,
        *,
        reconnect: bool = True,
        log_handler: Optional[logging.Handler] = MISSING,
        log_formatter: logging.Formatter = MISSING,
        log_level: int = MISSING,
        root_logger: bool = False,
    ) -> None:
        """A blocking call that abstracts away the event loop
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        This function also sets up the logging library to make it easier
        for beginners to know what is going on with the library. For more
        advanced users, this can be disabled by passing ``None`` to
        the ``log_handler`` parameter.

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.

        Parameters
        -----------
        token: :class:`str`
            The authentication token.
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as bad tokens).
        log_handler: Optional[:class:`logging.Handler`]
            The log handler to use for the library's logger. If this is ``None``
            then the library will not set up anything logging related. Logging
            will still work if ``None`` is passed, though it is your responsibility
            to set it up.

            The default log handler if not provided is :class:`logging.StreamHandler`.

            .. versionadded:: 2.0
        log_formatter: :class:`logging.Formatter`
            The formatter to use with the given log handler. If not provided then it
            defaults to a colour based logging formatter (if available).

            .. versionadded:: 2.0
        log_level: :class:`int`
            The default log level for the library's logger. This is only applied if the
            ``log_handler`` parameter is not ``None``. Defaults to ``logging.INFO``.

            .. versionadded:: 2.0
        root_logger: :class:`bool`
            Whether to set up the root logger rather than the library logger.
            By default, only the library logger (``'discord'``) is set up. If this
            is set to ``True`` then the root logger is set up as well.

            Defaults to ``False``.

            .. versionadded:: 2.0
        """

        async def runner():
            async with self:
                await self.start(token, reconnect=reconnect)

        if log_handler is not None:
            utils.setup_logging(
                handler=log_handler,
                formatter=log_formatter,
                level=log_level,
                root=root_logger,
            )

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
    def notification_settings(self) -> GuildSettings:
        """:class:`.GuildSettings`: Returns the notification settings for private channels.

        If not found, an instance is created with defaults applied. This follows Discord behaviour.

        .. versionadded:: 2.0
        """
        # The private channel pseudo-guild settings have a guild ID of null
        state = self._connection
        return state.guild_settings.get(None, state.default_guild_settings(None))

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
        elif all(isinstance(value, (BaseActivity, Spotify)) for value in values):
            self._connection._activities = [value.to_dict() for value in values]
        else:
            raise TypeError('activity must derive from BaseActivity')

    @property
    def initial_status(self) -> Optional[Status]:
        """Optional[:class:`.Status`]: The status set upon logging in.

        .. versionadded:: 2.0
        """
        if self._connection._status in {state.value for state in Status}:
            return Status(self._connection._status)

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
        status = getattr(self._connection.all_session, 'status', None)
        if status is None and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status or Status.offline

    @property
    def raw_status(self) -> str:
        """:class:`str`: The user's overall status as a string value.

        .. versionadded:: 2.0
        """
        return str(self.status)

    @property
    def client_status(self) -> Status:
        """:class:`.Status`: The library's status.

        .. versionadded:: 2.0
        """
        status = getattr(self._connection.current_session, 'status', None)
        if status is None and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status or Status.offline

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if the user is active on a mobile device.

        .. versionadded:: 2.0
        """
        return any(session.client == ClientType.mobile for session in self._connection._sessions.values())

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
        activities = state.all_session.activities if state.all_session else None
        if activities is None and not self.is_closed():
            activity = getattr(state.settings, 'custom_activity', None)
            activities = (activity,) if activity else activities
        return activities or ()

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
    def client_activities(self) -> Tuple[ActivityTypes]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the activities
        the client is currently doing through this library, if applicable.

        .. versionadded:: 2.0
        """
        state = self._connection
        activities = state.current_session.activities if state.current_session else None
        if activities is None and not self.is_closed():
            activity = getattr(state.settings, 'custom_activity', None)
            activities = (activity,) if activity else activities
        return activities or ()

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
        """List[:class:`~discord.User`]: Returns a list of all the users the current user can see."""
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

    def get_partial_messageable(
        self, id: int, *, guild_id: Optional[int] = None, type: Optional[ChannelType] = None
    ) -> PartialMessageable:
        """Returns a partial messageable with the given channel ID.

        This is useful if you have a channel_id but don't want to do an API call
        to send messages to it.

        .. versionadded:: 2.0

        Parameters
        -----------
        id: :class:`int`
            The channel ID to create a partial messageable for.
        guild_id: Optional[:class:`int`]
            The optional guild ID to create a partial messageable for.

            This is not required to actually send messages, but it does allow the
            :meth:`~discord.PartialMessageable.jump_url` and
            :attr:`~discord.PartialMessageable.guild` properties to function properly.
        type: Optional[:class:`.ChannelType`]
            The underlying channel type for the partial messageable.

        Returns
        --------
        :class:`.PartialMessageable`
            The partial messageable
        """
        return PartialMessageable(state=self._connection, id=id, guild_id=guild_id, type=type)

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
            or :meth:`.sticker_packs`.

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
        else:
            raise RuntimeError(
                'Client has not been properly initialised. '
                'Please use the login method or asynchronous context manager before calling this method'
            )

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
        activity: Optional[ActivityTypes] = None,
        activities: Optional[List[ActivityTypes]] = None,
        status: Optional[Status] = None,
        afk: bool = False,
        edit_settings: bool = True,
    ) -> None:
        """|coro|

        Changes the client's presence.

        .. versionchanged:: 2.0
            Edits are no longer in place.
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
            Required for setting/editing ``expires_at`` for custom activities.
            It's not recommended to change this, as setting it to ``False`` causes undefined behavior.

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
            if status != getattr(self.settings, 'status', None):
                payload['status'] = status
            if custom_activity != getattr(self.settings, 'custom_activity', None):
                payload['custom_activity'] = custom_activity
            if payload and self.settings:
                await self.settings.edit(**payload)

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

        .. versionadded:: 2.0

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

    async def fetch_guilds(self, *, with_counts: bool = True) -> List[UserGuild]:
        """|coro|

        Retrieves all your guilds.

        .. note::

            This method is an API call. For general usage, consider :attr:`guilds` instead.

        .. versionchanged:: 2.0

            This method now returns a list of :class:`.UserGuild` instead of :class:`.Guild`.

        Parameters
        -----------
        with_counts: :class:`bool`
            Whether to fill :attr:`.Guild.approximate_member_count` and :attr:`.Guild.approximate_presence_count`.

        Raises
        ------
        HTTPException
            Getting the guilds failed.

        Returns
        --------
        List[:class:`.UserGuild`]
            A list of all your guilds.
        """
        state = self._connection
        guilds = await state.http.get_guilds(with_counts)
        return [UserGuild(data=data, state=state) for data in guilds]

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
            Whether to include count information in the guild. This fills in
            :attr:`.Guild.approximate_member_count` and :attr:`.Guild.approximate_presence_count`.

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

    async def invites(self) -> List[Invite]:
        r"""|coro|

        Gets a list of the user's friend :class:`.Invite`\s.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Getting the invites failed.

        Returns
        --------
        List[:class:`.Invite`]
            The list of invites.
        """
        state = self._connection
        data = await state.http.get_friend_invites()
        return [Invite.from_incomplete(state=state, data=d) for d in data]

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

    async def accept_invite(self, url: Union[Invite, str], /) -> Invite:
        """|coro|

        Uses an invite.
        Either joins a guild, joins a group DM, or adds a friend.

        .. versionadded:: 2.0

        Parameters
        ----------
        url: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID, URL (must be a discord.gg URL), or :class:`.Invite`.

        Raises
        ------
        HTTPException
            Using the invite failed.

        Returns
        -------
        :class:`.Invite`
            The accepted invite.
        """
        state = self._connection
        resolved = utils.resolve_invite(url)

        data = await state.http.get_invite(
            resolved.code,
            with_counts=True,
            with_expiration=True,
            input_value=resolved.code if isinstance(url, Invite) else url,
        )
        if isinstance(url, Invite):
            invite = url
        else:
            invite = Invite.from_incomplete(state=state, data=data)

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
        return Invite.from_incomplete(state=state, data=data, message=invite._message)

    async def delete_invite(self, invite: Union[Invite, str], /) -> Invite:
        """|coro|

        Revokes an :class:`.Invite`, URL, or ID to an invite.

        You must have :attr:`~.Permissions.manage_channels` in
        the associated guild to do this.

        .. versionchanged:: 2.0

            ``invite`` parameter is now positional-only.

        .. versionchanged:: 2.0

            The function now returns the deleted invite.

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

        Returns
        --------
        :class:`.Invite`
            The deleted invite.
        """
        resolved = utils.resolve_invite(invite)
        state = self._connection
        data = await state.http.delete_invite(resolved.code)
        return Invite.from_incomplete(state=state, data=data)

    async def revoke_invites(self) -> List[Invite]:
        r"""|coro|

        Revokes all of the user's friend :class:`.Invite`\s.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Revoking the invites failed.

        Returns
        --------
        List[:class:`.Invite`]
            The revoked invites.
        """
        state = self._connection
        data = await state.http.delete_friend_invites()
        return [Invite(state=state, data=d) for d in data]

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

            This API route is not well-used by the Discord client and may increase your chances at getting detected.
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
        self,
        user_id: int,
        /,
        *,
        with_mutual_guilds: bool = True,
        with_mutual_friends_count: bool = False,
        with_mutual_friends: bool = True,
    ) -> UserProfile:
        """|coro|

        Retrieves a :class:`.UserProfile` based on their user ID.

        You must share a guild, be friends with this user,
        or have an incoming friend request from them to
        get this information (unless the user is a bot).

        .. versionchanged:: 2.0

            ``user_id`` parameter is now positional-only.

        Parameters
        ------------
        user_id: :class:`int`
            The ID of the user to fetch their profile for.
        with_mutual_guilds: :class:`bool`
            Whether to fetch mutual guilds.
            This fills in :attr:`.UserProfile.mutual_guilds`.

            .. versionadded:: 2.0
        with_mutual_friends_count: :class:`bool`
            Whether to fetch the number of mutual friends.
            This fills in :attr:`.UserProfile.mutual_friends_count`.

            .. versionadded:: 2.0
        with_mutual_friends: :class:`bool`
            Whether to fetch mutual friends.
            This fills in :attr:`.UserProfile.mutual_friends` and :attr:`.UserProfile.mutual_friends_count`,
            but requires an extra API call.

            .. versionadded:: 2.0

        Raises
        -------
        NotFound
            A user with this ID does not exist.
        Forbidden
            You do not have a mutual with this user, and and the user is not a bot.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`.UserProfile`
            The profile of the user.
        """
        state = self._connection
        data = await state.http.get_user_profile(
            user_id, with_mutual_guilds=with_mutual_guilds, with_mutual_friends_count=with_mutual_friends_count
        )
        mutual_friends = None
        if with_mutual_friends and not data['user'].get('bot', False):
            mutual_friends = await state.http.get_mutual_friends(user_id)

        return UserProfile(state=state, data=data, mutual_friends=mutual_friends)

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
            guild = self._connection._get_or_create_unavailable_guild(guild_id)
            # the factory should be a GuildChannel or Thread
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

    async def sticker_packs(self) -> List[StickerPack]:
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
        state = self._connection
        data = await self.http.list_premium_sticker_packs(state.country_code or 'US', state.locale)
        return [StickerPack(state=state, data=pack) for pack in data['sticker_packs']]

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
            Retrieving the notes failed.

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
            Retrieving the note failed.

        Returns
        --------
        :class:`.Note`
            The note you requested.
        """
        note = Note(self._connection, int(user_id))
        await note.fetch()
        return note

    async def fetch_connections(self) -> List[Connection]:
        """|coro|

        Retrieves all of your connections.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving your connections failed.

        Returns
        -------
        List[:class:`.Connection`]
            All your connections.
        """
        state = self._connection
        data = await state.http.get_connections()
        return [Connection(data=d, state=state) for d in data]

    async def authorize_connection(
        self,
        type: ConnectionType,
        two_way_link_type: Optional[ClientType] = None,
        two_way_user_code: Optional[str] = None,
        continuation: bool = False,
    ) -> str:
        """|coro|

        Retrieves a URL to authorize a connection with a third-party service.

        .. versionadded:: 2.0

        Parameters
        -----------
        type: :class:`.ConnectionType`
            The type of connection to authorize.
        two_way_link_type: Optional[:class:`.ClientType`]
            The type of two-way link to use, if any.
        two_way_user_code: Optional[:class:`str`]
            The device code to use for two-way linking, if any.
        continuation: :class:`bool`
            Whether this is a continuation of a previous authorization.

        Raises
        -------
        HTTPException
            Authorizing the connection failed.

        Returns
        --------
        :class:`str`
            The URL to redirect the user to.
        """
        data = await self.http.authorize_connection(
            str(type), str(two_way_link_type) if two_way_link_type else None, two_way_user_code, continuation=continuation
        )
        return data['url']

    async def create_connection(
        self,
        type: ConnectionType,
        code: str,
        state: str,
        *,
        two_way_link_code: Optional[str] = None,
        insecure: bool = True,
        friend_sync: bool = MISSING,
    ) -> None:
        """|coro|

        Creates a new connection.

        This is a low-level method that requires data obtained from other APIs.

        .. versionadded:: 2.0

        Parameters
        -----------
        type: :class:`.ConnectionType`
            The type of connection to add.
        code: :class:`str`
            The authorization code for the connection.
        state: :class:`str`
            The state used to authorize the connection.
        two_way_link_code: Optional[:class:`str`]
            The code to use for two-way linking, if any.
        insecure: :class:`bool`
            Whether the authorization is insecure.
        friend_sync: :class:`bool`
            Whether friends are synced over the connection.

            Defaults to ``True`` for :attr:`.ConnectionType.facebook` and :attr:`.ConnectionType.contacts`, else ``False``.

        Raises
        -------
        HTTPException
            Creating the connection failed.
        """
        friend_sync = (
            friend_sync if friend_sync is not MISSING else type in (ConnectionType.facebook, ConnectionType.contacts)
        )
        await self.http.add_connection(
            str(type),
            code=code,
            state=state,
            two_way_link_code=two_way_link_code,
            insecure=insecure,
            friend_sync=friend_sync,
        )

    async def fetch_private_channels(self) -> List[PrivateChannel]:
        """|coro|

        Retrieves all your private channels.

        .. versionadded:: 2.0

        .. note::

            This method is an API call. For general usage, consider :attr:`private_channels` instead.

        Raises
        -------
        HTTPException
            Retrieving your private channels failed.

        Returns
        --------
        List[:class:`.abc.PrivateChannel`]
            All your private channels.
        """
        state = self._connection
        channels = await state.http.get_private_channels()
        return [_private_channel_factory(data['type'])[0](me=self.user, data=data, state=state) for data in channels]  # type: ignore # user is always present when logged in

    async def fetch_settings(self) -> UserSettings:
        """|coro|

        Retrieves your user settings.

        .. versionadded:: 2.0

        .. note::

            This method is an API call. For general usage, consider :attr:`settings` instead.

        Raises
        -------
        HTTPException
            Retrieving your settings failed.

        Returns
        --------
        :class:`.UserSettings`
            The current settings for your account.
        """
        state = self._connection
        data = await state.http.get_proto_settings(1)
        return UserSettings(state, data['settings'])

    @utils.deprecated('Client.fetch_settings')
    async def legacy_settings(self) -> LegacyUserSettings:
        """|coro|

        Retrieves your legacy user settings.

        .. versionadded:: 2.0

        .. deprecated:: 2.0

        .. note::

            This method is no longer the recommended way to fetch your settings. Use :meth:`fetch_settings` instead.

        .. note::

            This method is an API call. For general usage, consider :attr:`settings` instead.

        Raises
        -------
        HTTPException
            Retrieving your settings failed.

        Returns
        --------
        :class:`.LegacyUserSettings`
            The current settings for your account.
        """
        state = self._connection
        data = await state.http.get_settings()
        return LegacyUserSettings(data=data, state=state)

    async def email_settings(self) -> EmailSettings:
        """|coro|

        Retrieves your email settings.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Getting the email settings failed.

        Returns
        -------
        :class:`.EmailSettings`
            The email settings.
        """
        state = self._connection
        data = await state.http.get_email_settings()
        return EmailSettings(data=data, state=state)

    async def fetch_tracking_settings(self) -> TrackingSettings:
        """|coro|

        Retrieves your Discord tracking consents.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the tracking settings failed.

        Returns
        -------
        :class:`.TrackingSettings`
            The tracking settings.
        """
        state = self._connection
        data = await state.http.get_tracking()
        return TrackingSettings(state=state, data=data)

    @utils.deprecated('Client.edit_settings')
    @utils.copy_doc(LegacyUserSettings.edit)
    async def edit_legacy_settings(self, **kwargs) -> LegacyUserSettings:
        payload = {}

        content_filter = kwargs.pop('explicit_content_filter', None)
        if content_filter:
            payload['explicit_content_filter'] = content_filter.value

        animate_stickers = kwargs.pop('animate_stickers', None)
        if animate_stickers:
            payload['animate_stickers'] = animate_stickers.value

        friend_source_flags = kwargs.pop('friend_source_flags', None)
        if friend_source_flags:
            payload['friend_source_flags'] = friend_source_flags.to_dict()

        friend_discovery_flags = kwargs.pop('friend_discovery_flags', None)
        if friend_discovery_flags:
            payload['friend_discovery_flags'] = friend_discovery_flags.value

        guild_positions = kwargs.pop('guild_positions', None)
        if guild_positions:
            guild_positions = [str(x.id) for x in guild_positions]
            payload['guild_positions'] = guild_positions

        restricted_guilds = kwargs.pop('restricted_guilds', None)
        if restricted_guilds:
            restricted_guilds = [str(x.id) for x in restricted_guilds]
            payload['restricted_guilds'] = restricted_guilds

        activity_restricted_guilds = kwargs.pop('activity_restricted_guilds', None)
        if activity_restricted_guilds:
            activity_restricted_guilds = [str(x.id) for x in activity_restricted_guilds]
            payload['activity_restricted_guild_ids'] = activity_restricted_guilds

        activity_joining_restricted_guilds = kwargs.pop('activity_joining_restricted_guilds', None)
        if activity_joining_restricted_guilds:
            activity_joining_restricted_guilds = [str(x.id) for x in activity_joining_restricted_guilds]
            payload['activity_joining_restricted_guild_ids'] = activity_joining_restricted_guilds

        status = kwargs.pop('status', None)
        if status:
            payload['status'] = status.value

        custom_activity = kwargs.pop('custom_activity', MISSING)
        if custom_activity is not MISSING:
            payload['custom_status'] = custom_activity and custom_activity.to_legacy_settings_dict()

        theme = kwargs.pop('theme', None)
        if theme:
            payload['theme'] = theme.value

        locale = kwargs.pop('locale', None)
        if locale:
            payload['locale'] = str(locale)

        payload.update(kwargs)

        state = self._connection
        data = await state.http.edit_settings(**payload)
        return LegacyUserSettings(data=data, state=state)

    async def fetch_relationships(self) -> List[Relationship]:
        """|coro|

        Retrieves all your relationships.

        .. versionadded:: 2.0

        .. note::

            This method is an API call. For general usage, consider :attr:`relationships` instead.

        Raises
        -------
        HTTPException
            Retrieving your relationships failed.

        Returns
        --------
        List[:class:`.Relationship`]
            All your relationships.
        """
        state = self._connection
        data = await state.http.get_relationships()
        return [Relationship(state=state, data=d) for d in data]

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
    async def send_friend_request(self, user: _UserTag, /) -> None:
        ...

    @overload
    async def send_friend_request(self, user: str, /) -> None:
        ...

    @overload
    async def send_friend_request(self, username: str, discriminator: str, /) -> None:
        ...

    async def send_friend_request(self, *args: Union[_UserTag, str]) -> None:
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
            if isinstance(user, _UserTag):
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

    async def fetch_application(self, application_id: int, /) -> Application:
        """|coro|

        Retrieves the application with the given ID.

        The application must be owned by you or a team you are a part of.

        .. versionadded:: 2.0

        Parameters
        -----------
        application_id: :class:`int`
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
        data = await state.http.get_my_application(application_id)
        return Application(state=state, data=data)

    async def fetch_partial_application(self, application_id: int, /) -> PartialApplication:
        """|coro|

        Retrieves the partial application with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        application_id: :class:`int`
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
        data = await state.http.get_partial_application(application_id)
        return PartialApplication(state=state, data=data)

    async def fetch_public_application(self, application_id: int, /, *, with_guild: bool = False) -> PartialApplication:
        """|coro|

        Retrieves the public application with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        application_id: :class:`int`
            The ID of the public application to fetch.
        with_guild: :class:`bool`
            Whether to include the public guild of the application.

        Raises
        -------
        NotFound
            The public application was not found.
        HTTPException
            Retrieving the public application failed.

        Returns
        --------
        :class:`.PartialApplication`
            The retrieved application.
        """
        state = self._connection
        data = await state.http.get_public_application(application_id, with_guild=with_guild)
        return PartialApplication(state=state, data=data)

    async def fetch_public_applications(self, *application_ids: int) -> List[PartialApplication]:
        r"""|coro|

        Retrieves a list of public applications. Only found applications are returned.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*application_ids: :class:`int`
            The IDs of the public applications to fetch.

        Raises
        -------
        HTTPException
            Retrieving the applications failed.

        Returns
        -------
        List[:class:`.PartialApplication`]
            The public applications.
        """
        if not application_ids:
            return []

        state = self._connection
        data = await state.http.get_public_applications(application_ids)
        return [PartialApplication(state=state, data=d) for d in data]

    async def teams(self, *, with_payout_account_status: bool = False) -> List[Team]:
        """|coro|

        Retrieves all the teams you're a part of.

        .. versionadded:: 2.0

        Parameters
        -----------
        with_payout_account_status: :class:`bool`
            Whether to return the payout account status of the teams.

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
        data = await state.http.get_teams(include_payout_account_status=with_payout_account_status)
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

    async def create_application(self, name: str, /, *, team: Optional[Snowflake] = None) -> Application:
        """|coro|

        Creates an application.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The name of the application.
        team: :class:`~discord.abc.Snowflake`
            The team to create the application under.

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
        data = await state.http.create_app(name, team.id if team else None)
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

    async def search_companies(self, query: str, /) -> List[Company]:
        """|coro|

        Query your created companies.

        .. versionadded:: 2.0

        Parameters
        -----------
        query: :class:`str`
            The query to search for.

        Raises
        -------
        HTTPException
            Searching failed.

        Returns
        -------
        List[:class:`.Company`]
            The companies found.
        """
        state = self._connection
        data = await state.http.search_companies(query)
        return [Company(data=d) for d in data]

    async def activity_statistics(self) -> List[ApplicationActivityStatistics]:
        """|coro|

        Retrieves the available activity usage statistics for your owned applications.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the statistics failed.

        Returns
        -------
        List[:class:`.ApplicationActivityStatistics`]
            The activity statistics.
        """
        state = self._connection
        data = await state.http.get_activity_statistics()
        return [ApplicationActivityStatistics(state=state, data=d) for d in data]

    async def relationship_activity_statistics(self) -> List[ApplicationActivityStatistics]:
        """|coro|

        Retrieves the available activity usage statistics for your relationships' owned applications.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the statistics failed.

        Returns
        -------
        List[:class:`.ApplicationActivityStatistics`]
            The activity statistics.
        """
        state = self._connection
        data = await state.http.get_global_activity_statistics()
        return [ApplicationActivityStatistics(state=state, data=d) for d in data]

    async def payment_sources(self) -> List[PaymentSource]:
        """|coro|

        Retrieves all the payment sources for your account.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the payment sources failed.

        Returns
        -------
        List[:class:`.PaymentSource`]
            The payment sources.
        """
        state = self._connection
        data = await state.http.get_payment_sources()
        return [PaymentSource(state=state, data=d) for d in data]

    async def fetch_payment_source(self, source_id: int, /) -> PaymentSource:
        """|coro|

        Retrieves the payment source with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        source_id: :class:`int`
            The ID of the payment source to fetch.

        Raises
        -------
        NotFound
            The payment source was not found.
        HTTPException
            Retrieving the payment source failed.

        Returns
        -------
        :class:`.PaymentSource`
            The retrieved payment source.
        """
        state = self._connection
        data = await state.http.get_payment_source(source_id)
        return PaymentSource(state=state, data=data)

    async def create_payment_source(
        self,
        *,
        token: str,
        payment_gateway: PaymentGateway,
        billing_address: BillingAddress,
        billing_address_token: Optional[str] = MISSING,
        return_url: Optional[str] = None,
        bank: Optional[str] = None,
    ) -> PaymentSource:
        """|coro|

        Creates a payment source.

        This is a low-level method that requires data obtained from other APIs.

        .. versionadded:: 2.0

        Parameters
        ----------
        token: :class:`str`
            The payment source token.
        payment_gateway: :class:`.PaymentGateway`
            The payment gateway to use.
        billing_address: :class:`.BillingAddress`
            The billing address to use.
        billing_address_token: Optional[:class:`str`]
            The billing address token. If not provided, the library will fetch it for you.
            Not required for all payment gateways.
        return_url: Optional[:class:`str`]
            The URL to return to after the payment source is created.
        bank: Optional[:class:`str`]
            The bank information for the payment source.
            Not required for most payment gateways.

        Raises
        -------
        HTTPException
            Creating the payment source failed.

        Returns
        -------
        :class:`.PaymentSource`
            The newly-created payment source.
        """
        state = self._connection
        billing_address._state = state

        data = await state.http.create_payment_source(
            token=token,
            payment_gateway=int(payment_gateway),
            billing_address=billing_address.to_dict(),
            billing_address_token=billing_address_token or await billing_address.validate()
            if billing_address is not None
            else None,
            return_url=return_url,
            bank=bank,
        )
        return PaymentSource(state=state, data=data)

    async def subscriptions(self, limit: Optional[int] = None, with_inactive: bool = False) -> List[Subscription]:
        """|coro|

        Retrieves all the subscriptions on your account.

        .. versionadded:: 2.0

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The maximum number of subscriptions to retrieve.
            Defaults to all subscriptions.
        with_inactive: :class:`bool`
            Whether to include inactive subscriptions.

        Raises
        -------
        HTTPException
            Retrieving the subscriptions failed.

        Returns
        -------
        List[:class:`.Subscription`]
            Your account's subscriptions.
        """
        state = self._connection
        data = await state.http.get_subscriptions(limit=limit, include_inactive=with_inactive)
        return [Subscription(state=state, data=d) for d in data]

    async def premium_guild_subscriptions(self) -> List[PremiumGuildSubscription]:
        """|coro|

        Retrieves all the premium guild subscriptions (boosts) on your account.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the subscriptions failed.

        Returns
        -------
        List[:class:`.PremiumGuildSubscription`]
            Your account's premium guild subscriptions.
        """
        state = self._connection
        data = await state.http.get_applied_guild_subscriptions()
        return [PremiumGuildSubscription(state=state, data=d) for d in data]

    async def premium_guild_subscription_slots(self) -> List[PremiumGuildSubscriptionSlot]:
        """|coro|

        Retrieves all the premium guild subscription (boost) slots available on your account.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the subscriptions failed.

        Returns
        -------
        List[:class:`.PremiumGuildSubscriptionSlot`]
            Your account's premium guild subscription slots.
        """
        state = self._connection
        data = await state.http.get_guild_subscription_slots()
        return [PremiumGuildSubscriptionSlot(state=state, data=d) for d in data]

    async def premium_guild_subscription_cooldown(self) -> PremiumGuildSubscriptionCooldown:
        """|coro|

        Retrieves the cooldown for your premium guild subscriptions (boosts).

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the cooldown failed.

        Returns
        -------
        :class:`.PremiumGuildSubscriptionCooldown`
            Your account's premium guild subscription cooldown.
        """
        state = self._connection
        data = await state.http.get_guild_subscriptions_cooldown()
        return PremiumGuildSubscriptionCooldown(state=state, data=data)

    async def fetch_subscription(self, subscription_id: int, /) -> Subscription:
        """|coro|

        Retrieves the subscription with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        subscription_id: :class:`int`
            The ID of the subscription to fetch.

        Raises
        -------
        NotFound
            The subscription was not found.
        HTTPException
            Retrieving the subscription failed.

        Returns
        -------
        :class:`.Subscription`
            The retrieved subscription.
        """
        state = self._connection
        data = await state.http.get_subscription(subscription_id)
        return Subscription(state=state, data=data)

    async def preview_subscription(
        self,
        items: List[SubscriptionItem],
        *,
        payment_source: Optional[Snowflake] = None,
        currency: str = 'usd',
        trial: Optional[Snowflake] = None,
        apply_entitlements: bool = True,
        renewal: bool = False,
        code: Optional[str] = None,
        metadata: Optional[MetadataObject] = None,
        guild: Optional[Snowflake] = None,
    ) -> SubscriptionInvoice:
        """|coro|

        Preview an invoice for the subscription with the given parameters.

        All parameters are optional and default to the current subscription values.

        .. versionadded:: 2.0

        Parameters
        ----------
        items: List[:class:`.SubscriptionItem`]
            The items the previewed subscription should have.
        payment_source: Optional[:class:`.PaymentSource`]
            The payment source the previewed subscription should be paid with.
        currency: :class:`str`
            The currency the previewed subscription should be paid in.
        trial: Optional[:class:`.SubscriptionTrial`]
            The trial plan the previewed subscription should be on.
        apply_entitlements: :class:`bool`
            Whether to apply entitlements (credits) to the previewed subscription.
        renewal: :class:`bool`
            Whether the previewed subscription should be a renewal.
        code: Optional[:class:`str`]
            Unknown.
        metadata: Optional[:class:`.Metadata`]
            Extra metadata about the subscription.
        guild: Optional[:class:`.Guild`]
            The guild the previewed subscription's entitlements should be applied to.

        Raises
        ------
        HTTPException
            Failed to preview the invoice.

        Returns
        -------
        :class:`.SubscriptionInvoice`
            The previewed invoice.
        """
        state = self._connection

        metadata = dict(metadata) if metadata else {}
        if guild:
            metadata['guild_id'] = str(guild.id)
        data = await state.http.preview_subscriptions_update(
            [item.to_dict(False) for item in items],
            currency,
            payment_source_id=payment_source.id if payment_source else None,
            trial_id=trial.id if trial else None,
            apply_entitlements=apply_entitlements,
            renewal=renewal,
            code=code,
            metadata=metadata if metadata else None,
        )
        return SubscriptionInvoice(None, data=data, state=state)

    async def create_subscription(
        self,
        items: List[SubscriptionItem],
        payment_source: Snowflake,
        currency: str = 'usd',
        *,
        trial: Optional[Snowflake] = None,
        payment_source_token: Optional[str] = None,
        purchase_token: Optional[str] = None,
        return_url: Optional[str] = None,
        gateway_checkout_context: Optional[str] = None,
        code: Optional[str] = None,
        metadata: Optional[MetadataObject] = None,
        guild: Optional[Snowflake] = None,
    ) -> Subscription:
        """|coro|

        Creates a new subscription.

        .. versionadded:: 2.0

        Parameters
        ----------
        items: List[:class:`.SubscriptionItem`]
            The items in the subscription.
        payment_source: :class:`.PaymentSource`
            The payment source to pay with.
        currency: :class:`str`
            The currency to pay with.
        trial: Optional[:class:`.SubscriptionTrial`]
            The trial to apply to the subscription.
        payment_source_token: Optional[:class:`str`]
            The token used to authorize with the payment source.
        purchase_token: Optional[:class:`str`]
            The purchase token to use.
        return_url: Optional[:class:`str`]
            The URL to return to after the payment is complete.
        gateway_checkout_context: Optional[:class:`str`]
            The current checkout context.
        code: Optional[:class:`str`]
            Unknown.
        metadata: Optional[:class:`.Metadata`]
            Extra metadata about the subscription.
        guild: Optional[:class:`.Guild`]
            The guild the subscription's entitlements should be applied to.

        Raises
        -------
        HTTPException
            Creating the subscription failed.

        Returns
        -------
        :class:`.Subscription`
            The newly-created subscription.
        """
        state = self._connection

        metadata = dict(metadata) if metadata else {}
        if guild:
            metadata['guild_id'] = str(guild.id)
        data = await state.http.create_subscription(
            [i.to_dict(False) for i in items],
            payment_source.id,
            currency,
            trial_id=trial.id if trial else None,
            payment_source_token=payment_source_token,
            return_url=return_url,
            purchase_token=purchase_token,
            gateway_checkout_context=gateway_checkout_context,
            code=code,
            metadata=metadata if metadata else None,
        )
        return Subscription(state=state, data=data)

    async def payments(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
    ) -> AsyncIterator[Payment]:
        """Returns an :term:`asynchronous iterator` that enables receiving your payments.

        .. versionadded:: 2.0

        Examples
        ---------

        Usage ::

            counter = 0
            async for payment in client.payments(limit=200):
                if payment.is_purchased_externally():
                    counter += 1

        Flattening into a list: ::

            payments = [payment async for payment in client.payments(limit=123)]
            # payments is now a list of Payment...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of payments to retrieve.
            If ``None``, retrieves every payment you have made. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve payments before this date or payment.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages after this date or payment.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        oldest_first: Optional[:class:`bool`]
            If set to ``True``, return payments in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.

        Raises
        ------
        HTTPException
            The request to get payments failed.

        Yields
        -------
        :class:`.Payment`
            The payment made.
        """

        _state = self._connection

        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await _state.http.get_payments(retrieve, after=after_id)

            if data:
                if limit is not None:
                    limit -= len(data)

                after = Object(id=int(data[0]['id']))

            return data, after, limit

        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await _state.http.get_payments(retrieve, before=before_id)

            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[-1]['id']))

            return data, before, limit

        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))

        if oldest_first is None:
            reverse = after is not None
        else:
            reverse = oldest_first

        after = after or OLDEST_OBJECT
        predicate = None

        if reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda m: int(m['id']) > after.id

        while True:
            retrieve = min(100 if limit is None else limit, 100)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            # Terminate loop on next iteration; there's no data left after this
            if len(data) < 100:
                limit = 0

            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)

            for payment in data:
                yield Payment(data=payment, state=_state)

    async def fetch_payment(self, payment_id: int) -> Payment:
        """|coro|

        Retrieves the payment with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        payment_id: :class:`int`
            The ID of the payment to fetch.

        Raises
        ------
        HTTPException
            Fetching the payment failed.

        Returns
        -------
        :class:`.Payment`
            The retrieved payment.
        """
        state = self._connection
        data = await state.http.get_payment(payment_id)
        return Payment(data=data, state=state)

    async def promotions(self, claimed: bool = False) -> List[Promotion]:
        """|coro|

        Retrieves all the promotions available for your account.

        .. versionadded:: 2.0

        Parameters
        -----------
        claimed: :class:`bool`
            Whether to only retrieve claimed promotions.
            These will have :attr:`.Promotion.claimed_at` and :attr:`.Promotion.code` set.

        Raises
        -------
        HTTPException
            Retrieving the promotions failed.

        Returns
        -------
        List[:class:`.Promotion`]
            The promotions available for you.
        """
        state = self._connection
        data = (
            await state.http.get_claimed_promotions(state.locale)
            if claimed
            else await state.http.get_promotions(state.locale)
        )
        return [Promotion(state=state, data=d) for d in data]

    async def trial_offer(self) -> TrialOffer:
        """|coro|

        Retrieves the current trial offer for your account.

        .. versionadded:: 2.0

        Raises
        -------
        NotFound
            You do not have a trial offer.
        HTTPException
            Retrieving the trial offer failed.

        Returns
        -------
        :class:`.TrialOffer`
            The trial offer for your account.
        """
        state = self._connection
        data = await state.http.get_trial_offer()
        return TrialOffer(data=data, state=state)

    async def pricing_promotion(self) -> Optional[PricingPromotion]:
        """|coro|

        Retrieves the current localized pricing promotion for your account, if any.

        This also updates your current country code.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the pricing promotion failed.

        Returns
        -------
        Optional[:class:`.PricingPromotion`]
            The pricing promotion for your account, if any.
        """
        state = self._connection
        data = await state.http.get_pricing_promotion()
        state.country_code = data['country_code']
        if data['localized_pricing_promo'] is not None:
            return PricingPromotion(data=data['localized_pricing_promo'])

    async def library(self) -> List[LibraryApplication]:
        """|coro|

        Retrieves the applications in your library.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the library failed.

        Returns
        -------
        List[:class:`.LibraryApplication`]
            The applications in your library.
        """
        state = self._connection
        data = await state.http.get_library_entries(state.country_code or 'US')
        return [LibraryApplication(state=state, data=d) for d in data]

    async def entitlements(
        self, *, with_sku: bool = True, with_application: bool = True, entitlement_type: Optional[EntitlementType] = None
    ) -> List[Entitlement]:
        """|coro|

        Retrieves all the entitlements for your account.

        .. versionadded:: 2.0

        Parameters
        -----------
        with_sku: :class:`bool`
            Whether to include the SKU information in the returned entitlements.
        with_application: :class:`bool`
            Whether to include the application in the returned entitlements' SKUs.
            The premium subscription application is always returned.
        entitlement_type: Optional[:class:`.EntitlementType`]
            The type of entitlement to retrieve. If ``None`` then all entitlements are returned.

        Raises
        -------
        HTTPException
            Retrieving the entitlements failed.

        Returns
        -------
        List[:class:`.Entitlement`]
            The entitlements for your account.
        """
        state = self._connection
        data = await state.http.get_user_entitlements(
            with_sku=with_sku,
            with_application=with_application,
            entitlement_type=int(entitlement_type) if entitlement_type else None,
        )
        return [Entitlement(state=state, data=d) for d in data]

    async def giftable_entitlements(self) -> List[Entitlement]:
        """|coro|

        Retrieves the giftable entitlements for your account.

        These are entitlements you are able to gift to other users.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Retrieving the giftable entitlements failed.

        Returns
        -------
        List[:class:`.Entitlement`]
            The giftable entitlements for your account.
        """
        state = self._connection
        data = await state.http.get_giftable_entitlements(state.country_code or 'US')
        return [Entitlement(state=state, data=d) for d in data]

    async def premium_entitlements(self, *, exclude_consumed: bool = True) -> List[Entitlement]:
        """|coro|

        Retrieves the entitlements this account has granted for the premium application.

        These are the entitlements used for premium subscriptions, referred to as "Nitro Credits".

        .. versionadded:: 2.0

        Parameters
        -----------
        exclude_consumed: :class:`bool`
            Whether to exclude consumed entitlements.

        Raises
        -------
        HTTPException
            Fetching the entitlements failed.

        Returns
        --------
        List[:class:`.Entitlement`]
            The entitlements retrieved.
        """
        return await self.fetch_entitlements(
            self._connection.premium_subscriptions_application.id, exclude_consumed=exclude_consumed
        )

    async def fetch_entitlements(self, application_id: int, /, *, exclude_consumed: bool = True) -> List[Entitlement]:
        """|coro|

        Retrieves the entitlements this account has granted for the given application.

        Parameters
        -----------
        application_id: :class:`int`
            The ID of the application to fetch the entitlements for.
        exclude_consumed: :class:`bool`
            Whether to exclude consumed entitlements.

        Raises
        -------
        HTTPException
            Fetching the entitlements failed.

        Returns
        --------
        List[:class:`.Entitlement`]
            The entitlements retrieved.
        """
        state = self._connection
        data = await state.http.get_user_app_entitlements(application_id, exclude_consumed=exclude_consumed)
        return [Entitlement(data=entitlement, state=state) for entitlement in data]

    async def fetch_gift(
        self, code: Union[Gift, str], *, with_application: bool = False, with_subscription_plan: bool = True
    ) -> Gift:
        """|coro|

        Retrieves a gift with the given code.

        .. versionadded:: 2.0

        Parameters
        -----------
        code: Union[:class:`.Gift`, :class:`str`]
            The code of the gift to retrieve.
        with_application: :class:`bool`
            Whether to include the application in the response's store listing.
            The premium subscription application is always returned.
        with_subscription_plan: :class:`bool`
            Whether to include the subscription plan in the response.

        Raises
        -------
        NotFound
            The gift does not exist.
        HTTPException
            Retrieving the gift failed.

        Returns
        -------
        :class:`.Gift`
            The retrieved gift.
        """
        state = self._connection
        code = utils.resolve_gift(code)
        data = await state.http.get_gift(
            code, with_application=with_application, with_subscription_plan=with_subscription_plan
        )
        return Gift(state=state, data=data)

    async def fetch_sku(self, sku_id: int, /, *, localize: bool = True) -> SKU:
        """|coro|

        Retrieves a SKU with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        sku_id: :class:`int`
            The ID of the SKU to retrieve.
        localize: :class:`bool`
            Whether to localize the SKU name and description to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        NotFound
            The SKU does not exist.
        Forbidden
            You do not have access to the SKU.
        HTTPException
            Retrieving the SKU failed.

        Returns
        -------
        :class:`.SKU`
            The retrieved SKU.
        """
        state = self._connection
        data = await state.http.get_sku(sku_id, country_code=state.country_code or 'US', localize=localize)
        return SKU(state=state, data=data)

    async def fetch_store_listing(self, listing_id: int, /, *, localize: bool = True) -> StoreListing:
        """|coro|

        Retrieves a store listing with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        listing_id: :class:`int`
            The ID of the listing to retrieve.
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        NotFound
            The listing does not exist.
        Forbidden
            You do not have access to the listing.
        HTTPException
            Retrieving the listing failed.

        Returns
        -------
        :class:`.StoreListing`
            The store listing.
        """
        state = self._connection
        data = await state.http.get_store_listing(listing_id, country_code=state.country_code or 'US', localize=localize)
        return StoreListing(state=state, data=data)

    async def fetch_published_store_listing(self, sku_id: int, /, *, localize: bool = True) -> StoreListing:
        """|coro|

        Retrieves a published store listing with the given SKU ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        sku_id: :class:`int`
            The ID of the SKU to retrieve the listing for.
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        NotFound
            The listing does not exist or is not public.
        HTTPException
            Retrieving the listing failed.

        Returns
        -------
        :class:`.StoreListing`
            The store listing.
        """
        state = self._connection
        data = await state.http.get_store_listing_by_sku(
            sku_id,
            country_code=state.country_code or 'US',
            localize=localize,
        )
        return StoreListing(state=state, data=data)

    async def fetch_published_store_listings(self, application_id: int, /, localize: bool = True) -> List[StoreListing]:
        """|coro|

        Retrieves all published store listings for the given application ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        application_id: :class:`int`
            The ID of the application to retrieve the listings for.
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        -------
        HTTPException
            Retrieving the listings failed.

        Returns
        -------
        List[:class:`.StoreListing`]
            The store listings.
        """
        state = self._connection
        data = await state.http.get_app_store_listings(
            application_id, country_code=state.country_code or 'US', localize=localize
        )
        return [StoreListing(state=state, data=d) for d in data]

    async def fetch_primary_store_listing(self, application_id: int, /, *, localize: bool = True) -> StoreListing:
        """|coro|

        Retrieves the primary store listing for the given application ID.

        This is the public store listing of the primary SKU.

        .. versionadded:: 2.0

        Parameters
        -----------
        application_id: :class:`int`
            The ID of the application to retrieve the listing for.
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        ------
        NotFound
            The application does not exist or have a primary SKU.
        HTTPException
            Retrieving the store listing failed.

        Returns
        -------
        :class:`.StoreListing`
            The retrieved store listing.
        """
        state = self._connection
        data = await state.http.get_app_store_listing(
            application_id, country_code=state.country_code or 'US', localize=localize
        )
        return StoreListing(state=state, data=data)

    async def fetch_primary_store_listings(self, *application_ids: int, localize: bool = True) -> List[StoreListing]:
        r"""|coro|

        Retrieves the primary store listings for the given application IDs.

        This is the public store listing of the primary SKU.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*application_ids: :class:`int`
            A list of application IDs to retrieve the listings for.
        localize: :class:`bool`
            Whether to localize the store listings to the current user's locale.
            If ``False`` then all localizations are returned.

        Raises
        ------
        HTTPException
            Retrieving the store listings failed.

        Returns
        -------
        List[:class:`.StoreListing`]
            The retrieved store listings.
        """
        if not application_ids:
            return []

        state = self._connection
        data = await state.http.get_apps_store_listing(
            application_ids, country_code=state.country_code or 'US', localize=localize
        )
        return [StoreListing(state=state, data=listing) for listing in data]

    async def premium_subscription_plans(self) -> List[SubscriptionPlan]:
        """|coro|

        Retrieves all premium subscription plans.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the premium subscription plans failed.

        Returns
        -------
        List[:class:`.SubscriptionPlan`]
            The premium subscription plans.
        """
        state = self._connection
        sku_ids = [v for k, v in state.premium_subscriptions_sku_ids.items() if k != 'none']
        data = await state.http.get_store_listings_subscription_plans(sku_ids)
        return [SubscriptionPlan(state=state, data=d) for d in data]

    async def fetch_sku_subscription_plans(
        self,
        sku_id: int,
        /,
        *,
        country_code: str = MISSING,
        payment_source: Snowflake = MISSING,
        with_unpublished: bool = False,
    ) -> List[SubscriptionPlan]:
        """|coro|

        Retrieves all subscription plans for the given SKU ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        sku_id: :class:`int`
            The ID of the SKU to retrieve the subscription plans for.
        country_code: :class:`str`
            The country code to retrieve the subscription plan prices for.
            Defaults to the country code of the current user.
        payment_source: :class:`.PaymentSource`
            The specific payment source to retrieve the subscription plan prices for.
            Defaults to all payment sources of the current user.
        with_unpublished: :class:`bool`
            Whether to include unpublished subscription plans.

            If ``True``, then you require access to the application.

        Raises
        ------
        HTTPException
            Retrieving the subscription plans failed.

        Returns
        -------
        List[:class:`.SubscriptionPlan`]
            The subscription plans.
        """
        state = self._connection
        data = await state.http.get_store_listing_subscription_plans(
            sku_id,
            country_code=country_code if country_code is not MISSING else None,
            payment_source_id=payment_source.id if payment_source is not MISSING else None,
            include_unpublished=with_unpublished,
        )
        return [SubscriptionPlan(state=state, data=d) for d in data]

    async def fetch_skus_subscription_plans(
        self,
        *sku_ids: int,
        country_code: str = MISSING,
        payment_source: Snowflake = MISSING,
        with_unpublished: bool = False,
    ) -> List[SubscriptionPlan]:
        r"""|coro|

        Retrieves all subscription plans for the given SKU IDs.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*sku_ids: :class:`int`
            A list of SKU IDs to retrieve the subscription plans for.
        country_code: :class:`str`
            The country code to retrieve the subscription plan prices for.
            Defaults to the country code of the current user.
        payment_source: :class:`.PaymentSource`
            The specific payment source to retrieve the subscription plan prices for.
            Defaults to all payment sources of the current user.
        with_unpublished: :class:`bool`
            Whether to include unpublished subscription plans.

            If ``True``, then you require access to the application(s).

        Raises
        ------
        HTTPException
            Retrieving the subscription plans failed.

        Returns
        -------
        List[:class:`.SubscriptionPlan`]
            The subscription plans.
        """
        if not sku_ids:
            return []

        state = self._connection
        data = await state.http.get_store_listings_subscription_plans(
            sku_ids,
            country_code=country_code if country_code is not MISSING else None,
            payment_source_id=payment_source.id if payment_source is not MISSING else None,
            include_unpublished=with_unpublished,
        )
        return [SubscriptionPlan(state=state, data=d) for d in data]

    async def fetch_eula(self, eula_id: int, /) -> EULA:
        """|coro|

        Retrieves a EULA with the given ID.

        .. versionadded:: 2.0

        Parameters
        -----------
        eula_id: :class:`int`
            The ID of the EULA to retrieve.

        Raises
        -------
        NotFound
            The EULA does not exist.
        HTTPException
            Retrieving the EULA failed.

        Returns
        -------
        :class:`.EULA`
            The retrieved EULA.
        """
        data = await self._connection.http.get_eula(eula_id)
        return EULA(data=data)

    async def fetch_live_build_ids(self, *branch_ids: int) -> Dict[int, Optional[int]]:
        r"""|coro|

        Retrieves the live build IDs for the given branch IDs.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*branch_ids: :class:`int`
            A list of branch IDs to retrieve the live build IDs for.

        Raises
        ------
        HTTPException
            Retrieving the live build IDs failed.

        Returns
        -------
        Dict[:class:`int`, Optional[:class:`int`]]
            A mapping of found branch IDs to their live build ID, if any.
        """
        if not branch_ids:
            return {}

        data = await self._connection.http.get_build_ids(branch_ids)
        return {int(b['id']): utils._get_as_snowflake(b, 'live_build_id') for b in data}

    async def price_tiers(self) -> List[int]:
        """|coro|

        Retrieves all price tiers.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the price tiers failed.

        Returns
        -------
        List[:class:`int`]
            The price tiers.
        """
        return await self._connection.http.get_price_tiers()

    async def fetch_price_tier(self, price_tier: int, /) -> Dict[str, int]:
        """|coro|

        Retrieves a mapping of currency to price for the given price tier.

        .. versionadded:: 2.0

        Parameters
        -----------
        price_tier: :class:`int`
            The price tier to retrieve.

        Raises
        -------
        NotFound
            The price tier does not exist.
        HTTPException
            Retrieving the price tier failed.

        Returns
        -------
        Dict[:class:`str`, :class:`int`]
            The retrieved price tier mapping.
        """
        return await self._connection.http.get_price_tier(price_tier)

    async def premium_usage(self) -> PremiumUsage:
        """|coro|

        Retrieves the usage of the premium perks on your account.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the premium usage failed.

        Returns
        -------
        :class:`.PremiumUsage`
            The premium usage.
        """
        data = await self._connection.http.get_premium_usage()
        return PremiumUsage(data=data)

    async def recent_mentions(
        self,
        *,
        limit: Optional[int] = 25,
        before: SnowflakeTime = MISSING,
        guild: Snowflake = MISSING,
        roles: bool = True,
        everyone: bool = True,
    ) -> AsyncIterator[Message]:
        """Returns an :term:`asynchronous iterator` that enables receiving your recent mentions.

        .. versionadded:: 2.0

        Examples
        ---------

        Usage ::

            counter = 0
            async for message in client.recent_mentions(limit=200):
                if message.author == client.user:
                    counter += 1

        Flattening into a list: ::

            messages = [message async for message in client.recent_mentions(limit=123)]
            # messages is now a list of Message...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of messages to retrieve.
            If ``None``, retrieves every recent mention received in the past week. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages before this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        guild: :class:`.Guild`
            The guild to retrieve recent mentions from.
            If not provided, then the mentions are retrieved from all guilds.
        roles: :class:`bool`
            Whether to include role mentions.
        everyone: :class:`bool`
            Whether to include @everyone or @here mentions.

        Raises
        ------
        HTTPException
            The request to get recent message history failed.

        Yields
        -------
        :class:`.Message`
            The message with the message data parsed.
        """
        _state = self._connection

        async def strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await _state.http.get_recent_mentions(
                retrieve, before=before_id, guild_id=guild.id if guild else None, roles=roles, everyone=everyone
            )

            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[-1]['id']))

            return data, before, limit

        if isinstance(before, datetime):
            state = Object(id=utils.time_snowflake(before, high=False))
        else:
            state = before

        while True:
            retrieve = min(100 if limit is None else limit, 100)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            # Terminate loop on next iteration; there's no data left after this
            if len(data) < 100:
                limit = 0

            for raw_message in data:
                channel, _ = _state._get_guild_channel(raw_message)
                yield _state.create_message(channel=channel, data=raw_message)  # type: ignore

    async def delete_recent_mention(self, message: Snowflake) -> None:
        """|coro|

        Acknowledges a message the current user has been mentioned in.

        .. versionadded:: 2.0

        Parameters
        -----------
        message: :class:`.abc.Snowflake`
            The message to delete.

        Raises
        ------
        HTTPException
            Deleting the recent mention failed.
        """
        await self._connection.http.delete_recent_mention(message.id)

    async def user_affinities(self) -> List[UserAffinity]:
        """|coro|

        Retrieves the user affinities for the current user.

        User affinities are the users you interact with most frecently.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the user affinities failed.

        Returns
        -------
        List[:class:`.UserAffinity`]
            The user affinities.
        """
        state = self._connection
        data = await state.http.get_user_affinities()
        return [UserAffinity(data=d, state=state) for d in data['user_affinities']]

    async def guild_affinities(self) -> List[GuildAffinity]:
        """|coro|

        Retrieves the guild affinities for the current user.

        Guild affinities are the guilds you interact with most frecently.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Retrieving the guild affinities failed.

        Returns
        -------
        List[:class:`.GuildAffinity`]
            The guild affinities.
        """
        state = self._connection
        data = await state.http.get_guild_affinities()
        return [GuildAffinity(data=d, state=state) for d in data['guild_affinities']]

    async def join_active_developer_program(self, *, application: Snowflake, channel: Snowflake) -> int:
        """|coro|

        Joins the current user to the active developer program.

        .. versionadded:: 2.0

        Parameters
        -----------
        application: :class:`.Application`
            The application to join the active developer program with.
        channel: :class:`.TextChannel`
            The channel to add the developer program webhook to.

        Raises
        -------
        HTTPException
            Joining the active developer program failed.

        Returns
        -------
        :class:`int`
            The created webhook ID.
        """
        data = await self._connection.http.enroll_active_developer(application.id, channel.id)
        return int(data['follower']['webhook_id'])

    async def leave_active_developer_program(self) -> None:
        """|coro|

        Leaves the current user from the active developer program.
        This does not remove the created webhook.

        .. versionadded:: 2.0

        Raises
        -------
        HTTPException
            Leaving the active developer program failed.
        """
        await self._connection.http.unenroll_active_developer()
