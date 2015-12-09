# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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

from . import endpoints
from .user import User
from .channel import Channel, PrivateChannel
from .server import Server
from .message import Message
from .invite import Invite
from .object import Object
from .errors import *
from .state import ConnectionState
from . import utils
from .enums import ChannelType, ServerRegion
from .voice_client import VoiceClient

import asyncio
import aiohttp
import websockets

import logging, traceback
import sys, time, re, json

log = logging.getLogger(__name__)
request_logging_format = '{method} {response.url} has returned {response.status}'
request_success_log = '{response.url} with {json} received {data}'

class Client:
    """Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client`.

    .. _deque: https://docs.python.org/3.4/library/collections.html#collections.deque
    .. _event loop: https://docs.python.org/3/library/asyncio-eventloops.html

    Parameters
    ----------
    max_messages : Optional[int]
        The maximum number of messages to store in :attr:`messages`.
        This defaults to 5000. Passing in `None` or a value less than 100
        will use the default instead of the passed in value.
    loop : Optional[event loop].
        The `event loop`_ to use for asynchronous operations. Defaults to ``None``,
        in which case the default event loop is used via ``asyncio.get_event_loop()``.

    Attributes
    -----------
    user : Optional[:class:`User`]
        Represents the connected client. None if not logged in.
    servers : list of :class:`Server`
        The servers that the connected client is a member of.
    private_channels : list of :class:`PrivateChannel`
        The private channels that the connected client is participating on.
    messages
        A deque_ of :class:`Message` that the client has received from all
        servers and private messages. The number of messages stored in this
        deque is controlled by the ``max_messages`` parameter.
    email
        The email used to login. This is only set if login is successful,
        otherwise it's None.
    gateway
        The websocket gateway the client is currently connected to. Could be None.
    loop
        The `event loop`_ that the client uses for HTTP requests and websocket operations.

    """
    def __init__(self, *, loop=None, **options):
        self.ws = None
        self.token = None
        self.gateway = None
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._listeners = []

        max_messages = options.get('max_messages')
        if max_messages is None or max_messages < 100:
            max_messages = 5000

        self.connection = ConnectionState(self.dispatch, max_messages)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.headers = {
            'content-type': 'application/json',
        }
        self._closed = False
        self._is_logged_in = False

        # this is shared state between Client and VoiceClient
        # could this lead to issues? Not sure. I want to say no.
        self._is_voice_connected = asyncio.Event(loop=self.loop)

        # These two events correspond to the two events necessary
        # for a connection to be made
        self._voice_data_found = asyncio.Event(loop=self.loop)
        self._session_id_found = asyncio.Event(loop=self.loop)

    # internals

    def handle_message(self, message):
        removed = []
        for i, (condition, future) in enumerate(self._listeners):
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

    def _resolve_mentions(self, content, mentions):
        if isinstance(mentions, list):
            return [user.id for user in mentions]
        elif mentions == True:
            return re.findall(r'<@(\d+)>', content)
        else:
            return []

    def _resolve_invite(self, invite):
        if isinstance(invite, Invite) or isinstance(invite, Object):
            return invite.id
        else:
            rx = r'(?:https?\:\/\/)?discord\.gg\/(.+)'
            m = re.match(rx, invite)
            if m:
                return m.group(1)
        return invite

    def _resolve_destination(self, destination):
        if isinstance(destination, (Channel, PrivateChannel, Server)):
            return destination.id
        elif isinstance(destination, User):
            found = utils.find(lambda pm: pm.user == destination, self.private_channels)
            if found is None:
                # Couldn't find the user, so start a PM with them first.
                self.start_private_message(destination)
                channel_id = self.private_channels[-1].id
                return channel_id
            else:
                return found.id
        elif isinstance(destination, Object):
            return destination.id
        else:
            raise InvalidArgument('Destination must be Channel, PrivateChannel, User, or Object')

    def __getattr__(self, name):
        if name in ('user', 'email', 'servers', 'private_channels', 'messages'):
            return getattr(self.connection, name)
        else:
            msg = "'{}' object has no attribute '{}'"
            raise AttributeError(msg.format(self.__class__, name))

    def __setattr__(self, name, value):
        if name in ('user', 'email', 'servers', 'private_channels',
                    'messages'):
            return setattr(self.connection, name, value)
        else:
            object.__setattr__(self, name, value)

    @asyncio.coroutine
    def _get_gateway(self):
        resp = yield from self.session.get(endpoints.GATEWAY, headers=self.headers)
        if resp.status != 200:
            raise GatewayNotFound()
        data = yield from resp.json()
        return data.get('url')

    @asyncio.coroutine
    def _run_event(self, event, *args, **kwargs):
        try:
            yield from getattr(self, event)(*args, **kwargs)
        except Exception as e:
            yield from self.on_error(event, *args, **kwargs)

    def dispatch(self, event, *args, **kwargs):
        log.debug('Dispatching event {}'.format(event))
        method = 'on_' + event
        handler = 'handle_' + event

        if hasattr(self, handler):
            getattr(self, handler)(*args, **kwargs)

        if hasattr(self, method):
            utils.create_task(self._run_event(method, *args, **kwargs), loop=self.loop)

    @asyncio.coroutine
    def keep_alive_handler(self, interval):
        while not self._closed:
            payload = {
                'op': 1,
                'd': int(time.time())
            }

            msg = 'Keeping websocket alive with timestamp {}'
            log.debug(msg.format(payload['d']))
            yield from self.ws.send(utils.to_json(payload))
            yield from asyncio.sleep(interval)

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

    def received_message(self, msg):
        log.debug('WebSocket Event: {}'.format(msg))
        self.dispatch('socket_response', msg)

        op = msg.get('op')
        data = msg.get('d')

        if op != 0:
            log.info('Unhandled op {}'.format(op))
            return

        event = msg.get('t')

        if event == 'READY':
            interval = data['heartbeat_interval'] / 1000.0
            self.keep_alive = utils.create_task(self.keep_alive_handler(interval), loop=self.loop)

        if event == 'VOICE_STATE_UPDATE':
            user_id = data.get('user_id')
            if user_id == self.user.id:
                self.session_id = data.get('session_id')
                self._session_id_found.set()

        if event == 'VOICE_SERVER_UPDATE':
            self._voice_data_found.data = data
            self._voice_data_found.set()

        if event in ('READY', 'MESSAGE_CREATE', 'MESSAGE_DELETE',
                     'MESSAGE_UPDATE', 'PRESENCE_UPDATE', 'USER_UPDATE',
                     'CHANNEL_DELETE', 'CHANNEL_UPDATE', 'CHANNEL_CREATE',
                     'GUILD_MEMBER_ADD', 'GUILD_MEMBER_REMOVE', 'GUILD_UPDATE'
                     'GUILD_MEMBER_UPDATE', 'GUILD_CREATE', 'GUILD_DELETE',
                     'GUILD_ROLE_CREATE', 'GUILD_ROLE_DELETE', 'TYPING_START',
                     'GUILD_ROLE_UPDATE', 'VOICE_STATE_UPDATE'):
            parser = 'parse_' + event.lower()
            getattr(self.connection, parser)(data)
        else:
            log.info("Unhandled event {}".format(event))

    @asyncio.coroutine
    def _make_websocket(self):
        if not self.is_logged_in:
            raise ClientException('You must be logged in to connect')

        self.gateway = yield from self._get_gateway()
        self.ws = yield from websockets.connect(self.gateway)
        self.ws.max_size = None
        log.info('Created websocket connected to {0.gateway}'.format(self))
        payload = {
            'op': 2,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'discord.py',
                    '$device': 'discord.py',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                'v': 3
            }
        }

        yield from self.ws.send(utils.to_json(payload))
        log.info('sent the initial payload to create the websocket')

    # properties

    @property
    def is_logged_in(self):
        """bool: Indicates if the client has logged in successfully."""
        return self._is_logged_in

    @property
    def is_closed(self):
        """bool: Indicates if the websocket connection is closed."""
        return self._closed

    # helpers/getters

    def get_channel(self, id):
        """Returns a :class:`Channel` or :class:`PrivateChannel` with the following ID. If not found, returns None."""
        return self.connection.get_channel(id)

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

            @client.async_event
            def on_message(message):
                if message.content.startswith('$greet')
                    yield from client.send_message(message.channel, 'Say hello')
                    msg = yield from client.wait_for_message(author=message.author, content='hello')
                    yield from client.send_message(message.channel, 'Hello.')

        Asking for a follow-up question:

        .. code-block:: python
            :emphasize-lines: 6

            @client.async_event
            def on_message(message):
                if message.content.startswith('$start')
                    yield from client.send_message(message.channel, 'Type $stop 4 times.')
                    for i in range(4):
                        msg = yield from client.wait_for_message(author=message.author, content='$stop')
                        fmt = '{} left to go...'
                        yield from client.send_message(message.channel, fmt.format(3 - i))

                    yield from client.send_message(message.channel, 'Good job!')

        Advanced filters using ``check``:

        .. code-block:: python
            :emphasize-lines: 9

            @client.async_event
            def on_message(message):
                if message.content.startswith('$cool'):
                    yield from client.send_message(message.channel, 'Who is cool? Type $name namehere')

                    def check(msg):
                        return msg.content.startswith('$name')

                    message = yield from client.wait_for_message(author=message.author, check=check)
                    name = message.content[len('$name'):].strip()
                    yield from client.send_message(message.channel, '{} is cool indeed'.format(name))


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
            result = message.author == author
            if content is not None:
                result = result and message.content == content

            if channel is not None:
                result = result and message.channel.id == channel.id

            if callable(check):
                # the exception thrown by check is propagated through the future.
                result = result and check(message)

            return result

        future = asyncio.Future(loop=self.loop)
        self._listeners.append((predicate, future))
        try:
            message = yield from asyncio.wait_for(future, timeout, loop=self.loop)
        except asyncio.TimeoutError:
            message = None
        return message

    # login state management

    @asyncio.coroutine
    def login(self, email, password):
        """|coro|

        Logs in the client with the specified credentials.

        Parameters
        ----------
        email : str
            The email used to login.
        password : str
            The password used to login.

        Raises
        ------
        LoginFailure
            The wrong credentials are passed.
        HTTPException
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """
        payload = {
            'email': email,
            'password': password
        }

        data = utils.to_json(payload)
        resp = yield from self.session.post(endpoints.LOGIN, data=data, headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=resp))
        if resp.status == 400:
            raise LoginFailure('Improper credentials have been passed.')
        elif resp.status != 200:
            data = yield from resp.json()
            raise HTTPException(resp, data.get('message'))

        log.info('logging in returned status code {}'.format(resp.status))
        self.email = email

        body = yield from resp.json()
        self.token = body['token']
        self.headers['authorization'] = self.token
        self._is_logged_in = True

    @asyncio.coroutine
    def logout(self):
        """|coro|

        Logs out of Discord and closes all connections."""
        response = yield from self.session.post(endpoints.LOGOUT, headers=self.headers)
        yield from self.close()
        self._is_logged_in = False
        log.debug(request_logging_format.format(method='POST', response=response))

    @asyncio.coroutine
    def connect(self):
        """|coro|

        Creates a websocket connection and connects to the websocket listen
        to messages from discord.

        This function is implemented using a while loop in the background.
        If you need to run this event listening in another thread then
        you should run it in an executor or schedule the coroutine to
        be executed later using ``loop.create_task``.

        Raises
        -------
        ClientException
            If this is called before :meth:`login` was invoked successfully.
        """
        yield from self._make_websocket()

        while not self._closed:
            msg = yield from self.ws.recv()
            if msg is None:
                yield from self.close()
                break

            self.received_message(json.loads(msg))

    @asyncio.coroutine
    def close(self):
        """Closes the websocket connection.

        To reconnect the websocket connection, :meth:`connect` must be used.
        """
        if self._closed:
            return

        yield from self.ws.close()
        self.keep_alive.cancel()
        self._closed = True

    @asyncio.coroutine
    def start(self, email, password):
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        """
        yield from self.login(email, password)
        yield from self.connect()

    def run(self, email, password):
        """A blocking call that abstracts away the `event loop`_
        initialisation from you.

        Equivalent to: ::

            loop.run_until_complete(start(email, password))
            loop.close()
        """

        self.loop.run_until_complete(self.start(email, password))
        self.loop.close()

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

        payload = {
            'recipient_id': user.id
        }

        url = '{}/@me/channels'.format(endpoints.USERS)
        r = yield from self.session.post(url, data=utils.to_json(payload), headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=r))
        yield from utils._verify_successful_response(r)
        data = yield from r.json()
        log.debug(request_success_log.format(response=r, json=payload, data=data))
        self.private_channels.append(PrivateChannel(id=data['id'], user=user))

    @asyncio.coroutine
    def send_message(self, destination, content, *, mentions=True, tts=False):
        """|coro|

        Sends a message to the destination given with the content given.

        The destination could be a :class:`Channel`, :class:`PrivateChannel` or :class:`Server`.
        For convenience it could also be a :class:`User`. If it's a :class:`User` or :class:`PrivateChannel`
        then it sends the message via private message, otherwise it sends the message to the channel.
        If the destination is a :class:`Server` then it's equivalent to calling
        :meth:`Server.get_default_channel` and sending it there.

        If it is a :class:`Object` instance then it is assumed to be the
        destination ID. The destination ID is a *channel* so passing in a user
        ID will not be a valid destination.

        .. versionchanged:: 0.9.0
            ``str`` being allowed was removed and replaced with :class:`Object`.

        The content must be a type that can convert to a string through ``str(content)``.

        The mentions must be either an array of :class:`User` to mention or a boolean. If
        ``mentions`` is ``True`` then all the users mentioned in the content are mentioned, otherwise
        no one is mentioned. Note that to mention someone in the content, you should use :meth:`User.mention`.

        Parameters
        ------------
        destination
            The location to send the message.
        content
            The content of the message to send.
        mentions
            A list of :class:`User` to mention in the message or a boolean. Ignored for private messages.
        tts : bool
            Indicates if the message should be sent using text-to-speech.

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

        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel_id = self._resolve_destination(destination)

        content = str(content)
        mentions = self._resolve_mentions(content, mentions)

        url = '{base}/{id}/messages'.format(base=endpoints.CHANNELS, id=channel_id)
        payload = {
            'content': content,
            'mentions': mentions
        }

        if tts:
            payload['tts'] = True

        resp = yield from self.session.post(url, data=utils.to_json(payload), headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=resp))
        yield from utils._verify_successful_response(resp)
        data = yield from resp.json()
        log.debug(request_success_log.format(response=resp, json=payload, data=data))
        channel = self.get_channel(data.get('channel_id'))
        message = Message(channel=channel, **data)
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

        channel_id = self._resolve_destination(destination)

        url = '{base}/{id}/typing'.format(base=endpoints.CHANNELS, id=channel_id)

        response = yield from self.session.post(url, headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def send_file(self, destination, fp, filename=None):
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

        Raises
        -------
        InvalidArgument
            If ``fp.name`` is an invalid default for ``filename``.
        HTTPException
            Sending the file failed.

        Returns
        --------
        :class:`Message`
            The message sent.
        """

        channel_id = self._resolve_destination(destination)

        url = '{base}/{id}/messages'.format(base=endpoints.CHANNELS, id=channel_id)

        try:
            # attempt to open the file and send the request
            with open(fp, 'rb') as f:
                files = {
                    'file': (fp if filename is None else filename, f)
                }
        except TypeError:
            # if we got a TypeError then this is probably a file-like object
            fname = getattr(fp, 'name', None) if filename is None else filename
            if fname is None:
                raise InvalidArgument('file-like object has no name attribute and no filename was specified')

            files = {
                'file': (fname, fp)
            }

        response = yield from self.session.post(url, files=files, headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=response))
        yield from utils._verify_successful_response(response)
        data = yield from response.json()
        msg = 'POST {0.url} returned {0.status} with {1} response'
        log.debug(msg.format(response, data))
        channel = self.get_channel(data.get('channel_id'))
        message = Message(channel=channel, **data)
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

        url = '{}/{}/messages/{}'.format(endpoints.CHANNELS, message.channel.id, message.id)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def edit_message(self, message, new_content, *, mentions=True):
        """|coro|

        Edits a :class:`Message` with the new message content.

        The new_content must be able to be transformed into a string via ``str(new_content)``.

        Parameters
        -----------
        message : :class:`Message`
            The message to edit.
        new_content
            The new content to replace the message with.
        mentions
            The mentions for the user. Same as :meth:`send_message`.

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
        content = str(new_content)

        url = '{}/{}/messages/{}'.format(endpoints.CHANNELS, channel.id, message.id)
        payload = {
            'content': content,
            'mentions': self._resolve_mentions(content, mentions)
        }

        response = yield from self.session.patch(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=response))
        yield from utils._verify_successful_response(response)
        data = yield from response.json()
        log.debug(request_success_log.format(response=response, json=payload, data=data))
        return Message(channel=channel, **data)

    @asyncio.coroutine
    def logs_from(self, channel, limit=100, *, before=None, after=None):
        """|coro|

        This coroutine returns a generator that obtains logs from a specified channel.

        Parameters
        -----------
        channel : :class:`Channel`
            The channel to obtain the logs from.
        limit : int
            The number of messages to retrieve.
        before : :class:`Message`
            The message before which all returned messages must be.
        after : :class:`Message`
            The message after which all returned messages must be.

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
        """

        def generator_wrapper(data):
            for message in data:
                yield Message(channel=channel, **message)

        url = '{}/{}/messages'.format(endpoints.CHANNELS, channel.id)
        params = {
            'limit': limit
        }

        if before:
            params['before'] = before.id
        if after:
            params['after'] = after.id

        response = yield from self.session.get(url, params=params, headers=self.headers)
        log.debug(request_logging_format.format(method='GET', response=response))
        yield from utils._verify_successful_response(response)
        messages = yield from response.json()
        return generator_wrapper(messages)

    # Member management

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

        url = '{0}/{1.server.id}/members/{1.id}'.format(endpoints.SERVERS, member)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def ban(self, member):
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

        Raises
        -------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """

        url = '{0}/{1.server.id}/bans/{1.id}'.format(endpoints.SERVERS, member)
        response = yield from self.session.put(url, headers=self.headers)
        log.debug(request_logging_format.format(method='PUT', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def unban(self, member):
        """|coro|

        Unbans a :class:`Member` from the server they belong to.

        Warning
        --------
        This function unbans the :class:`Member` based on the server it
        belongs to, which is accessed via :attr:`Member.server`. So you
        must have the proper permissions in that server.

        Parameters
        -----------
        member : :class:`Member`
            The member to unban from their server.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """

        url = '{0}/{1.server.id}/bans/{1.id}'.format(endpoints.SERVERS, member)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def server_voice_state(self, member, *, mute=False, deafen=False):
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
        mute : bool
            Indicates if the member should be server muted or un-muted.
        deafen : bool
            Indicates if the member should be server deafened or un-deafened.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to deafen or mute.
        HTTPException
            The operation failed.
        """

        url = '{0}/{1.server.id}/members/{1.id}'.format(endpoints.SERVERS, member)
        payload = {
            'mute': mute,
            'deaf': deafen
        }

        response = yield from self.session.patch(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def edit_profile(self, password, **fields):
        """|coro|

        Edits the current profile of the client.

        All fields except ``password`` are optional.

        The profile is **not** edited in place.

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
            The current password for the client's account.
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

        payload = {
            'password': password,
            'new_password': fields.get('new_password'),
            'email': fields.get('email', self.email),
            'username': fields.get('username', self.user.name),
            'avatar': avatar
        }

        url = '{0}/@me'.format(endpoints.USERS)
        r = yield from self.session.patch(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=r))
        yield from utils._verify_successful_response(r)

        data = yield from r.json()
        log.debug(request_success_log.format(response=r, json=payload, data=data))
        self.token = data['token']
        self.email = data['email']
        self.headers['authorization'] = self.token

    @asyncio.coroutine
    def change_status(self, game_id=None, idle=False):
        """|coro|

        Changes the client's status.

        The game_id parameter is a numeric ID (not a string) that represents
        a game being played currently. The list of game_id to actual games changes
        constantly and would thus be out of date pretty quickly. An old version of
        the game_id database can be seen `here`_ to help you get started.

        The idle parameter is a boolean parameter that indicates whether the
        client should go idle or not.

        .. _here: https://gist.github.com/Rapptz/a82b82381b70a60c281b

        Parameters
        ----------
        game_id : Optional[int]
            The game ID being played. None if no game is being played.
        idle : bool
            Indicates if the client should go idle.

        Raises
        ------
        InvalidArgument
            If the ``game_id`` parameter is convertible integer or None.
        """

        idle_since = None if idle == False else int(time.time() * 1000)
        try:
            game_id = None if game_id is None else int(game_id)
        except:
            raise InvalidArgument('game_id must be convertible to an integer or None')

        payload = {
            'op': 3,
            'd': {
                'game_id': game_id,
                'idle_since': idle_since
            }
        }

        sent = utils.to_json(payload)
        log.debug('Sending "{}" to change status'.format(sent))
        yield from self.ws.send(sent)

    # Channel management

    @asyncio.coroutine
    def edit_channel(self, channel, **options):
        """|coro|

        Edits a :class:`Channel`.

        You must have the proper permissions to edit the channel.

        The channel is **not** edited in-place.

        Parameters
        ----------
        channel : :class:`Channel`
            The channel to update.
        name : str
            The new channel name.
        position : int
            The new channel's position in the GUI.
        topic : str
            The new channel's topic.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """

        url = '{0}/{1.id}'.format(endpoints.CHANNELS, channel)
        payload = {
            'name': options.get('name', channel.name),
            'topic': options.get('topic', channel.topic),
            'position': options.get('position', channel.position)
        }

        r = yield from self.session.patch(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=r))
        yield from utils._verify_successful_response(r)

        data = yield from r.json()
        log.debug(request_success_log.format(response=r, json=payload, data=data))

    @asyncio.coroutine
    def create_channel(self, server, name, type=None):
        """|coro|

        Creates a :class:`Channel` in the specified :class:`Server`.

        Note that you need the proper permissions to create the channel.

        Parameters
        -----------
        server : :class:`Server`
            The server to create the channel in.
        name : str
            The channel's name.
        type : :class:`ChannelType`
            The type of channel to create. Defaults to :attr:`ChannelType.text`.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to create the channel.
        NotFound
            The server specified was not found.
        HTTPException
            Creating the channel failed.

        Returns
        -------
        :class:`Channel`
            The channel that was just created. This channel is
            different than the one that will be added in cache.
        """

        if type is None:
            type = ChannelType.text

        payload = {
            'name': name,
            'type': str(type)
        }

        url = '{0}/{1.id}/channels'.format(endpoints.SERVERS, server)
        response = yield from self.session.post(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='POST', response=response))
        yield from utils._verify_successful_response(response)

        data = yield from response.json()
        log.debug(request_success_log.format(response=response, data=data, json=payload))
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

        url = '{}/{}'.format(endpoints.CHANNELS, channel.id)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    # Server management

    @asyncio.coroutine
    def leave_server(self, server):
        """|coro|

        Leaves a :class:`Server`.

        Warning
        --------
        If you are the owner of the server then it is deleted.

        Parameters
        ----------
        server : :class:`Server`
            The server to leave.

        Raises
        --------
        HTTPException
            If leaving the server failed.
        """

        url = '{0}/{1.id}'.format(endpoints.SERVERS, server)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def create_server(self, name, region=None, icon=None):
        """|coro|

        Creates a :class:`Server`.

        Parameters
        ----------
        name : str
            The name of the server.
        region : :class:`ServerRegion`
            The region for the voice communication server.
            Defaults to :attr`ServerRegion.us_west`.
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

        r = yield from self.session.post(endpoints.SERVERS, headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=r))
        yield from utils._verify_successful_response(r)
        data = yield from r.json()
        log.debug(request_success_log.format(response=r, json=payload, data=data))
        return Server(**data)

    @asyncio.coroutine
    def edit_server(self, server, **fields):
        """|coro|

        Edits a :class:`Server`.

        You must have the proper permissions to edit the server.

        The server is **not** edited in-place.

        Parameters
        ----------
        server : :class:`Server`
            The server to edit.
        name : str
            The new name of the server.
        icon : bytes
            A *bytes-like* object representing the icon. See :meth:`edit_profile`
            for more details. Could be ``None`` to denote
        region : :class:`ServerRegion`
            The new region for the server's voice communication.
        afk_channel : :class:`Channel`
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout : int
            The number of seconds until someone is moved to the AFK channel.

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
            PNG or JPG.
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

        payload = {
            'region': str(fields.get('region', server.region)),
            'afk_timeout': fields.get('afk_timeout', server.afk_timeout),
            'icon': icon,
            'name': fields.get('name', server.name),
        }

        afk_channel = fields.get('afk_channel')
        if afk_channel is None:
            afk_channel = server.afk_channel

        payload['afk_channel'] = getattr(afk_channel, 'id', None)

        url = '{0}/{1.id}'.format(endpoints.SERVERS, server)
        r = yield from self.session.patch(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=r))
        yield from utils._verify_successful_response(r)
        yield from r.release()

    # Invite management

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
        xkcd : bool
            Indicates if the invite URL is human readable. Defaults to False.

        Raises
        -------
        HTTPException
            Invite creation failed.

        Returns
        --------
        :class:`Invite`
            The invite that was created.
        """

        payload = {
            'max_age': options.get('max_age', 0),
            'max_uses': options.get('max_uses', 0),
            'temporary': options.get('temporary', False),
            'xkcdpass': options.get('xkcd', False)
        }

        url = '{0}/{1.id}/invites'.format(endpoints.CHANNELS, destination)
        response = yield from self.session.post(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='POST', response=response))

        yield from utils._verify_successful_response(response)
        data = yield from response.json()
        log.debug(request_success_log.format(json=payload, response=response, data=data))

        data['server'] = self.connection._get_server(data['guild']['id'])
        channel_id = data['channel']['id']
        data['channel'] = utils.find(lambda ch: ch.id == channel_id, data['server'].channels)
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

        destination = self._resolve_invite(url)
        rurl = '{0}/invite/{1}'.format(endpoints.API_BASE, destination)
        response = yield from self.session.get(rurl, headers=self.headers)
        log.debug(request_logging_format.format(method='GET', response=response))
        yield from utils._verify_successful_response(response)
        data = yield from response.json()
        server = self.connection._get_server(data['guild']['id'])
        if server is not None:
            ch_id = data['channel']['id']
            channels = getattr(server, 'channels', [])
            channel = utils.find(lambda c: c.id == ch_id, channels)
        else:
            server = Object(id=data['guild']['id'])
            server.name = data['guild']['name']
            channel = Object(id=data['channel']['id'])
            channel.name = data['channel']['name']
        data['server'] = server
        data['channel'] = channel
        return Invite(**data)

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
        """

        destination = self._resolve_invite(invite)
        url = '{0}/invite/{1}'.format(endpoints.API_BASE, destination)
        response = yield from self.session.post(url, headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

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

        destination = self._resolve_invite(invite)
        url = '{0}/invite/{1}'.format(endpoints.API_BASE, destination)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    # Role management

    @asyncio.coroutine
    def edit_role(self, server, role, **fields):
        """|coro|

        Edits the specified :class:`Role` for the entire :class:`Server`.

        This does **not** edit the role in place.

        All fields except ``server`` and ``role`` are optional.

        .. versionchanged:: 0.8.0
            Editing now uses keyword arguments instead of editing the :class:`Role` object directly.

        Note
        -----
        At the moment, the Discord API allows you to set the colour to any
        RGB value. This might change in the future so it is recommended that
        you use the constants in the :class:`Colour` instead such as
        :meth:`Colour.green`.

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

        Raises
        -------
        Forbidden
            You do not have permissions to change the role.
        HTTPException
            Editing the role failed.
        """

        url = '{0}/{1.id}/roles/{2.id}'.format(endpoints.SERVERS, server, role)
        color = fields.get('color')
        if color is None:
            color = fields.get('colour', role.colour)

        payload = {
            'name': fields.get('name', role.name),
            'permissions': fields.get('permissions', role.permissions).value,
            'color': color.value,
            'hoist': fields.get('hoist', role.hoist)
        }

        r = yield from self.session.patch(url, data=utils.to_json(payload), headers=self.headers)
        log.debug(request_logging_format.format(method='PATCH', response=r))
        yield from utils._verify_successful_response(r)

        data = yield from r.json()
        log.debug(request_success_log.format(json=payload, response=r, data=data))

    @asyncio.coroutine
    def delete_role(self, server, role):
        """|coro|

        Deletes the specified :class:`Role` for the entire :class:`Server`.

        Works in a similar matter to :func:`edit_role`.

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

        url = '{0}/{1.id}/roles/{2.id}'.format(endpoints.SERVERS, server, role)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()

    @asyncio.coroutine
    def add_roles(self, member, *roles):
        """|coro|

        Gives the specified :class:`Member` a number of :class:`Role` s.

        You must have the proper permissions to use this function.

        This method **appends** a role to a member but does **not** do it
        in-place.

        Parameters
        -----------
        member : :class:`Member`
            The member to give roles to.
        *roles
            An argument list of :class:`Role` s to give the member.

        Raises
        -------
        Forbidden
            You do not have permissions to add roles.
        HTTPException
            Adding roles failed.
        """

        new_roles = [role.id for role in itertools.chain(member.roles, roles)]
        yield from self.replace_roles(member, *new_roles)

    @asyncio.coroutine
    def remove_roles(self, member, *roles):
        """|coro|

        Removes the :class:`Role` s from the :class:`Member`.

        You must have the proper permissions to use this function.

        This method does **not** do edit the member in-place.

        Parameters
        -----------
        member : :class:`Member`
            The member to revoke roles from.
        *roles
            An argument list of :class:`Role` s to revoke the member.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke roles.
        HTTPException
            Removing roles failed.
        """
        new_roles = {role.id for role in member.roles}
        new_roles = new_roles.difference(roles)
        yield from self.replace_roles(member, *new_roles)

    @asyncio.coroutine
    def replace_roles(self, member, *roles):
        """|coro|

        Replaces the :class:`Member`'s roles.

        You must have the proper permissions to use this function.

        This function **replaces** all roles that the member has.
        For example if the member has roles ``[a, b, c]`` and the
        call is ``client.replace_roles(member, d, e, c)`` then
        the member has the roles ``[d, e, c]``.

        This method does **not** do edit the member in-place.

        Parameters
        -----------
        member : :class:`Member`
            The member to replace roles from.
        *roles
            An argument list of :class:`Role` s to replace the roles with.

        Raises
        -------
        Forbidden
            You do not have permissions to revoke roles.
        HTTPException
            Removing roles failed.
        """

        url = '{0}/{1.server.id}/members/{1.id}'.format(endpoints.SERVERS, member)

        payload = {
            'roles': [role.id for role in roles]
        }

        r = yield from self.session.patch(url, headers=self.headers, data=utils.to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=r))
        yield from utils._verify_successful_response(r)
        yield from r.release()

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

        url = '{0}/{1.id}/roles'.format(endpoints.SERVERS, server)
        r = yield from self.session.post(url, headers=self.headers)
        log.debug(request_logging_format.format(method='POST', response=r))
        yield from utils._verify_successful_response(r)

        data = yield from r.json()
        everyone = server.id == data.get('id')
        role = Role(everyone=everyone, **data)

        # we have to call edit because you can't pass a payload to the
        # http request currently.
        yield from self.edit_role(server, role, **fields)
        return role

    @asyncio.coroutine
    def edit_channel_permissions(self, channel, target, *, allow=None, deny=None):
        """|coro|

        Sets the channel specific permission overwrites for a target in the
        specified :class:`Channel`.

        The ``target`` parameter should either be a :class:`Member` or a
        :class:`Role` that belongs to the channel's server.

        You must have the proper permissions to do this.

        Examples
        ----------

        Setting allow and deny: ::

            allow = discord.Permissions.none()
            deny = discord.Permissions.none()
            allow.can_mention_everyone = True
            deny.can_manage_messages = True
            yield from client.set_channel_permissions(message.channel, message.author, allow=allow, deny=deny)

        Parameters
        -----------
        channel : :class:`Channel`
            The channel to give the specific permissions for.
        target
            The :class:`Member` or :class:`Role` to overwrite permissions for.
        allow : :class:`Permissions`
            The permissions to explicitly allow. (optional)
        deny : :class:`Permissions`
            The permissions to explicitly deny. (optional)

        Raises
        -------
        Forbidden
            You do not have permissions to edit channel specific permissions.
        NotFound
            The channel specified was not found.
        HTTPException
            Editing channel specific permissions failed.
        InvalidArgument
            The allow or deny arguments were not of type :class:`Permissions`
            or the target type was not :class:`Role` or :class:`Member`.
        """

        url = '{0}/{1.id}/permissions/{2.id}'.format(endpoints.CHANNELS, channel, target)

        allow = Permissions.none() if allow is None else allow
        deny = Permissions.none() if deny is None else deny

        if not (isinstance(allow, Permissions) and isinstance(deny, Permissions)):
            raise InvalidArgument('allow and deny parameters must be discord.Permissions')

        deny =  deny.value
        allow = allow.value

        payload = {
            'id': target.id,
            'allow': allow,
            'deny': deny
        }

        if isinstance(target, Member):
            payload['type'] = 'member'
        elif isinstance(target, Role):
            payload['type'] = 'role'
        else:
            raise InvalidArgument('target parameter must be either discord.Member or discord.Role')

        r = yield from self.session.put(url, data=utils.to_json(payload), headers=self.headers)
        log.debug(request_logging_format.format(method='PUT', response=r))
        yield from utils._verify_successful_response(r)
        yield from r.release()

    @asyncio.coroutine
    def delete_channel_permissions(self, channel, target):
        """|coro|

        Removes a channel specific permission overwrites for a target
        in the specified :class:`Channel`.

        The target parameter follows the same rules as :meth:`set_channel_permissions`.

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

        url = '{0}/{1.id}/permissions/{2.id}'.format(endpoints.CHANNELS, channel, target)
        response = yield from self.session.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(method='DELETE', response=response))
        yield from utils._verify_successful_response(response)
        yield from response.release()


    # Voice management

    @asyncio.coroutine
    def join_voice_channel(self, channel):
        """|coro|

        Joins a voice channel and creates a :class:`VoiceClient` to
        establish your connection to the voice server.

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

        if self._is_voice_connected.is_set():
            raise ClientException('Already connected to a voice channel')

        if getattr(channel, 'type', ChannelType.text) != ChannelType.voice:
            raise InvalidArgument('Channel passed must be a voice channel')

        self.voice_channel = channel
        log.info('attempting to join voice channel {0.name}'.format(channel))

        payload = {
            'op': 4,
            'd': {
                'guild_id': self.voice_channel.server.id,
                'channel_id': self.voice_channel.id,
                'self_mute': False,
                'self_deaf': False
            }
        }

        yield from self.ws.send(utils.to_json(payload))
        yield from asyncio.wait_for(self._session_id_found.wait(), timeout=5.0, loop=self.loop)
        yield from asyncio.wait_for(self._voice_data_found.wait(), timeout=5.0, loop=self.loop)

        self._session_id_found.clear()
        self._voice_data_found.clear()

        kwargs = {
            'user': self.user,
            'connected': self._is_voice_connected,
            'channel': self.voice_channel,
            'data': self._voice_data_found.data,
            'loop': self.loop,
            'session_id': self.session_id,
            'main_ws': self.ws
        }

        result = VoiceClient(**kwargs)
        yield from result.connect()
        return result
