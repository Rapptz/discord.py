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

import requests
import json, re
import endpoints
from collections import deque
from ws4py.client.threadedclient import WebSocketClient
from sys import platform as sys_platform
from errors import InvalidEventName, InvalidDestination
from user import User
from channel import Channel, PrivateChannel
from server import Server
from message import Message

def _null_event(*args, **kwargs):
    pass

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

    .. _deque: https://docs.python.org/3.4/library/collections.html#collections.deque
    """

    def __init__(self, **kwargs):
        self._is_logged_in = False
        self.user = None
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
            'on_message_delete': _null_event
        }

        self.ws = WebSocketClient(endpoints.WEBSOCKET_HUB, protocols=['http-only', 'chat'])

        # this is kind of hacky, but it's to avoid deadlocks.
        # i.e. python does not allow me to have the current thread running if it's self
        # it throws a 'cannot join current thread' RuntimeError
        # So instead of doing a basic inheritance scheme, we're overriding the member functions.

        self.ws.opened = self._opened
        self.ws.closed = self._closed
        self.ws.received_message = self._received_message
        self.ws.connect()

        # the actual headers for the request...
        # we only override 'authorization' since the rest could use the defaults.
        self.headers = {
            'authorization': self.token,
        }

    def _received_message(self, msg):
        response = json.loads(str(msg))
        if response.get('op') != 0:
            return

        self.events['on_response'](response)
        event = response.get('t')
        data = response.get('d')

        if event == 'READY':
            self.user = User(**data['user'])
            guilds = data.get('guilds')

            for guild in guilds:
                guild['roles'] = [role.get('name') for role in guild['roles']]
                guild['members'] = [User(**member['user']) for member in guild['members']]

                self.servers.append(Server(**guild))
                channels = [Channel(server=self.servers[-1], **channel) for channel in guild['channels']]
                self.servers[-1].channels = channels

            for pm in data.get('private_channels'):
                self.private_channels.append(PrivateChannel(id=pm['id'], user=User(**pm['recipient'])))

            # set the keep alive interval..
            self.ws.heartbeat_freq = data.get('heartbeat_interval')

            # we're all ready
            self.events['on_ready']()
        elif event == 'MESSAGE_CREATE':
            channel = self.get_channel(data.get('channel_id'))
            message = Message(channel=channel, **data)
            self.events['on_message'](message)
            self.messages.append(message)
        elif event == 'MESSAGE_DELETE':
            channel = self.get_channel(data.get('channel_id'))
            message_id = data.get('id')
            found = next((m for m in self.messages if m.id == message_id), None)
            if found is not None:
                self.events['on_message_delete'](found)
                self.messages.remove(found)

    def _opened(self):
        print('Opened!')

    def _closed(self, code, reason=None):
        print('closed with ', code, reason)

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

        r = response.post('{}/{}/channels'.format(endpoints.USERS, self.user.id), json=payload, headers=self.headers)
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

        if isinstance(mentions, list):
            mentions = [user.id for user in mentions]
        elif mentions == True:
            mentions = re.findall(r'@<(\d+)>', content)
        else:
            mentions = []

        url = '{base}/{id}/messages'.format(base=endpoints.CHANNELS, id=channel_id)
        payload = {
            'content': content,
        }

        if not is_private_message:
            payload['mentions'] = mentions

        response = requests.post(url, json=payload, headers=self.headers)


    def login(self, email, password):
        """Logs in the user with the following credentials.

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
            body = r.json()
            self.token = body['token']
            self.headers['authorization'] = self.token
            second_payload = {
                'op': 2,
                'd': {
                    'token': self.token,
                    'properties': {
                        '$os': sys_platform,
                        '$browser': 'pydiscord',
                        '$device': 'pydiscord',
                        '$referrer': '',
                        '$referring_domain': ''
                    }
                }
            }

            self.ws.send(json.dumps(second_payload))
            self._is_logged_in = True

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

