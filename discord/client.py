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
from .errors import InvalidEventName, InvalidDestination, GatewayNotFound
from .user import User
from .channel import Channel, PrivateChannel
from .server import Server, Member, Permissions, Role
from .message import Message
from . import utils
from .invite import Invite

import requests
import json, re, time, copy
from collections import deque
import threading
from ws4py.client.threadedclient import WebSocketClient
import sys
import logging

log = logging.getLogger(__name__)
request_logging_format = '{name}: {response.request.method} {response.url} has returned {response.status_code}'
request_success_log = '{name}: {response.url} with {json} received {data}'

def _null_event(*args, **kwargs):
    pass

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
            self.socket.send(json.dumps(payload))

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
        self.user = None
        self.email = None
        self.servers = []
        self.private_channels = []
        self.token = ''
        self.messages = deque([], maxlen=kwargs.get('max_length', 5000))
        self.events = {
            'on_ready': _null_event,
            'on_disconnect': _null_event,
            'on_error': _null_event,
            'on_response': _null_event,
            'on_message': _null_event,
            'on_message_delete': _null_event,
            'on_message_edit': _null_event,
            'on_status': _null_event,
            'on_channel_delete': _null_event,
            'on_channel_create': _null_event,
            'on_channel_update': _null_event,
            'on_member_join': _null_event,
            'on_member_remove': _null_event,
            'on_member_update': _null_event,
            'on_server_create': _null_event,
            'on_server_delete': _null_event,
        }

        # the actual headers for the request...
        # we only override 'authorization' since the rest could use the defaults.
        self.headers = {
            'authorization': self.token,
        }

    def _get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, self.messages)

    def _get_server(self, guild_id):
        return utils.find(lambda g: g.id == guild_id, self.servers)

    def _add_server(self, guild):
        guild['roles'] = [Role(**role) for role in guild['roles']]
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

        channels = [Channel(server=server, **channel) for channel in guild['channels']]
        server.channels = channels
        self.servers.append(server)

    def _create_websocket(self, url, reconnect=False):
        if url is None:
            raise GatewayNotFound()
        log.info('websocket gateway found')
        self.ws = WebSocketClient(url, protocols=['http-only', 'chat'])

        # this is kind of hacky, but it's to avoid deadlocks.
        # i.e. python does not allow me to have the current thread running if it's self
        # it throws a 'cannot join current thread' RuntimeError
        # So instead of doing a basic inheritance scheme, we're overriding the member functions.

        self.ws.opened = self._opened
        self.ws.closed = self._closed
        self.ws.received_message = self._received_message
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
                    'v': 2
                }
            }

            self.ws.send(json.dumps(second_payload))

    def _resolve_mentions(self, content, mentions):
        if isinstance(mentions, list):
            return [user.id for user in mentions]
        elif mentions == True:
            return re.findall(r'@<(\d+)>', content)
        else:
            return []

    def _invoke_event(self, event_name, *args, **kwargs):
        try:
            log.info('attempting to invoke event {}'.format(event_name))
            self.events[event_name](*args, **kwargs)
        except Exception as e:
            log.error('an error ({}) occurred in event {} so on_error is invoked instead'.format(type(e).__name__, event_name))
            self.events['on_error'](event_name, *sys.exc_info())

    def _received_message(self, msg):
        response = json.loads(str(msg))
        log.debug('WebSocket Event: {}'.format(response))
        if response.get('op') != 0:
            return

        self._invoke_event('on_response', response)
        event = response.get('t')
        data = response.get('d')

        if event == 'READY':
            self.user = User(**data['user'])
            guilds = data.get('guilds')

            for guild in guilds:
                self._add_server(guild)

            for pm in data.get('private_channels'):
                self.private_channels.append(PrivateChannel(id=pm['id'], user=User(**pm['recipient'])))

            # set the keep alive interval..
            interval = data.get('heartbeat_interval') / 1000.0
            self.keep_alive = KeepAliveHandler(interval, self.ws)
            self.keep_alive.start()

            # we're all ready
            self._invoke_event('on_ready')
        elif event == 'MESSAGE_CREATE':
            channel = self.get_channel(data.get('channel_id'))
            message = Message(channel=channel, **data)
            self._invoke_event('on_message', message)
            self.messages.append(message)
        elif event == 'MESSAGE_DELETE':
            channel = self.get_channel(data.get('channel_id'))
            message_id = data.get('id')
            found = self._get_message(message_id)
            if found is not None:
                self._invoke_event('on_message_delete', found)
                self.messages.remove(found)
        elif event == 'MESSAGE_UPDATE':
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
                self._invoke_event('on_message_edit', older_message, message)
                # update the older message
                older_message = message

        elif event == 'PRESENCE_UPDATE':
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
                    self._invoke_event('on_status', member)
                    self._invoke_event('on_member_update', member)
        elif event == 'USER_UPDATE':
            self.user = User(**data)
        elif event == 'CHANNEL_DELETE':
            server =  self._get_server(data.get('guild_id'))
            if server is not None:
                channel_id = data.get('id')
                channel = utils.find(lambda c: c.id == channel_id, server.channels)
                server.channels.remove(channel)
                self._invoke_event('on_channel_delete', channel)
        elif event == 'CHANNEL_UPDATE':
            server = self._get_server(data.get('guild_id'))
            if server is not None:
                channel_id = data.get('id')
                channel = utils.find(lambda c: c.id == channel_id, server.channels)
                channel.update(server=server, **data)
                self._invoke_event('on_channel_update', channel)
        elif event == 'CHANNEL_CREATE':
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

            self._invoke_event('on_channel_create', channel)
        elif event == 'GUILD_MEMBER_ADD':
            server = self._get_server(data.get('guild_id'))
            member = Member(server=server, deaf=False, mute=False, **data)
            server.members.append(member)
            self._invoke_event('on_member_join', member)
        elif event == 'GUILD_MEMBER_REMOVE':
            server = self._get_server(data.get('guild_id'))
            user_id = data['user']['id']
            member = utils.find(lambda m: m.id == user_id, server.members)
            server.members.remove(member)
            self._invoke_event('on_member_remove', member)
        elif event == 'GUILD_MEMBER_UPDATE':
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

                self._invoke_event('on_member_update', member)
        elif event == 'GUILD_CREATE':
            self._add_server(data)
            self._invoke_event('on_server_create', self.servers[-1])
        elif event == 'GUILD_DELETE':
            server = self._get_server(data.get('id'))
            self.servers.remove(server)
            self._invoke_event('on_server_delete', server)

    def _opened(self):
        log.info('Opened at {}'.format(int(time.time())))

    def _closed(self, code, reason=None):
        log.info('Closed with {} ("{}") at {}'.format(code, reason, int(time.time())))
        self._invoke_event('on_disconnect')

    def run(self):
        """Runs the client and allows it to receive messages and events."""
        log.info('Client is being run')
        self.ws.run_forever()

    @property
    def is_logged_in(self):
        """Returns True if the client is successfully logged in. False otherwise."""
        return self._is_logged_in

    def get_channel(self, id):
        """Returns a :class:`Channel` or :class:`PrivateChannel` with the following ID. If not found, returns None."""
        if id is None:
            return None

        for server in self.servers:
            for channel in server.channels:
                if channel.id == id:
                    return channel

        for pm in self.private_channels:
            if pm.id == id:
                return pm

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
        if r.status_code == 200:
            data = r.json()
            log.debug(request_success_log.format(name='start_private_message', response=r, json=payload, data=data))
            self.private_channels.append(PrivateChannel(id=data['id'], user=user))
        else:
            log.error(request_logging_format.format(name='start_private_message', response=r))

    def send_message(self, destination, content, mentions=True, tts=False):
        """Sends a message to the destination given with the content given.

        The destination could be a :class:`Channel` or a :class:`PrivateChannel`. For convenience
        it could also be a :class:`User`. If it's a :class:`User` or :class:`PrivateChannel` then it
        sends the message via private message, otherwise it sends the message to the channel.

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

        channel_id = ''
        is_private_message = True
        if isinstance(destination, Channel) or isinstance(destination, PrivateChannel):
            channel_id = destination.id
            is_private_message = destination.is_private
        elif isinstance(destination, User):
            found = utils.find(lambda pm: pm.user == destination, self.private_channels)
            if found is None:
                # Couldn't find the user, so start a PM with them first.
                self.start_private_message(destination)
                channel_id = self.private_channels[-1].id
            else:
                channel_id = found.id
        else:
            raise InvalidDestination('Destination must be Channel, PrivateChannel, or User')

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
        if response.status_code == 200:
            data = response.json()
            log.debug(request_success_log.format(name='send_message', response=response, json=payload, data=data))
            channel = self.get_channel(data.get('channel_id'))
            message = Message(channel=channel, **data)
            return message
        else:
            log.error(request_logging_format.format(name='send_message', response=response))

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
        return response.status_code == 200

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
        if response.status_code == 200:
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

        if r.status_code == 200:
            log.info('logging in returned status code 200')
            self.email = email

            body = r.json()
            self.token = body['token']
            self.headers['authorization'] = self.token

            gateway = requests.get(endpoints.GATEWAY, headers=self.headers)
            if gateway.status_code != 200:
                raise GatewayNotFound()
            self._create_websocket(gateway.json().get('url'), reconnect=False)
            self._is_logged_in = True
        else:
            log.error(request_logging_format.format(name='login', response=r))

    def logout(self):
        """Logs out of Discord and closes all connections."""
        response = requests.post(endpoints.LOGOUT)
        self.ws.close()
        self._is_logged_in = False
        self.keep_alive.stop.set()
        log.debug(request_logging_format.format(name='logout', response=response))

    def logs_from(self, channel, limit=500):
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
        if response.status_code == 200:
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

        if function.__name__ not in self.events:
            raise InvalidEventName('The function name {} is not a valid event name'.format(function.__name__))

        self.events[function.__name__] = function
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
        return response.status_code == 200

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
        return response.status_code == 200

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
        return response.status_code == 200

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
        return response.status_code == 200

    def edit_profile(self, password, **fields):
        """Edits the current profile of the client.

        All fields except password are optional.

        :param password: The current password for the client's account.
        :param new_password: The new password you wish to change to.
        :param email: The new email you wish to change to.
        :param username: The new username you wish to change to.
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

        if response.status_code == 200:
            data = response.json()
            log.debug(request_success_log.format(name='edit_profile', response=response, json=payload, data=data))
            self.token = data['token']
            self.email = data['email']
            self.headers['authorization'] = self.token
            self.user = User(**data)
        else:
            log.debug(request_logging_format.format(response=response, name='edit_profile'))

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
        if response.status_code == 200:
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
        if response.status_code in (200, 201):
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
        return response.status_code == 200

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
        if response.status_code in (200, 201):
            data = response.json()
            log.debug(request_success_log.format(name='create_invite', json=payload, response=response, data=data))
            data['server'] = self._get_server(data['guild']['id'])
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

        destination = None
        if isinstance(invite, Invite):
            destination = invite.id
        else:
            rx = r'(?:https?\:\/\/)?discord\.gg\/(.+)'
            m = re.match(rx, invite)
            if m:
                destination = m.group(1)

        if destination is None:
            return False

        url = '{0}/invite/{1}'.format(endpoints.API_BASE, destination)
        response = requests.post(url, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='accept_invite'))
        return response.status_code in (200, 201)

    def edit_role(self, server, role):
        """Edits the specified :class:`Role` for the entire :class:`Server`.

        To use this you have to edit the role yourself and then pass it
        to this member function. For example: ::

            server = message.channel.server
            role = find(lambda r: r.name == 'My Cool Role', server.roles)
            role.name = 'My Not So Cool Role'
            role.permissions.can_kick_members = False
            role.permissions.can_ban_members = False
            client.edit_role(server, role)

        Note that you cannot edit the name of the @everyone role as that role is special.

        :param server: The :class:`Server` the role belongs to.
        :param role: The :class:`Role` to edit.
        :return: ``True`` if editing was successful, ``False`` otherwise.
        """

        url = '{0}/{1.id}/roles/{2.id}'.format(endpoints.SERVERS, server, role)

        payload = {
            'name': role.name,
            'permissions': role.permissions.value
        }

        response = requests.patch(url, json=payload, headers=self.headers)
        log.debug(request_logging_format.format(response=response, name='edit_role'))
        return response.status_code == 204

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
        return response.status_code == 204
