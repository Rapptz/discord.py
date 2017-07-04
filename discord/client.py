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

from . import __version__ as library_version
from .user import User
from .member import Member
from .channel import Channel, PrivateChannel
from .server import Server
from .message import Message
from .invite import Invite
from .object import Object
from .reaction import Reaction
from .role import Role
from .errors import *
from .state import ConnectionState
from .permissions import Permissions, PermissionOverwrite
from . import utils, compat
from .enums import ChannelType, ServerRegion, VerificationLevel, Status
from .voice_client import VoiceClient
from .iterators import LogsFromIterator
from .gateway import *
from .emoji import Emoji
from .http import HTTPClient

import asyncio
import aiohttp
import websockets

import logging, traceback
import sys, re, io, enum
import tempfile, os, hashlib
import itertools
import datetime
from collections import namedtuple
from os.path import split as path_split

PY35 = sys.version_info >= (3, 5)
log = logging.getLogger(__name__)

AppInfo = namedtuple('AppInfo', 'id name description icon owner')
WaitedReaction = namedtuple('WaitedReaction', 'reaction user')

def app_info_icon_url(self):
    """Retrieves the application's icon_url if it exists. Empty string otherwise."""
    if not self.icon:
        return ''

    return 'https://cdn.discordapp.com/app-icons/{0.id}/{0.icon}.jpg'.format(self)

AppInfo.icon_url = property(app_info_icon_url)

class WaitForType(enum.Enum):
    message  = 0
    reaction = 1

ChannelPermissions = namedtuple('ChannelPermissions', 'target overwrite')
ChannelPermissions.__new__.__defaults__ = (PermissionOverwrite(),)

class Client:
    """Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client`.

    .. _deque: https://docs.python.org/3.4/library/collections.html#collections.deque
    .. _event loop: https://docs.python.org/3/library/asyncio-eventloops.html
    .. _connector: http://aiohttp.readthedocs.org/en/stable/client_reference.html#connectors
    .. _ProxyConnector: http://aiohttp.readthedocs.org/en/stable/client_reference.html#proxyconnector

    Parameters
    ----------
    max_messages : Optional[int]
        The maximum number of messages to store in :attr:`messages`.
        This defaults to 5000. Passing in `None` or a value less than 100
        will use the default instead of the passed in value.
    loop : Optional[event loop].
        The `event loop`_ to use for asynchronous operations. Defaults to ``None``,
        in which case the default event loop is used via ``asyncio.get_event_loop()``.
    cache_auth : Optional[bool]
        Indicates if :meth:`login` should cache the authentication tokens. Defaults
        to ``True``. The method in which the cache is written is done by writing to
        disk to a temporary directory.
    connector : aiohttp.BaseConnector
        The `connector`_ to use for connection pooling. Useful for proxies, e.g.
        with a `ProxyConnector`_.
    shard_id : Optional[int]
        Integer starting at 0 and less than shard_count.
    shard_count : Optional[int]
        The total number of shards.

    Attributes
    -----------
    user : Optional[:class:`User`]
        Represents the connected client. None if not logged in.
    voice_clients : iterable of :class:`VoiceClient`
        Represents a list of voice connections. To connect to voice use
        :meth:`join_voice_channel`. To query the voice connection state use
        :meth:`is_voice_connected`.
    servers : iterable of :class:`Server`
        The servers that the connected client is a member of.
    private_channels : iterable of :class:`PrivateChannel`
        The private channels that the connected client is participating on.
    messages
        A deque_ of :class:`Message` that the client has received from all
        servers and private messages. The number of messages stored in this
        deque is controlled by the ``max_messages`` parameter.
    email
        The email used to login. This is only set if login is successful,
        otherwise it's None.
    ws
        The websocket gateway the client is currently connected to. Could be None.
    loop
        The `event loop`_ that the client uses for HTTP requests and websocket operations.

    """
    def __init__(self, *, loop=None, **options):
        self.ws = None
        self.email = None
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._listeners = []
        self.cache_auth = options.get('cache_auth', True)
        self.shard_id = options.get('shard_id')
        self.shard_count = options.get('shard_count')

        max_messages = options.get('max_messages')
        if max_messages is None or max_messages < 100:
            max_messages = 5000

        self.connection = ConnectionState(self.dispatch, self.request_offline_members,
                                          self._syncer, max_messages, loop=self.loop)

        connector = options.pop('connector', None)
        self.http = HTTPClient(connector, loop=self.loop)

        self._closed = asyncio.Event(loop=self.loop)
        self._is_logged_in = asyncio.Event(loop=self.loop)
        self._is_ready = asyncio.Event(loop=self.loop)

        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            log.warning("PyNaCl is not installed, voice will NOT be supported")

    # internals

    @asyncio.coroutine
    def _syncer(self, guilds):
        yield from self.ws.request_sync(guilds)

    def _get_cache_filename(self, email):
        filename = hashlib.md5(email.encode('utf-8')).hexdigest()
        return os.path.join(tempfile.gettempdir(), 'discord_py', filename)

    def _get_cache_token(self, email, password):
        try:
            log.info('attempting to login via cache')
            cache_file = self._get_cache_filename(email)
            self.email = email
            with open(cache_file, 'r') as f:
                log.info('login cache file found')
                return f.read()

            # at this point our check failed
            # so we have to login and get the proper token and then
            # redo the cache
        except OSError:
            log.info('a problem occurred while opening login cache')
            return None # file not found et al

    def _update_cache(self, email, password):
        try:
            cache_file = self._get_cache_filename(email)
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with os.fdopen(os.open(cache_file, os.O_WRONLY | os.O_CREAT, 0o0600), 'w') as f:
                log.info('updating login cache')
                f.write(self.http.token)
        except OSError:
            log.info('a problem occurred while updating the login cache')
            pass

    def handle_reaction_add(self, reaction, user):
        removed = []
        for i, (condition, future, event_type) in enumerate(self._listeners):
            if event_type is not WaitForType.reaction:
                continue

            if future.cancelled():
                removed.append(i)
                continue

            try:
                result = condition(reaction, user)
            except Exception as e:
                future.set_exception(e)
                removed.append(i)
            else:
                if result:
                    future.set_result(WaitedReaction(reaction, user))
                    removed.append(i)


        for idx in reversed(removed):
            del self._listeners[idx]

    def handle_message(self, message):
        removed = []
        for i, (condition, future, event_type) in enumerate(self._listeners):
            if event_type is not WaitForType.message:
                continue

            if future.cancelled():
                removed.append(i)
                continue

            try:
                result = condition(message)
            except Exception as e:
                future.set_exception(e)
                removed.append(i)
            else:
                if result:
                    future.set_result(message)
                    removed.append(i)


        for idx in reversed(removed):
            del self._listeners[idx]

    def handle_ready(self):
        self._is_ready.set()

    def _resolve_invite(self, invite):
        if isinstance(invite, Invite) or isinstance(invite, Object):
            return invite.id
        else:
            rx = r'(?:https?\:\/\/)?discord\.gg\/(.+)'
            m = re.match(rx, invite)
            if m:
                return m.group(1)
        return invite

    @asyncio.coroutine
    def _resolve_destination(self, destination):
        if isinstance(destination, Channel):
            return destination.id, destination.server.id
        elif isinstance(destination, PrivateChannel):
            return destination.id, None
        elif isinstance(destination, Server):
            return destination.id, destination.id
        elif isinstance(destination, User):
            found = self.connection._get_private_channel_by_user(destination.id)
            if found is None:
                # Couldn't find the user, so start a PM with them first.
                channel = yield from self.start_private_message(destination)
                return channel.id, None
            else:
                return found.id, None
        elif isinstance(destination, Object):
            found = self.get_channel(destination.id)
            if found is not None:
                return (yield from self._resolve_destination(found))

            # couldn't find it in cache so YOLO
            return destination.id, destination.id
        else:
            fmt = 'Destination must be Channel, PrivateChannel, User, or Object. Received {0.__class__.__name__}'
            raise InvalidArgument(fmt.format(destination))

    def __getattr__(self, name):
        if name in ('user', 'servers', 'private_channels', 'messages', 'voice_clients'):
            return getattr(self.connection, name)
        else:
            msg = "'{}' object has no attribute '{}'"
            raise AttributeError(msg.format(self.__class__, name))

    def __setattr__(self, name, value):
        if name in ('user', 'servers', 'private_channels', 'messages', 'voice_clients'):
            return setattr(self.connection, name, value)
        else:
            object.__setattr__(self, name, value)

    @asyncio.coroutine
    def _run_event(self, event, *args, **kwargs):
        try:
            yield from getattr(self, event)(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                yield from self.on_error(event, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def dispatch(self, event, *args, **kwargs):
        log.debug('Dispatching event {}'.format(event))
        method = 'on_' + event
        handler = 'handle_' + event

        if hasattr(self, handler):
            getattr(self, handler)(*args, **kwargs)

        if hasattr(self, method):
            compat.create_task(self._run_event(method, *args, **kwargs), loop=self.loop)

    @asyncio.coroutine
    def on_error(self, event_method, *args, **kwargs):
        """|coro|

        The default error handler provided by the client.

        By default this prints to ``sys.stderr`` however it could be
        overridden to have a different implementation.
        Check :func:`discord.on_error` for more details.
        """
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

    # login state management

    @asyncio.coroutine
    def _login_1(self, token, **kwargs):
        log.info('logging in using static token')
        is_bot = kwargs.pop('bot', True)
        data = yield from self.http.static_login(token, bot=is_bot)
        self.email = data.get('email', None)
        self.connection.is_bot = is_bot
        self._is_logged_in.set()

    @asyncio.coroutine
    def _login_2(self, email, password, **kwargs):
        # attempt to read the token from cache
        self.connection.is_bot = False

        if self.cache_auth:
            token = self._get_cache_token(email, password)
            try:
                yield from self.http.static_login(token, bot=False)
            except:
                log.info('cache auth token is out of date')
            else:
                self._is_logged_in.set()
                return


        yield from self.http.email_login(email, password)
        self.email = email
        self._is_logged_in.set()

        # since we went through all this trouble
        # let's make sure we don't have to do it again
        if self.cache_auth:
            self._update_cache(email, password)

    @asyncio.coroutine
    def login(self, *args, **kwargs):
        """|coro|

        Logs in the client with the specified credentials.

        This function can be used in two different ways.

        .. code-block:: python

            await client.login('token')

            # or

            await client.login('email', 'password')

        More than 2 parameters or less than 1 parameter raises a
        :exc:`TypeError`.

        Parameters
        -----------
        bot : bool
            Keyword argument that specifies if the account logging on is a bot
            token or not. Only useful for logging in with a static token.
            Ignored for the email and password combo. Defaults to ``True``.

        Raises
        ------
        LoginFailure
            The wrong credentials are passed.
        HTTPException
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        TypeError
            The incorrect number of parameters is passed.
        """

        n = len(args)
        if n in (2, 1):
            yield from getattr(self, '_login_' + str(n))(*args, **kwargs)
        else:
            raise TypeError('login() takes 1 or 2 positional arguments but {} were given'.format(n))

    @asyncio.coroutine
    def logout(self):
        """|coro|

        Logs out of Discord and closes all connections.
        """
        yield from self.close()
        self._is_logged_in.clear()

    @asyncio.coroutine
    def connect(self):
        """|coro|

        Creates a websocket connection and lets the websocket listen
        to messages from discord.

        Raises
        -------
        GatewayNotFound
            If the gateway to connect to discord is not found. Usually if this
            is thrown then there is a discord API outage.
        ConnectionClosed
            The websocket connection has been terminated.
        """
        self.ws = yield from DiscordWebSocket.from_client(self)

        while not self.is_closed:
            try:
                yield from self.ws.poll_event()
            except (ReconnectWebSocket, ResumeWebSocket) as e:
                resume = type(e) is ResumeWebSocket
                log.info('Got ' + type(e).__name__)
                self.ws = yield from DiscordWebSocket.from_client(self, resume=resume)
            except ConnectionClosed as e:
                yield from self.close()
                if e.code != 1000:
                    raise

    @asyncio.coroutine
    def close(self):
        """|coro|

        Closes the connection to discord.
        """
        if self.is_closed:
            return

        for voice in list(self.voice_clients):
            try:
                yield from voice.disconnect()
            except:
                # if an error happens during disconnects, disregard it.
                pass

            self.connection._remove_voice_client(voice.server.id)

        if self.ws is not None and self.ws.open:
            yield from self.ws.close()


        yield from self.http.close()
        self._closed.set()
        self._is_ready.clear()

    @asyncio.coroutine
    def start(self, *args, **kwargs):
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        """
        yield from self.login(*args, **kwargs)
        yield from self.connect()

    def run(self, *args, **kwargs):
        """A blocking call that abstracts away the `event loop`_
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(logout())
                # cancel all tasks lingering
            finally:
                loop.close()

        Warning
        --------
        This function must be the last function to call due to the fact that it
        is blocking. That means that registration of events or anything being
        called after this function call will not execute until it returns.
        """

        try:
            self.loop.run_until_complete(self.start(*args, **kwargs))
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.logout())
            pending = asyncio.Task.all_tasks(loop=self.loop)
            gathered = asyncio.gather(*pending, loop=self.loop)
            try:
                gathered.cancel()
                self.loop.run_until_complete(gathered)

                # we want to retrieve any exceptions to make sure that
                # they don't nag us about it being un-retrieved.
                gathered.exception()
            except:
                pass
        finally:
            self.loop.close()

        # properties

    @property
    def is_logged_in(self):
        """bool: Indicates if the client has logged in successfully."""
        return self._is_logged_in.is_set()

    @property
    def is_closed(self):
        """bool: Indicates if the websocket connection is closed."""
        return self._closed.is_set()

    # helpers/getters

    def get_channel(self, id):
        """Returns a :class:`Channel` or :class:`PrivateChannel` with the following ID. If not found, returns None."""
        return self.connection.get_channel(id)

    def get_server(self, id):
        """Returns a :class:`Server` with the given ID. If not found, returns None."""
        return self.connection._get_server(id)

    def get_all_emojis(self):
        """Returns a generator with every :class:`Emoji` the client can see."""
        for server in self.servers:
            for emoji in server.emojis:
                yield emoji

    def get_all_channels(self):
        """A generator that retrieves every :class:`Channel` the client can 'access'.

        This is equivalent to: ::

            for server in client.servers:
                for channel in server.channels:
                    yield channel

        Note
        -----
        Just because you receive a :class:`Channel` does not mean that
        you can communicate in said channel. :meth:`Channel.permissions_for` should
        be used for that.
        """

        for server in self.servers:
            for channel in server.channels:
                yield channel

    def get_all_members(self):
        """Returns a generator with every :class:`Member` the client can see.

        This is equivalent to: ::

            for server in client.servers:
                for member in server.members:
                    yield member

        """
        for server in self.servers:
            for member in server.members:
                yield member

    # listeners/waiters

    @asyncio.coroutine
    def wait_until_ready(self):
        """|coro|

        This coroutine waits until the client is all ready. This could be considered
        another way of asking for :func:`discord.on_ready` except meant for your own
        background tasks.
        """
        yield from self._is_ready.wait()

    @asyncio.coroutine
    def wait_until_login(self):
        """|coro|

        This coroutine waits until the client is logged on successfully. This
        is different from waiting until the client's state is all ready. For
        that check :func:`discord.on_ready` and :meth:`wait_until_ready`.
        """
        yield from self._is_logged_in.wait()

    @asyncio.coroutine
    def wait_for_message(self, timeout=None, *, author=None, channel=None, content=None, check=None):
        """|coro|

        Waits for a message reply from Discord. This could be seen as another
        :func:`discord.on_message` event outside of the actual event. This could
        also be used for follow-ups and easier user interactions.

        The keyword arguments passed into this function are combined using the logical and
        operator. The ``check`` keyword argument can be used to pass in more complicated
        checks and must be a regular function (not a coroutine).

        The ``timeout`` parameter is passed into `asyncio.wait_for`_. By default, it
        does not timeout. Instead of throwing ``asyncio.TimeoutError`` the coroutine
        catches the exception and returns ``None`` instead of a :class:`Message`.

        If the ``check`` predicate throws an exception, then the exception is propagated.

        This function returns the **first message that meets the requirements**.

        .. _asyncio.wait_for: https://docs.python.org/3/library/asyncio-task.html#asyncio.wait_for

        Examples
        ----------

        Basic example:

        .. code-block:: python
            :emphasize-lines: 5

            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    await client.send_message(message.channel, 'Say hello')
                    msg = await client.wait_for_message(author=message.author, content='hello')
                    await client.send_message(message.channel, 'Hello.')

        Asking for a follow-up question:

        .. code-block:: python
            :emphasize-lines: 6

            @client.event
            async def on_message(message):
                if message.content.startswith('$start'):
                    await client.send_message(message.channel, 'Type $stop 4 times.')
                    for i in range(4):
                        msg = await client.wait_for_message(author=message.author, content='$stop')
                        fmt = '{} left to go...'
                        await client.send_message(message.channel, fmt.format(3 - i))

                    await client.send_message(message.channel, 'Good job!')

        Advanced filters using ``check``:

        .. code-block:: python
            :emphasize-lines: 9

            @client.event
            async def on_message(message):
                if message.content.startswith('$cool'):
                    await client.send_message(message.channel, 'Who is cool? Type $name namehere')

                    def check(msg):
                        return msg.content.startswith('$name')

                    message = await client.wait_for_message(author=message.author, check=check)
                    name = message.content[len('$name'):].strip()
                    await client.send_message(message.channel, '{} is cool indeed'.format(name))


        Parameters
        -----------
        timeout : float
            The number of seconds to wait before returning ``None``.
        author : :class:`Member` or :class:`User`
            The author the message must be from.
        channel : :class:`Channel` or :class:`PrivateChannel` or :class:`Object`
            The channel the message must be from.
        content : str
            The exact content the message must have.
        check : function
            A predicate for other complicated checks. The predicate must take
            a :class:`Message` as its only parameter.

        Returns
        --------
        :class:`Message`
            The message that you requested for.
        """

        def predicate(message):
            result = True
            if author is not None:
                result = result and message.author == author

            if content is not None:
                result = result and message.content == content

            if channel is not None:
                result = result and message.channel.id == channel.id

            if callable(check):
                # the exception thrown by check is propagated through the future.
                result = result and check(message)

            return result

        future = asyncio.Future(loop=self.loop)
        self._listeners.append((predicate, future, WaitForType.message))
        try:
            message = yield from asyncio.wait_for(future, timeout, loop=self.loop)
        except asyncio.TimeoutError:
            message = None
        return message


    @asyncio.coroutine
    def wait_for_reaction(self, emoji=None, *, user=None, timeout=None, message=None, check=None):
        """|coro|

        Waits for a message reaction from Discord. This is similar to :meth:`wait_for_message`
        and could be seen as another :func:`on_reaction_add` event outside of the actual event.
        This could be used for follow up situations.

        Similar to :meth:`wait_for_message`, the keyword arguments are combined using logical
        AND operator. The ``check`` keyword argument can be used to pass in more complicated
        checks and must a regular function taking in two arguments, ``(reaction, user)``. It
        must not be a coroutine.

        The ``timeout`` parameter is passed into asyncio.wait_for. By default, it
        does not timeout. Instead of throwing ``asyncio.TimeoutError`` the coroutine
        catches the exception and returns ``None`` instead of a the ``(reaction, user)``
        tuple.

        If the ``check`` predicate throws an exception, then the exception is propagated.

        The ``emoji`` parameter can be either a :class:`Emoji`, a ``str`` representing
        an emoji, or a sequence of either type. If the ``emoji`` parameter is a sequence
        then the first reaction emoji that is in the list is returned. If ``None`` is
        passed then the first reaction emoji used is returned.

        This function returns the **first reaction that meets the requirements**.

        Examples
        ---------

        Basic Example:

        .. code-block:: python

            @client.event
            async def on_message(message):
                if message.content.startswith('$react'):
                    msg = await client.send_message(message.channel, 'React with thumbs up or thumbs down.')
                    res = await client.wait_for_reaction(['\N{THUMBS UP SIGN}', '\N{THUMBS DOWN SIGN}'], message=msg)
                    await client.send_message(message.channel, '{0.user} reacted with {0.reaction.emoji}!'.format(res))

        Checking for reaction emoji regardless of skin tone:

        .. code-block:: python

            @client.event
            async def on_message(message):
                if message.content.startswith('$react'):
                    msg = await client.send_message(message.channel, 'React with thumbs up or thumbs down.')

                    def check(reaction, user):
                        e = str(reaction.emoji)
                        return e.startswith(('\N{THUMBS UP SIGN}', '\N{THUMBS DOWN SIGN}'))

                    res = await client.wait_for_reaction(message=msg, check=check)
                    await client.send_message(message.channel, '{0.user} reacted with {0.reaction.emoji}!'.format(res))

        Parameters
        -----------
        timeout: float
            The number of seconds to wait before returning ``None``.
        user: :class:`Member` or :class:`User`
            The user the reaction must be from.
        emoji: str or :class:`Emoji` or sequence
            The emoji that we are waiting to react with.
        message: :class:`Message`
            The message that we want the reaction to be from.
        check: function
            A predicate for other complicated checks. The predicate must take
            ``(reaction, user)`` as its two parameters, which ``reaction`` being a
            :class:`Reaction` and ``user`` being either a :class:`User` or a
            :class:`Member`.

        Returns
        --------
        namedtuple
            A namedtuple with attributes ``reaction`` and ``user`` similar to :func:`on_reaction_add`.
        """

        if emoji is None:
            emoji_check = lambda r: True
        elif isinstance(emoji, (str, Emoji)):
            emoji_check = lambda r: r.emoji == emoji
        else:
            emoji_check = lambda r: r.emoji in emoji

        def predicate(reaction, reaction_user):
            result = emoji_check(reaction)

            if message is not None:
                result = result and message.id == reaction.message.id

            if user is not None:
                result = result and user.id == reaction_user.id

            if callable(check):
                # the exception thrown by check is propagated through the future.
                result = result and check(reaction, reaction_user)

            return result

        future = asyncio.Future(loop=self.loop)
        self._listeners.append((predicate, future, WaitForType.reaction))
        try:
            return (yield from asyncio.wait_for(future, timeout, loop=self.loop))
        except asyncio.TimeoutError:
            return None

    # event registration

    def event(self, coro):
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a |corourl|_, if not, :exc:`ClientException` is raised.

        Examples
        ---------

        Using the basic :meth:`event` decorator: ::

            @client.event
            @asyncio.coroutine
            def on_ready():
                print('Ready!')

        Saving characters by using the :meth:`async_event` decorator: ::

            @client.async_event
            def on_ready():
                print('Ready!')

        """

        if not asyncio.iscoroutinefunction(coro):
            raise ClientException('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        log.info('{0.__name__} has successfully been registered as an event'.format(coro))
        return coro

    def async_event(self, coro):
        """A shorthand decorator for ``asyncio.coroutine`` + :meth:`event`."""
        if not asyncio.iscoroutinefunction(coro):
            coro = asyncio.coroutine(coro)

        return self.event(coro)

    # Message sending/management

    @asyncio.coroutine
    def start_private_message(self, user):
        """|coro|

        Starts a private message with the user. This allows you to
        :meth:`send_message` to the user.

        Note
        -----
        This method should rarely be called as :meth:`send_message`
        does it automatically for you.

        Parameters
        -----------
        user : :class:`User`
            The user to start the private message with.

        Raises
        ------
        HTTPException
            The request failed.
        InvalidArgument
            The user argument was not of :class:`User`.
        """

        if not isinstance(user, User):
            raise InvalidArgument('user argument must be a User')

        data = yield from self.http.start_private_message(user.id)
        channel = PrivateChannel(me=self.user, **data)
        self.connection._add_private_channel(channel)
        return channel

    @asyncio.coroutine
    def add_reaction(self, message, emoji):
        """|coro|

        Add a reaction to the given message.

        The message must be a :class:`Message` that exists. emoji may be a unicode emoji,
        or a custom server :class:`Emoji`.

        Parameters
        ------------
        message : :class:`Message`
            The message to react to.
        emoji : :class:`Emoji` or str
            The emoji to react with.

        Raises
        --------
        HTTPException
            Adding the reaction failed.
        Forbidden
            You do not have the proper permissions to react to the message.
        NotFound
            The message or emoji you specified was not found.
        InvalidArgument
            The message or emoji parameter is invalid.
        """
        if not isinstance(message, Message):
            raise InvalidArgument('message argument must be a Message')
        if not isinstance(emoji, (str, Emoji)):
            raise InvalidArgument('emoji argument must be a string or Emoji')

        if isinstance(emoji, Emoji):
            emoji = '{}:{}'.format(emoji.name, emoji.id)

        yield from self.http.add_reaction(message.id, message.channel.id, emoji)

    @asyncio.coroutine
    def remove_reaction(self, message, emoji, member):
        """|coro|

        Remove a reaction by the member from the given message.

        If member != server.me, you need Manage Messages to remove the reaction.

        The message must be a :class:`Message` that exists. emoji may be a unicode emoji,
        or a custom server :class:`Emoji`.

        Parameters
        ------------
        message : :class:`Message`
            The message.
        emoji : :class:`Emoji` or str
            The emoji to remove.
        member : :class:`Member`
            The member for which to delete the reaction.

        Raises
        --------
        HTTPException
            Removing the reaction failed.
        Forbidden
            You do not have the proper permissions to remove the reaction.
        NotFound
            The message or emoji you specified was not found.
        InvalidArgument
            The message or emoji parameter is invalid.
        """
        if not isinstance(message, Message):
            raise InvalidArgument('message argument must be a Message')
        if not isinstance(emoji, (str, Emoji)):
            raise InvalidArgument('emoji must be a string or Emoji')

        if isinstance(emoji, Emoji):
            emoji = '{}:{}'.format(emoji.name, emoji.id)

        if member == self.user:
            member_id = '@me'
        else:
            member_id = member.id

        yield from self.http.remove_reaction(message.id, message.channel.id, emoji, member_id)

    @asyncio.coroutine
    def get_reaction_users(self, reaction, limit=100, after=None):
        """|coro|

        Get the users that added a reaction to a message.

        Parameters
        ------------
        reaction : :class:`Reaction`
            The reaction to retrieve users for.
        limit : int
            The maximum number of results to return.
        after : :class:`Member` or :class:`Object`
            For pagination, reactions are sorted by member.

        Raises
        --------
        HTTPException
            Getting the users for the reaction failed.
        NotFound
            The message or emoji you specified was not found.
        InvalidArgument
            The reaction parameter is invalid.
        """
        if not isinstance(reaction, Reaction):
            raise InvalidArgument('reaction must be a Reaction')

        emoji = reaction.emoji

        if isinstance(emoji, Emoji):
            emoji = '{}:{}'.format(emoji.name, emoji.id)

        if after:
            after = after.id

        data = yield from self.http.get_reaction_users(
            reaction.message.id, reaction.message.channel.id,
            emoji, limit, after=after)

        return [User(**user) for user in data]

    @asyncio.coroutine
    def clear_reactions(self, message):
        """|coro|

        Removes all the reactions from a given message.

        You need Manage Messages permission to use this.

        Parameters
        -----------
        message: :class:`Message`
            The message to remove all reactions from.

        Raises
        --------
        HTTPException
            Removing the reactions failed.
        Forbidden
            You do not have the proper permissions to remove all the reactions.
        """
        yield from self.http.clear_reactions(message.id, message.channel.id)

    @asyncio.coroutine
    def send_message(self, destination, content=None, *, tts=False, embed=None):
        """|coro|

        Sends a message to the destination given with the content given.

        The destination could be a :class:`Channel`, :class:`PrivateChannel` or :class:`Server`.
        For convenience it could also be a :class:`User`. If it's a :class:`User` or :class:`PrivateChannel`
        then it sends the message via private message, otherwise it sends the message to the channel.
        If the destination is a :class:`Server` then it's equivalent to calling
        :attr:`Server.default_channel` and sending it there.

        If it is a :class:`Object` instance then it is assumed to be the
        destination ID. The destination ID is a *channel* so passing in a user
        ID will not be a valid destination.

        .. versionchanged:: 0.9.0
            ``str`` being allowed was removed and replaced with :class:`Object`.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type.

        Parameters
        ------------
        destination
            The location to send the message.
        content
            The content of the message to send. If this is missing,
            then the ``embed`` parameter must be present.
        tts : bool
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`Embed`
            The rich embed for the content.

        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.
        NotFound
            The destination was not found and hence is invalid.
        InvalidArgument
            The destination parameter is invalid.

        Examples
        ----------

        Sending a regular message:

        .. code-block:: python

            await client.send_message(message.channel, 'Hello')

        Sending a TTS message:

        .. code-block:: python

            await client.send_message(message.channel, 'Goodbye.', tts=True)

        Sending an embed message:

        .. code-block:: python

            em = discord.Embed(title='My Embed Title', description='My Embed Content.', colour=0xDEADBF)
            em.set_author(name='Someone', icon_url=client.user.default_avatar_url)
            await client.send_message(message.channel, embed=em)

        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel_id, guild_id = yield from self._resolve_destination(destination)

        content = str(content) if content is not None else None

        if embed is not None:
            embed = embed.to_dict()

        data = yield from self.http.send_message(channel_id, content, guild_id=guild_id, tts=tts, embed=embed)
        channel = self.get_channel(data.get('channel_id'))
        message = self.connection._create_message(channel=channel, **data)
        return message

    @asyncio.coroutine
    def send_typing(self, destination):
        """|coro|

        Send a *typing* status to the destination.

        *Typing* status will go away after 10 seconds, or after a message is sent.

        The destination parameter follows the same rules as :meth:`send_message`.

        Parameters
        ----------
        destination
            The location to send the typing update.
        """

        channel_id, guild_id = yield from self._resolve_destination(destination)
        yield from self.http.send_typing(channel_id)

    @asyncio.coroutine
    def send_file(self, destination, fp, *, filename=None, content=None, tts=False):
        """|coro|

        Sends a message to the destination given with the file given.

        The destination parameter follows the same rules as :meth:`send_message`.

        The ``fp`` parameter should be either a string denoting the location for a
        file or a *file-like object*. The *file-like object* passed is **not closed**
        at the end of execution. You are responsible for closing it yourself.

        .. note::

            If the file-like object passed is opened via ``open`` then the modes
            'rb' should be used.

        The ``filename`` parameter is the filename of the file.
        If this is not given then it defaults to ``fp.name`` or if ``fp`` is a string
        then the ``filename`` will default to the string given. You can overwrite
        this value by passing this in.

        Parameters
        ------------
        destination
            The location to send the message.
        fp
            The *file-like object* or file path to send.
        filename : str
            The filename of the file. Defaults to ``fp.name`` if it's available.
        content
            The content of the message to send along with the file. This is
            forced into a string by a ``str(content)`` call.
        tts : bool
            If the content of the message should be sent with TTS enabled.

        Raises
        -------
        HTTPException
            Sending the file failed.

        Returns
        --------
        :class:`Message`
            The message sent.
        """

        channel_id, guild_id = yield from self._resolve_destination(destination)

        try:
            with open(fp, 'rb') as f:
                buffer = io.BytesIO(f.read())
                if filename is None:
                    _, filename = path_split(fp)
        except TypeError:
            buffer = fp

        content = str(content) if content is not None else None
        data = yield from self.http.send_file(channel_id, buffer, guild_id=guild_id,
                                              filename=filename, content=content, tts=tts)
        channel = self.get_channel(data.get('channel_id'))
        message = self.connection._create_message(channel=channel, **data)
        return message

    @asyncio.coroutine
    def delete_message(self, message):
        """|coro|

        Deletes a :class:`Message`.

        Your own messages could be deleted without any proper permissions. However to
        delete other people's messages, you need the proper permissions to do so.

        Parameters
        -----------
        message : :class:`Message`
            The message to delete.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        HTTPException
            Deleting the message failed.
        """
        channel = message.channel
        guild_id = channel.server.id if not getattr(channel, 'is_private', True) else None
        yield from self.http.delete_message(channel.id, message.id, guild_id)

    @asyncio.coroutine
    def delete_messages(self, messages):
        """|coro|

        Deletes a list of messages. This is similar to :func:`delete_message`
        except it bulk deletes multiple messages.

        The channel to check where the message is deleted from is handled via
        the first element of the iterable's ``.channel.id`` attributes. If the
        channel is not consistent throughout the entire sequence, then an
        :exc:`HTTPException` will be raised.

        Usable only by bot accounts.

        Parameters
        -----------
        messages : iterable of :class:`Message`
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete is less than 2 or more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
        HTTPException
            Deleting the messages failed.
        """

        messages = list(messages)
        if len(messages) > 100 or len(messages) < 2:
            raise ClientException('Can only delete messages in the range of [2, 100]')

        channel = messages[0].channel
        message_ids = [m.id for m in messages]
        guild_id = channel.server.id if not getattr(channel, 'is_private', True) else None
        yield from self.http.delete_messages(channel.id, message_ids, guild_id)

    @asyncio.coroutine
    def purge_from(self, channel, *, limit=100, check=None, before=None, after=None, around=None):
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have Manage Messages permission to delete messages even if they
        are your own. The Read Message History permission is also needed to
        retrieve message history.

        Usable only by bot accounts.

        Parameters
        -----------
        channel : :class:`Channel`
            The channel to purge from.
        limit : int
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check : predicate
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before : :class:`Message` or `datetime`
            The message or date before which all deleted messages must be.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after : :class:`Message` or `datetime`
            The message or date after which all deleted messages must be.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        around : :class:`Message` or `datetime`
            The message or date around which all deleted messages must be.
            If a date is provided it must be a timezone-naive datetime representing UTC time.

        Raises
        -------
        Forbidden
            You do not have proper permissions to do the actions required or
            you're not using a bot account.
        HTTPException
            Purging the messages failed.

        Examples
        ---------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await client.purge_from(channel, limit=100, check=is_me)
            await client.send_message(channel, 'Deleted {} message(s)'.format(len(deleted)))

        Returns
        --------
        list
            The list of messages that were deleted.
        """

        if check is None:
            check = lambda m: True

        if isinstance(before, datetime.datetime):
            before = Object(utils.time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(utils.time_snowflake(after, high=True))
        if isinstance(around, datetime.datetime):
            around = Object(utils.time_snowflake(around, high=True))

        iterator = LogsFromIterator(self, channel, limit, before=before, after=after, around=around)
        ret = []
        count = 0

        while True:
            try:
                msg = yield from iterator.iterate()
            except asyncio.QueueEmpty:
                # no more messages to poll
                if count >= 2:
                    # more than 2 messages -> bulk delete
                    to_delete = ret[-count:]
                    yield from self.delete_messages(to_delete)
                elif count == 1:
                    # delete a single message
                    yield from self.delete_message(ret[-1])

                return ret
            else:
                if count == 100:
                    # we've reached a full 'queue'
                    to_delete = ret[-100:]
                    yield from self.delete_messages(to_delete)
                    count = 0
                    yield from asyncio.sleep(1, loop=self.loop)

                if check(msg):
                    count += 1
                    ret.append(msg)

    @asyncio.coroutine
    def edit_message(self, message, new_content=None, *, embed=None):
        """|coro|

        Edits a :class:`Message` with the new message content.

        The new_content must be able to be transformed into a string via ``str(new_content)``.

        If the ``new_content`` is not provided, then ``embed`` must be provided, which must
        be of type :class:`Embed`.

        The :class:`Message` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        -----------
        message : :class:`Message`
            The message to edit.
        new_content
            The new content to replace the message with.
        embed: :class:`Embed`
            The new embed to replace the original embed with.

        Raises
        -------
        HTTPException
            Editing the message failed.

        Returns
        --------
        :class:`Message`
            The new edited message.
        """

        channel = message.channel
        content = str(new_content) if new_content else None
        embed = embed.to_dict() if embed else None
        guild_id = channel.server.id if not getattr(channel, 'is_private', True) else None
        data = yield from self.http.edit_message(message.id, channel.id, content, guild_id=guild_id, embed=embed)
        return self.connection._create_message(channel=channel, **data)

    @asyncio.coroutine
    def get_message(self, channel, id):
        """|coro|

        Retrieves a single :class:`Message` from a :class:`Channel`.

        This can only be used by bot accounts.

        Parameters
        ------------
        channel: :class:`Channel` or :class:`PrivateChannel`
            The text channel to retrieve the message from.
        id: str
            The message ID to look for.

        Returns
        --------
        :class:`Message`
            The message asked for.

        Raises
        --------
        NotFound
            The specified channel or message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.
        """

        data = yield from self.http.get_message(channel.id, id)
        return self.connection._create_message(channel=channel, **data)

    @asyncio.coroutine
    def pin_message(self, message):
        """|coro|

        Pins a message. You must have Manage Messages permissions
        to do this in a non-private channel context.

        Parameters
        -----------
        message: :class:`Message`
            The message to pin.

        Raises
        -------
        Forbidden
            You do not have permissions to pin the message.
        NotFound
            The message or channel was not found.
        HTTPException
            Pinning the message failed, probably due to the channel
            having more than 50 pinned messages.
        """
        yield from self.http.pin_message(message.channel.id, message.id)

    @asyncio.coroutine
    def unpin_message(self, message):
        """|coro|

        Unpins a message. You must have Manage Messages permissions
        to do this in a non-private channel context.

        Parameters
        -----------
        message: :class:`Message`
            The message to unpin.

        Raises
        -------
        Forbidden
            You do not have permissions to unpin the message.
        NotFound
            The message or channel was not found.
        HTTPException
            Unpinning the message failed.
        """
        yield from self.http.unpin_message(message.channel.id, message.id)

    @asyncio.coroutine
    def pins_from(self, channel):
        """|coro|

        Returns a list of :class:`Message` that are currently pinned for
        the specified :class:`Channel` or :class:`PrivateChannel`.

        Parameters
        -----------
        channel: :class:`Channel` or :class:`PrivateChannel`
            The channel to look through pins for.

        Raises
        -------
        NotFound
            The channel was not found.
        HTTPException
            Retrieving the pinned messages failed.
        """

        data = yield from self.http.pins_from(channel.id)
        return [self.connection._create_message(channel=channel, **m) for m in data]

    def _logs_from(self, channel, limit=100, before=None, after=None, around=None):
        """|coro|

        This coroutine returns a generator that obtains logs from a specified channel.

        Parameters
        -----------
        channel : :class:`Channel` or :class:`PrivateChannel`
            The channel to obtain the logs from.
        limit : int
            The number of messages to retrieve.
        before : :class:`Message` or `datetime`
            The message or date before which all returned messages must be.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after : :class:`Message` or `datetime`
            The message or date after which all returned messages must be.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        around : :class:`Message` or `datetime`
            The message or date around which all returned messages must be.
            If a date is provided it must be a timezone-naive datetime representing UTC time.

        Raises
        ------
        Forbidden
            You do not have permissions to get channel logs.
        NotFound
            The channel you are requesting for doesn't exist.
        HTTPException
            The request to get logs failed.

        Yields
        -------
        :class:`Message`
            The message with the message data parsed.

        Examples
        ---------

        Basic logging: ::

            logs = yield from client.logs_from(channel)
            for message in logs:
                if message.content.startswith('!hello'):
                    if message.author == client.user:
                        yield from client.edit_message(message, 'goodbye')

        Python 3.5 Usage ::

            counter = 0
            async for message in client.logs_from(channel, limit=500):
                if message.author == client.user:
                    counter += 1
        """
        before = getattr(before, 'id', None)
        after  = getattr(after, 'id', None)
        around  = getattr(around, 'id', None)

        return self.http.logs_from(channel.id, limit, before=before, after=after, around=around)

    if PY35:
        def logs_from(self, channel, limit=100, *, before=None, after=None, around=None, reverse=False):
            if isinstance(before, datetime.datetime):
                before = Object(utils.time_snowflake(before, high=False))
            if isinstance(after, datetime.datetime):
                after = Object(utils.time_snowflake(after, high=True))
            if isinstance(around, datetime.datetime):
                around = Object(utils.time_snowflake(around))

            return LogsFromIterator(self, channel, limit, before=before, after=after, around=around, reverse=reverse)
    else:
        @asyncio.coroutine
        def logs_from(self, channel, limit=100, *, before=None, after=None):
            if isinstance(before, datetime.datetime):
                before = Object(utils.time_snowflake(before, high=False))
            if isinstance(after, datetime.datetime):
                after = Object(utils.time_snowflake(after, high=True))

            def generator(data):
                for message in data:
                    yield self.connection._create_message(channel=channel, **message)

            result = []
            while limit > 0:
                retrieve = limit if limit <= 100 else 100
                data = yield from self._logs_from(channel, retrieve, before, after)
                if len(data):
                    limit -= retrieve
                    result.extend(data)
                    before = Object(id=data[-1]['id'])
                else:
                    break

            return generator(result)

    logs_from.__doc__ = _logs_from.__doc__

    # Member management

    @asyncio.coroutine
    def request_offline_members(self, server):
        """|coro|

        Requests previously offline members from the server to be filled up
        into the :attr:`Server.members` cache. This function is usually not
        called.

        When the client logs on and connects to the websocket, Discord does
        not provide the library with offline members if the number of members
        in the server is larger than 250. You can check if a server is large
        if :attr:`Server.large` is ``True``.

        Parameters
        -----------
        server : :class:`Server` or iterable
            The server to request offline members for. If this parameter is a
            iterable then it is interpreted as an iterator of servers to
            request offline members for.
        """

        if hasattr(server, 'id'):
            guild_id = server.id
        else:
            guild_id = [s.id for s in server]

        payload = {
            'op': 8,
            'd': {
                'guild_id': guild_id,
                'query': '',
                'limit': 0
            }
        }

        yield from self.ws.send_as_json(payload)

    @asyncio.coroutine
    def kick(self, member):
        """|coro|

        Kicks a :class:`Member` from the server they belong to.

        Warning
        --------
        This function kicks the :class:`Member` based on the server it
        belongs to, which is accessed via :attr:`Member.server`. So you
        must have the proper permissions in that server.

        Parameters
        -----------
        member : :class:`Member`
            The member to kick from their server.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to kick.
        HTTPException
            Kicking failed.
        """
        yield from self.http.kick(member.id, member.server.id)

    @asyncio.coroutine
    def ban(self, member, delete_message_days=1):
        """|coro|

        Bans a :class:`Member` from the server they belong to.

        Warning
        --------
        This function bans the :class:`Member` based on the server it
        belongs to, which is accessed via :attr:`Member.server`. So you
        must have the proper permissions in that server.

        Parameters
        -----------
        member : :class:`Member`
            The member to ban from their server.
        delete_message_days : int
            The number of days worth of messages to delete from the user
            in the server. The minimum is 0 and the maximum is 7.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """
        yield from self.http.ban(member.id, member.server.id, delete_message_days)

    @asyncio.coroutine
    def unban(self, server, user):
        """|coro|

        Unbans a :class:`User` from the server they are banned from.

        Parameters
        -----------
        server : :class:`Server`
            The server to unban the user from.
        user : :class:`User`
            The user to unban.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """
        yield from self.http.unban(user.id, server.id)

    @asyncio.coroutine
    def server_voice_state(self, member, *, mute=None, deafen=None):
        """|coro|

        Server mutes or deafens a specific :class:`Member`.

        Warning
        --------
        This function mutes or un-deafens the :class:`Member` based on the
        server it belongs to, which is accessed via :attr:`Member.server`.
        So you must have the proper permissions in that server.

        Parameters
        -----------
        member : :class:`Member`
            The member to unban from their server.
        mute: Optional[bool]
            Indicates if the member should be server muted or un-muted.
        deafen: Optional[bool]
            Indicates if the member should be server deafened or un-deafened.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to deafen or mute.
        HTTPException
            The operation failed.
        """
        yield from self.http.server_voice_state(member.id, member.server.id, mute=mute, deafen=deafen)

    @asyncio.coroutine
    def edit_profile(self, password=None, **fields):
        """|coro|

        Edits the current profile of the client.

        If a bot account is used then the password field is optional,
        otherwise it is required.

        The :attr:`Client.user` object is not modified directly afterwards until the
        corresponding WebSocket event is received.

        Note
        -----
        To upload an avatar, a *bytes-like object* must be passed in that
        represents the image being uploaded. If this is done through a file
        then the file must be opened via ``open('some_filename', 'rb')`` and
        the *bytes-like object* is given through the use of ``fp.read()``.

        The only image formats supported for uploading is JPEG and PNG.

        Parameters
        -----------
        password : str
            The current password for the client's account. Not used
            for bot accounts.
        new_password : str
            The new password you wish to change to.
        email : str
            The new email you wish to change to.
        username :str
            The new username you wish to change to.
        avatar : bytes
            A *bytes-like object* representing the image to upload.
            Could be ``None`` to denote no avatar.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar``.
        ClientException
            Password is required for non-bot accounts.
        """

        try:
            avatar_bytes = fields['avatar']
        except KeyError:
            avatar = self.user.avatar
        else:
            if avatar_bytes is not None:
                avatar = utils._bytes_to_base64_data(avatar_bytes)
            else:
                avatar = None

        not_bot_account = not self.user.bot
        if not_bot_account and password is None:
            raise ClientException('Password is required for non-bot accounts.')

        args = {
            'password': password,
            'username': fields.get('username', self.user.name),
            'avatar': avatar
        }

        if not_bot_account:
            args['email'] = fields.get('email', self.email)

            if 'new_password' in fields:
                args['new_password'] = fields['new_password']

        data = yield from self.http.edit_profile(**args)
        if not_bot_account:
            self.email = data['email']
            if 'token' in data:
                self.http._token(data['token'], bot=False)

            if self.cache_auth:
                self._update_cache(self.email, password)

    @asyncio.coroutine
    @utils.deprecated('change_presence')
    def change_status(self, game=None, idle=False):
        """|coro|

        Changes the client's status.

        The game parameter is a Game object (not a string) that represents
        a game being played currently.

        The idle parameter is a boolean parameter that indicates whether the
        client should go idle or not.

        .. deprecated:: v0.13.0
            Use :meth:`change_presence` instead.

        Parameters
        ----------
        game : Optional[:class:`Game`]
            The game being played. None if no game is being played.
        idle : bool
            Indicates if the client should go idle.

        Raises
        ------
        InvalidArgument
            If the ``game`` parameter is not :class:`Game` or None.
        """
        yield from self.ws.change_presence(game=game, idle=idle)

    @asyncio.coroutine
    def change_presence(self, *, game=None, status=None, afk=False):
        """|coro|

        Changes the client's presence.

        The game parameter is a Game object (not a string) that represents
        a game being played currently.

        Parameters
        ----------
        game: Optional[:class:`Game`]
            The game being played. None if no game is being played.
        status: Optional[:class:`Status`]
            Indicates what status to change to. If None, then
            :attr:`Status.online` is used.
        afk: bool
            Indicates if you are going AFK. This allows the discord
            client to know how to handle push notifications better
            for you in case you are actually idle and not lying.

        Raises
        ------
        InvalidArgument
            If the ``game`` parameter is not :class:`Game` or None.
        """

        if status is None:
            status = 'online'
        elif status is Status.offline:
            status = 'invisible'
        else:
            status = str(status)

        yield from self.ws.change_presence(game=game, status=status, afk=afk)

    @asyncio.coroutine
    def change_nickname(self, member, nickname):
        """|coro|

        Changes a member's nickname.

        You must have the proper permissions to change someone's
        (or your own) nickname.

        Parameters
        ----------
        member : :class:`Member`
            The member to change the nickname for.
        nickname : Optional[str]
            The nickname to change it to. ``None`` to remove
            the nickname.

        Raises
        ------
        Forbidden
            You do not have permissions to change the nickname.
        HTTPException
            Changing the nickname failed.
        """

        nickname = nickname if nickname else ''

        if member == self.user:
            yield from self.http.change_my_nickname(member.server.id, nickname)
        else:
            yield from self.http.change_nickname(member.server.id, member.id, nickname)

    # Channel management

    @asyncio.coroutine
    def edit_channel(self, channel, **options):
        """|coro|

        Edits a :class:`Channel`.

        You must have the proper permissions to edit the channel.

        To move the channel's position use :meth:`move_channel` instead.

        The :class:`Channel` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        ----------
        channel : :class:`Channel`
            The channel to update.
        name : str
            The new channel name.
        topic : str
            The new channel's topic.
        bitrate : int
            The new channel's bitrate. Voice only.
        user_limit : int
            The new channel's user limit. Voice only.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """

        keys = ('name', 'topic', 'position')
        for key in keys:
            if key not in options:
                options[key] = getattr(channel, key)

        yield from self.http.edit_channel(channel.id, **options)

    @asyncio.coroutine
    def move_channel(self, channel, position):
        """|coro|

        Moves the specified :class:`Channel` to the given position in the GUI.
        Note that voice channels and text channels have different position values.

        The :class:`Channel` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        .. warning::

            :class:`Object` instances do not work with this function.

        Parameters
        -----------
        channel : :class:`Channel`
            The channel to change positions of.
        position : int
            The position to insert the channel to.

        Raises
        -------
        InvalidArgument
            If position is less than 0 or greater than the number of channels.
        Forbidden
            You do not have permissions to change channel order.
        HTTPException
            If moving the channel failed, or you are of too low rank to move the channel.
        """

        if position < 0:
            raise InvalidArgument('Channel position cannot be less than 0.')

        channels = [c for c in channel.server.channels if c.type is channel.type]

        if position >= len(channels):
            raise InvalidArgument('Channel position cannot be greater than {}'.format(len(channels) - 1))

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(channel)
        except ValueError:
            # not there somehow lol
            return
        else:
            # add ourselves at our designated position
            channels.insert(position, channel)

        payload = [{'id': c.id, 'position': index } for index, c in enumerate(channels)]
        yield from self.http.move_channel_position(channel.server.id, payload)

    @asyncio.coroutine
    def create_channel(self, server, name, *overwrites, type=None):
        """|coro|

        Creates a :class:`Channel` in the specified :class:`Server`.

        Note that you need the proper permissions to create the channel.

        The ``overwrites`` argument list can be used to create a 'secret'
        channel upon creation. A namedtuple of :class:`ChannelPermissions`
        is exposed to create a channel-specific permission overwrite in a more
        self-documenting matter. You can also use a regular tuple of ``(target, overwrite)``
        where the ``overwrite`` expected has to be of type :class:`PermissionOverwrite`.

        Examples
        ----------

        Creating a voice channel:

        .. code-block:: python

            await client.create_channel(server, 'Voice', type=discord.ChannelType.voice)

        Creating a 'secret' text channel:

        .. code-block:: python

            everyone_perms = discord.PermissionOverwrite(read_messages=False)
            my_perms = discord.PermissionOverwrite(read_messages=True)

            everyone = discord.ChannelPermissions(target=server.default_role, overwrite=everyone_perms)
            mine = discord.ChannelPermissions(target=server.me, overwrite=my_perms)
            await client.create_channel(server, 'secret', everyone, mine)

        Or in a more 'compact' way:

        .. code-block:: python

            everyone = discord.PermissionOverwrite(read_messages=False)
            mine = discord.PermissionOverwrite(read_messages=True)
            await client.create_channel(server, 'secret', (server.default_role, everyone), (server.me, mine))

        Parameters
        -----------
        server : :class:`Server`
            The server to create the channel in.
        name : str
            The channel's name.
        type : :class:`ChannelType`
            The type of channel to create. Defaults to :attr:`ChannelType.text`.
        overwrites:
            An argument list of channel specific overwrites to apply on the channel on
            creation. Useful for creating 'secret' channels.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to create the channel.
        NotFound
            The server specified was not found.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite array is not in proper form.

        Returns
        -------
        :class:`Channel`
            The channel that was just created. This channel is
            different than the one that will be added in cache.
        """

        if type is None:
            type = ChannelType.text

        perms = []
        for overwrite in overwrites:
            target = overwrite[0]
            perm = overwrite[1]
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument('Expected PermissionOverwrite received {0.__name__}'.format(type(perm)))

            allow, deny = perm.pair()
            payload = {
                'allow': allow.value,
                'deny': deny.value,
                'id': target.id
            }

            if isinstance(target, User):
                payload['type'] = 'member'
            elif isinstance(target, Role):
                payload['type'] = 'role'
            else:
                raise InvalidArgument('Expected Role, User, or Member target, received {0.__name__}'.format(type(target)))

            perms.append(payload)

        data = yield from self.http.create_channel(server.id, name, str(type), permission_overwrites=perms)
        channel = Channel(server=server, **data)
        return channel

    @asyncio.coroutine
    def delete_channel(self, channel):
        """|coro|

        Deletes a :class:`Channel`.

        In order to delete the channel, the client must have the proper permissions
        in the server the channel belongs to.

        Parameters
        ------------
        channel : :class:`Channel`
            The channel to delete.

        Raises
        -------
        Forbidden
            You do not have proper permissions to delete the channel.
        NotFound
            The specified channel was not found.
        HTTPException
            Deleting the channel failed.
        """
        yield from self.http.delete_channel(channel.id)

    # Server management

    @asyncio.coroutine
    def leave_server(self, server):
        """|coro|

        Leaves a :class:`Server`.

        Note
        --------
        You cannot leave the server that you own, you must delete it instead
        via :meth:`delete_server`.

        Parameters
        ----------
        server : :class:`Server`
            The server to leave.

        Raises
        --------
        HTTPException
            If leaving the server failed.
        """
        yield from self.http.leave_server(server.id)

    @asyncio.coroutine
    def delete_server(self, server):
        """|coro|

        Deletes a :class:`Server`. You must be the server owner to delete the
        server.

        Parameters
        ----------
        server : :class:`Server`
            The server to delete.

        Raises
        --------
        HTTPException
            If deleting the server failed.
        Forbidden
            You do not have permissions to delete the server.
        """

        yield from self.http.delete_server(server.id)

    @asyncio.coroutine
    def create_server(self, name, region=None, icon=None):
        """|coro|

        Creates a :class:`Server`.

        Bot accounts generally are not allowed to create servers.
        See Discord's official documentation for more info.

        Parameters
        ----------
        name : str
            The name of the server.
        region : :class:`ServerRegion`
            The region for the voice communication server.
            Defaults to :attr:`ServerRegion.us_west`.
        icon : bytes
            The *bytes-like* object representing the icon. See :meth:`edit_profile`
            for more details on what is expected.

        Raises
        ------
        HTTPException
            Server creation failed.
        InvalidArgument
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`Server`
            The server created. This is not the same server that is
            added to cache.
        """
        if icon is not None:
            icon = utils._bytes_to_base64_data(icon)

        if region is None:
            region = ServerRegion.us_west.value
        else:
            region = region.value

        data = yield from self.http.create_server(name, region, icon)
        return Server(**data)

    @asyncio.coroutine
    def edit_server(self, server, **fields):
        """|coro|

        Edits a :class:`Server`.

        You must have the proper permissions to edit the server.

        The :class:`Server` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        ----------
        server: :class:`Server`
            The server to edit.
        name: str
            The new name of the server.
        icon: bytes
            A *bytes-like* object representing the icon. See :meth:`edit_profile`
            for more details. Could be ``None`` to denote no icon.
        splash: bytes
            A *bytes-like* object representing the invite splash. See
            :meth:`edit_profile` for more details. Could be ``None`` to denote
            no invite splash. Only available for partnered servers with
            ``INVITE_SPLASH`` feature.
        region: :class:`ServerRegion`
            The new region for the server's voice communication.
        afk_channel: Optional[:class:`Channel`]
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout: int
            The number of seconds until someone is moved to the AFK channel.
        owner: :class:`Member`
            The new owner of the server to transfer ownership to. Note that you must
            be owner of the server to do this.
        verification_level: :class:`VerificationLevel`
            The new verification level for the server.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the server.
        NotFound
            The server you are trying to edit does not exist.
        HTTPException
            Editing the server failed.
        InvalidArgument
            The image format passed in to ``icon`` is invalid. It must be
            PNG or JPG. This is also raised if you are not the owner of the
            server and request an ownership transfer.
        """

        try:
            icon_bytes = fields['icon']
        except KeyError:
            icon = server.icon
        else:
            if icon_bytes is not None:
                icon = utils._bytes_to_base64_data(icon_bytes)
            else:
                icon = None

        try:
            splash_bytes = fields['splash']
        except KeyError:
            splash = server.splash
        else:
            if splash_bytes is not None:
                splash = utils._bytes_to_base64_data(splash_bytes)
            else:
                splash = None

        fields['icon'] = icon
        fields['splash'] = splash

        try:
            afk_channel = fields.pop('afk_channel')
        except KeyError:
            pass
        else:
            if afk_channel is None:
                fields['afk_channel_id'] = afk_channel
            else:
                fields['afk_channel_id'] = afk_channel.id

        if 'owner' in fields:
            if server.owner != server.me:
                raise InvalidArgument('To transfer ownership you must be the owner of the server.')

            fields['owner_id'] = fields['owner'].id

        if 'region' in fields:
            fields['region'] = str(fields['region'])

        level = fields.get('verification_level', server.verification_level)
        if not isinstance(level, VerificationLevel):
            raise InvalidArgument('verification_level field must of type VerificationLevel')

        fields['verification_level'] = level.value
        yield from self.http.edit_server(server.id, **fields)

    @asyncio.coroutine
    def get_bans(self, server):
        """|coro|

        Retrieves all the :class:`User` s that are banned from the specified
        server.

        You must have proper permissions to get this information.

        Parameters
        ----------
        server : :class:`Server`
            The server to get ban information from.

        Raises
        -------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        --------
        list
            A list of :class:`User` that have been banned.
        """

        data = yield from self.http.get_bans(server.id)
        return [User(**user['user']) for user in data]

    @asyncio.coroutine
    def prune_members(self, server, *, days):
        """|coro|

        Prunes a :class:`Server` from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days and they have no roles.

        You must have the "Kick Members" permission to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        Parameters
        -----------
        server: :class:`Server`
            The server to prune from.
        days: int
            The number of days before counting as inactive.

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while pruning members.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        int
            The number of members pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        data = yield from self.http.prune_members(server.id, days)
        return data['pruned']

    @asyncio.coroutine
    def estimate_pruned_members(self, server, *, days):
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the server had it been called.

        Parameters
        -----------
        server: :class:`Server`
            The server to estimate a prune from.
        days: int
            The number of days before counting as inactive.

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while fetching the prune members estimate.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        int
            The number of members estimated to be pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        data = yield from self.http.estimate_pruned_members(server.id, days)
        return data['pruned']

    @asyncio.coroutine
    def create_custom_emoji(self, server, *, name, image):
        """|coro|

        Creates a custom :class:`Emoji` for a :class:`Server`.

        This endpoint is only allowed for user bots or white listed
        bots. If this is done by a user bot then this is a local
        emoji that can only be used inside that server.

        There is currently a limit of 50 local emotes per server.

        Parameters
        -----------
        server: :class:`Server`
            The server to add the emoji to.
        name: str
            The emoji name. Must be at least 2 characters.
        image: bytes
            The *bytes-like* object representing the image data to use.
            Only JPG and PNG images are supported.

        Returns
        --------
        :class:`Emoji`
            The created emoji.

        Raises
        -------
        Forbidden
            You are not allowed to create emojis.
        HTTPException
            An error occurred creating an emoji.
        """

        img = utils._bytes_to_base64_data(image)
        data = yield from self.http.create_custom_emoji(server.id, name, img)
        return Emoji(server=server, **data)

    @asyncio.coroutine
    def delete_custom_emoji(self, emoji):
        """|coro|

        Deletes a custom :class:`Emoji` from a :class:`Server`.

        This follows the same rules as :meth:`create_custom_emoji`.

        Parameters
        -----------
        emoji: :class:`Emoji`
            The emoji to delete.

        Raises
        -------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        yield from self.http.delete_custom_emoji(emoji.server.id, emoji.id)

    @asyncio.coroutine
    def edit_custom_emoji(self, emoji, *, name):
        """|coro|

        Edits a :class:`Emoji`.

        Parameters
        -----------
        emoji: :class:`Emoji`
            The emoji to edit.
        name: str
            The new emoji name.

        Raises
        -------
        Forbidden
            You are not allowed to edit emojis.
        HTTPException
            An error occurred editing the emoji.
        """

        yield from self.http.edit_custom_emoji(emoji.server.id, emoji.id, name=name)


    # Invite management

    def _fill_invite_data(self, data):
        server = self.connection._get_server(data['guild']['id'])
        if server is not None:
            ch_id = data['channel']['id']
            channel = server.get_channel(ch_id)
        else:
            server = Object(id=data['guild']['id'])
            server.name = data['guild']['name']
            channel = Object(id=data['channel']['id'])
            channel.name = data['channel']['name']
        data['server'] = server
        data['channel'] = channel

    @asyncio.coroutine
    def create_invite(self, destination, **options):
        """|coro|

        Creates an invite for the destination which could be either a
        :class:`Server` or :class:`Channel`.

        Parameters
        ------------
        destination
            The :class:`Server` or :class:`Channel` to create the invite to.
        max_age : int
            How long the invite should last. If it's 0 then the invite
            doesn't expire. Defaults to 0.
        max_uses : int
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to 0.
        temporary : bool
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to False.
        unique: bool
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to False then it will return a previously created
            invite.

        Raises
        -------
        HTTPException
            Invite creation failed.

        Returns
        --------
        :class:`Invite`
            The invite that was created.
        """

        data = yield from self.http.create_invite(destination.id, **options)
        self._fill_invite_data(data)
        return Invite(**data)

    @asyncio.coroutine
    def get_invite(self, url):
        """|coro|

        Gets a :class:`Invite` from a discord.gg URL or ID.

        Note
        ------
        If the invite is for a server you have not joined, the server and channel
        attributes of the returned invite will be :class:`Object` with the names
        patched in.

        Parameters
        -----------
        url : str
            The discord invite ID or URL (must be a discord.gg URL).

        Raises
        -------
        NotFound
            The invite has expired or is invalid.
        HTTPException
            Getting the invite failed.

        Returns
        --------
        :class:`Invite`
            The invite from the URL/ID.
        """

        invite_id = self._resolve_invite(url)
        data = yield from self.http.get_invite(invite_id)
        self._fill_invite_data(data)
        return Invite(**data)

    @asyncio.coroutine
    def invites_from(self, server):
        """|coro|

        Returns a list of all active instant invites from a :class:`Server`.

        You must have proper permissions to get this information.

        Parameters
        ----------
        server : :class:`Server`
            The server to get invites from.

        Raises
        -------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        list of :class:`Invite`
            The list of invites that are currently active.
        """

        data = yield from self.http.invites_from(server.id)
        result = []
        for invite in data:
            channel = server.get_channel(invite['channel']['id'])
            invite['channel'] = channel
            invite['server'] = server
            result.append(Invite(**invite))

        return result

    @asyncio.coroutine
    def accept_invite(self, invite):
        """|coro|

        Accepts an :class:`Invite`, URL or ID to an invite.

        The URL must be a discord.gg URL. e.g. "http://discord.gg/codehere".
        An ID for the invite is just the "codehere" portion of the invite URL.

        Parameters
        -----------
        invite
            The :class:`Invite` or URL to an invite to accept.

        Raises
        -------
        HTTPException
            Accepting the invite failed.
        NotFound
            The invite is invalid or expired.
        Forbidden
            You are a bot user and cannot use this endpoint.
        """

        invite_id = self._resolve_invite(invite)
        yield from self.http.accept_invite(invite_id)

    @asyncio.coroutine
    def delete_invite(self, invite):
        """|coro|

        Revokes an :class:`Invite`, URL, or ID to an invite.

        The ``invite`` parameter follows the same rules as
        :meth:`accept_invite`.

        Parameters
        ----------
        invite
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

        invite_id = self._resolve_invite(invite)
        yield from self.http.delete_invite(invite_id)

    # Role management

    @asyncio.coroutine
    def move_role(self, server, role, position):
        """|coro|

        Moves the specified :class:`Role` to the given position in the :class:`Server`.

        The :class:`Role` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        -----------
        server : :class:`Server`
            The server the role belongs to.
        role : :class:`Role`
            The role to edit.
        position : int
            The position to insert the role to.

        Raises
        -------
        InvalidArgument
            If position is 0, or role is server.default_role
        Forbidden
            You do not have permissions to change role order.
        HTTPException
            If moving the role failed, or you are of too low rank to move the role.
        """

        if position == 0:
            raise InvalidArgument("Cannot move role to position 0")

        if role == server.default_role:
            raise InvalidArgument("Cannot move default role")

        if role.position == position:
            return  # Save discord the extra request.

        change_range = range(min(role.position, position), max(role.position, position) + 1)

        roles = [r.id for r in sorted(filter(lambda x: (x.position in change_range) and x != role, server.roles), key=lambda x: x.position)]

        if role.position > position:
            roles.insert(0, role.id)
        else:
            roles.append(role.id)

        payload = [{"id": z[0], "position": z[1]} for z in zip(roles, change_range)]
        yield from self.http.move_role_position(server.id, payload)

    @asyncio.coroutine
    def edit_role(self, server, role, **fields):
        """|coro|

        Edits the specified :class:`Role` for the entire :class:`Server`.

        The :class:`Role` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        All fields except ``server`` and ``role`` are optional. To change
        the position of a role, use :func:`move_role` instead.

        .. versionchanged:: 0.8.0
            Editing now uses keyword arguments instead of editing the :class:`Role` object directly.

        Parameters
        -----------
        server : :class:`Server`
            The server the role belongs to.
        role : :class:`Role`
            The role to edit.
        name : str
            The new role name to change to.
        permissions : :class:`Permissions`
            The new permissions to change to.
        colour : :class:`Colour`
            The new colour to change to. (aliased to color as well)
        hoist : bool
            Indicates if the role should be shown separately in the online list.
        mentionable : bool
            Indicates if the role should be mentionable by others.

        Raises
        -------
        Forbidden
            You do not have permissions to change the role.
        HTTPException
            Editing the role failed.
        """

        colour = fields.get('colour')
        if colour is None:
            colour = fields.get('color', role.colour)

        payload = {
            'name': fields.get('name', role.name),
            'permissions': fields.get('permissions', role.permissions).value,
            'color': colour.value,
            'hoist': fields.get('hoist', role.hoist),
            'mentionable': fields.get('mentionable', role.mentionable)
        }

        yield from self.http.edit_role(server.id, role.id, **payload)

    @asyncio.coroutine
    def delete_role(self, server, role):
        """|coro|

        Deletes the specified :class:`Role` for the entire :class:`Server`.

        Parameters
        -----------
        server : :class:`Server`
            The server the role belongs to.
        role : :class:`Role`
            The role to delete.

        Raises
        --------
        Forbidden
            You do not have permissions to delete the role.
        HTTPException
            Deleting the role failed.
        """

        yield from self.http.delete_role(server.id, role.id)

    @asyncio.coroutine
    def _replace_roles(self, member, roles):
        yield from self.http.replace_roles(member.id, member.server.id, roles)

    @asyncio.coroutine
    def add_roles(self, member, *roles):
        """|coro|

        Gives the specified :class:`Member` a number of :class:`Role` s.

        You must have the proper permissions to use this function.

        The :class:`Member` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        -----------
        member : :class:`Member`
            The member to give roles to.
        \*roles
            An argument list of :class:`Role` s to give the member.

        Raises
        -------
        Forbidden
            You do not have permissions to add roles.
        HTTPException
            Adding roles failed.
        """

        new_roles = utils._unique(role.id for role in itertools.chain(member.roles, roles))
        yield from self._replace_roles(member, new_roles)

    @asyncio.coroutine
    def remove_roles(self, member, *roles):
        """|coro|

        Removes the :class:`Role` s from the :class:`Member`.

        You must have the proper permissions to use this function.

        The :class:`Member` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        -----------
        member : :class:`Member`
            The member to revoke roles from.
        \*roles
            An argument list of :class:`Role` s to revoke the member.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke roles.
        HTTPException
            Removing roles failed.
        """
        new_roles = [x.id for x in member.roles]
        for role in roles:
            try:
                new_roles.remove(role.id)
            except ValueError:
                pass

        yield from self._replace_roles(member, new_roles)

    @asyncio.coroutine
    def replace_roles(self, member, *roles):
        """|coro|

        Replaces the :class:`Member`'s roles.

        You must have the proper permissions to use this function.

        This function **replaces** all roles that the member has.
        For example if the member has roles ``[a, b, c]`` and the
        call is ``client.replace_roles(member, d, e, c)`` then
        the member has the roles ``[d, e, c]``.

        The :class:`Member` object is not directly modified afterwards until the
        corresponding WebSocket event is received.

        Parameters
        -----------
        member : :class:`Member`
            The member to replace roles from.
        \*roles
            An argument list of :class:`Role` s to replace the roles with.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke roles.
        HTTPException
            Removing roles failed.
        """

        new_roles = utils._unique(role.id for role in roles)
        yield from self._replace_roles(member, new_roles)

    @asyncio.coroutine
    def create_role(self, server, **fields):
        """|coro|

        Creates a :class:`Role`.

        This function is similar to :class:`edit_role` in both
        the fields taken and exceptions thrown.

        Returns
        --------
        :class:`Role`
            The newly created role. This not the same role that
            is stored in cache.
        """

        data = yield from self.http.create_role(server.id)
        role = Role(server=server, **data)

        # we have to call edit because you can't pass a payload to the
        # http request currently.
        yield from self.edit_role(server, role, **fields)
        return role

    @asyncio.coroutine
    def edit_channel_permissions(self, channel, target, overwrite=None):
        """|coro|

        Sets the channel specific permission overwrites for a target in the
        specified :class:`Channel`.

        The ``target`` parameter should either be a :class:`Member` or a
        :class:`Role` that belongs to the channel's server.

        You must have the proper permissions to do this.

        Examples
        ----------

        Setting allow and deny: ::

            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = True
            overwrite.ban_members = False
            await client.edit_channel_permissions(message.channel, message.author, overwrite)

        Parameters
        -----------
        channel : :class:`Channel`
            The channel to give the specific permissions for.
        target
            The :class:`Member` or :class:`Role` to overwrite permissions for.
        overwrite: :class:`PermissionOverwrite`
            The permissions to allow and deny to the target.

        Raises
        -------
        Forbidden
            You do not have permissions to edit channel specific permissions.
        NotFound
            The channel specified was not found.
        HTTPException
            Editing channel specific permissions failed.
        InvalidArgument
            The overwrite parameter was not of type :class:`PermissionOverwrite`
            or the target type was not :class:`Role` or :class:`Member`.
        """

        overwrite = PermissionOverwrite() if overwrite is None else overwrite


        if not isinstance(overwrite, PermissionOverwrite):
            raise InvalidArgument('allow and deny parameters must be PermissionOverwrite')

        allow, deny = overwrite.pair()

        if isinstance(target, Member):
            perm_type = 'member'
        elif isinstance(target, Role):
            perm_type = 'role'
        else:
            raise InvalidArgument('target parameter must be either Member or Role')

        yield from self.http.edit_channel_permissions(channel.id, target.id, allow.value, deny.value, perm_type)

    @asyncio.coroutine
    def delete_channel_permissions(self, channel, target):
        """|coro|

        Removes a channel specific permission overwrites for a target
        in the specified :class:`Channel`.

        The target parameter follows the same rules as :meth:`edit_channel_permissions`.

        You must have the proper permissions to do this.

        Parameters
        ----------
        channel : :class:`Channel`
            The channel to give the specific permissions for.
        target
            The :class:`Member` or :class:`Role` to overwrite permissions for.

        Raises
        ------
        Forbidden
            You do not have permissions to delete channel specific permissions.
        NotFound
            The channel specified was not found.
        HTTPException
            Deleting channel specific permissions failed.
        """
        yield from self.http.delete_channel_permissions(channel.id, target.id)

    # Voice management

    @asyncio.coroutine
    def move_member(self, member, channel):
        """|coro|

        Moves a :class:`Member` to a different voice channel.

        You must have proper permissions to do this.

        Note
        -----
        You cannot pass in a :class:`Object` instead of a :class:`Channel`
        object in this function.

        Parameters
        -----------
        member : :class:`Member`
            The member to move to another voice channel.
        channel : :class:`Channel`
            The voice channel to move the member to.

        Raises
        -------
        InvalidArgument
            The channel provided is not a voice channel.
        HTTPException
            Moving the member failed.
        Forbidden
            You do not have permissions to move the member.
        """

        if getattr(channel, 'type', ChannelType.text) != ChannelType.voice:
            raise InvalidArgument('The channel provided must be a voice channel.')

        yield from self.http.move_member(member.id, member.server.id, channel.id)

    @asyncio.coroutine
    def join_voice_channel(self, channel):
        """|coro|

        Joins a voice channel and creates a :class:`VoiceClient` to
        establish your connection to the voice server.

        After this function is successfully called, :attr:`voice` is
        set to the returned :class:`VoiceClient`.

        Parameters
        ----------
        channel : :class:`Channel`
            The voice channel to join to.

        Raises
        -------
        InvalidArgument
            The channel was not a voice channel.
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ClientException
            You are already connected to a voice channel.
        OpusNotLoaded
            The opus library has not been loaded.

        Returns
        -------
        :class:`VoiceClient`
            A voice client that is fully connected to the voice server.
        """
        if isinstance(channel, Object):
            channel = self.get_channel(channel.id)

        if getattr(channel, 'type', ChannelType.text) != ChannelType.voice:
            raise InvalidArgument('Channel passed must be a voice channel')

        server = channel.server

        if self.is_voice_connected(server):
            raise ClientException('Already connected to a voice channel in this server')

        log.info('attempting to join voice channel {0.name}'.format(channel))

        def session_id_found(data):
            user_id = data.get('user_id')
            guild_id = data.get('guild_id')
            return user_id == self.user.id and guild_id == server.id

        # register the futures for waiting
        session_id_future = self.ws.wait_for('VOICE_STATE_UPDATE', session_id_found)
        voice_data_future = self.ws.wait_for('VOICE_SERVER_UPDATE', lambda d: d.get('guild_id') == server.id)

        # request joining
        yield from self.ws.voice_state(server.id, channel.id)

        try:
            session_id_data = yield from asyncio.wait_for(session_id_future, timeout=10.0, loop=self.loop)
            data = yield from asyncio.wait_for(voice_data_future, timeout=10.0, loop=self.loop)
        except asyncio.TimeoutError as e:
            yield from self.ws.voice_state(server.id, None, self_mute=True)
            raise e

        kwargs = {
            'user': self.user,
            'channel': channel,
            'data': data,
            'loop': self.loop,
            'session_id': session_id_data.get('session_id'),
            'main_ws': self.ws
        }

        voice = VoiceClient(**kwargs)
        try:
            yield from voice.connect()
        except asyncio.TimeoutError as e:
            try:
                yield from voice.disconnect()
            except:
                # we don't care if disconnect failed because connection failed
                pass
            raise e # re-raise

        self.connection._add_voice_client(server.id, voice)
        return voice

    def is_voice_connected(self, server):
        """Indicates if we are currently connected to a voice channel in the
        specified server.

        Parameters
        -----------
        server : :class:`Server`
            The server to query if we're connected to it.
        """
        voice = self.voice_client_in(server)
        return voice is not None

    def voice_client_in(self, server):
        """Returns the voice client associated with a server.

        If no voice client is found then ``None`` is returned.

        Parameters
        -----------
        server : :class:`Server`
            The server to query if we have a voice client for.

        Returns
        --------
        :class:`VoiceClient`
            The voice client associated with the server.
        """
        return self.connection._get_voice_client(server.id)

    def group_call_in(self, channel):
        """Returns the :class:`GroupCall` associated with a private channel.

        If no group call is found then ``None`` is returned.

        Parameters
        -----------
        channel: :class:`PrivateChannel`
            The group private channel to query the group call for.

        Returns
        --------
        Optional[:class:`GroupCall`]
            The group call.
        """
        return self.connection._calls.get(channel.id)

    # Miscellaneous stuff

    @asyncio.coroutine
    def application_info(self):
        """|coro|

        Retrieve's the bot's application information.

        Returns
        --------
        :class:`AppInfo`
            A namedtuple representing the application info.

        Raises
        -------
        HTTPException
            Retrieving the information failed somehow.
        """
        data = yield from self.http.application_info()
        return AppInfo(id=data['id'], name=data['name'],
                       description=data['description'], icon=data['icon'],
                       owner=User(**data['owner']))

    @asyncio.coroutine
    def get_user_info(self, user_id):
        """|coro|

        Retrieves a :class:`User` based on their ID. This can only
        be used by bot accounts. You do not have to share any servers
        with the user to get this information, however many operations
        do require that you do.

        Parameters
        -----------
        user_id: str
            The user's ID to fetch from.

        Returns
        --------
        :class:`User`
            The user you requested.

        Raises
        -------
        NotFound
            A user with this ID does not exist.
        HTTPException
            Fetching the user failed.
        """
        data = yield from self.http.get_user_info(user_id)
        return User(**data)
