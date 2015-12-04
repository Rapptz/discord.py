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

import asyncio
import aiohttp
import websockets

import logging, traceback
import sys, time, re, json

log = logging.getLogger(__name__)
request_logging_format = '{method} {response.url} has returned {response.status}'
request_success_log = '{response.url} with {json} received {data}'

def to_json(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=True)

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

        max_messages = options.get('max_messages')
        if max_messages is None or max_messages < 100:
            max_messages = 5000

        self.connection = ConnectionState(self.dispatch, max_messages)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.headers = {
            'content-type': 'application/json',
        }
        self._closed = False

    # internals

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
            yield from self.ws.send(to_json(payload))
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

        if event in ('READY', 'MESSAGE_CREATE', 'MESSAGE_DELETE',
                     'MESSAGE_UPDATE', 'PRESENCE_UPDATE', 'USER_UPDATE',
                     'CHANNEL_DELETE', 'CHANNEL_UPDATE', 'CHANNEL_CREATE',
                     'GUILD_MEMBER_ADD', 'GUILD_MEMBER_REMOVE',
                     'GUILD_MEMBER_UPDATE', 'GUILD_CREATE', 'GUILD_DELETE',
                     'GUILD_ROLE_CREATE', 'GUILD_ROLE_DELETE', 'TYPING_START',
                     'GUILD_ROLE_UPDATE', 'VOICE_STATE_UPDATE'):
            parser = 'parse_' + event.lower()
            if hasattr(self.connection, parser):
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

        yield from self.ws.send(to_json(payload))
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

        data = to_json(payload)
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

        This function throws :exc:`ClientException` if called before
        logging in via :meth:`login`.
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

        url = '{}/{}/channels'.format(endpoints.USERS, self.user.id)
        r = yield from self.session.post(url, data=to_json(payload), headers=self.headers)
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
        :meth:`Server.get_default_channel` and sending it there. If it is a :class:`Object`
        instance then it is assumed to be the destination ID.

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

        resp = yield from self.session.post(url, data=to_json(payload), headers=self.headers)
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

        response = yield from self.session.patch(url, headers=self.headers, data=to_json(payload))
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

        response = yield from self.session.patch(url, headers=self.headers, data=to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=response))
        yield from utils._verify_successful_response(response)

    @asyncio.coroutine
    def edit_profile(self, password, **fields):
        """|coro|

        Edits the current profile of the client.

        All fields except ``password`` are optional.

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

        Raises
        ------
        HTTPException
            Editing your profile failed.
        """

        avatar_bytes = fields.get('avatar')
        avatar = None
        if avatar_bytes is not None:
            fmt = 'data:{mime};base64,{data}'
            mime = utils._get_mime_type_for_image(avatar_bytes)
            b64 = b64encode(avatar_bytes).decode('ascii')
            avatar = fmt.format(mime=mime, data=b64)

        payload = {
            'password': password,
            'new_password': fields.get('new_password'),
            'email': fields.get('email', self.email),
            'username': fields.get('username', self.user.name),
            'avatar': avatar
        }

        url = '{0}/@me'.format(endpoints.USERS)
        r = yield from self.session.patch(url, headers=self.headers, data=to_json(payload))
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

        sent = to_json(payload)
        log.debug('Sending "{}" to change status'.format(sent))
        yield from self.ws.send(sent)

    # Channel management

    @asyncio.coroutine
    def edit_channel(self, channel, **options):
        """|coro|

        Edits a :class:`Channel`.

        You must have the proper permissions to edit the channel.

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

        r = yield from self.session.patch(url, headers=self.headers, data=to_json(payload))
        log.debug(request_logging_format.format(method='PATCH', response=r))
        yield from utils._verify_successful_response(r)

        data = yield from r.json()
        log.debug(request_success_log.format(response=r, json=payload, data=data))

    @asyncio.coroutine
    def create_channel(self, server, name, type='text'):
        """|coro|

        Creates a :class:`Channel` in the specified :class:`Server`.

        Note that you need the proper permissions to create the channel.

        Parameters
        -----------
        server : :class:`Server`
            The server to create the channel in.
        name : str
            The channel's name.
        type : str
            The type of channel to create. 'text' or 'voice'.

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

        payload = {
            'name': name,
            'type': type
        }

        url = '{0}/{1.id}/channels'.format(endpoints.SERVERS, server)
        response = yield from self.session.post(url, headers=self.headers, data=to_json(payload))
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

