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
from .utils import parse_time
from .invite import Invite

import requests
import json, re, time, copy
from collections import deque
from threading import Timer
from ws4py.client.threadedclient import WebSocketClient
import sys

def _null_event(*args, **kwargs):
    pass

def _keep_alive_handler(seconds, ws):
    def wrapper():
        _keep_alive_handler(seconds, ws)
        payload = {
            'op': 1,
            'd': int(time.time())
        }

        ws.send(json.dumps(payload))

    t =  Timer(seconds, wrapper)
    t.start()
    return t

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
        return next((m for m in self.messages if m.id == msg_id), None)

    def _get_server(self, guild_id):
        return next((s for s in self.servers if s.id == guild_id), None)

    def _add_server(self, guild):
        guild['roles'] = [Role(**role) for role in guild['roles']]
        members = guild['members']
        owner = guild['owner_id']
        for i, member in enumerate(members):
            roles = member['roles']
            for j, roleid in enumerate(roles):
                role = next((r for r in guild['roles'] if r.id == roleid), None)
                if role is not None:
                    roles[j] = role
            members[i] = Member(**member)

            # found the member that owns the server
            if members[i].id == owner:
                owner = members[i]

        for presence in guild['presences']:
            user_id = presence['user']['id']
            member = next((m for m in members if m.id == user_id), None)
            if member is not None:
                member.status = presence['status']
                member.game_id = presence['game_id']


        server = Server(owner=owner, **guild)

        # give all the members their proper server
        for member in server.members:
            member.server = server

        for channel in guild['channels']:
            changed_roles = []
            permission_overwrites = channel['permission_overwrites']

            for overridden in permission_overwrites:
                # this is pretty inefficient due to the deep nested loops unfortunately
                role = next((role for role in guild['roles'] if role.id == overridden['id']), None)
                if role is None:
                    continue
                denied = overridden.get('deny', 0)
                allowed = overridden.get('allow', 0)
                override = copy.deepcopy(role)

                # Basically this is what's happening here.
                # We have an original bit array, e.g. 1010
                # Then we have another bit array that is 'denied', e.g. 1111
                # And then we have the last one which is 'allowed', e.g. 0101
                # We want original OP denied to end up resulting in whatever is in denied to be set to 0.
                # So 1010 OP 1111 -> 0000
                # Then we take this value and look at the allowed values. And whatever is allowed is set to 1.
                # So 0000 OP2 0101 -> 0101
                # The OP is (base ^ denied) & ~denied.
                # The OP2 is base | allowed.
                override.permissions.value = ((override.permissions.value ^ denied) & ~denied) | allowed
                changed_roles.append(override)

            channel['permission_overwrites'] = changed_roles
        channels = [Channel(server=server, **channel) for channel in guild['channels']]
        server.channels = channels
        self.servers.append(server)

    def _resolve_mentions(self, content, mentions):
        if isinstance(mentions, list):
            return [user.id for user in mentions]
        elif mentions == True:
            return re.findall(r'@<(\d+)>', content)
        else:
            return []

    def _invoke_event(self, event_name, *args, **kwargs):
        try:
            self.events[event_name](*args, **kwargs)
        except Exception as e:
            self.events['on_error'](event_name, *sys.exc_info())


    def _received_message(self, msg):
        response = json.loads(str(msg))
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
            self.keep_alive = _keep_alive_handler(interval, self.ws)

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
                        setattr(message, attr, parse_time(value))
                    else:
                        setattr(message, attr, value)
                self._invoke_event('on_message_edit', older_message, message)
                # update the older message
                older_message = message

        elif event == 'PRESENCE_UPDATE':
            server = self._get_server(data.get('guild_id'))
            if server is not None:
                status = data.get('status')
                member_id = data['user']['id']
                member = next((u for u in server.members if u.id == member_id), None)
                if member is not None:
                    member.status = data.get('status')
                    member.game_id = data.get('game_id')
                    # call the event now
                    self._invoke_event('on_status', member)
        elif event == 'USER_UPDATE':
            self.user = User(**data)
        elif event == 'CHANNEL_DELETE':
            server =  self._get_server(data.get('guild_id'))
            if server is not None:
                channel_id = data.get('id')
                channel = next((c for c in server.channels if c.id == channel_id), None)
                server.channels.remove(channel)
                self._invoke_event('on_channel_delete', channel)
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
            member = Member(deaf=False, mute=False, **data)
            server.members.append(member)
            self._invoke_event('on_member_join', member)
        elif event == 'GUILD_MEMBER_REMOVE':
            server = self._get_server(data.get('guild_id'))
            user_id = data['user']['id']
            member = next((m for m in server.members if m.id == user_id), None)
            server.members.remove(member)
            self._invoke_event('on_member_remove', member)
        elif event == 'GUILD_MEMBER_UPDATE':
            server = self._get_server(data.get('guild_id'))
            user_id = data['user']['id']
            member = next((m for m in server.members if m.id == user_id), None)
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
        print('Opened at {}'.format(int(time.time())))

    def _closed(self, code, reason=None):
        print('Closed with {} ("{}") at {}'.format(code, reason, int(time.time())))
        self._invoke_event('on_disconnect')

    def run(self):
        """Runs the client and allows it to receive messages and events."""
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
            self.private_channels.append(PrivateChannel(id=data['id'], user=user))

    def send_message(self, destination, content, mentions=True):
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
        :return: The :class:`Message` sent or None if error occurred.
        """

        channel_id = ''
        is_private_message = True
        if isinstance(destination, Channel) or isinstance(destination, PrivateChannel):
            channel_id = destination.id
            is_private_message = destination.is_private
        elif isinstance(destination, User):
            found = next((pm for pm in self.private_channels if pm.user == destination), None)
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

        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            channel = self.get_channel(data.get('channel_id'))
            message = Message(channel=channel, **data)
            return message

    def delete_message(self, message):
        """Deletes a :class:`Message`

        A fairly straightforward function.

        :param message: The :class:`Message` to delete.
        """
        url = '{}/{}/messages/{}'.format(endpoints.CHANNELS, message.channel.id, message.id)
        response = requests.delete(url, headers=self.headers)

    def edit_message(self, message, new_content, mentions=True):
        """Edits a :class:`Message` with the new message content.

        The new_content must be able to be transformed into a string via ``str(new_content)``.

        :param message: The :class:`Message` to edit.
        :param new_content: The new content to replace the message with.
        :param mentions: The mentions for the user. Same as :meth:`send_message`.
        :return: The new edited message or None if an error occurred."""
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
            return Message(channel=channel, **data)

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
            self.email = email

            body = r.json()
            self.token = body['token']
            self.headers['authorization'] = self.token

            gateway = requests.get(endpoints.GATEWAY, headers=self.headers)
            if gateway.status_code != 200:
                raise GatewayNotFound()
            gateway_js = gateway.json()
            url = gateway_js.get('url')
            if url is None:
                raise GatewayNotFound()

            self.ws = WebSocketClient(url, protocols=['http-only', 'chat'])

            # this is kind of hacky, but it's to avoid deadlocks.
            # i.e. python does not allow me to have the current thread running if it's self
            # it throws a 'cannot join current thread' RuntimeError
            # So instead of doing a basic inheritance scheme, we're overriding the member functions.

            self.ws.opened = self._opened
            self.ws.closed = self._closed
            self.ws.received_message = self._received_message
            self.ws.connect()

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
            self._is_logged_in = True

    def logout(self):
        """Logs out of Discord and closes all connections."""
        response = requests.post(endpoints.LOGOUT)
        self.ws.close()
        self._is_logged_in = False
        self.keep_alive.cancel()

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
            for message in messages:
                yield Message(channel=channel, **message)

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
        return function

    def create_channel(self, server, name, type='text'):
        """Creates a channel in the specified server.

        In order to create the channel the client must have the proper permissions.

        :param server: The :class:`Server` to create the channel from.
        :param name: The name of the channel to create.
        :param type: The type of channel to create. Valid values are 'text' or 'voice'.
        :returns: The recently created :class:`Channel`.
        """
        url = '{}/{}/channels'.format(endpoints.SERVERS, server.id)
        payload = {
            'name': name,
            'type': type
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            channel = Channel(server=server, **response.json())
            return channel

    def delete_channel(self, channel):
        """Deletes a channel.

        In order to delete the channel, the client must have the proper permissions
        in the server the channel belongs to.

        :param channel: The :class:`Channel` to delete.
        """
        url = '{}/{}'.format(endpoints.CHANNELS, channel.id)
        response = requests.delete(url, headers=self.headers)

    def kick(self, server, user):
        """Kicks a :class:`User` from their respective :class:`Server`.

        You must have the proper permissions to kick a user in the server.

        :param server: The :class:`Server` to kick the member from.
        :param user: The :class:`User` to kick.
        """

        url = '{base}/{server}/members/{user}'.format(base=endpoints.SERVERS, server=server.id, user=user.id)
        response = requests.delete(url, headers=self.headers)

    def ban(self, server, user):
        """Bans a :class:`User` from their respective :class:`Server`.

        You must have the proper permissions to ban a user in the server.

        :param server: The :class:`Server` to ban the member from.
        :param user: The :class:`User` to ban.
        """

        url = '{base}/{server}/bans/{user}'.format(base=endpoints.SERVERS, server=server.id, user=user.id)
        response = requests.put(url, headers=self.headers)

    def unban(self, server, name):
        """Unbans a :class:`User` from their respective :class:`Server`.

        You must have the proper permissions to unban a user in the server.

        :param server: The :class:`Server` to unban the member from.
        :param user: The :class:`User` to unban.
        """

        url = '{base}/{server}/bans/{user}'.format(base=endpoints.SERVERS, server=server.id, user=user.id)
        response = requests.delete(url, headers=self.headers)

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
            self.token = data['token']
            self.email = data['email']
            self.headers['authorization'] = self.token
            self.user = User(**data)

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
            channel = Channel(server=server, **data)
            # We don't append it to server.channels because CHANNEL_CREATE handles it for us.
            return channel

        return None

    def delete_channel(self, channel):
        """Deletes a :class:`Channel` from its respective :class:`Server`.

        Note that you need proper permissions to delete the channel.

        :param channel: The :class:`Channel` to delete.
        """

        url = '{0}/{1.id}'.format(endpoints.CHANNELS, channel)
        requests.delete(url, headers=self.headers)

    def leave_server(self, server):
        """Leaves a :class:`Server`.

        :param server: The :class:`Server` to leave.
        """

        url = '{0}/{1.id}'.format(endpoints.SERVERS, server)
        requests.delete(url, headers=self.headers)

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
            data['server'] = self._get_server(data['guild']['id'])
            data['channel'] = next((ch for ch in data['server'].channels if ch.id == data['channel']['id']))
            return Invite(**data)

        return None

    def accept_invite(self, invite):
        """Accepts an :class:`Invite`.

        :param invite: The :class:`Invite` to accept.
        :returns: True if the invite was successfully accepted, False otherwise.
        """

        url = '{0}/invite/{1.id}'.format(endpoints.API_BASE, invite)
        response = requests.post(url, headers=self.headers)
        return response.status_code in (200, 201)
