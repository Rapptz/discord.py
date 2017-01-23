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
from .emoji import Emoji
from .reaction import Reaction
from .message import Message
from .channel import Channel, PrivateChannel
from .member import Member
from .role import Role
from . import utils, compat
from .enums import Status, ChannelType, try_enum
from .calls import GroupCall

from collections import deque, namedtuple
import copy, enum, math
import datetime
import asyncio
import logging

class ListenerType(enum.Enum):
    chunk = 0

Listener = namedtuple('Listener', ('type', 'future', 'predicate'))
log = logging.getLogger(__name__)
ReadyState = namedtuple('ReadyState', ('launch', 'servers'))

class ConnectionState:
    def __init__(self, dispatch, chunker, syncer, max_messages, *, loop):
        self.loop = loop
        self.max_messages = max_messages
        self.dispatch = dispatch
        self.chunker = chunker
        self.syncer = syncer
        self.is_bot = None
        self._listeners = []
        self.clear()

    def clear(self):
        self.user = None
        self.sequence = None
        self.session_id = None
        self._calls = {}
        self._servers = {}
        self._voice_clients = {}
        self._private_channels = {}
        # extra dict to look up private channels by user id
        self._private_channels_by_user = {}
        self.messages = deque(maxlen=self.max_messages)

    def process_listeners(self, listener_type, argument, result):
        removed = []
        for i, listener in enumerate(self._listeners):
            if listener.type != listener_type:
                continue

            future = listener.future
            if future.cancelled():
                removed.append(i)
                continue

            try:
                passed = listener.predicate(argument)
            except Exception as e:
                future.set_exception(e)
                removed.append(i)
            else:
                if passed:
                    future.set_result(result)
                    removed.append(i)
                    if listener.type == ListenerType.chunk:
                        break

        for index in reversed(removed):
            del self._listeners[index]

    @property
    def voice_clients(self):
        return self._voice_clients.values()

    def _get_voice_client(self, guild_id):
        return self._voice_clients.get(guild_id)

    def _add_voice_client(self, guild_id, voice):
        self._voice_clients[guild_id] = voice

    def _remove_voice_client(self, guild_id):
        self._voice_clients.pop(guild_id, None)

    def _update_references(self, ws):
        for vc in self.voice_clients:
            vc.main_ws = ws

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
        if channel.type is ChannelType.private:
            self._private_channels_by_user[channel.user.id] = channel

    def _remove_private_channel(self, channel):
        self._private_channels.pop(channel.id, None)
        if channel.type is ChannelType.private:
            self._private_channels_by_user.pop(channel.user.id, None)

    def _get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, self.messages)

    def _add_server_from_data(self, guild):
        server = Server(**guild)
        Server.me = property(lambda s: s.get_member(self.user.id))
        Server.voice_client = property(lambda s: self._get_voice_client(s.id))
        self._add_server(server)
        return server

    def chunks_needed(self, server):
        for chunk in range(math.ceil(server._member_count / 1000)):
            yield self.receive_chunk(server.id)

    @asyncio.coroutine
    def _delay_ready(self):
        launch = self._ready_state.launch
        while not launch.is_set():
            # this snippet of code is basically waiting 2 seconds
            # until the last GUILD_CREATE was sent
            launch.set()
            yield from asyncio.sleep(2, loop=self.loop)

        servers = self._ready_state.servers

        # get all the chunks
        chunks = []
        for server in servers:
            chunks.extend(self.chunks_needed(server))

        # we only want to request ~75 guilds per chunk request.
        splits = [servers[i:i + 75] for i in range(0, len(servers), 75)]
        for split in splits:
            yield from self.chunker(split)

        # wait for the chunks
        if chunks:
            try:
                yield from asyncio.wait(chunks, timeout=len(chunks) * 30.0, loop=self.loop)
            except asyncio.TimeoutError:
                log.info('Somehow timed out waiting for chunks.')

        # remove the state
        try:
            del self._ready_state
        except AttributeError:
            pass # already been deleted somehow

        # call GUILD_SYNC after we're done chunking
        if not self.is_bot:
            log.info('Requesting GUILD_SYNC for %s guilds' % len(self.servers))
            yield from self.syncer([s.id for s in self.servers])

        # dispatch the event
        self.dispatch('ready')

    def parse_ready(self, data):
        self._ready_state = ReadyState(launch=asyncio.Event(), servers=[])
        self.user = User(**data['user'])
        guilds = data.get('guilds')

        servers = self._ready_state.servers
        for guild in guilds:
            server = self._add_server_from_data(guild)
            if (not self.is_bot and not server.unavailable) or server.large:
                servers.append(server)

        for pm in data.get('private_channels'):
            self._add_private_channel(PrivateChannel(self.user, **pm))

        compat.create_task(self._delay_ready(), loop=self.loop)

    def parse_resumed(self, data):
        self.dispatch('resumed')

    def parse_message_create(self, data):
        channel = self.get_channel(data.get('channel_id'))
        message = self._create_message(channel=channel, **data)
        self.dispatch('message', message)
        self.messages.append(message)

    def parse_message_delete(self, data):
        message_id = data.get('id')
        found = self._get_message(message_id)
        if found is not None:
            self.dispatch('message_delete', found)
            self.messages.remove(found)

    def parse_message_delete_bulk(self, data):
        message_ids = set(data.get('ids', []))
        to_be_deleted = list(filter(lambda m: m.id in message_ids, self.messages))
        for msg in to_be_deleted:
            self.dispatch('message_delete', msg)
            self.messages.remove(msg)

    def parse_message_update(self, data):
        message = self._get_message(data.get('id'))
        if message is not None:
            older_message = copy.copy(message)
            if 'call' in data:
                # call state message edit
                message._handle_call(data['call'])
            elif 'content' not in data:
                # embed only edit
                message.embeds = data['embeds']
            else:
                message._update(channel=message.channel, **data)

            self.dispatch('message_edit', older_message, message)

    def parse_message_reaction_add(self, data):
        message = self._get_message(data['message_id'])
        if message is not None:
            emoji = self._get_reaction_emoji(**data.pop('emoji'))
            reaction = utils.get(message.reactions, emoji=emoji)

            is_me = data['user_id'] == self.user.id

            if not reaction:
                reaction = Reaction(
                    message=message, emoji=emoji, me=is_me, **data)
                message.reactions.append(reaction)
            else:
                reaction.count += 1
                if is_me:
                    reaction.me = True

            channel = self.get_channel(data['channel_id'])
            member = self._get_member(channel, data['user_id'])

            self.dispatch('reaction_add', reaction, member)

    def parse_message_reaction_remove_all(self, data):
        message =  self._get_message(data['message_id'])
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch('reaction_clear', message, old_reactions)

    def parse_message_reaction_remove(self, data):
        message = self._get_message(data['message_id'])
        if message is not None:
            emoji = self._get_reaction_emoji(**data['emoji'])
            reaction = utils.get(message.reactions, emoji=emoji)

            # Eventual consistency means we can get out of order or duplicate removes.
            if not reaction:
                log.warning("Unexpected reaction remove {}".format(data))
                return

            reaction.count -= 1
            if data['user_id'] == self.user.id:
                reaction.me = False
            if reaction.count == 0:
                message.reactions.remove(reaction)

            channel = self.get_channel(data['channel_id'])
            member = self._get_member(channel, data['user_id'])

            self.dispatch('reaction_remove', reaction, member)

    def parse_presence_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is None:
            return

        status = data.get('status')
        user = data['user']
        member_id = user['id']
        member = server.get_member(member_id)
        if member is None:
            if 'username' not in user:
                # sometimes we receive 'incomplete' member data post-removal.
                # skip these useless cases.
                return

            member = self._make_member(server, data)
            server._add_member(member)

        old_member = member._copy()
        member.status = data.get('status')
        try:
            member.status = Status(member.status)
        except:
            pass

        game = data.get('game', {})
        member.game = Game(**game) if game else None
        member.name = user.get('username', member.name)
        member.avatar = user.get('avatar', member.avatar)
        member.discriminator = user.get('discriminator', member.discriminator)

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
        channel_type = try_enum(ChannelType, data.get('type'))
        channel_id = data.get('id')
        if channel_type is ChannelType.group:
            channel = self._get_private_channel(channel_id)
            old_channel = copy.copy(channel)
            channel._update_group(**data)
            self.dispatch('channel_update', old_channel, channel)
            return

        server = self._get_server(data.get('guild_id'))
        if server is not None:
            channel = server.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                channel._update(server=server, **data)
                self.dispatch('channel_update', old_channel, channel)

    def parse_channel_create(self, data):
        ch_type = try_enum(ChannelType, data.get('type'))
        channel = None
        if ch_type in (ChannelType.group, ChannelType.private):
            channel = PrivateChannel(self.user, **data)
            self._add_private_channel(channel)
        else:
            server = self._get_server(data.get('guild_id'))
            if server is not None:
                channel = Channel(server=server, **data)
                server._add_channel(channel)

        self.dispatch('channel_create', channel)

    def parse_channel_recipient_add(self, data):
        channel = self._get_private_channel(data.get('channel_id'))
        user = User(**data.get('user', {}))
        channel.recipients.append(user)
        self.dispatch('group_join', channel, user)

    def parse_channel_recipient_remove(self, data):
        channel = self._get_private_channel(data.get('channel_id'))
        user = User(**data.get('user', {}))
        try:
            channel.recipients.remove(user)
        except ValueError:
            pass
        else:
            self.dispatch('group_remove', channel, user)

    def _make_member(self, server, data):
        roles = [server.default_role]
        for roleid in data.get('roles', []):
            role = utils.get(server.roles, id=roleid)
            if role is not None:
                roles.append(role)

        data['roles'] = sorted(roles, key=lambda r: int(r.id))
        return Member(server=server, **data)

    def parse_guild_member_add(self, data):
        server = self._get_server(data.get('guild_id'))
        member = self._make_member(server, data)
        server._add_member(member)
        server._member_count += 1
        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            user_id = data['user']['id']
            member = server.get_member(user_id)
            if member is not None:
                server._remove_member(member)
                server._member_count -= 1

                # remove them from the voice channel member list
                vc = member.voice_channel
                if vc is not None:
                    try:
                        vc.voice_members.remove(member)
                    except:
                        pass

                self.dispatch('member_remove', member)

    def parse_guild_member_update(self, data):
        server = self._get_server(data.get('guild_id'))
        user_id = data['user']['id']
        member = server.get_member(user_id)
        if member is not None:
            user = data['user']
            old_member = member._copy()
            member.name = user['username']
            member.discriminator = user['discriminator']
            member.avatar = user['avatar']
            member.bot = user.get('bot', False)

            # the nickname change is optional,
            # if it isn't in the payload then it didn't change
            if 'nick' in data:
                member.nick = data['nick']

            # update the roles
            member.roles = [server.default_role]
            for role in server.roles:
                if role.id in data['roles']:
                    member.roles.append(role)

            # sort the roles by ID since they can be "randomised"
            member.roles.sort(key=lambda r: int(r.id))
            self.dispatch('member_update', old_member, member)

    def parse_guild_emojis_update(self, data):
        server = self._get_server(data.get('guild_id'))
        before_emojis = server.emojis
        server.emojis = [Emoji(server=server, **e) for e in data.get('emojis', [])]
        self.dispatch('server_emojis_update', before_emojis, server.emojis)

    def _get_create_server(self, data):
        if data.get('unavailable') == False:
            # GUILD_CREATE with unavailable in the response
            # usually means that the server has become available
            # and is therefore in the cache
            server = self._get_server(data.get('id'))
            if server is not None:
                server.unavailable = False
                server._from_data(data)
                return server

        return self._add_server_from_data(data)

    @asyncio.coroutine
    def _chunk_and_dispatch(self, server, unavailable):
        chunks = list(self.chunks_needed(server))
        yield from self.chunker(server)
        if chunks:
            try:
                yield from asyncio.wait(chunks, timeout=len(chunks), loop=self.loop)
            except asyncio.TimeoutError:
                log.info('Somehow timed out waiting for chunks.')

        if unavailable == False:
            self.dispatch('server_available', server)
        else:
            self.dispatch('server_join', server)

    def parse_guild_create(self, data):
        unavailable = data.get('unavailable')
        if unavailable == True:
            # joined a server with unavailable == True so..
            return

        server = self._get_create_server(data)

        # check if it requires chunking
        if server.large:
            if unavailable == False:
                # check if we're waiting for 'useful' READY
                # and if we are, we don't want to dispatch any
                # event such as server_join or server_available
                # because we're still in the 'READY' phase. Or
                # so we say.
                try:
                    state = self._ready_state
                    state.launch.clear()
                    state.servers.append(server)
                except AttributeError:
                    # the _ready_state attribute is only there during
                    # processing of useful READY.
                    pass
                else:
                    return

            # since we're not waiting for 'useful' READY we'll just
            # do the chunk request here
            compat.create_task(self._chunk_and_dispatch(server, unavailable), loop=self.loop)
            return

        # Dispatch available if newly available
        if unavailable == False:
            self.dispatch('server_available', server)
        else:
            self.dispatch('server_join', server)

    def parse_guild_sync(self, data):
        server = self._get_server(data.get('id'))
        server._sync(data)

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
        role = Role(server=server, **role_data)
        server._add_role(role)
        self.dispatch('server_role_create', role)

    def parse_guild_role_delete(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            role_id = data.get('role_id')
            role = utils.find(lambda r: r.id == role_id, server.roles)
            try:
                server._remove_role(role)
            except ValueError:
                return
            else:
                self.dispatch('server_role_delete', role)

    def parse_guild_role_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            role_id = data['role']['id']
            role = utils.find(lambda r: r.id == role_id, server.roles)
            if role is not None:
                old_role = copy.copy(role)
                role._update(**data['role'])
                self.dispatch('server_role_update', old_role, role)

    def parse_guild_members_chunk(self, data):
        server = self._get_server(data.get('guild_id'))
        members = data.get('members', [])
        for member in members:
            m = self._make_member(server, member)
            existing = server.get_member(m.id)
            if existing is None or existing.joined_at is None:
                server._add_member(m)

        # if the owner is offline, server.owner is potentially None
        # therefore we should check if this chunk makes it point to a valid
        # member.
        server.owner = server.get_member(server.owner_id)
        log.info('processed a chunk for {} members.'.format(len(members)))
        self.process_listeners(ListenerType.chunk, server, len(members))

    def parse_voice_state_update(self, data):
        server = self._get_server(data.get('guild_id'))
        if server is not None:
            channel = server.get_channel(data.get('channel_id'))
            if data.get('user_id') == self.user.id:
                voice = self._get_voice_client(server.id)
                if voice is not None:
                    voice.channel = channel

            before, after = server._update_voice_state(data)
            if after is not None:
                self.dispatch('voice_state_update', before, after)
        else:
            # in here we're either at private or group calls
            call = self._calls.get(data.get('channel_id'), None)
            if call is not None:
                call._update_voice_state(data)

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

    def parse_call_create(self, data):
        message = self._get_message(data.get('message_id'))
        if message is not None:
            call = GroupCall(call=message, **data)
            self._calls[data['channel_id']] = call
            self.dispatch('call', call)

    def parse_call_update(self, data):
        call = self._calls.get(data.get('channel_id'), None)
        if call is not None:
            before = copy.copy(call)
            call._update(**data)
            self.dispatch('call_update', before, call)

    def parse_call_delete(self, data):
        call = self._calls.pop(data.get('channel_id'), None)
        if call is not None:
            self.dispatch('call_remove', call)

    def _get_member(self, channel, id):
        if channel.is_private:
            if id == self.user.id:
                return self.user
            return utils.get(channel.recipients, id=id)
        else:
            return channel.server.get_member(id)

    def _create_message(self, **message):
        """Helper mostly for injecting reactions."""
        reactions = [
            self._create_reaction(**r) for r in message.pop('reactions', [])
        ]
        return Message(channel=message.pop('channel'),
                       reactions=reactions, **message)

    def _create_reaction(self, **reaction):
        emoji = self._get_reaction_emoji(**reaction.pop('emoji'))
        return Reaction(emoji=emoji, **reaction)

    def _get_reaction_emoji(self, **data):
        id = data['id']

        if not id:
            return data['name']

        for server in self.servers:
            for emoji in server.emojis:
                if emoji.id == id:
                    return emoji
        return Emoji(server=None, **data)

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

    def receive_chunk(self, guild_id):
        future = asyncio.Future(loop=self.loop)
        listener = Listener(ListenerType.chunk, future, lambda s: s.id == guild_id)
        self._listeners.append(listener)
        return future
