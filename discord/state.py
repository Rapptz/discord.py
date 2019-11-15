# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

import asyncio
from collections import deque, namedtuple, OrderedDict
import copy
import datetime
import itertools
import logging
import math
import weakref
import inspect

from .guild import Guild
from .activity import _ActivityTag
from .user import User, ClientUser
from .emoji import Emoji, PartialEmoji
from .message import Message
from .relationship import Relationship
from .channel import *
from .raw_models import *
from .member import Member
from .role import Role
from .enums import ChannelType, try_enum, Status, Enum
from . import utils
from .embeds import Embed
from .object import Object

class ListenerType(Enum):
    chunk = 0

Listener = namedtuple('Listener', ('type', 'future', 'predicate'))
log = logging.getLogger(__name__)
ReadyState = namedtuple('ReadyState', ('launch', 'guilds'))

class ConnectionState:
    def __init__(self, *, dispatch, chunker, handlers, syncer, http, loop, **options):
        self.loop = loop
        self.http = http
        self.max_messages = max(options.get('max_messages', 5000), 100)
        self.dispatch = dispatch
        self.chunker = chunker
        self.syncer = syncer
        self.is_bot = None
        self.handlers = handlers
        self.shard_count = None
        self._ready_task = None
        self._fetch_offline = options.get('fetch_offline_members', True)
        self.heartbeat_timeout = options.get('heartbeat_timeout', 60.0)
        self._listeners = []

        activity = options.get('activity', None)
        if activity:
            if not isinstance(activity, _ActivityTag):
                raise TypeError('activity parameter must be one of Game, Streaming, or Activity.')

            activity = activity.to_dict()

        status = options.get('status', None)
        if status:
            if status is Status.offline:
                status = 'invisible'
            else:
                status = str(status)

        self._activity = activity
        self._status = status

        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func

        self.clear()

    def clear(self):
        self.user = None
        self._users = weakref.WeakValueDictionary()
        self._emojis = {}
        self._calls = {}
        self._guilds = {}
        self._voice_clients = {}

        # LRU of max size 128
        self._private_channels = OrderedDict()
        # extra dict to look up private channels by user id
        self._private_channels_by_user = {}
        self._messages = deque(maxlen=self.max_messages)

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
            except Exception as exc:
                future.set_exception(exc)
                removed.append(i)
            else:
                if passed:
                    future.set_result(result)
                    removed.append(i)
                    if listener.type == ListenerType.chunk:
                        break

        for index in reversed(removed):
            del self._listeners[index]

    def call_handlers(self, key, *args, **kwargs):
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    @property
    def self_id(self):
        u = self.user
        return u.id if u else None

    @property
    def voice_clients(self):
        return list(self._voice_clients.values())

    def _get_voice_client(self, guild_id):
        return self._voice_clients.get(guild_id)

    def _add_voice_client(self, guild_id, voice):
        self._voice_clients[guild_id] = voice

    def _remove_voice_client(self, guild_id):
        self._voice_clients.pop(guild_id, None)

    def _update_references(self, ws):
        for vc in self.voice_clients:
            vc.main_ws = ws

    def store_user(self, data):
        # this way is 300% faster than `dict.setdefault`.
        user_id = int(data['id'])
        try:
            return self._users[user_id]
        except KeyError:
            user = User(state=self, data=data)
            if user.discriminator != '0000':
                self._users[user_id] = user
            return user

    def get_user(self, id):
        return self._users.get(id)

    def store_emoji(self, guild, data):
        emoji_id = int(data['id'])
        self._emojis[emoji_id] = emoji = Emoji(guild=guild, state=self, data=data)
        return emoji

    @property
    def guilds(self):
        return list(self._guilds.values())

    def _get_guild(self, guild_id):
        return self._guilds.get(guild_id)

    def _add_guild(self, guild):
        self._guilds[guild.id] = guild

    def _remove_guild(self, guild):
        self._guilds.pop(guild.id, None)

        for emoji in guild.emojis:
            self._emojis.pop(emoji.id, None)

        del guild

    @property
    def emojis(self):
        return list(self._emojis.values())

    def get_emoji(self, emoji_id):
        return self._emojis.get(emoji_id)

    @property
    def private_channels(self):
        return list(self._private_channels.values())

    def _get_private_channel(self, channel_id):
        try:
            value = self._private_channels[channel_id]
        except KeyError:
            return None
        else:
            self._private_channels.move_to_end(channel_id)
            return value

    def _get_private_channel_by_user(self, user_id):
        return self._private_channels_by_user.get(user_id)

    def _add_private_channel(self, channel):
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if self.is_bot and len(self._private_channels) > 128:
            _, to_remove = self._private_channels.popitem(last=False)
            if isinstance(to_remove, DMChannel):
                self._private_channels_by_user.pop(to_remove.recipient.id, None)

        if isinstance(channel, DMChannel):
            self._private_channels_by_user[channel.recipient.id] = channel

    def add_dm_channel(self, data):
        channel = DMChannel(me=self.user, state=self, data=data)
        self._add_private_channel(channel)
        return channel

    def _remove_private_channel(self, channel):
        self._private_channels.pop(channel.id, None)
        if isinstance(channel, DMChannel):
            self._private_channels_by_user.pop(channel.recipient.id, None)

    def _get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, reversed(self._messages))

    def _add_guild_from_data(self, guild):
        guild = Guild(data=guild, state=self)
        self._add_guild(guild)
        return guild

    def chunks_needed(self, guild):
        for _ in range(math.ceil(guild._member_count / 1000)):
            yield self.receive_chunk(guild.id)

    def _get_guild_channel(self, data):
        channel_id = int(data['channel_id'])
        try:
            guild = self._get_guild(int(data['guild_id']))
        except KeyError:
            channel = self.get_channel(channel_id)
            guild = None
        else:
            channel = guild and guild.get_channel(channel_id)

        return channel or Object(id=channel_id), guild

    async def request_offline_members(self, guilds):
        # get all the chunks
        chunks = []
        for guild in guilds:
            chunks.extend(self.chunks_needed(guild))

        # we only want to request ~75 guilds per chunk request.
        splits = [guilds[i:i + 75] for i in range(0, len(guilds), 75)]
        for split in splits:
            await self.chunker(split)

        # wait for the chunks
        if chunks:
            try:
                await utils.sane_wait_for(chunks, timeout=len(chunks) * 30.0, loop=self.loop)
            except asyncio.TimeoutError:
                log.info('Somehow timed out waiting for chunks.')

    async def _delay_ready(self):
        try:
            launch = self._ready_state.launch

            # only real bots wait for GUILD_CREATE streaming
            if self.is_bot:
                while not launch.is_set():
                    # this snippet of code is basically waiting 2 seconds
                    # until the last GUILD_CREATE was sent
                    launch.set()
                    await asyncio.sleep(2, loop=self.loop)

            guilds = next(zip(*self._ready_state.guilds), [])
            if self._fetch_offline:
                await self.request_offline_members(guilds)

            for guild, unavailable in self._ready_state.guilds:
                if unavailable is False:
                    self.dispatch('guild_available', guild)
                else:
                    self.dispatch('guild_join', guild)

            # remove the state
            try:
                del self._ready_state
            except AttributeError:
                pass # already been deleted somehow

            # call GUILD_SYNC after we're done chunking
            if not self.is_bot:
                log.info('Requesting GUILD_SYNC for %s guilds', len(self.guilds))
                await self.syncer([s.id for s in self.guilds])
        except asyncio.CancelledError:
            pass
        else:
            # dispatch the event
            self.call_handlers('ready')
            self.dispatch('ready')
        finally:
            self._ready_task = None

    def parse_ready(self, data):
        if self._ready_task is not None:
            self._ready_task.cancel()

        self._ready_state = ReadyState(launch=asyncio.Event(), guilds=[])
        self.clear()
        self.user = user = ClientUser(state=self, data=data['user'])
        self._users[user.id] = user

        guilds = self._ready_state.guilds
        for guild_data in data['guilds']:
            guild = self._add_guild_from_data(guild_data)
            if (not self.is_bot and not guild.unavailable) or guild.large:
                guilds.append((guild, guild.unavailable))

        for relationship in data.get('relationships', []):
            try:
                r_id = int(relationship['id'])
            except KeyError:
                continue
            else:
                user._relationships[r_id] = Relationship(state=self, data=relationship)

        for pm in data.get('private_channels', []):
            factory, _ = _channel_factory(pm['type'])
            self._add_private_channel(factory(me=user, data=pm, state=self))

        self.dispatch('connect')
        self._ready_task = asyncio.ensure_future(self._delay_ready(), loop=self.loop)

    def parse_resumed(self, data):
        self.dispatch('resumed')

    def parse_message_create(self, data):
        channel, _ = self._get_guild_channel(data)
        message = Message(channel=channel, data=data, state=self)
        self.dispatch('message', message)
        self._messages.append(message)
        if channel and channel.__class__ is TextChannel:
            channel.last_message_id = message.id

    def parse_message_delete(self, data):
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(raw.message_id)
        raw.cached_message = found
        self.dispatch('raw_message_delete', raw)
        if found is not None:
            self.dispatch('message_delete', found)
            self._messages.remove(found)

    def parse_message_delete_bulk(self, data):
        raw = RawBulkMessageDeleteEvent(data)
        found_messages = [message for message in self._messages if message.id in raw.message_ids]
        raw.cached_messages = found_messages
        self.dispatch('raw_bulk_message_delete', raw)
        if found_messages:
            self.dispatch('bulk_message_delete', found_messages)
            for msg in found_messages:
                self._messages.remove(msg)

    def parse_message_update(self, data):
        raw = RawMessageUpdateEvent(data)
        message = self._get_message(raw.message_id)
        if message is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch('raw_message_edit', raw)
            message._update(data)
            self.dispatch('message_edit', older_message, message)
        else:
            self.dispatch('raw_message_edit', raw)

    def parse_message_reaction_add(self, data):
        emoji = data['emoji']
        emoji_id = utils._get_as_snowflake(emoji, 'id')
        emoji = PartialEmoji.with_state(self, animated=emoji.get('animated', False), id=emoji_id, name=emoji['name'])
        raw = RawReactionActionEvent(data, emoji)
        self.dispatch('raw_reaction_add', raw)

        # rich interface here
        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            user = self._get_reaction_user(message.channel, raw.user_id)
            if user:
                self.dispatch('reaction_add', reaction, user)

    def parse_message_reaction_remove_all(self, data):
        raw = RawReactionClearEvent(data)
        self.dispatch('raw_reaction_clear', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch('reaction_clear', message, old_reactions)

    def parse_message_reaction_remove(self, data):
        emoji = data['emoji']
        emoji_id = utils._get_as_snowflake(emoji, 'id')
        emoji = PartialEmoji.with_state(self, animated=emoji.get('animated', False), id=emoji_id, name=emoji['name'])
        raw = RawReactionActionEvent(data, emoji)
        self.dispatch('raw_reaction_remove', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            try:
                reaction = message._remove_reaction(data, emoji, raw.user_id)
            except (AttributeError, ValueError): # eventual consistency lol
                pass
            else:
                user = self._get_reaction_user(message.channel, raw.user_id)
                if user:
                    self.dispatch('reaction_remove', reaction, user)

    def parse_presence_update(self, data):
        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is None:
            log.warning('PRESENCE_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        user = data['user']
        member_id = int(user['id'])
        member = guild.get_member(member_id)
        if member is None:
            if 'username' not in user:
                # sometimes we receive 'incomplete' member data post-removal.
                # skip these useless cases.
                return

            member, old_member = Member._from_presence_update(guild=guild, data=data, state=self)
            guild._add_member(member)
        else:
            old_member = Member._copy(member)
            user_update = member._presence_update(data=data, user=user)
            if user_update:
                self.dispatch('user_update', user_update[0], user_update[1])

        self.dispatch('member_update', old_member, member)

    def parse_user_update(self, data):
        self.user._update(data)

    def parse_channel_delete(self, data):
        guild = self._get_guild(utils._get_as_snowflake(data, 'guild_id'))
        channel_id = int(data['id'])
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                guild._remove_channel(channel)
                self.dispatch('guild_channel_delete', channel)
        else:
            # the reason we're doing this is so it's also removed from the
            # private channel by user cache as well
            channel = self._get_private_channel(channel_id)
            if channel is not None:
                self._remove_private_channel(channel)
                self.dispatch('private_channel_delete', channel)

    def parse_channel_update(self, data):
        channel_type = try_enum(ChannelType, data.get('type'))
        channel_id = int(data['id'])
        if channel_type is ChannelType.group:
            channel = self._get_private_channel(channel_id)
            old_channel = copy.copy(channel)
            channel._update_group(data)
            self.dispatch('private_channel_update', old_channel, channel)
            return

        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                channel._update(guild, data)
                self.dispatch('guild_channel_update', old_channel, channel)
            else:
                log.warning('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
        else:
            log.warning('CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_channel_create(self, data):
        factory, ch_type = _channel_factory(data['type'])
        if factory is None:
            log.warning('CHANNEL_CREATE referencing an unknown channel type %s. Discarding.', data['type'])
            return

        channel = None

        if ch_type in (ChannelType.group, ChannelType.private):
            channel_id = int(data['id'])
            if self._get_private_channel(channel_id) is None:
                channel = factory(me=self.user, data=data, state=self)
                self._add_private_channel(channel)
                self.dispatch('private_channel_create', channel)
        else:
            guild_id = utils._get_as_snowflake(data, 'guild_id')
            guild = self._get_guild(guild_id)
            if guild is not None:
                channel = factory(guild=guild, state=self, data=data)
                guild._add_channel(channel)
                self.dispatch('guild_channel_create', channel)
            else:
                log.warning('CHANNEL_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
                return

    def parse_channel_pins_update(self, data):
        channel_id = int(data['channel_id'])
        channel = self.get_channel(channel_id)
        if channel is None:
            log.warning('CHANNEL_PINS_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        last_pin = utils.parse_time(data['last_pin_timestamp']) if data['last_pin_timestamp'] else None

        try:
            # I have not imported discord.abc in this file
            # the isinstance check is also 2x slower than just checking this attribute
            # so we're just gonna check it since it's easier and faster and lazier
            channel.guild
        except AttributeError:
            self.dispatch('private_channel_pins_update', channel, last_pin)
        else:
            self.dispatch('guild_channel_pins_update', channel, last_pin)

    def parse_channel_recipient_add(self, data):
        channel = self._get_private_channel(int(data['channel_id']))
        user = self.store_user(data['user'])
        channel.recipients.append(user)
        self.dispatch('group_join', channel, user)

    def parse_channel_recipient_remove(self, data):
        channel = self._get_private_channel(int(data['channel_id']))
        user = self.store_user(data['user'])
        try:
            channel.recipients.remove(user)
        except ValueError:
            pass
        else:
            self.dispatch('group_remove', channel, user)

    def parse_guild_member_add(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            log.warning('GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = Member(guild=guild, data=data, state=self)
        guild._add_member(member)
        guild._member_count += 1
        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            user_id = int(data['user']['id'])
            member = guild.get_member(user_id)
            if member is not None:
                guild._remove_member(member)
                guild._member_count -= 1
                self.dispatch('member_remove', member)
        else:
            log.warning('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_member_update(self, data):
        guild = self._get_guild(int(data['guild_id']))
        user = data['user']
        user_id = int(user['id'])
        if guild is None:
            log.warning('GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = guild.get_member(user_id)
        if member is not None:
            old_member = copy.copy(member)
            member._update(data)
            self.dispatch('member_update', old_member, member)
        else:
            log.warning('GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)

    def parse_guild_emojis_update(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            log.warning('GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            self._emojis.pop(emoji.id, None)
        guild.emojis = tuple(map(lambda d: self.store_emoji(guild, d), data['emojis']))
        self.dispatch('guild_emojis_update', guild, before_emojis, guild.emojis)

    def _get_create_guild(self, data):
        if data.get('unavailable') is False:
            # GUILD_CREATE with unavailable in the response
            # usually means that the guild has become available
            # and is therefore in the cache
            guild = self._get_guild(int(data['id']))
            if guild is not None:
                guild.unavailable = False
                guild._from_data(data)
                return guild

        return self._add_guild_from_data(data)

    async def _chunk_and_dispatch(self, guild, unavailable):
        chunks = list(self.chunks_needed(guild))
        await self.chunker(guild)
        if chunks:
            try:
                await utils.sane_wait_for(chunks, timeout=len(chunks), loop=self.loop)
            except asyncio.TimeoutError:
                log.info('Somehow timed out waiting for chunks.')

        if unavailable is False:
            self.dispatch('guild_available', guild)
        else:
            self.dispatch('guild_join', guild)

    def parse_guild_create(self, data):
        unavailable = data.get('unavailable')
        if unavailable is True:
            # joined a guild with unavailable == True so..
            return

        guild = self._get_create_guild(data)

        # check if it requires chunking
        if guild.large:
            if unavailable is False:
                # check if we're waiting for 'useful' READY
                # and if we are, we don't want to dispatch any
                # event such as guild_join or guild_available
                # because we're still in the 'READY' phase. Or
                # so we say.
                try:
                    state = self._ready_state
                    state.launch.clear()
                    state.guilds.append((guild, unavailable))
                except AttributeError:
                    # the _ready_state attribute is only there during
                    # processing of useful READY.
                    pass
                else:
                    return

            # since we're not waiting for 'useful' READY we'll just
            # do the chunk request here if wanted
            if self._fetch_offline:
                asyncio.ensure_future(self._chunk_and_dispatch(guild, unavailable), loop=self.loop)
                return

        # Dispatch available if newly available
        if unavailable is False:
            self.dispatch('guild_available', guild)
        else:
            self.dispatch('guild_join', guild)

    def parse_guild_sync(self, data):
        guild = self._get_guild(int(data['id']))
        guild._sync(data)

    def parse_guild_update(self, data):
        guild = self._get_guild(int(data['id']))
        if guild is not None:
            old_guild = copy.copy(guild)
            guild._from_data(data)
            self.dispatch('guild_update', old_guild, guild)
        else:
            log.warning('GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.', data['id'])

    def parse_guild_delete(self, data):
        guild = self._get_guild(int(data['id']))
        if guild is None:
            log.warning('GUILD_DELETE referencing an unknown guild ID: %s. Discarding.', data['id'])
            return

        if data.get('unavailable', False) and guild is not None:
            # GUILD_DELETE with unavailable being True means that the
            # guild that was available is now currently unavailable
            guild.unavailable = True
            self.dispatch('guild_unavailable', guild)
            return

        # do a cleanup of the messages cache
        self._messages = deque((msg for msg in self._messages if msg.guild != guild), maxlen=self.max_messages)

        self._remove_guild(guild)
        self.dispatch('guild_remove', guild)

    def parse_guild_ban_add(self, data):
        # we make the assumption that GUILD_BAN_ADD is done
        # before GUILD_MEMBER_REMOVE is called
        # hence we don't remove it from cache or do anything
        # strange with it, the main purpose of this event
        # is mainly to dispatch to another event worth listening to for logging
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                user = User(data=data['user'], state=self)
            except KeyError:
                pass
            else:
                member = guild.get_member(user.id) or user
                self.dispatch('member_ban', guild, member)

    def parse_guild_ban_remove(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            if 'user' in data:
                user = self.store_user(data['user'])
                self.dispatch('member_unban', guild, user)

    def parse_guild_role_create(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            log.warning('GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        role_data = data['role']
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.dispatch('guild_role_create', role)

    def parse_guild_role_delete(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            role_id = int(data['role_id'])
            try:
                role = guild._remove_role(role_id)
            except KeyError:
                return
            else:
                self.dispatch('guild_role_delete', role)
        else:
            log.warning('GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_role_update(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            role_data = data['role']
            role_id = int(role_data['id'])
            role = guild.get_role(role_id)
            if role is not None:
                old_role = copy.copy(role)
                role._update(role_data)
                self.dispatch('guild_role_update', old_role, role)
        else:
            log.warning('GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_members_chunk(self, data):
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        members = data.get('members', [])
        for member in members:
            m = Member(guild=guild, data=member, state=self)
            existing = guild.get_member(m.id)
            if existing is None or existing.joined_at is None:
                guild._add_member(m)

        log.info('Processed a chunk for %s members in guild ID %s.', len(members), guild_id)
        self.process_listeners(ListenerType.chunk, guild, len(members))

    def parse_guild_integrations_update(self, data):
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            self.dispatch('guild_integrations_update', guild)
        else:
            log.warning('GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_webhooks_update(self, data):
        channel = self.get_channel(int(data['channel_id']))
        if channel is not None:
            self.dispatch('webhooks_update', channel)
        else:
            log.warning('WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])

    def parse_voice_state_update(self, data):
        guild = self._get_guild(utils._get_as_snowflake(data, 'guild_id'))
        channel_id = utils._get_as_snowflake(data, 'channel_id')
        if guild is not None:
            if int(data['user_id']) == self.user.id:
                voice = self._get_voice_client(guild.id)
                if voice is not None:
                    ch = guild.get_channel(channel_id)
                    if ch is not None:
                        voice.channel = ch

            member, before, after = guild._update_voice_state(data, channel_id)
            if member is not None:
                self.dispatch('voice_state_update', member, before, after)
            else:
                log.warning('VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', data['user_id'])
        else:
            # in here we're either at private or group calls
            call = self._calls.get(channel_id)
            if call is not None:
                call._update_voice_state(data)

    def parse_voice_server_update(self, data):
        try:
            key_id = int(data['guild_id'])
        except KeyError:
            key_id = int(data['channel_id'])

        vc = self._get_voice_client(key_id)
        if vc is not None:
            asyncio.ensure_future(vc._create_socket(key_id, data))

    def parse_typing_start(self, data):
        channel, guild = self._get_guild_channel(data)
        if channel is not None:
            member = None
            user_id = utils._get_as_snowflake(data, 'user_id')
            if isinstance(channel, DMChannel):
                member = channel.recipient
            elif isinstance(channel, TextChannel) and guild is not None:
                member = guild.get_member(user_id)
            elif isinstance(channel, GroupChannel):
                member = utils.find(lambda x: x.id == user_id, channel.recipients)

            if member is not None:
                timestamp = datetime.datetime.utcfromtimestamp(data.get('timestamp'))
                self.dispatch('typing', channel, member, timestamp)

    def parse_relationship_add(self, data):
        key = int(data['id'])
        old = self.user.get_relationship(key)
        new = Relationship(state=self, data=data)
        self.user._relationships[key] = new
        if old is not None:
            self.dispatch('relationship_update', old, new)
        else:
            self.dispatch('relationship_add', new)

    def parse_relationship_remove(self, data):
        key = int(data['id'])
        try:
            old = self.user._relationships.pop(key)
        except KeyError:
            pass
        else:
            self.dispatch('relationship_remove', old)

    def _get_reaction_user(self, channel, user_id):
        if isinstance(channel, TextChannel):
            return channel.guild.get_member(user_id)
        return self.get_user(user_id)

    def get_reaction_emoji(self, data):
        emoji_id = utils._get_as_snowflake(data, 'id')

        if not emoji_id:
            return data['name']

        try:
            return self._emojis[emoji_id]
        except KeyError:
            return PartialEmoji(animated=data.get('animated', False), id=emoji_id, name=data['name'])

    def _upgrade_partial_emoji(self, emoji):
        emoji_id = emoji.id
        if not emoji_id:
            return emoji.name
        try:
            return self._emojis[emoji_id]
        except KeyError:
            return emoji

    def get_channel(self, id):
        if id is None:
            return None

        pm = self._get_private_channel(id)
        if pm is not None:
            return pm

        for guild in self.guilds:
            channel = guild.get_channel(id)
            if channel is not None:
                return channel

    def create_message(self, *, channel, data):
        return Message(state=self, channel=channel, data=data)

    def receive_chunk(self, guild_id):
        future = self.loop.create_future()
        listener = Listener(ListenerType.chunk, future, lambda s: s.id == guild_id)
        self._listeners.append(listener)
        return future

class AutoShardedConnectionState(ConnectionState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready_task = None

    async def request_offline_members(self, guilds, *, shard_id):
        # get all the chunks
        chunks = []
        for guild in guilds:
            chunks.extend(self.chunks_needed(guild))

        # we only want to request ~75 guilds per chunk request.
        splits = [guilds[i:i + 75] for i in range(0, len(guilds), 75)]
        for split in splits:
            await self.chunker(split, shard_id=shard_id)

        # wait for the chunks
        if chunks:
            try:
                await utils.sane_wait_for(chunks, timeout=len(chunks) * 30.0, loop=self.loop)
            except asyncio.TimeoutError:
                log.info('Somehow timed out waiting for chunks.')

    async def _delay_ready(self):
        launch = self._ready_state.launch
        while not launch.is_set():
            # this snippet of code is basically waiting 2 seconds
            # until the last GUILD_CREATE was sent
            launch.set()
            await asyncio.sleep(2.0 * self.shard_count, loop=self.loop)

        if self._fetch_offline:
            guilds = sorted(self._ready_state.guilds, key=lambda g: g[0].shard_id)

            for shard_id, sub_guilds_info in itertools.groupby(guilds, key=lambda g: g[0].shard_id):
                sub_guilds, sub_available = zip(*sub_guilds_info)
                await self.request_offline_members(sub_guilds, shard_id=shard_id)

                for guild, unavailable in zip(sub_guilds, sub_available):
                    if unavailable is False:
                        self.dispatch('guild_available', guild)
                    else:
                        self.dispatch('guild_join', guild)
                self.dispatch('shard_ready', shard_id)
        else:
            for guild, unavailable in self._ready_state.guilds:
                if unavailable is False:
                    self.dispatch('guild_available', guild)
                else:
                    self.dispatch('guild_join', guild)

        # remove the state
        try:
            del self._ready_state
        except AttributeError:
            pass # already been deleted somehow

        # regular users cannot shard so we won't worry about it here.

        # clear the current task
        self._ready_task = None

        # dispatch the event
        self.call_handlers('ready')
        self.dispatch('ready')

    def parse_ready(self, data):
        if not hasattr(self, '_ready_state'):
            self._ready_state = ReadyState(launch=asyncio.Event(), guilds=[])

        self.user = user = ClientUser(state=self, data=data['user'])
        self._users[user.id] = user

        guilds = self._ready_state.guilds
        for guild_data in data['guilds']:
            guild = self._add_guild_from_data(guild_data)
            if guild.large:
                guilds.append((guild, guild.unavailable))

        for pm in data.get('private_channels', []):
            factory, _ = _channel_factory(pm['type'])
            self._add_private_channel(factory(me=user, data=pm, state=self))

        self.dispatch('connect')
        if self._ready_task is None:
            self._ready_task = asyncio.ensure_future(self._delay_ready(), loop=self.loop)
