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

from .server import Server
from .user import User
from .game import Game
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
        self.max_messages = max_messages
        self.dispatch = dispatch
        self.clear()

    def clear(self):
        self.user = None
        self._servers = {}
        self._private_channels = {}
        # extra dict to look up private channels by user id
        self._private_channels_by_user = {}
        self.messages = deque(maxlen=self.max_messages)

    @property
    def servers(self):
        return self._servers.values()

    def _get_server(self, server_id):
        return self._servers.get(server_id)

    def _add_server(self, server):
        self._servers[server.id] = server

    def _remove_server(self, server):
        self._servers.pop(server.id, None)

    @property
    def private_channels(self):
        return self._private_channels.values()

    def _get_private_channel(self, channel_id):
        return self._private_channels.get(channel_id)

    def _get_private_channel_by_user(self, user_id):
        return self._private_channels_by_user.get(user_id)

    def _add_private_channel(self, channel):
        self._private_channels[channel.id] = channel
        self._private_channels_by_user[channel.user.id] = channel

    def _remove_private_channel(self, channel):
        self._private_channels.pop(channel.id, None)
        self._private_channels_by_user.pop(channel.user.id, None)

    def _get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, self.messages)

    def _add_server_from_data(self, guild):
        server = Server(**guild)
        server.me = server.get_member(self.user.id)
        self._add_server(server)
        return server

    def parse_ready(self, data):
        self.user = User(**data['user'])
        guilds = data.get('guilds')

        for guild in guilds:
            self._add_server_from_data(guild)

        for pm in data.get('private_channels'):
            self._add_private_channel(PrivateChannel(id=pm['id'],
                                     user=User(**pm['recipient'])))

        # we're all ready
        self.dispatch('ready')

    def parse_message_create(self, data):
        channel = self.get_channel(data.get('channel_id'))
        message = Message(channel=channel, **data)
        self.dispatch('message', message)
        self.messages.append(message)

    def parse_message_delete(self, data):
        message_id = data.get('id')
        found = self._get_message(message_id)
        if found is not None:
            self.dispatch('message_delete', found)
            self.messages.remove(found)

    def parse_message_update(self, data):
        older_message = self._get_message(data.get('id'))
        if older_message is not None:
            if 'content' not in data:
                # embed only edit
                message = copy.copy(older_message)
                message.embeds = data['embeds']
            else:
                message = Message(channel=older_message.channel, **data)
            self.dispatch('message_edit', older_message, message)
            # update the older message
            older_message = message

    def parse_presence_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            status = data.get('status')
            user = data['user']
            member_id = user['id']
            member = server.get_member(member_id)
            if member is not None:
                old_member = copy.copy(member)
                member.status = data.get('status')
                try:
                    member.status = Status(member.status)
                except:
                    pass

                game = data.get('game')
                member.game = game and Game(**game)
                member.name = user.get('username', member.name)
                member.avatar = user.get('avatar', member.avatar)

                self.dispatch('member_update', old_member, member)

    def parse_user_update(self, data):
        self.user = User(**data)

    def parse_channel_delete(self, data):
        server =  self._get_server(data.get('guild_id'))
        if server is not None:
            channel_id = data.get('id')
            channel = server.get_channel(channel_id)
            if channel is not None:
                server._remove_channel(channel)
                self.dispatch('channel_delete', channel)

    def parse_channel_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            channel_id = data.get('id')
            channel = server.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                channel._update(server=server, **data)
                self.dispatch('channel_update', old_channel, channel)

    def parse_channel_create(self, data):
        is_private = data.get('is_private', False)
        channel = None
        if is_private:
            recipient = User(**data.get('recipient'))
            pm_id = data.get('id')
            channel = PrivateChannel(id=pm_id, user=recipient)
            self._add_private_channel(channel)
        else:
            server = self._get_server(data.get('guild_id'))
            if server is not None:
                channel = Channel(server=server, **data)
                server._add_channel(channel)

        self.dispatch('channel_create', channel)

    def parse_guild_member_add(self, data):
        server = self._get_server(data.get('guild_id'))
        member = Member(server=server, deaf=False, mute=False, **data)
        member.roles.append(server.default_role)
        server._add_member(member)
        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            user_id = data['user']['id']
            member = server.get_member(user_id)
            if member is not None:
                server._remove_member(member)
                self.dispatch('member_remove', member)

    def parse_guild_member_update(self, data):
        server = self._get_server(data.get('guild_id'))
        user_id = data['user']['id']
        member = server.get_member(user_id)
        if member is not None:
            user = data['user']
            old_member = copy.copy(member)
            member.name = user['username']
            member.discriminator = user['discriminator']
            member.avatar = user['avatar']
            member.roles = [server.default_role]
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

        server = self._add_server_from_data(data)
        self.dispatch('server_join', server)

    def parse_guild_update(self, data):
        server = self._get_server(data.get('id'))
        if server is not None:
            old_server = copy.copy(server)
            server._from_data(data)
            self.dispatch('server_update', old_server, server)

    def parse_guild_delete(self, data):
        server = self._get_server(data.get('id'))
        if server is None:
            return

        if data.get('unavailable', False) and server is not None:
            # GUILD_DELETE with unavailable being True means that the
            # server that was available is now currently unavailable
            server.unavailable = True
            self.dispatch('server_unavailable', server)
            return

        # do a cleanup of the messages cache
        self.messages = deque((msg for msg in self.messages if msg.server != server), maxlen=self.max_messages)

        self._remove_server(server)
        self.dispatch('server_remove', server)


    def parse_guild_ban_add(self, data):
        # we make the assumption that GUILD_BAN_ADD is done
        # before GUILD_MEMBER_REMOVE is called
        # hence we don't remove it from cache or do anything
        # strange with it, the main purpose of this event
        # is mainly to dispatch to another event worth listening to for logging
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            user_id = data.get('user', {}).get('id')
            member = utils.get(server.members, id=user_id)
            if member is not None:
                self.dispatch('member_ban', member)

    def parse_guild_ban_remove(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            if 'user' in data:
                user = User(**data['user'])
                self.dispatch('member_unban', server, user)

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
            if role is not None:
                old_role = copy.copy(role)
                role._update(**data['role'])
                self.dispatch('server_role_update', old_role, role)

    def parse_voice_state_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            updated_members = server._update_voice_state(data)
            self.dispatch('voice_state_update', *updated_members)

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
                member = channel.server.get_member(user_id)

            if member is not None:
                timestamp = datetime.datetime.utcfromtimestamp(data.get('timestamp'))
                self.dispatch('typing', channel, member, timestamp)

    def get_channel(self, id):
        if id is None:
            return None

        for server in self.servers:
            channel = server.get_channel(id)
            if channel is not None:
                return channel

        pm = self._get_private_channel(id)
        if pm is not None:
            return pm
