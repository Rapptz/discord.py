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

from __future__ import print_function

from . import endpoints
from .errors import InvalidEventName, InvalidDestination, GatewayNotFound
from .user import User
from .channel import Channel, PrivateChannel
from .server import Server, Member
from .role import Role, Permissions
from .message import Message
from . import utils
from .invite import Invite

import traceback
import requests
import json, re, time, copy
from collections import deque
import threading
from ws4py.client import WebSocketBaseClient
import sys
import logging
import itertools


log = logging.getLogger(__name__)
request_logging_format = '{name}: {response.request.method} {response.url} has returned {response.status_code}'
request_success_log = '{name}: {response.url} with {json} received {data}'

def _null_event(*args, **kwargs):
    pass

def is_response_successful(response):
    """Helper function for checking if the status code is in the 200 range"""
    code = response.status_code
    return code >= 200 and code < 300

class KeepAliveHandler(threading.Thread):
    def __init__(self, seconds, socket, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.seconds = seconds
        self.socket = socket
        self.stop = threading.Event()

    def run(self):
        while not self.stop.wait(self.seconds):
            payload = {
                'op': 1,
                'd': int(time.time())
            }

            msg = 'Keeping websocket alive with timestamp {0}'
            log.debug(msg.format(payload['d']))
            self.socket.send(json.dumps(payload, separators=(',', ':')))

class WebSocket(WebSocketBaseClient):
    def __init__(self, dispatch, url):
        WebSocketBaseClient.__init__(self, url,
                                     protocols=['http-only', 'chat'])
        self.dispatch = dispatch
        self.keep_alive = None

    def opened(self):
        log.info('Opened at {}'.format(int(time.time())))
        self.dispatch('socket_opened')

    def closed(self, code, reason=None):
        if self.keep_alive is not None:
            self.keep_alive.stop.set()
        log.info('Closed with {} ("{}") at {}'.format(code, reason,
                                                      int(time.time())))
        self.dispatch('socket_closed')

    def handshake_ok(self):
        pass

    def send(self, payload, binary=False):
        self.dispatch('socket_raw_send', payload, binary)
        WebSocketBaseClient.send(self, payload, binary)

    def received_message(self, msg):
        self.dispatch('socket_raw_receive', msg)
        response = json.loads(str(msg))
        log.debug('WebSocket Event: {}'.format(response))
        self.dispatch('socket_response', response)

        op = response.get('op')
        data = response.get('d')

        if op != 0:
            log.info("Unhandled op {}".format(op))
            return # What about op 7?

        event = response.get('t')

        if event == 'READY':
            interval = data['heartbeat_interval'] / 1000.0
            self.keep_alive = KeepAliveHandler(interval, self)
            self.keep_alive.start()


        if event in ('READY', 'MESSAGE_CREATE', 'MESSAGE_DELETE',
                     'MESSAGE_UPDATE', 'PRESENCE_UPDATE', 'USER_UPDATE',
                     'CHANNEL_DELETE', 'CHANNEL_UPDATE', 'CHANNEL_CREATE',
                     'GUILD_MEMBER_ADD', 'GUILD_MEMBER_REMOVE',
                     'GUILD_MEMBER_UPDATE', 'GUILD_CREATE', 'GUILD_DELETE',
                     'GUILD_ROLE_CREATE', 'GUILD_ROLE_DELETE',
                     'GUILD_ROLE_UPDATE', 'VOICE_STATE_UPDATE'):
            self.dispatch('socket_update', event, data)

        else:
            log.info("Unhandled event {}".format(event))


class ConnectionState(object):
    def __init__(self, dispatch, **kwargs):
        self.dispatch = dispatch
        self.user = None
        self.email = None
        self.servers = []
        self.private_channels = []
        self.messages = deque([], maxlen=kwargs.get('max_length', 5000))

    def _get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, self.messages)

    def _get_server(self, guild_id):
        return utils.find(lambda g: g.id == guild_id, self.servers)

    def _update_voice_state(self, server, data):
        user_id = data.get('user_id')
        member = utils.find(lambda m: m.id == user_id, server.members)
        if member is not None:
            ch_id = data.get('channel_id')
            channel = utils.find(lambda c: c.id == ch_id, server.channels)
            member.update_voice_state(voice_channel=channel, **data)
        return member

    def _add_server(self, guild):
        guild['roles'] = [Role(everyone=(guild['id'] == role['id']), **role) for role in guild['roles']]
        members = guild['members']
        owner = guild['owner_id']
        for i, member in enumerate(members):
            roles = member['roles']
            for j, roleid in enumerate(roles):
                role = utils.find(lambda r: r.id == roleid, guild['roles'])
                if role is not None:
                    roles[j] = role
            members[i] = Member(**member)

            # found the member that owns the server
            if members[i].id == owner:
                owner = members[i]

        for presence in guild['presences']:
            user_id = presence['user']['id']
            member = utils.find(lambda m: m.id == user_id, members)
            if member is not None:
                member.status = presence['status']
                member.game_id = presence['game_id']


        server = Server(owner=owner, **guild)

        # give all the members their proper server
        for member in server.members:
            member.server = server

        channels = [Channel(server=server, **channel)
                    for channel in guild['channels']]
        server.channels = channels
        for obj in guild.get('voice_states', []):
            self._update_voice_state(server, obj)
        self.servers.append(server)

    def handle_ready(self, data):
        self.user = User(**data['user'])
        guilds = data.get('guilds')

        for guild in guilds:
            if guild.get('unavailable', False):
                continue
            self._add_server(guild)

        for pm in data.get('private_channels'):
            self.private_channels.append(PrivateChannel(id=pm['id'],
                                         user=User(**pm['recipient'])))

        # we're all ready
        self.dispatch('ready')

    def handle_message_create(self, data):
        channel = self.get_channel(data.get('channel_id'))
        message = Message(channel=channel, **data)
        self.dispatch('message', message)
        self.messages.append(message)

    def handle_message_delete(self, data):
        channel = self.get_channel(data.get('channel_id'))
        message_id = data.get('id')
        found = self._get_message(message_id)
        if found is not None:
            self.dispatch('message_delete', found)
            self.messages.remove(found)

    def handle_message_update(self, data):
        older_message = self._get_message(data.get('id'))
        if older_message is not None:
            # create a copy of the new message
            message = copy.deepcopy(older_message)
            # update the new update
            for attr in data:
                if attr == 'channel_id' or attr == 'author':
                    continue
                value = data[attr]
                if 'time' in attr:
                    setattr(message, attr, utils.parse_time(value))
                else:
                    setattr(message, attr, value)
            self.dispatch('message_edit', older_message, message)
            # update the older message
            older_message = message

    def handle_presence_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            status = data.get('status')
            user = data['user']
            member_id = user['id']
            member = utils.find(lambda m: m.id == member_id, server.members)
            if member is not None:
                member.status = data.get('status')
                member.game_id = data.get('game_id')
                member.name = user.get('username', member.name)
                member.avatar = user.get('avatar', member.avatar)

                # call the event now
                self.dispatch('status', member)
                self.dispatch('member_update', member)

    def handle_user_update(self, data):
        self.user = User(**data)

    def handle_channel_delete(self, data):
        server =  self._get_server(data.get('guild_id'))
        if server is not None:
            channel_id = data.get('id')
            channel = utils.find(lambda c: c.id == channel_id, server.channels)
            server.channels.remove(channel)
            self.dispatch('channel_delete', channel)

    def handle_channel_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            channel_id = data.get('id')
            channel = utils.find(lambda c: c.id == channel_id, server.channels)
            channel.update(server=server, **data)
            self.dispatch('channel_update', channel)

    def handle_channel_create(self, data):
        is_private = data.get('is_private', False)
        channel = None
        if is_private:
            recipient = User(**data.get('recipient'))
            pm_id = data.get('id')
            channel = PrivateChannel(id=pm_id, user=recipient)
            self.private_channels.append(channel)
        else:
            server = self._get_server(data.get('guild_id'))
            if server is not None:
                channel = Channel(server=server, **data)
                server.channels.append(channel)

        self.dispatch('channel_create', channel)

    def handle_guild_member_add(self, data):
        server = self._get_server(data.get('guild_id'))
        member = Member(server=server, deaf=False, mute=False, **data)
        server.members.append(member)
        self.dispatch('member_join', member)

    def handle_guild_member_remove(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            user_id = data['user']['id']
            member = utils.find(lambda m: m.id == user_id, server.members)
            server.members.remove(member)
            self.dispatch('member_remove', member)

    def handle_guild_member_update(self, data):
        server = self._get_server(data.get('guild_id'))
        user_id = data['user']['id']
        member = utils.find(lambda m: m.id == user_id, server.members)
        if member is not None:
            user = data['user']
            member.name = user['username']
            member.discriminator = user['discriminator']
            member.avatar = user['avatar']
            member.roles = []
            # update the roles
            for role in server.roles:
                if role.id in data['roles']:
                    member.roles.append(role)

            self.dispatch('member_update', member)

    def handle_guild_create(self, data):
        if data.get('unavailable') is not None:
            # GUILD_CREATE with unavailable in the response
            # usually means that the server has become available
            # and is therefore in the cache
            server = self._get_server(data.get('id'))
            if server is not None:
                server.unavailable = False
                self.dispatch('server_available', server)
                return

            # if we're at this point then it was probably
            # unavailable during the READY event and is now
            # available, so it isn't in the cache...

        self._add_server(data)
        self.dispatch('server_create', self.servers[-1])

    def handle_guild_delete(self, data):
        if data.get('unavailable', False):
            # GUILD_DELETE with unavailable being True means that the
            # server that was available is now currently unavailable
            server = self._get_server(data.get('id'))
            if server is not None:
                server.unavailable = True
                self.dispatch('server_unavailable', server)
                return

        server = self._get_server(data.get('id'))
        self.servers.remove(server)
        self.dispatch('server_delete', server)

    def handle_guild_role_create(self, data):
        server = self._get_server(data.get('guild_id'))
        role_data = data.get('role', {})
        everyone = server.id == role_data.get('id')
        role = Role(everyone=everyone, **role_data)
        server.roles.append(role)
        self.dispatch('server_role_create', server, role)

    def handle_guild_role_delete(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            role_id = data.get('role_id')
            role = utils.find(lambda r: r.id == role_id, server.roles)
            server.roles.remove(role)
            self.dispatch('server_role_delete', server, role)

    def handle_guild_role_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            role_id = data['role']['id']
            role = utils.find(lambda r: r.id == role_id, server.roles)
            role.update(**data['role'])
            self.dispatch('server_role_update', role)

    def handle_voice_state_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            updated_member = self._update_voice_state(server, data)
            self.dispatch('voice_state_update', updated_member)

    def get_channel(self, id):
        if id is None:
            return None

        for server in self.servers:
            for channel in server.channels:
                if channel.id == id:
                    return channel

        for pm in self.private_channels:
            if pm.id == id:
                return pm


class Client(object):
    """Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    A number of options can be passed to the :class:`Client` via keyword arguments.

    :param int max_length: The maximum number of messages to store in :attr:`messages`. Defaults to 5000.

    Instance attributes:

     .. attribute:: user

         A :class:`User` that represents the connected client. None if not logged in.
     .. attribute:: servers

         A list of :class:`Server` that the connected client has available.
     .. attribute:: private_channels

         A list of :class:`PrivateChannel` that the connected client is participating on.
     .. attribute:: messages

        A deque_ of :class:`Message` that the client has received from all servers and private messages.
     .. attribute:: email

        The email used to login. This is only set if login is successful, otherwise it's None.

    .. _deque: https://docs.python.org/3.4/library/collections.html#collections.deque
    """

    def __init__(self, **kwargs):
        self._is_logged_in = False
        self._close = False
        self.options = kwargs
        self.connection = ConnectionState(self.dispatch, **kwargs)
        self.dispatch_lock = threading.RLock()
        self.token = ''

        # the actual headers for the request...
        # we only override 'authorization' since the rest could use the defaults.
        self.headers = {
            'authorization': self.token,
        }

    def _create_websocket(self, url, reconnect=False):
        if url is None:
            raise GatewayNotFound()
        log.info('websocket gateway found')
        self.ws = WebSocket(self.dispatch, url)
        self.ws.connect()
        log.info('websocket has connected')

        if reconnect == False:
            second_payload = {
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

            self.ws.send(json.dumps(second_payload, separators=(',', ':')))

    def _resolve_mentions(self, content, mentions):
        if isinstance(mentions, list):
            return [user.id for user in mentions]
        elif mentions == True:
            return re.findall(r'<@(\d+)>', content)
        else:
            return []

    def _resolve_invite(self, invite):
        if isinstance(invite, Invite):
            return invite.id
        else:
            rx = r'(?:https?\:\/\/)?discord\.gg\/(.+)'
            m = re.match(rx, invite)
            if m:
                return m.group(1)
        return None

    def _resolve_destination(self, destination):
        if isinstance(destination, Channel) or isinstance(destination, PrivateChannel):
            return (destination.id, destination.is_private)
        elif isinstance(destination, User):
            found = utils.find(lambda pm: pm.user == destination, self.private_channels)
            if found is None:
                # Couldn't find the user, so start a PM with them first.
                self.start_private_message(destination)
                channel_id = self.private_channels[-1].id
                return (channel_id, True)
            else:
                return (found.id, True)
        elif isinstance(destination, str):
            channel_id = destination
            return (destination, True)
        else:
            raise InvalidDestination('Destination must be Channel, PrivateChannel, User, or str')

    def on_error(self, event_method, *args, **kwargs):
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()

    # Compatibility shim
    def __getattr__(self, name):
        if name in ('user', 'email', 'servers', 'private_channels', 'messages'):
            return getattr(self.connection, name)
        else:
            msg = "'{}' object has no attribute '{}'"
            raise AttributeError(msg.format(self.__class__, name))

    # Compatibility shim
    def __setattr__(self, name, value):
        if name in ('user', 'email', 'servers', 'private_channels',
                    'messages'):
            return setattr(self.connection, name, value)
        else:
            object.__setattr__(self, name, value)

    def dispatch(self, event, *args, **kwargs):
        with self.dispatch_lock:
            log.debug("Dispatching event {}".format(event))
            handle_method = '_'.join(('handle', event))
            event_method = '_'.join(('on', event))
            getattr(self, handle_method, _null_event)(*args, **kwargs)
            try:
                getattr(self, event_method, _null_event)(*args, **kwargs)
            except Exception as e:
                getattr(self, 'on_error')(event_method, *args, **kwargs)

    def handle_socket_update(self, event, data):
        method = '_'.join(('handle', event.lower()))
        getattr(self.connection, method)(data)

    def run(self):
        """Runs the client and allows it to receive messages and events."""
        log.info('Client is being run')
        self.ws.run()

        # The WebSocket is guaranteed to be terminated after ws.run().
        # Check if we wanted it to close and reconnect if not.
        while not self._close:
            gateway = requests.get(endpoints.GATEWAY, headers=self.headers)
            if gateway.status_code != 200:
                raise GatewayNotFound()
            self.connection = ConnectionState(self.dispatch, **self.options)
            self._create_websocket(gateway.json().get('url'), reconnect=False)
            self.ws.run()

        log.info('Client exiting')

    @property
    def is_logged_in(self):
        """Returns True if the client is successfully logged in. False otherwise."""
        return self._is_logged_in

    def get_channel(self, id):
        """Returns a :class:`Channel` or :class:`PrivateChannel` with the
        following ID. If not found, returns None.
        """
        return self.connection.get_channel(id)

    def start_private_message(self, user):
        """Starts a private message with the user. This allows you to :meth:`send_message` to it.

        Note that this method should rarely be called as :meth:`send_message` does it automatically.

        :param user: A :class:`User` to start the private message with.
        """
        if not isinstance(user, User):
            raise TypeError('user argument must be a User')

        payload = {
            'recipient_id': user.id
        }

        r = requests.post('{}/{}/channels'.format(endpoints.USERS, self.user.id), json=payload, headers=self.headers)
        if is_response_successful(r):
            data = r.json()
            log.debug(request_success_log.format(name='start_private_message', response=r, json=payload, data=data))
            self.private_channels.append(PrivateChannel(id=data['id'], user=user))
        else:
            log.error(request_logging_format.format(name='start_private_message', response=r))

    def send_message(self, destination, content, mentions=True, tts=False):
        """Sends a message to the destination given with the content given.

        The destination could be a :class:`Channel` or a :class:`PrivateChannel`. For convenience
        it could also be a :class:`User`. If it's a :class:`User` or :class:`PrivateChannel` then it
        sends the message via private message, otherwise it sends the message to the channel. If it's
        a ``str`` instance, then it assumes it's a channel ID and uses that for its destination.

        The content must be a type that can convert to a string through ``str(content)``.

        The mentions must be either an array of :class:`User` to mention or a boolean. If
        ``mentions`` is ``True`` then all the users mentioned in the content are mentioned, otherwise
        no one is mentioned. Note that to mention someone in the content, you should use :meth:`User.mention`.

        :param destination: The location to send the message.
        :param content: The content of the message to send.
        :param mentions: A list of :class:`User` to mention in the message or a boolean. Ignored for private messages.
        :param tts: If ``True``, sends tries to send the message using text-to-speech.
        :return: The :class:`Message` sent or None if error occurred.
        """

        channel_id, is_private_message = self._resolve_destination(destination)

        content = str(content)
        mentions = self._resolve_mentions(content, mentions)

        url = '{base}/{id}/messages'.format(base=endpoints.CHANNELS, id=channel_id)
        payload = {
            'content': content,
        }

        if not is_private_message:
            payload['mentions'] = mentions

        if tts:
            payload['tts'] = True

        response = requests.post(url, json=payload, headers=self.headers)
        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='send_message', response=response, json=payload, data=data))
            channel = self.get_channel(data.get('channel_id'))
            message = Message(channel=channel, **data)
            return message
        else:
            log.error(request_logging_format.format(name='send_message', response=response))

    def send_file(self, destination, filename):
        """Sends a message to the destination given with the file given.

        The destination parameter follows the same rules as :meth:`send_message`.

        Note that this requires proper permissions in order to work.

        :param destination: The location to send the message.
        :param filename: The file to send.
        :return: The :class:`Message` sent or None if an error occurred.
        """

        channel_id, is_private_message = self._resolve_destination(destination)

        url = '{base}/{id}/messages'.format(base=endpoints.CHANNELS, id=channel_id)
        response = None

        with open(filename, 'rb') as f:
            files = {
                'file': (filename, f)
            }
            response = requests.post(url, files=files, headers=self.headers)

        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='send_file', response=response, json=response.text, data=filename))
            channel = self.get_channel(data.get('channel_id'))
            message = Message(channel=channel, **data)
            return message
        else:
            log.error(request_logging_format.format(name='send_file', response=response))

    def delete_message(self, message):
        """Deletes a :class:`Message`.

        Your own messages could be deleted without any proper permissions. However to
        delete other people's messages, you need the proper permissions to do so.

        :param message: The :class:`Message` to delete.
        :returns: True if the message was deleted successfully, False otherwise.
        """

        url = '{}/{}/messages/{}'.format(endpoints.CHANNELS, message.channel.id, message.id)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(name='delete_message', response=response))
        return is_response_successful(response)

    def edit_message(self, message, new_content, mentions=True):
        """Edits a :class:`Message` with the new message content.

        The new_content must be able to be transformed into a string via ``str(new_content)``.

        :param message: The :class:`Message` to edit.
        :param new_content: The new content to replace the message with.
        :param mentions: The mentions for the user. Same as :meth:`send_message`.
        :return: The new edited message or None if an error occurred.
        """

        channel = message.channel
        content = str(new_content)

        url = '{}/{}/messages/{}'.format(endpoints.CHANNELS, channel.id, message.id)
        payload = {
            'content': content
        }

        if not channel.is_private:
            payload['mentions'] = self._resolve_mentions(content, mentions)

        response = requests.patch(url, headers=self.headers, json=payload)
        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='edit_message', response=response, json=payload, data=data))
            return Message(channel=channel, **data)
        else:
            log.error(request_logging_format.format(name='edit_message', response=response))

    def login(self, email, password):
        """Logs in the user with the following credentials and initialises
        the connection to Discord.

        After this function is called, :attr:`is_logged_in` returns True if no
        errors occur.

        :param str email: The email used to login.
        :param str password: The password used to login.
        """

        payload = {
            'email': email,
            'password': password
        }

        r = requests.post(endpoints.LOGIN, json=payload)

        if is_response_successful(r):
            log.info('logging in returned status code {}'.format(r.status_code))
            self.email = email

            body = r.json()
            self.token = body['token']
            self.headers['authorization'] = self.token

            gateway = requests.get(endpoints.GATEWAY, headers=self.headers)
            if not is_response_successful(gateway):
                raise GatewayNotFound()
            self._create_websocket(gateway.json().get('url'), reconnect=False)
            self._is_logged_in = True
        else:
            log.error(request_logging_format.format(name='login', response=r))

    def register(self, username, invite, fingerprint=None):
        """Register a new unclaimed account using an invite to a server.

        After this function is called, the client will be logged in to the
        user created and :attr:`is_logged_in` returns True if no errors
        occur.

        :param str username: The username to register as.
        :param invite: An invite URL or :class:`Invite` to register with.
        :param str fingerprint: Unkown API parameter, defaults to None
        """

        payload = {
            'fingerprint': fingerprint,
            'username': username,
            'invite': self._resolve_invite(invite)
        }

        r = requests.post(endpoints.REGISTER, json=payload)

        if r.status_code == 201:
            log.info('register returned status code 200')
            self.email = ''

            body = r.json()
            self.token = body['token']
            self.headers['authorization'] = self.token

            gateway = requests.get(endpoints.GATEWAY, headers=self.headers)
            if gateway.status_code != 200:
                raise GatewayNotFound()
            self._create_websocket(gateway.json().get('url'), reconnect=False)
            self._is_logged_in = True
        else:
            log.error(request_logging_format.format(name='register',
                                                    response=r))

    def logout(self):
        """Logs out of Discord and closes all connections."""
        response = requests.post(endpoints.LOGOUT)
        self._close = True
        self.ws.close()
        self._is_logged_in = False
        log.debug(request_logging_format.format(name='logout', response=response))

    def logs_from(self, channel, limit=100):
        """A generator that obtains logs from a specified channel.

        Yielding from the generator returns a :class:`Message` object with the message data.

        Example: ::

            for message in client.logs_from(channel):
                if message.content.startswith('!hello'):
                    if message.author == client.user:
                        client.edit_message(message, 'goodbye')


        :param channel: The :class:`Channel` to obtain the logs from.
        :param limit: The number of messages to retrieve.
        """

        url = '{}/{}/messages'.format(endpoints.CHANNELS, channel.id)
        params = {
            'limit': limit
        }
        response = requests.get(url, params=params, headers=self.headers)
        if is_response_successful(response):
            messages = response.json()
            log.info('logs_from: {0.url} was successful'.format(response))
            for message in messages:
                yield Message(channel=channel, **message)
        else:
            log.error(request_logging_format.format(name='logs_from', response=response))

    def event(self, function):
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        Example: ::

            @client.event
            def on_ready():
                print('Ready!')
        """

        setattr(self, function.__name__, function)
        log.info('{0.__name__} has successfully been registered as an event'.format(function))
        return function

    def delete_channel(self, channel):
        """Deletes a channel.

        In order to delete the channel, the client must have the proper permissions
        in the server the channel belongs to.

        :param channel: The :class:`Channel` to delete.
        :returns: True if channel was deleted successfully, False otherwise.
        """

        url = '{}/{}'.format(endpoints.CHANNELS, channel.id)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='delete_channel'))
        return is_response_successful(response)

    def kick(self, server, user):
        """Kicks a :class:`User` from their respective :class:`Server`.

        You must have the proper permissions to kick a user in the server.

        :param server: The :class:`Server` to kick the member from.
        :param user: The :class:`User` to kick.
        :returns: True if kick was successful, False otherwise.
        """

        url = '{base}/{server}/members/{user}'.format(base=endpoints.SERVERS, server=server.id, user=user.id)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='kick'))
        return is_response_successful(response)

    def ban(self, server, user):
        """Bans a :class:`User` from their respective :class:`Server`.

        You must have the proper permissions to ban a user in the server.

        :param server: The :class:`Server` to ban the member from.
        :param user: The :class:`User` to ban.
        :returns: True if ban was successful, False otherwise.
        """

        url = '{base}/{server}/bans/{user}'.format(base=endpoints.SERVERS, server=server.id, user=user.id)
        response = requests.put(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='ban'))
        return is_response_successful(response)

    def unban(self, server, name):
        """Unbans a :class:`User` from their respective :class:`Server`.

        You must have the proper permissions to unban a user in the server.

        :param server: The :class:`Server` to unban the member from.
        :param user: The :class:`User` to unban.
        :returns: True if unban was successful, False otherwise.
        """

        url = '{base}/{server}/bans/{user}'.format(base=endpoints.SERVERS, server=server.id, user=user.id)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='unban'))
        return is_response_successful(response)

    def edit_profile(self, password, **fields):
        """Edits the current profile of the client.

        All fields except password are optional.

        :param password: The current password for the client's account.
        :param new_password: The new password you wish to change to.
        :param email: The new email you wish to change to.
        :param username: The new username you wish to change to.
        :returns: True if profile edit was successful, False otherwise.
        """

        payload = {
            'password': password,
            'new_password': fields.get('new_password'),
            'email': fields.get('email', self.email),
            'username': fields.get('username', self.user.name),
            'avatar': self.user.avatar
        }

        url = '{0}/@me'.format(endpoints.USERS)
        response = requests.patch(url, headers=self.headers, json=payload)

        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='edit_profile', response=response, json=payload, data=data))
            self.token = data['token']
            self.email = data['email']
            self.headers['authorization'] = self.token
            self.user = User(**data)
            return True
        else:
            log.debug(request_logging_format.format(response=response, name='edit_profile'))
            return False

    def edit_channel(self, channel, **options):
        """Edits a :class:`Channel`.

        You must have the proper permissions to edit the channel.

        References pointed to the channel will be updated with the new information.

        :param channel: The :class:`Channel` to update.
        :param name: The new channel name.
        :param position: The new channel's position in the GUI.
        :param topic: The new channel's topic.
        :returns: True if editing was successful, False otherwise.
        """

        url = '{0}/{1.id}'.format(endpoints.CHANNELS, channel)
        payload = {
            'name': options.get('name', channel.name),
            'topic': options.get('topic', channel.topic),
            'position': options.get('position', channel.position)
        }

        response = requests.patch(url, headers=self.headers, json=payload)
        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='edit_channel', response=response, json=payload, data=data))
            channel.update(server=channel.server, **data)
            return True
        else:
            log.debug(request_logging_format.format(response=response, name='edit_channel'))
            return False

    def create_channel(self, server, name, type='text'):
        """Creates a :class:`Channel` in the specified :class:`Server`.

        Note that you need the proper permissions to create the channel.

        :param server: The :class:`Server` to create the channel in.
        :param name: The channel's name.
        :param type: The type of channel to create. 'text' or 'voice'.
        :returns: The newly created :class:`Channel` if successful, else None.
        """

        payload = {
            'name': name,
            'type': type
        }

        url = '{0}/{1.id}/channels'.format(endpoints.SERVERS, server)
        response = requests.post(url, headers=self.headers, json=payload)
        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='create_channel', response=response, data=data, json=payload))
            channel = Channel(server=server, **data)
            # We don't append it to server.channels because CHANNEL_CREATE handles it for us.
            return channel
        else:
            log.debug(request_logging_format.format(response=response, name='create_channel'))

    def leave_server(self, server):
        """Leaves a :class:`Server`.

        :param server: The :class:`Server` to leave.
        :returns: True if leaving was successful, False otherwise.
        """

        url = '{0}/{1.id}'.format(endpoints.SERVERS, server)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='leave_server'))
        return is_response_successful(response)

    def create_invite(self, destination, **options):
        """Creates an invite for the destination which could be either a :class:`Server` or :class:`Channel`.

        The available options are:

        :param destination: The :class:`Server` or :class:`Channel` to create the invite to.
        :param max_age: How long the invite should last. If it's 0 then the invite doesn't expire. Defaults to 0.
        :param max_uses: How many uses the invite could be used for. If it's 0 then there are unlimited uses. Defaults to 0.
        :param temporary: A boolean to denote that the invite grants temporary membership (i.e. they get kicked after they disconnect). Defaults to False.
        :param xkcd: A boolean to indicate if the invite URL is human readable. Defaults to False.
        :returns: The :class:`Invite` if creation is successful, None otherwise.
        """

        payload = {
            'max_age': options.get('max_age', 0),
            'max_uses': options.get('max_uses', 0),
            'temporary': options.get('temporary', False),
            'xkcdpass': options.get('xkcd', False)
        }

        url = '{0}/{1.id}/invites'.format(endpoints.CHANNELS, destination)
        response = requests.post(url, headers=self.headers, json=payload)
        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='create_invite', json=payload, response=response, data=data))
            data['server'] = self.connection._get_server(data['guild']['id'])
            channel_id = data['channel']['id']
            data['channel'] = utils.find(lambda ch: ch.id == channel_id, data['server'].channels)
            return Invite(**data)
        else:
            log.debug(request_logging_format.format(response=response, name='create_invite'))

    def accept_invite(self, invite):
        """Accepts an :class:`Invite` or a URL to an invite.

        The URL must be a discord.gg URL. e.g. "http://discord.gg/codehere"

        :param invite: The :class:`Invite` or URL to an invite to accept.
        :returns: True if the invite was successfully accepted, False otherwise.
        """

        destination = self._resolve_invite(invite)

        if destination is None:
            return False

        url = '{0}/invite/{1}'.format(endpoints.API_BASE, destination)
        response = requests.post(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='accept_invite'))
        return is_response_successful(response)

    def edit_role(self, server, role, **fields):
        """Edits the specified :class:`Role` for the entire :class:`Server`.

        .. versionchanged:: 0.8.0
            Editing now uses keyword arguments instead of editing the :class:`Role` object directly.

        .. note::

            At the moment, the Discord API allows you to set the colour to any
            RGB value. This will change in the future so it is recommended that
            you use the constants in the :class:`Colour` instead such as
            :attr:`Colour.NAVY_BLUE`.

        :param server: The :class:`Server` the role belongs to.
        :param role: The :class:`Role` to edit.
        :param name: The new role name to change to. (optional)
        :param permissions: The new :class:`Permissions` to change to. (optional)
        :param colour: The new :class:`Colour` to change to. (optional) (aliased to color as well)
        :param hoist: A boolean indicating if the role should be shown separately. (optional)
        :return: ``True`` if editing was successful, ``False`` otherwise. If editing is successful,
                 the ``role`` parameter will be updated with the changes.
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

        response = requests.patch(url, json=payload, headers=self.headers)
        if is_response_successful(response):
            data = response.json()
            log.debug(request_success_log.format(name='edit_role', json=payload, response=response, data=data))
            role.update(**data)
            return True

        log.debug(request_logging_format.format(response=response, name='edit_role'))
        return False

    def delete_role(self, server, role):
        """Deletes the specified :class:`Role` for the entire :class:`Server`.

        Works in a similar matter to :func:`edit_role`.

        :param server: The :class:`Server` the role belongs to.
        :param role: The :class:`Role` to delete.
        :return: ``True`` if deleting was successful, ``False`` otherwise.
        """

        url = '{0}/{1.id}/roles/{2.id}'.format(endpoints.SERVERS, server, role)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='delete_role'))
        return is_response_successful(response)

    def add_roles(self, member, *roles):
        """Gives the specified :class:`Member` a number of :class:`Role` s.

        You must have the proper permissions to use this function.

        This method **appends** a role to a member.

        :param member: The :class:`Member` to give roles to.
        :param roles: An iterable of :class:`Role` s to give the member.
        :return: ``True`` if the operation was successful, ``False`` otherwise.
        """

        url = '{0}/{1.server.id}/members/{1.id}'.format(endpoints.SERVERS, member)
        new_roles = [role.id for role in itertools.chain(member.roles, roles)]
        payload = {
            'roles': new_roles
        }

        response = requests.patch(url, headers=self.headers, json=payload)
        log.debug(request_logging_format.format(response=response, name='add_roles'))
        return is_response_successful(response)

    def remove_roles(self, member, *roles):
        """Removes the :class:`Role` s from the :class:`Member`.

        You must have the proper permissions to use this function.

        :param member: The :class:`Member` to remove roles from.
        :param roles: An iterable of :class:`Role` s to remove from the member.
        :return: ``True`` if the operation was successful, ``False`` otherwise.
        """

        url = '{0}/{1.server.id}/members/{1.id}'.format(endpoints.SERVERS, member)

        new_roles = [role.id for role in member.roles]
        for role in roles:
            if role.id in new_roles:
                new_roles.remove(role.id)

        payload = {
            'roles': new_roles
        }

        response = requests.patch(url, headers=self.headers, json=payload)
        log.debug(request_logging_format.format(response=response, name='remove_roles'))
        return is_response_successful(response)

    def replace_roles(self, member, *roles):
        """Replaces the :class:`Member`'s roles.

        You must have the proper permissions to use this function.

        This function **replaces** all roles that the member has.
        For example if the member has roles ``[a, b, c]`` and the
        call is ``client.replace_roles(member, d, e, c)`` then
        the member has the roles ``[d, e, c]``.

        :param member: The :class:`Member` to replace roles for.
        :param roles: An iterable of :class:`Role` s to replace with.
        :return: ``True`` if the operation was successful, ``False`` otherwise.
        """

        url = '{0}/{1.server.id}/members/{1.id}'.format(endpoints.SERVERS, member)

        payload = {
            'roles': [role.id for role in roles]
        }

        response = requests.patch(url, headers=self.headers, json=payload)
        log.debug(request_logging_format.format(response=response, name='replace_roles'))
        if is_response_successful(response):
            member.roles = list(roles)
            return True

        return False

    def create_role(self, server, **fields):
        """Creates a :class:`Role`.

        The fields parameter is the same as :func:`edit_role`.

        :return: The :class:`Role` if creation was successful, None otherwise.
        """

        url = '{0}/{1.id}/roles'.format(endpoints.SERVERS, server)
        response = requests.post(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='create_role'))

        if is_response_successful(response):
            data = response.json()
            everyone = server.id == data.get('id')
            role = Role(everyone=everyone, **data)
            if self.edit_role(server, role, **fields):
                # we have to call edit because you can't pass a payload to the
                # http request currently.
                return role

        return None

    def set_channel_permissions(self, channel, target, allow=None, deny=None):
        """Sets the channel specific permission overwrites for a target in the
        specified :class:`Channel`.

        The ``target`` parameter should either be a :class:`Member` or a
        :class:`Role` that belongs to the channel's server.

        You must have the proper permissions to do this.

        Example code: ::

            allow = discord.Permissions.none()
            deny = discord.Permissions.none()
            allow.can_mention_everyone = True
            deny.can_manage_messages = True
            client.set_channel_permissions(message.channel, message.author, allow, deny)

        :param channel: The :class:`Channel` to give the specific permissions for.
        :param target: The :class:`Member` or :class:`Role` to overwrite permissions for.
        :param allow: A :class:`Permissions` object representing the permissions to explicitly allow. (optional)
        :param deny: A :class:`Permissions` object representing the permissions to explicitly deny. (optional)
        :return: ``True`` if setting is successful, ``False`` otherwise.
        """

        url = '{0}/{1.id}/permissions/{2.id}'.format(endpoints.CHANNELS, channel, target)

        allow = Permissions.none() if allow is None else allow
        deny = Permissions.none() if deny is None else deny

        if not (isinstance(allow, Permissions) and isinstance(deny, Permissions)):
            raise TypeError('allow and deny parameters must be discord.Permissions')

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
            raise TypeError('target parameter must be either discord.Member or discord.Role')

        response = requests.put(url, json=payload, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='set_channel_permissions'))
        return is_response_successful(response)

    def delete_channel_permissions(self, channel, target):
        """Removes a channel specific permission overwrites for a target
        in the specified :class:`Channel`.

        The target parameter follows the same rules as :meth:`set_channel_permissions`.

        You must have the proper permissions to do this.

        :param channel: The :class:`Channel` to give the specific permissions for.
        :param target: The :class:`Member` or :class:`Role` to overwrite permissions for.
        :return: ``True`` if deletion is successful, ``False`` otherwise.
        """

        url = '{0}/{1.id}/permissions/{2.id}'.format(endpoints.CHANNELS, channel, target)
        response = requests.delete(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='delete_channel_permissions'))
        return is_response_successful(response)

    def change_status(self, game_id=None, idle=False):
        """Changes the client's status.

        The game_id parameter is a numeric ID (not a string) that represents
        a game being played currently. The list of game_id to actual games changes
        constantly and would thus be out of date pretty quickly. An old version of
        the game_id database can be seen `here`_ to help you get started.

        The idle parameter is a boolean parameter that indicates whether the
        client should go idle or not.

        .. _here: https://gist.github.com/Rapptz/a82b82381b70a60c281b

        :param game_id: The numeric game ID being played. None if no game is being played.
        :param idle: A boolean indicating if the client should go idle."""

        idle_since = None if idle == False else int(time.time() * 1000)
        payload = {
            'op': 3,
            'd': {
                'game_id': game_id,
                'idle_since': idle_since
            }
        }

        sent = json.dumps(payload)
        log.debug('Sending "{}" to change status'.format(sent))
        self.ws.send(sent)

