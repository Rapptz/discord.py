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

from .server import Server
from .user import User
from .message import Message
from .channel import Channel, PrivateChannel
from .member import Member
from .role import Role
from . import utils
from .enums import Status

from collections import deque
import copy
import datetime

class ConnectionState:
    def __init__(self, dispatch, max_messages):
        self.user = None
        self.email = None
        self.servers = []
        self.private_channels = []
        self.messages = deque(maxlen=max_messages)
        self.dispatch = dispatch

    def _get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, self.messages)

    def _get_server(self, guild_id):
        return utils.find(lambda g: g.id == guild_id, self.servers)

    def _add_server(self, guild):
        server = Server(**guild)
        self.servers.append(server)
        return server

    def parse_ready(self, data):
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

    def parse_message_create(self, data):
        channel = self.get_channel(data.get('channel_id'))
        message = Message(channel=channel, **data)
        self.dispatch('message', message)
        self.messages.append(message)

    def parse_message_delete(self, data):
        channel = self.get_channel(data.get('channel_id'))
        message_id = data.get('id')
        found = self._get_message(message_id)
        if found is not None:
            self.dispatch('message_delete', found)
            self.messages.remove(found)

    def parse_message_update(self, data):
        older_message = self._get_message(data.get('id'))
        if older_message is not None:
            # create a copy of the new message
            message = copy.copy(older_message)
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

    def parse_presence_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            status = data.get('status')
            user = data['user']
            member_id = user['id']
            member = utils.find(lambda m: m.id == member_id, server.members)
            if member is not None:
                old_member = copy.copy(member)
                member.status = data.get('status')
                try:
                    member.status = Status(member.status)
                except:
                    pass
                member.game_id = data.get('game_id')
                member.name = user.get('username', member.name)
                member.avatar = user.get('avatar', member.avatar)

                # call the event now
                self.dispatch('status', member, old_member.game_id, old_member.status)
                self.dispatch('member_update', old_member, member)

    def parse_user_update(self, data):
        self.user = User(**data)

    def parse_channel_delete(self, data):
        server =  self._get_server(data.get('guild_id'))
        if server is not None:
            channel_id = data.get('id')
            channel = utils.find(lambda c: c.id == channel_id, server.channels)
            try:
                server.channels.remove(channel)
            except ValueError:
                return
            else:
                self.dispatch('channel_delete', channel)

    def parse_channel_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            channel_id = data.get('id')
            channel = utils.find(lambda c: c.id == channel_id, server.channels)
            channel.update(server=server, **data)
            self.dispatch('channel_update', channel)

    def parse_channel_create(self, data):
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

    def parse_guild_member_add(self, data):
        server = self._get_server(data.get('guild_id'))
        member = Member(server=server, deaf=False, mute=False, **data)
        member.roles.append(server.get_default_role())
        server.members.append(member)
        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            user_id = data['user']['id']
            member = utils.find(lambda m: m.id == user_id, server.members)
            try:
                server.members.remove(member)
            except ValueError:
                return
            else:
                self.dispatch('member_remove', member)

    def parse_guild_member_update(self, data):
        server = self._get_server(data.get('guild_id'))
        user_id = data['user']['id']
        member = utils.find(lambda m: m.id == user_id, server.members)
        if member is not None:
            user = data['user']
            old_member = copy.copy(member)
            member.name = user['username']
            member.discriminator = user['discriminator']
            member.avatar = user['avatar']
            member.roles = [server.get_default_role()]
            # update the roles
            for role in server.roles:
                if role.id in data['roles']:
                    member.roles.append(role)

            self.dispatch('member_update', old_member, member)

    def parse_guild_create(self, data):
        unavailable = data.get('unavailable')
        if unavailable == False:
            # GUILD_CREATE with unavailable in the response
            # usually means that the server has become available
            # and is therefore in the cache
            server = self._get_server(data.get('id'))
            if server is not None:
                server.unavailable = False
                self.dispatch('server_available', server)
                return

        if unavailable == True:
            # joined a server with unavailable == True so..
            return

            # if we're at this point then it was probably
            # unavailable during the READY event and is now
            # available, so it isn't in the cache...

        server = self._add_server(data)
        self.dispatch('server_join', server)

    def parse_guild_update(self, data):
        server = self._get_server(data.get('id'))
        if server is not None:
            old_server = copy.copy(server)
            server._from_data(data)
            self.dispatch('server_update', old_server, server)

    def parse_guild_delete(self, data):
        server = self._get_server(data.get('id'))
        if data.get('unavailable', False) and server is not None:
            # GUILD_DELETE with unavailable being True means that the
            # server that was available is now currently unavailable
            server.unavailable = True
            self.dispatch('server_unavailable', server)
            return

        try:
            self.servers.remove(server)
        except ValueError:
            return
        else:
            self.dispatch('server_remove', server)

    def parse_guild_role_create(self, data):
        server = self._get_server(data.get('guild_id'))
        role_data = data.get('role', {})
        everyone = server.id == role_data.get('id')
        role = Role(everyone=everyone, **role_data)
        server.roles.append(role)
        self.dispatch('server_role_create', server, role)

    def parse_guild_role_delete(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            role_id = data.get('role_id')
            role = utils.find(lambda r: r.id == role_id, server.roles)
            try:
                server.roles.remove(role)
            except ValueError:
                return
            else:
                self.dispatch('server_role_delete', server, role)

    def parse_guild_role_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            role_id = data['role']['id']
            role = utils.find(lambda r: r.id == role_id, server.roles)
            role.update(**data['role'])
            self.dispatch('server_role_update', role)

    def parse_voice_state_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            updated_member = server._update_voice_state(data)
            self.dispatch('voice_state_update', updated_member)

    def parse_typing_start(self, data):
        channel = self.get_channel(data.get('channel_id'))
        if channel is not None:
            member = None
            user_id = data.get('user_id')
            is_private = getattr(channel, 'is_private', None)
            if is_private == None:
                return

            if is_private:
                member = channel.user
            else:
                members = channel.server.members
                member = utils.find(lambda m: m.id == user_id, members)

            if member is not None:
                timestamp = datetime.datetime.utcfromtimestamp(data.get('timestamp'))
                self.dispatch('typing', channel, member, timestamp)

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
