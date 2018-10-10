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

from .user import User, Profile
from .invite import Invite
from .object import Object
from .guild import Guild
from .errors import *
from .enums import Status, VoiceRegion
from .gateway import *
from .activity import _ActivityTag, create_activity
from .voice_client import VoiceClient
from .http import HTTPClient
from .state import ConnectionState
from . import utils
from .backoff import ExponentialBackoff
from .webhook import Webhook

import asyncio
import aiohttp
import websockets

import logging, traceback
import sys, re
import signal
from collections import namedtuple

log = logging.getLogger(__name__)

AppInfo = namedtuple('AppInfo',
                     'id name description rpc_origins bot_public bot_require_code_grant icon owner')

def app_info_icon_url(self):
    """Retrieves the application's icon_url if it exists. Empty string otherwise."""
    if not self.icon:
        return ''

    return 'https://cdn.discordapp.com/app-icons/{0.id}/{0.icon}.jpg'.format(self)

AppInfo.icon_url = property(app_info_icon_url)

class Client:
    """Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client`.

    .. _event loop: https://docs.python.org/3/library/asyncio-eventloops.html
    .. _connector: http://aiohttp.readthedocs.org/en/stable/client_reference.html#connectors
    .. _ProxyConnector: http://aiohttp.readthedocs.org/en/stable/client_reference.html#proxyconnector

    Parameters
    -----------
    max_messages : Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to 5000. Passing in `None` or a value less than 100
        will use the default instead of the passed in value.
    loop : Optional[event loop]
        The `event loop`_ to use for asynchronous operations. Defaults to ``None``,
        in which case the default event loop is used via ``asyncio.get_event_loop()``.
    connector : aiohttp.BaseConnector
        The `connector`_ to use for connection pooling.
    proxy : Optional[:class:`str`]
        Proxy URL.
    proxy_auth : Optional[aiohttp.BasicAuth]
        An object that represents proxy HTTP Basic Authorization.
    shard_id : Optional[:class:`int`]
        Integer starting at 0 and less than shard_count.
    shard_count : Optional[:class:`int`]
        The total number of shards.
    fetch_offline_members: :class:`bool`
        Indicates if :func:`on_ready` should be delayed to fetch all offline
        members from the guilds the bot belongs to. If this is ``False``\, then
        no offline members are received and :meth:`request_offline_members`
        must be used to fetch the offline members of the guild.
    status: Optional[:class:`Status`]
        A status to start your presence with upon logging on to Discord.
    activity: Optional[Union[:class:`Activity`, :class:`Game`, :class:`Streaming`]]
        An activity to start your presence with upon logging on to Discord.
    heartbeat_timeout: :class:`float`
        The maximum numbers of seconds before timing out and restarting the
        WebSocket in the case of not receiving a HEARTBEAT_ACK. Useful if
        processing the initial packets take too long to the point of disconnecting
        you. The default timeout is 60 seconds.

    Attributes
    -----------
    ws
        The websocket gateway the client is currently connected to. Could be None.
    loop
        The `event loop`_ that the client uses for HTTP requests and websocket operations.
    """
    def __init__(self, *, loop=None, **options):
        self.ws = None
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._listeners = {}
        self.shard_id = options.get('shard_id')
        self.shard_count = options.get('shard_count')

        connector = options.pop('connector', None)
        proxy = options.pop('proxy', None)
        proxy_auth = options.pop('proxy_auth', None)
        self.http = HTTPClient(connector, proxy=proxy, proxy_auth=proxy_auth, loop=self.loop)

        self._handlers = {
            'ready': self._handle_ready
        }

        self._connection = ConnectionState(dispatch=self.dispatch, chunker=self._chunker, handlers=self._handlers,
                                           syncer=self._syncer, http=self.http, loop=self.loop, **options)

        self._connection.shard_count = self.shard_count
        self._closed = asyncio.Event(loop=self.loop)
        self._ready = asyncio.Event(loop=self.loop)
        self._connection._get_websocket = lambda g: self.ws

        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            log.warning("PyNaCl is not installed, voice will NOT be supported")

    # internals

    async def _syncer(self, guilds):
        await self.ws.request_sync(guilds)

    async def _chunker(self, guild):
        try:
            guild_id = guild.id
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

        await self.ws.send_as_json(payload)

    def _handle_ready(self):
        self._ready.set()

    def _resolve_invite(self, invite):
        if isinstance(invite, Invite) or isinstance(invite, Object):
            return invite.id
        else:
            rx = r'(?:https?\:\/\/)?discord\.gg\/(.+)'
            m = re.match(rx, invite)
            if m:
                return m.group(1)
        return invite

    @property
    def latency(self):
        """:obj:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This could be referred to as the Discord WebSocket protocol latency.
        """
        ws = self.ws
        return float('nan') if not ws else ws.latency

    @property
    def user(self):
        """Optional[:class:`ClientUser`]: Represents the connected client. None if not logged in."""
        return self._connection.user

    @property
    def guilds(self):
        """List[:class:`Guild`]: The guilds that the connected client is a member of."""
        return self._connection.guilds

    @property
    def emojis(self):
        """List[:class:`Emoji`]: The emojis that the connected client has."""
        return self._connection.emojis

    @property
    def private_channels(self):
        """List[:class:`abc.PrivateChannel`]: The private channels that the connected client is participating on.

        .. note::

            This returns only up to 128 most recent private channels due to an internal working
            on how Discord deals with private channels.
        """
        return self._connection.private_channels

    @property
    def voice_clients(self):
        """List[:class:`VoiceClient`]: Represents a list of voice connections."""
        return self._connection.voice_clients

    def is_ready(self):
        """:obj:`bool`: Specifies if the client's internal cache is ready for use."""
        return self._ready.is_set()

    async def _run_event(self, coro, event_name, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def dispatch(self, event, *args, **kwargs):
        log.debug('Dispatching event %s', event)
        method = 'on_' + event
        handler = '_handle_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as e:
                    future.set_exception(e)
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
            asyncio.ensure_future(self._run_event(coro, method, *args, **kwargs), loop=self.loop)

    async def on_error(self, event_method, *args, **kwargs):
        """|coro|

        The default error handler provided by the client.

        By default this prints to ``sys.stderr`` however it could be
        overridden to have a different implementation.
        Check :func:`discord.on_error` for more details.
        """
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

    async def request_offline_members(self, *guilds):
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

        await self._connection.request_offline_members(guilds)

    # login state management

    async def login(self, token, *, bot=True):
        """|coro|

        Logs in the client with the specified credentials.

        This function can be used in two different ways.

        .. warning::

            Logging on with a user token is against the Discord
            `Terms of Service <https://support.discordapp.com/hc/en-us/articles/115002192352>`_
            and doing so might potentially get your account banned.
            Use this at your own risk.

        Parameters
        -----------
        token: str
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.
        bot: bool
            Keyword argument that specifies if the account logging on is a bot
            token or not.

        Raises
        ------
        LoginFailure
            The wrong credentials are passed.
        HTTPException
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """

        log.info('logging in using static token')
        await self.http.static_login(token, bot=bot)
        self._connection.is_bot = bot

    async def logout(self):
        """|coro|

        Logs out of Discord and closes all connections.
        """
        await self.close()

    async def _connect(self):
        coro = DiscordWebSocket.from_client(self, shard_id=self.shard_id)
        self.ws = await asyncio.wait_for(coro, timeout=180.0, loop=self.loop)
        while True:
            try:
                await self.ws.poll_event()
            except ResumeWebSocket:
                log.info('Got a request to RESUME the websocket.')
                coro = DiscordWebSocket.from_client(self, shard_id=self.shard_id, session=self.ws.session_id,
                                                    sequence=self.ws.sequence, resume=True)
                self.ws = await asyncio.wait_for(coro, timeout=180.0, loop=self.loop)

    async def connect(self, *, reconnect=True):
        """|coro|

        Creates a websocket connection and lets the websocket listen
        to messages from discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        -----------
        reconnect: bool
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).

        Raises
        -------
        GatewayNotFound
            If the gateway to connect to discord is not found. Usually if this
            is thrown then there is a discord API outage.
        ConnectionClosed
            The websocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        while not self.is_closed():
            try:
                await self._connect()
            except (OSError,
                    HTTPException,
                    GatewayNotFound,
                    ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError) as e:

                if not reconnect:
                    await self.close()
                    if isinstance(e, ConnectionClosed) and e.code == 1000:
                        # clean close, don't re-raise this
                        return
                    raise

                if self.is_closed():
                    return

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, no sharding, etc)
                # sometimes, discord sends us 1000 for unknown reasons so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(e, ConnectionClosed):
                    if e.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry, loop=self.loop)

    async def close(self):
        """|coro|

        Closes the connection to discord.
        """
        if self.is_closed():
            return

        self._closed.set()

        for voice in self.voice_clients:
            try:
                await voice.disconnect()
            except:
                # if an error happens during disconnects, disregard it.
                pass

        if self.ws is not None and self.ws.open:
            await self.ws.close()


        await self.http.close()
        self._ready.clear()

    def clear(self):
        """Clears the internal state of the bot.

        After this, the bot can be considered "re-opened", i.e. :meth:`.is_closed`
        and :meth:`.is_ready` both return ``False`` along with the bot's internal
        cache cleared.
        """
        self._closed.clear()
        self._ready.clear()
        self._connection.clear()
        self.http.recreate()

    async def start(self, *args, **kwargs):
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        """

        bot = kwargs.pop('bot', True)
        reconnect = kwargs.pop('reconnect', True)
        await self.login(*args, bot=bot)
        await self.connect(reconnect=reconnect)

    def _do_cleanup(self):
        log.info('Cleaning up event loop.')
        loop = self.loop
        if loop.is_closed():
            return # we're already cleaning up

        task = asyncio.ensure_future(self.close(), loop=loop)

        def _silence_gathered(fut):
            try:
                fut.result()
            except:
                pass
            finally:
                loop.stop()

        def when_future_is_done(fut):
            pending = asyncio.Task.all_tasks(loop=loop)
            if pending:
                log.info('Cleaning up after %s tasks', len(pending))
                gathered = asyncio.gather(*pending, loop=loop)
                gathered.cancel()
                gathered.add_done_callback(_silence_gathered)
            else:
                loop.stop()

        task.add_done_callback(when_future_is_done)
        if not loop.is_running():
            loop.run_forever()
        else:
            # on Linux, we're still running because we got triggered via
            # the signal handler rather than the natural KeyboardInterrupt
            # Since that's the case, we're going to return control after
            # registering the task for the event loop to handle later
            return None

        try:
            return task.result() # suppress unused task warning
        except:
            return None

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
        is_windows = sys.platform == 'win32'
        loop = self.loop
        if not is_windows:
            loop.add_signal_handler(signal.SIGINT, self._do_cleanup)
            loop.add_signal_handler(signal.SIGTERM, self._do_cleanup)

        task = asyncio.ensure_future(self.start(*args, **kwargs), loop=loop)

        def stop_loop_on_finish(fut):
            loop.stop()

        task.add_done_callback(stop_loop_on_finish)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.info('Received signal to terminate bot and event loop.')
        finally:
            task.remove_done_callback(stop_loop_on_finish)
            if is_windows:
                self._do_cleanup()

            loop.close()
            if task.cancelled() or not task.done():
                return None
            return task.result()

    # properties

    def is_closed(self):
        """:obj:`bool`: Indicates if the websocket connection is closed."""
        return self._closed.is_set()

    @property
    def activity(self):
        """Optional[Union[:class:`Activity`, :class:`Game`, :class:`Streaming`]]: The activity being used upon logging in."""
        return create_activity(self._connection._activity)

    @activity.setter
    def activity(self, value):
        if value is None:
            self._connection._activity = None
        elif isinstance(value, _ActivityTag):
            self._connection._activity = value.to_dict()
        else:
            raise TypeError('activity must be one of Game, Streaming, or Activity.')

    # helpers/getters

    @property
    def users(self):
        """Returns a :obj:`list` of all the :class:`User` the bot can see."""
        return list(self._connection._users.values())

    def get_channel(self, id):
        """Returns a :class:`abc.GuildChannel` or :class:`abc.PrivateChannel` with the following ID.

        If not found, returns None.
        """
        return self._connection.get_channel(id)

    def get_guild(self, id):
        """Returns a :class:`Guild` with the given ID. If not found, returns None."""
        return self._connection._get_guild(id)

    def get_user(self, id):
        """Returns a :class:`User` with the given ID. If not found, returns None."""
        return self._connection.get_user(id)

    def get_emoji(self, id):
        """Returns a :class:`Emoji` with the given ID. If not found, returns None."""
        return self._connection.get_emoji(id)

    def get_all_channels(self):
        """A generator that retrieves every :class:`abc.GuildChannel` the client can 'access'.

        This is equivalent to: ::

            for guild in client.guilds:
                for channel in guild.channels:
                    yield channel

        Note
        -----
        Just because you receive a :class:`abc.GuildChannel` does not mean that
        you can communicate in said channel. :meth:`abc.GuildChannel.permissions_for` should
        be used for that.
        """

        for guild in self.guilds:
            for channel in guild.channels:
                yield channel

    def get_all_members(self):
        """Returns a generator with every :class:`Member` the client can see.

        This is equivalent to: ::

            for guild in client.guilds:
                for member in guild.members:
                    yield member

        """
        for guild in self.guilds:
            for member in guild.members:
                yield member

    # listeners/waiters

    async def wait_until_ready(self):
        """|coro|

        Waits until the client's internal cache is all ready.
        """
        await self._ready.wait()

    def wait_for(self, event, *, check=None, timeout=None):
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By default,
        it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided for
        ease of use.

        In case the event returns multiple arguments, a :obj:`tuple` containing those
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
                    await channel.send('Hello {.author}!'.format(msg))

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
        event: str
            The event name, similar to the :ref:`event reference <discord-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[predicate]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[float]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.

        Raises
        -------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        --------
        Any
            Returns no arguments, a single argument, or a :obj:`tuple` of multiple
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
        return asyncio.wait_for(future, timeout, loop=self.loop)

    # event registration

    def event(self, coro):
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a |corourl|_, if not, :exc:`ClientException` is raised.

        Example
        ---------

		::
            @client.event
            async def on_ready():
                print('Ready!')

        """

        if not asyncio.iscoroutinefunction(coro):
            raise ClientException('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

    async def change_presence(self, *, activity=None, status=None, afk=False):
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

        Raises
        ------
        InvalidArgument
            If the ``activity`` parameter is not the proper type.
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

        await self.ws.change_presence(activity=activity, status=status, afk=afk)

        for guild in self._connection.guilds:
            me = guild.me
            if me is None:
                continue

            me.activity = activity
            me.status = status_enum

    # Guild stuff

    async def create_guild(self, name, region=None, icon=None):
        """|coro|

        Creates a :class:`Guild`.

        Bot accounts in more than 10 guilds are not allowed to create guilds.

        Parameters
        ----------
        name: str
            The name of the guild.
        region: :class:`VoiceRegion`
            The region for the voice communication server.
            Defaults to :attr:`VoiceRegion.us_west`.
        icon: bytes
            The :term:`py:bytes-like object` representing the icon. See :meth:`~ClientUser.edit`
            for more details on what is expected.

        Raises
        ------
        HTTPException
            Guild creation failed.
        InvalidArgument
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`Guild`
            The guild created. This is not the same guild that is
            added to cache.
        """
        if icon is not None:
            icon = utils._bytes_to_base64_data(icon)

        if region is None:
            region = VoiceRegion.us_west.value
        else:
            region = region.value

        data = await self.http.create_guild(name, region, icon)
        return Guild(data=data, state=self._connection)

    # Invite management

    async def get_invite(self, url):
        """|coro|

        Gets an :class:`Invite` from a discord.gg URL or ID.

        Note
        ------
        If the invite is for a guild you have not joined, the guild and channel
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
        data = await self.http.get_invite(invite_id)
        return Invite.from_incomplete(state=self._connection, data=data)

    async def delete_invite(self, invite):
        """|coro|

        Revokes an :class:`Invite`, URL, or ID to an invite.

        You must have the :attr:`~Permissions.manage_channels` permission in
        the associated guild to do this.

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
        await self.http.delete_invite(invite_id)

    # Miscellaneous stuff

    async def application_info(self):
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
        data = await self.http.application_info()
        if 'rpc_origins' not in data:
            data['rpc_origins'] = None
        return AppInfo(id=int(data['id']), name=data['name'],
                       description=data['description'], icon=data['icon'],
                       rpc_origins=data['rpc_origins'], bot_public=data['bot_public'],
                       bot_require_code_grant=data['bot_require_code_grant'],
                       owner=User(state=self._connection, data=data['owner']))

    async def get_user_info(self, user_id):
        """|coro|

        Retrieves a :class:`User` based on their ID. This can only
        be used by bot accounts. You do not have to share any guilds
        with the user to get this information, however many operations
        do require that you do.

        Parameters
        -----------
        user_id: int
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
        data = await self.http.get_user_info(user_id)
        return User(state=self._connection, data=data)

    async def get_user_profile(self, user_id):
        """|coro|

        Gets an arbitrary user's profile. This can only be used by non-bot accounts.

        Parameters
        ------------
        user_id: int
            The ID of the user to fetch their profile for.

        Raises
        -------
        Forbidden
            Not allowed to fetch profiles.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`Profile`
            The profile of the user.
        """

        state = self._connection
        data = await self.http.get_user_profile(user_id)

        def transform(d):
            return state._get_guild(int(d['id']))

        since = data.get('premium_since')
        mutual_guilds = list(filter(None, map(transform, data.get('mutual_guilds', []))))
        user = data['user']
        return Profile(flags=user.get('flags', 0),
                       premium_since=utils.parse_time(since),
                       mutual_guilds=mutual_guilds,
                       user=User(data=user, state=state),
                       connected_accounts=data['connected_accounts'])

    async def get_webhook_info(self, webhook_id):
        """|coro|

        Retrieves a :class:`Webhook` with the specified ID.

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
        :class:`Webhook`
            The webhook you requested.
        """
        data = await self.http.get_webhook(webhook_id)
        return Webhook.from_state(data, state=self._connection)
