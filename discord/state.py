"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from __future__ import annotations

import asyncio
from collections import deque
import copy
import datetime
import logging
from typing import Dict, Optional, TYPE_CHECKING, Union, Callable, Any, List, TypeVar, Coroutine, Tuple, Deque
import inspect
import time
import os
import random
from sys import intern

from .errors import NotFound
from .guild import CommandCounts, Guild
from .activity import BaseActivity, create_activity
from .user import User, ClientUser
from .emoji import Emoji
from .mentions import AllowedMentions
from .partial_emoji import PartialEmoji
from .message import Message
from .channel import *
from .channel import _channel_factory, _private_channel_factory
from .raw_models import *
from .member import Member
from .relationship import Relationship
from .role import Role
from .enums import ChannelType, RequiredActionType, Status, try_enum, UnavailableGuildType, VoiceRegion
from . import utils
from .flags import GuildSubscriptionOptions, MemberCacheFlags
from .invite import Invite
from .integrations import _integration_factory
from .stage_instance import StageInstance
from .threads import Thread, ThreadMember
from .sticker import GuildSticker
from .settings import UserSettings, GuildSettings
from .tracking import Tracking
from .interactions import Interaction

if TYPE_CHECKING:
    from .abc import PrivateChannel
    from .message import MessageableChannel
    from .guild import GuildChannel, VocalGuildChannel
    from .http import HTTPClient
    from .voice_client import VoiceProtocol
    from .client import Client
    from .gateway import DiscordWebSocket
    from .calls import Call
    from .member import VoiceState

    from .types.activity import Activity as ActivityPayload
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import User as UserPayload
    from .types.emoji import Emoji as EmojiPayload
    from .types.sticker import GuildSticker as GuildStickerPayload
    from .types.guild import Guild as GuildPayload
    from .types.message import Message as MessagePayload
    from .types.voice import GuildVoiceState

    T = TypeVar('T')
    CS = TypeVar('CS', bound='ConnectionState')
    Channel = Union[GuildChannel, VocalGuildChannel, PrivateChannel, PartialMessageable]

MISSING = utils.MISSING


class ChunkRequest:
    def __init__(
        self,
        guild_id: int,
        loop: asyncio.AbstractEventLoop,
        resolver: Callable[[int], Any],
        *,
        cache: bool = True,
    ) -> None:
        self.guild_id: int = guild_id
        self.resolver: Callable[[int], Any] = resolver
        self.loop: asyncio.AbstractEventLoop = loop
        self.cache: bool = cache
        self.nonce: str = str(utils.time_snowflake(utils.utcnow()))
        self.buffer: List[Member] = []
        self.waiters: List[asyncio.Future[List[Member]]] = []

    def add_members(self, members: List[Member]) -> None:
        self.buffer.extend(members)
        if self.cache:
            guild = self.resolver(self.guild_id)
            if guild is None:
                return

            for member in members:
                existing = guild.get_member(member.id)
                if existing is None or existing.joined_at is None:
                    guild._add_member(member)

    async def wait(self) -> List[Member]:
        future = self.loop.create_future()
        self.waiters.append(future)
        try:
            return await future
        finally:
            self.waiters.remove(future)

    def get_future(self) -> asyncio.Future[List[Member]]:
        future = self.loop.create_future()
        self.waiters.append(future)
        return future

    def done(self) -> None:
        for future in self.waiters:
            if not future.done():
                future.set_result(self.buffer)


_log = logging.getLogger(__name__)


async def logging_coroutine(coroutine: Coroutine[Any, Any, T], *, info: str) -> Optional[T]:
    try:
        await coroutine
    except Exception:
        _log.exception('Exception occurred during %s.', info)


class ConnectionState:
    def __init__(
        self,
        *,
        dispatch: Callable,
        handlers: Dict[str, Callable],
        hooks: Dict[str, Callable],
        http: HTTPClient,
        loop: asyncio.AbstractEventLoop,
        client: Client,
        **options: Any,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.http: HTTPClient = http
        self.client = client
        self.max_messages: Optional[int] = options.get('max_messages', 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.dispatch: Callable = dispatch
        self.handlers: Dict[str, Callable] = handlers
        self.hooks: Dict[str, Callable] = hooks
        self._ready_task: Optional[asyncio.Task] = None
        self.heartbeat_timeout: float = options.get('heartbeat_timeout', 60.0)

        allowed_mentions = options.get('allowed_mentions')
        if allowed_mentions is not None and not isinstance(allowed_mentions, AllowedMentions):
            raise TypeError('allowed_mentions parameter must be AllowedMentions')

        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions
        self._chunk_requests: Dict[Union[int, str], ChunkRequest] = {}

        activities = options.get('activities', [])
        if not activities:
            activity = options.get('activity')
            if activity is not None:
                activities = [activity]

        if not all(isinstance(activity, BaseActivity) for activity in activities):
            raise TypeError('activity parameter must derive from BaseActivity.')
        activities = [activity.to_dict() for activity in activities]

        status = options.get('status', None)
        if status:
            if status is Status.offline:
                status = 'invisible'
            else:
                status = str(status)

        self._chunk_guilds: bool = options.get('chunk_guilds_at_startup', True)
        self._request_guilds = options.get('request_guilds', True)

        subscription_options = options.get('guild_subscription_options')
        if subscription_options is None:
            subscription_options = GuildSubscriptionOptions.off()
        else:
            if not isinstance(subscription_options, GuildSubscriptionOptions):
                raise TypeError(f'subscription_options parameter must be GuildSubscriptionOptions not {type(subscription_options)!r}')
        self._subscription_options = subscription_options
        self._subscribe_guilds = subscription_options.auto_subscribe

        cache_flags = options.get('member_cache_flags', None)
        if cache_flags is None:
            cache_flags = MemberCacheFlags.all()
        else:
            if not isinstance(cache_flags, MemberCacheFlags):
                raise TypeError(f'member_cache_flags parameter must be MemberCacheFlags not {type(cache_flags)!r}')

        self.member_cache_flags: MemberCacheFlags = cache_flags
        self._activities: List[ActivityPayload] = activities
        self._status: Optional[str] = status

        if cache_flags._empty:
            self.store_user = self.create_user  # type: ignore
            self.deref_user = lambda _: None  # type: ignore

        parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func
        self.parsers: Dict[str, Callable[[Dict[str, Any]], None]] = parsers

        self.clear()

    def clear(self) -> None:
        self.user: Optional[ClientUser] = None
        self.settings: Optional[UserSettings] = None
        self.consents: Optional[Tracking] = None
        self.analytics_token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.preferred_region: Optional[VoiceRegion] = None
        # Originally, this code used WeakValueDictionary to maintain references to the
        # global user mapping

        # However, profiling showed that this came with two cons:

        # 1. The __weakref__ slot caused a non-trivial increase in memory
        # 2. The performance of the mapping caused store_user to be a bottleneck

        # Since this is undesirable, a mapping is now used instead with stored
        # references now using a regular dictionary with eviction being done
        # using __del__ 
        # Testing this for memory leaks led to no discernable leaks
        self._users: Dict[int, User] = {}
        self._emojis: Dict[int, Emoji] = {}
        self._stickers: Dict[int, GuildSticker] = {}
        self._guilds: Dict[int, Guild] = {}
        self._queued_guilds: Dict[int, Guild] = {}
        self._unavailable_guilds: Dict[int, UnavailableGuildType] = {}

        self._calls: Dict[int, Call] = {}
        self._call_message_cache: List[Message] = []  # Hopefully this won't be a memory leak
        self._voice_clients: Dict[int, VoiceProtocol] = {}
        self._voice_states: Dict[int, VoiceState] = {}

        self._interactions: Dict[Union[int, str], Union[Tuple[int, Optional[str]], Interaction]] = {}
        self._relationships: Dict[int, Relationship] = {}
        self._private_channels: Dict[int, PrivateChannel] = {}
        self._private_channels_by_user: Dict[int, DMChannel] = {}
        self._last_private_channel: tuple = (None, None)

        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages)
        else:
            self._messages: Optional[Deque[Message]] = None

    def process_chunk_requests(self, guild_id: int, nonce: Optional[str], members: List[Member], complete: bool) -> None:
        removed = []
        for key, request in self._chunk_requests.items():
            if request.guild_id == guild_id and request.nonce == nonce:
                request.add_members(members)
                if complete:
                    request.done()
                    removed.append(key)

        for key in removed:
            del self._chunk_requests[key]

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    async def call_hooks(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            coro = self.hooks[key]
        except KeyError:
            pass
        else:
            await coro(*args, **kwargs)

    @property
    def ws(self):
        return self.client.ws

    @property
    def self_id(self) -> Optional[int]:
        u = self.user
        return u.id if u else None

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        return list(self._voice_clients.values())

    def _update_voice_state(self, data: GuildVoiceState, channel_id: int) -> Tuple[User, VoiceState, VoiceState]:
        user_id = int(data['user_id'])
        user = self.get_user(user_id)
        channel = self._get_private_channel(channel_id)

        try:
            # Check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy.copy(after)
            after._update(data, channel)
        except KeyError:
            # if we're here then add it into the cache
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after

        return user, before, after

    def _voice_state_for(self, user_id: int) -> Optional[VoiceState]:
        return self._voice_states.get(user_id)

    def _get_voice_client(self, guild_id: Optional[int]) -> Optional[VoiceProtocol]:
        # The keys of self._voice_clients are ints
        return self._voice_clients.get(guild_id)  # type: ignore

    def _add_voice_client(self, guild_id: int, voice: VoiceProtocol) -> None:
        self._voice_clients[guild_id] = voice

    def _remove_voice_client(self, guild_id: int) -> None:
        self._voice_clients.pop(guild_id, None)

    def _update_references(self, ws: DiscordWebSocket) -> None:
        for vc in self.voice_clients:
            vc.main_ws = ws  # type: ignore

    def store_user(self, data: UserPayload) -> User:
        user_id = int(data['id'])
        try:
            user = self._users[user_id]
            # We use the data available to us since we
            # might not have events for that user
            # However, the data may only have an ID
            try:
                user._update(data)
            except KeyError:
                pass
            return user
        except KeyError:
            user = User(state=self, data=data)
            if user.discriminator != '0000':
                self._users[user_id] = user
                user._stored = True
            return user

    def deref_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    def create_user(self, data: UserPayload) -> User:
        return User(state=self, data=data)

    def get_user(self, id: Optional[int]) -> Optional[User]:
        # The keys of self._users are ints
        return self._users.get(id)  # type: ignore

    def store_emoji(self, guild: Guild, data: EmojiPayload) -> Emoji:
        # The id will be present here
        emoji_id = int(data['id'])  # type: ignore
        self._emojis[emoji_id] = emoji = Emoji(guild=guild, state=self, data=data)
        return emoji

    def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        sticker_id = int(data['id'])
        self._stickers[sticker_id] = sticker = GuildSticker(state=self, data=data)
        return sticker

    @property
    def guilds(self) -> List[Guild]:
        return list(self._guilds.values())

    def _get_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        # The keys of self._guilds are ints
        guild = self._guilds.get(guild_id)  # type: ignore
        if guild is None:
            guild = self._queued_guilds.get(guild_id)  # type: ignore
        return guild

    def _add_guild(self, guild: Guild) -> None:
        self._guilds[guild.id] = guild

    def _remove_guild(self, guild: Guild) -> None:
        self._guilds.pop(guild.id, None)

        for emoji in guild.emojis:
            self._emojis.pop(emoji.id, None)

        for sticker in guild.stickers:
            self._stickers.pop(sticker.id, None)

        del guild

    @property
    def emojis(self) -> List[Emoji]:
        return list(self._emojis.values())

    @property
    def stickers(self) -> List[GuildSticker]:
        return list(self._stickers.values())

    def get_emoji(self, emoji_id: Optional[int]) -> Optional[Emoji]:
        # the keys of self._emojis are ints
        return self._emojis.get(emoji_id)  # type: ignore

    def get_sticker(self, sticker_id: Optional[int]) -> Optional[GuildSticker]:
        # the keys of self._stickers are ints
        return self._stickers.get(sticker_id)  # type: ignore

    @property
    def private_channels(self) -> List[PrivateChannel]:
        return list(self._private_channels.values())

    async def access_private_channel(self, channel_id: int) -> None:
        if not self._get_accessed_private_channel(channel_id):
            await self._access_private_channel(channel_id)
            self._set_accessed_private_channel(channel_id)

    async def _access_private_channel(self, channel_id: int) -> None:
        if (ws := self.ws) is None:
            return

        try:
            await ws.access_dm(channel_id)
        except Exception as exc:
            _log.warning('Sending ACCESS_DM failed for channel %s, (%s).', channel_id, exc)

    def _set_accessed_private_channel(self, channel_id):
        self._last_private_channel = (channel_id, time.time())

    def _get_accessed_private_channel(self, channel_id):
        timestamp, existing_id = self._last_private_channel
        return existing_id == channel_id and int(time.time() - timestamp) < random.randrange(120000, 420000)

    def _get_private_channel(self, channel_id: Optional[int]) -> Optional[PrivateChannel]:
        # The keys of self._private_channels are ints
        return self._private_channels.get(channel_id)  # type: ignore

    def _get_private_channel_by_user(self, user_id: Optional[int]) -> Optional[DMChannel]:
        # The keys of self._private_channels are ints
        return self._private_channels_by_user.get(user_id)  # type: ignore

    def _add_private_channel(self, channel: PrivateChannel) -> None:
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if isinstance(channel, DMChannel) and channel.recipient:
            self._private_channels_by_user[channel.recipient.id] = channel

    def add_dm_channel(self, data: DMChannelPayload) -> DMChannel:
        # self.user is *always* cached when this is called
        channel = DMChannel(me=self.user, state=self, data=data)  # type: ignore
        self._add_private_channel(channel)
        return channel

    def _remove_private_channel(self, channel: PrivateChannel) -> None:
        self._private_channels.pop(channel.id, None)
        if isinstance(channel, DMChannel):
            recipient = channel.recipient
            if recipient is not None:
                self._private_channels_by_user.pop(recipient.id, None)

    def _get_message(self, msg_id: Optional[int]) -> Optional[Message]:
        return utils.find(lambda m: m.id == msg_id, reversed(self._messages)) if self._messages else None

    def _add_guild_from_data(self, guild: GuildPayload, *, from_ready: bool = False) -> Guild:
        guild_id = int(guild['id'])
        unavailable = guild.get('unavailable', False)

        if not unavailable:
            guild = Guild(data=guild, state=self)
            self._add_guild(guild)
            return guild
        else:
            self._unavailable_guilds[guild_id] = UnavailableGuildType.existing if from_ready else UnavailableGuildType.joined
            _log.debug('Forcing GUILD_CREATE for unavailable guild %s.' % guild_id)
            asyncio.ensure_future(self.request_guild(guild_id), loop=self.loop)

    def _guild_needs_chunking(self, guild: Guild) -> bool:
        if not guild.me:  # Dear god this will break everything
            return False
        return self._chunk_guilds and not guild.chunked and any({
            guild.me.guild_permissions.kick_members,
            guild.me.guild_permissions.manage_roles,
            guild.me.guild_permissions.ban_members
        })

    def _guild_needs_subscribing(self, guild):  # TODO: rework
        return not guild.subscribed and self._subscribe_guilds

    def _get_guild_channel(self, data: MessagePayload) -> Tuple[Union[Channel, Thread], Optional[Guild]]:
        channel_id = int(data['channel_id'])
        try:
            guild = self._get_guild(int(data['guild_id']))
        except KeyError:
            channel = self.get_channel(channel_id)
            guild = None
        else:
            channel = guild and guild._resolve_channel(channel_id)

        return channel or PartialMessageable(state=self, id=channel_id), guild

    async def _delete_messages(self, channel_id, messages):
        delete_message = self.http.delete_message
        for msg in messages:
            try:
                await delete_message(channel_id, msg.id)
            except NotFound:
                pass

    def request_guild(self, guild_id: int) -> Coroutine:
        return self.ws.request_lazy_guild(guild_id, typing=True, activities=True, threads=True)

    def chunker(
        self, guild_id: int, query: str = '', limit: int = 0, presences: bool = True, *, nonce: Optional[str] = None
    ):
        return self.ws.request_chunks(guild_id, query=query, limit=limit, presences=presences, nonce=nonce)

    async def query_members(self, guild: Guild, query: str, limit: int, user_ids: List[int], cache: bool, presences: bool):
        guild_id = guild.id
        request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
        self._chunk_requests[request.nonce] = request

        try:
            await self.ws.request_chunks(
                [guild_id], query=query, limit=limit, user_ids=user_ids, presences=presences, nonce=request.nonce
            )
            return await asyncio.wait_for(request.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            _log.warning('Timed out waiting for chunks with query %r and limit %d for guild_id %d.', query, limit, guild_id)
            raise

    async def _delay_ready(self) -> None:
        try:
            states = []
            subscribes = []
            for guild in self._guilds.values():
                if self._request_guilds:
                    await self.request_guild(guild.id)

                if self._guild_needs_chunking(guild):
                    future = await self.chunk_guild(guild, wait=False)
                    states.append((guild, future))

                if self._guild_needs_subscribing(guild):
                    subscribes.append(guild)

            for guild, future in states:
                try:
                    await asyncio.wait_for(future, timeout=5.0)
                except asyncio.TimeoutError:
                    _log.warning('Timed out waiting for chunks for guild_id %s.', guild.id)

            options = self._subscription_options
            ticket = asyncio.Semaphore(options.concurrent_guilds)
            await asyncio.gather(*[guild.subscribe(ticket=ticket, max_online=options.max_online) for guild in subscribes])

        except asyncio.CancelledError:
            pass
        else:
            # Dispatch the event
            self.call_handlers('ready')
            self.dispatch('ready')
        finally:
            self._ready_task = None

    def parse_ready(self, data) -> None:
        # Before parsing, we wait for READY_SUPPLEMENTAL
        # This has voice state objects, as well as an initial member cache
        self._ready_data: dict = data

    def parse_ready_supplemental(self, data) -> None:
        if self._ready_task is not None:
            self._ready_task.cancel()

        self.clear()

        extra_data, data = data, self._ready_data
        guild_settings = data.get('user_guild_settings', {}).get('entries', [])

        # Discord bad
        for guild_data, guild_extra, merged_members, merged_me, merged_presences in zip(
            data.get('guilds', []),
            extra_data.get('guilds', []),
            extra_data.get('merged_members', []),
            data.get('merged_members', []),
            extra_data['merged_presences'].get('guilds', [])
        ):
            guild_data['settings'] = utils.find(
                lambda i: i['guild_id'] == guild_data['id'],
                guild_settings,
            ) or {'guild_id': guild_data['id']}

            guild_data['voice_states'] = guild_extra.get('voice_states', [])
            guild_data['merged_members'] = merged_me
            guild_data['merged_members'].extend(merged_members)
            guild_data['merged_presences'] = merged_presences
            # There's also a friends key that has presence data for your friends
            # Parsing that would require a redesign of the Relationship class ;-;

        # Self parsing
        self.user = user = ClientUser(state=self, data=data['user'])
        self.store_user(data['user'])

        # Temp user parsing
        temp_users = {user.id: user._to_minimal_user_json()}
        for u in data.get('users', []):
            u_id = int(u['id'])
            temp_users[u_id] = u

        # Guild parsing
        for guild_data in data.get('guilds', []):
            for member in guild_data['merged_members']:
                if 'user' not in member:
                    member['user'] = temp_users.get(int(member.pop('user_id')))
            self._add_guild_from_data(guild_data, from_ready=True)

        # Relationship parsing
        for relationship in data.get('relationships', []):
            try:
                r_id = int(relationship['id'])
            except KeyError:
                continue
            else:
                if 'user' not in relationship:
                    relationship['user'] = temp_users[int(relationship.pop('user_id'))]
                self._relationships[r_id] = Relationship(state=self, data=relationship)

        # Private channel parsing
        for pm in data.get('private_channels', []):
            factory, _ = _private_channel_factory(pm['type'])
            if 'recipients' not in pm:
                pm['recipients'] = [temp_users[int(u_id)] for u_id in pm.pop('recipient_ids')]
            self._add_private_channel(factory(me=user, data=pm, state=self))

        # Extras
        self.session_id = data.get('session_id')
        self.analytics_token = data.get('analytics_token')
        region = data.get('geo_ordered_rtc_regions', ['us-west'])[0]
        self.preferred_region = try_enum(VoiceRegion, region)
        self.settings = UserSettings(data=data.get('user_settings', {}), state=self)
        self.consents = Tracking(data=data.get('consents', {}), state=self)

        if 'required_action' in data:  # Locked more than likely
            self.parse_user_required_action_update(data)

        if 'sessions' in data:
            self.parse_sessions_replace(data['sessions'])

        # We're done
        del self._ready_data
        self.call_handlers('connect')
        self.dispatch('connect')
        self._ready_task = asyncio.create_task(self._delay_ready())

    def parse_resumed(self, _) -> None:
        self.dispatch('resumed')

    def parse_message_create(self, data) -> None:
        guild_id = utils._get_as_snowflake(data, 'guild_id')
        channel, _ = self._get_guild_channel(data)
        if guild_id in self._unavailable_guilds:  # I don't know how I feel about this :(
            return

        # channel will be the correct type here
        message = Message(channel=channel, data=data, state=self)  # type: ignore
        self.dispatch('message', message)
        if self._messages is not None:
            self._messages.append(message)
        if message.call is not None:
            self._call_message_cache[message.id] = message

        # We ensure that the channel is either a TextChannel or Thread
        if channel and channel.__class__ in (TextChannel, Thread):
            channel.last_message_id = message.id  # type: ignore

    def parse_message_delete(self, data) -> None:
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(raw.message_id)
        raw.cached_message = found
        self.dispatch('raw_message_delete', raw)
        if self._messages is not None and found is not None:
            self.dispatch('message_delete', found)
            self._messages.remove(found)

    def parse_message_delete_bulk(self, data) -> None:
        raw = RawBulkMessageDeleteEvent(data)
        if self._messages:
            found_messages = [message for message in self._messages if message.id in raw.message_ids]
        else:
            found_messages = []
        raw.cached_messages = found_messages
        self.dispatch('raw_bulk_message_delete', raw)
        if found_messages:
            self.dispatch('bulk_message_delete', found_messages)
            for msg in found_messages:
                # self._messages won't be None here
                self._messages.remove(msg)  # type: ignore

    def parse_message_update(self, data) -> None:
        raw = RawMessageUpdateEvent(data)
        message = self._get_message(raw.message_id)
        if message is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch('raw_message_edit', raw)
            message._update(data)
            # Coerce the `after` parameter to take the new updated Member
            # ref: #5999
            older_message.author = message.author
            self.dispatch('message_edit', older_message, message)
        else:
            self.dispatch('raw_message_edit', raw)

    def parse_message_reaction_add(self, data) -> None:
        emoji = data['emoji']
        emoji_id = utils._get_as_snowflake(emoji, 'id')
        emoji = PartialEmoji.with_state(self, id=emoji_id, animated=emoji.get('animated', False), name=emoji['name'])
        raw = RawReactionActionEvent(data, emoji, 'REACTION_ADD')

        member_data = data.get('member')
        if member_data:
            guild = self._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = Member(data=member_data, guild=guild, state=self)
            else:
                raw.member = None
        else:
            raw.member = None
        self.dispatch('raw_reaction_add', raw)

        # rich interface here
        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            user = raw.member or self._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.dispatch('reaction_add', reaction, user)

    def parse_message_reaction_remove_all(self, data) -> None:
        raw = RawReactionClearEvent(data)
        self.dispatch('raw_reaction_clear', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch('reaction_clear', message, old_reactions)

    def parse_message_reaction_remove(self, data) -> None:
        emoji = data['emoji']
        emoji_id = utils._get_as_snowflake(emoji, 'id')
        emoji = PartialEmoji.with_state(self, id=emoji_id, name=emoji['name'])
        raw = RawReactionActionEvent(data, emoji, 'REACTION_REMOVE')
        self.dispatch('raw_reaction_remove', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            try:
                reaction = message._remove_reaction(data, emoji, raw.user_id)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                user = self._get_reaction_user(message.channel, raw.user_id)
                if user:
                    self.dispatch('reaction_remove', reaction, user)

    def parse_message_reaction_remove_emoji(self, data) -> None:
        emoji = data['emoji']
        emoji_id = utils._get_as_snowflake(emoji, 'id')
        emoji = PartialEmoji.with_state(self, id=emoji_id, name=emoji['name'])
        raw = RawReactionClearEmojiEvent(data, emoji)
        self.dispatch('raw_reaction_clear_emoji', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            try:
                reaction = message._clear_emoji(emoji)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                if reaction:
                    self.dispatch('reaction_clear_emoji', reaction)

    def parse_presence_update(self, data) -> None:
        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('PRESENCE_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        user = data['user']
        member_id = int(user['id'])
        member = guild.get_member(member_id)
        if member is None:
            _log.debug('PRESENCE_UPDATE referencing an unknown member ID: %s. Discarding', member_id)
            return

        old_member = Member._copy(member)
        user_update = member._presence_update(data=data, user=user)
        if user_update:
            self.dispatch('user_update', user_update[0], user_update[1])

        self.dispatch('presence_update', old_member, member)

    def parse_user_update(self, data) -> None:
        # self.user is *always* cached when this is called
        user: ClientUser = self.user  # type: ignore
        user._update(data)
        ref = self._users.get(user.id)
        if ref:
            ref._update(data)

    def parse_user_settings_update(self, data) -> None:
        new_settings = self.settings
        old_settings = copy.copy(new_settings)
        new_settings._update(data)  # type: ignore
        self.dispatch('settings_update', old_settings, new_settings)
        self.dispatch('internal_settings_update', old_settings, new_settings)

    def parse_user_guild_settings_update(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('USER_GUILD_SETTINGS_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        settings = guild.notification_settings
        if settings is not None:
            old_settings = copy.copy(settings)
            settings._update(data)
        else:
            old_settings = None
            settings = GuildSettings(data=data, state=self)
        self.dispatch('guild_settings_update', old_settings, settings)

    def parse_user_required_action_update(self, data) -> None:
        required_action = try_enum(RequiredActionType, data['required_action'])
        self.dispatch('required_action_update', required_action)

    def parse_sessions_replace(self, data: List[Dict[str, Any]]) -> None:
        overall = MISSING
        this = MISSING
        client_status = {}
        client_activities = {}

        if len(data) == 1:
            overall = this = data[0]

        def parse_key(key):
            index = 0
            while True:
                if key not in client_status:
                    return key
                if not index:
                    key += f'-{str(index + 1)}'
                else:
                    key = key.replace(str(index), str(index + 1))
                index += 1

        for session in data:
            if session['session_id'] == 'all':
                overall = session
                data.remove(session)
                continue
            elif session['session_id'] == self.session_id:
                this = session
                continue
            key = parse_key(intern(session['client_info']['client']))
            client_status[key] = intern(session['status'])
            client_activities[key] = tuple(session['activities'])

        if overall is MISSING and this is MISSING:
            _log.debug('SESSIONS_REPLACE has weird data: %s.', data)
            return  # ._.
        elif overall is MISSING:
            overall = this
        elif this is MISSING:
            this = overall

        client_status[None] = overall['status']
        client_activities[None] = tuple(overall['activities'])
        client_activities['this'] = tuple(this['activities'])
        client_status['this'] = this['status']

        client = self.client
        client._client_status = client_status
        client._client_activities = client_activities
        client._session_count = len(data)

    def parse_invite_create(self, data) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch('invite_create', invite)

    def parse_invite_delete(self, data) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch('invite_delete', invite)

    def parse_channel_delete(self, data) -> None:
        guild = self._get_guild(utils._get_as_snowflake(data, 'guild_id'))
        channel_id = int(data['id'])
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                guild._remove_channel(channel)
                self.dispatch('guild_channel_delete', channel)
        else:
            channel = self._get_private_channel(channel_id)
            if channel is not None:
                self._remove_private_channel(channel)
                self.dispatch('private_channel_delete', channel)

    def parse_channel_update(self, data) -> None:
        channel_type = try_enum(ChannelType, data.get('type'))
        channel_id = int(data['id'])
        if channel_type is ChannelType.group:
            channel = self._get_private_channel(channel_id)
            old_channel = copy.copy(channel)
            # The channel is a GroupChannel
            channel._update_group(data)  # type: ignore
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
                _log.debug('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
        else:
            _log.debug('CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_channel_create(self, data) -> None:
        factory, _ = _channel_factory(data['type'])
        if factory is None:
            _log.debug('CHANNEL_CREATE referencing an unknown channel type %s. Discarding.', data['type'])
            return

        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is not None:
            # the factory can't be a DMChannel or GroupChannel here
            channel = factory(guild=guild, state=self, data=data)  # type: ignore
            guild._add_channel(channel)  # type: ignore
            self.dispatch('guild_channel_create', channel)
        else:
            _log.debug('CHANNEL_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

    def parse_channel_pins_update(self, data) -> None:
        channel_id = int(data['channel_id'])
        try:
            guild = self._get_guild(int(data['guild_id']))
        except KeyError:
            guild = None
            channel = self._get_private_channel(channel_id)
        else:
            channel = guild and guild._resolve_channel(channel_id)

        if channel is None:
            _log.debug('CHANNEL_PINS_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        last_pin = utils.parse_time(data['last_pin_timestamp']) if data['last_pin_timestamp'] else None

        if guild is None:
            self.dispatch('private_channel_pins_update', channel, last_pin)
        else:
            self.dispatch('guild_channel_pins_update', channel, last_pin)

    def parse_channel_recipient_add(self, data) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        user = self.store_user(data['user'])
        channel.recipients.append(user)
        self.dispatch('group_join', channel, user)

    def parse_channel_recipient_remove(self, data) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        user = self.store_user(data['user'])
        try:
            channel.recipients.remove(user)
        except ValueError:
            pass
        else:
            self.dispatch('group_remove', channel, user)

    def parse_thread_create(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        existing = guild.get_thread(int(data['id']))
        if existing is not None:  # Shouldn't happen
            old = existing._update(data)
            if old is not None:
                self.dispatch('thread_update', old, existing)
        else:
            thread = Thread(guild=guild, state=self, data=data)
            guild._add_thread(thread)
            if data.get('newly_created', False):
                self.dispatch('thread_create', thread)
            else:
                self.dispatch('thread_join', thread)

    def parse_thread_update(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_UPDATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        existing = guild.get_thread(int(data['id']))
        if existing is not None:
            old = existing._update(data)
            if old is not None:
                self.dispatch('thread_update', old, existing)
        else:  # Shouldn't happen
            thread = Thread(guild=guild, state=self, data=data)
            guild._add_thread(thread)

    def parse_thread_delete(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_DELETE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        thread_id = int(data['id'])
        thread = guild.get_thread(thread_id)
        if thread is not None:
            guild._remove_thread(thread)  # type: ignore
            self.dispatch('thread_delete', thread)

    def parse_thread_list_sync(self, data) -> None:
        self_id = self.self_id
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_LIST_SYNC referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        try:
            channel_ids = set(data['channel_ids'])
        except KeyError:
            channel_ids = None
            threads = guild._threads.copy()
        else:
            threads = guild._filter_threads(channel_ids)

        new_threads = {}
        for d in data.get('threads', []):
            if (thread := threads.pop(int(d['id']), None)) is not None:
                old = thread._update(d)
                if old is not None:
                    self.dispatch('thread_update', old, thread)  # Honestly not sure if this is right
            else:
                thread = Thread(guild=guild, state=self, data=d)
                new_threads[thread.id] = thread
        old_threads = [t for t in threads.values() if t.id not in new_threads]

        for member in data.get('members', []):
            try:  # Note: member['id'] is the thread_id
                thread = threads[member['id']]
            except KeyError:
                continue
            else:
                thread._add_member(ThreadMember(thread, member))

        for k in new_threads.values():
            guild._add_thread(k)

        for k in old_threads:
            del guild._threads[k.id]
            self.dispatch('thread_delete', k)  # Again, not sure

        for message in data.get('most_recent_messages', []):
            guild_id = utils._get_as_snowflake(message, 'guild_id')
            channel, _ = self._get_guild_channel(message)
            if guild_id in self._unavailable_guilds:  # I don't know how I feel about this :(
                continue

            # channel will be the correct type here
            message = Message(channel=channel, data=message, state=self)  # type: ignore
            if self._messages is not None:
                self._messages.append(message)

    def parse_thread_member_update(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.debug('THREAD_MEMBER_UPDATE referencing an unknown thread ID: %s. Discarding.', thread_id)
            return

        member = ThreadMember(thread, data)
        thread.me = member

    def parse_thread_members_update(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_MEMBERS_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.debug('THREAD_MEMBERS_UPDATE referencing an unknown thread ID: %s. Discarding.', thread_id)
            return

        added_members = [ThreadMember(thread, d) for d in data.get('added_members', [])]
        removed_member_ids = [int(x) for x in data.get('removed_member_ids', [])]
        self_id = self.self_id
        for member in added_members:
            if member.id != self_id:
                thread._add_member(member)
                self.dispatch('thread_member_join', member)
            else:
                thread.me = member
                self.dispatch('thread_join', thread)

        for member_id in removed_member_ids:
            member = thread._pop_member(member_id)
            if member_id != self_id:
                if member is not None:
                    self.dispatch('thread_member_remove', member)
                else:
                    self.dispatch('raw_thread_member_remove', thread, member_id)
            else:
                self.dispatch('thread_remove', thread)

    def parse_guild_member_add(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = Member(guild=guild, data=data, state=self)
        if self.member_cache_flags.joined:
            guild._add_member(member)

        try:
            guild._member_count += 1
        except AttributeError:
            pass

        # self.dispatch('member_join', member)

        if (presence := data.get('presence')) is not None:
            old_member = copy.copy(member)
            member._presence_update(presence, tuple())
            self.dispatch('presence_update', old_member, member)

    def parse_guild_member_remove(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                guild._member_count -= 1
            except AttributeError:
                pass

            user_id = int(data['user']['id'])
            member = guild.get_member(user_id)
            if member is not None:
                guild._remove_member(member)  # type: ignore
                # self.dispatch('member_remove', member)
        else:
            _log.debug('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_member_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        user = data['user']
        user_id = int(user['id'])
        if guild is None:
            _log.debug('GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = guild.get_member(user_id)
        if member is not None:
            old_member = Member._copy(member)
            member._update(data)
            user_update = member._update_inner_user(user)
            if user_update:
                self.dispatch('user_update', user_update[0], user_update[1])

            self.dispatch('member_update', old_member, member)
        else:
            if self.member_cache_flags.joined:
                member = Member(data=data, guild=guild, state=self)

                # Force an update on the inner user if necessary
                user_update = member._update_inner_user(user)
                if user_update:
                    self.dispatch('user_update', user_update[0], user_update[1])

                guild._add_member(member)
            _log.debug('GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)

        if (presence := data.get('presence')) is not None:
            member._presence_update(presence, tuple())
            if old_member is not None:
                self.dispatch('presence_update', old_member, member)

    def parse_guild_sync(self, data) -> None:
        print('I noticed you triggered a `GUILD_SYNC`.\nIf you want to share your secrets, please feel free to email me.')

    def parse_guild_member_list_update(self, data) -> None:  # Rewrite incoming...
        self.dispatch('raw_guild_member_list_update', data)
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_LIST_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        ops = data['ops']

        if data['member_count'] > 0:
            guild._member_count = data['member_count']

        online_count = 0
        for group in data['groups']:
            online_count += group['count'] if group['id'] != 'offline' else 0
        guild._online_count = online_count

        for opdata in ops:
            op = opdata['op']
            # There are two OPs I'm not parsing.
            # INVALIDATE: Usually invalid (hehe).
            # DELETE: Sends the index, not the user ID, so I can't do anything with
            # it unless I keep a seperate list of the member sidebar (maybe in future).

            if op == 'SYNC':
                members = [Member(guild=guild, data=member['member'], state=self) for member in [item for item in opdata.get('items', []) if 'member' in item]]

                member_dict = {str(member.id): member for member in members}
                for presence in [item for item in opdata.get('items', []) if 'member' in item]:
                    presence = presence['member']['presence']
                    user = presence['user']
                    member_id = user['id']
                    member = member_dict.get(member_id)
                    member._presence_update(presence, user)

                for member in members:
                    guild._add_member(member)

            if op == 'INSERT':
                if 'member' not in opdata['item']:
                    # Hoisted role INSERT
                    return

                mdata = opdata['item']['member']
                user = mdata['user']
                user_id = int(user['id'])

                member = guild.get_member(user_id)
                if member is not None:  # INSERTs are also sent when a user changes range
                    old_member = Member._copy(member)
                    member._update(mdata)
                    user_update = member._update_inner_user(user)
                    if 'presence' in mdata:
                        presence = mdata['presence']
                        user = presence['user']
                        member_id = user['id']
                        member._presence_update(presence, user)
                    if user_update:
                        self.dispatch('user_update', user_update[0], user_update[1])

                    self.dispatch('member_update', old_member, member)
                else:
                    member = Member(data=mdata, guild=guild, state=self)
                    guild._add_member(member)

            if op == 'UPDATE':
                if 'member' not in opdata['item']:
                    # Hoisted role UPDATE
                    return

                mdata = opdata['item']['member']
                user = mdata['user']
                user_id = int(user['id'])

                member = guild.get_member(user_id)
                if member is not None:
                    old_member = Member._copy(member)
                    member._update(mdata)
                    user_update = member._update_inner_user(user)
                    if 'presence' in mdata:
                        presence = mdata['presence']
                        user = presence['user']
                        member_id = user['id']
                        member._presence_update(presence, user)
                    if user_update:
                        self.dispatch('user_update', user_update[0], user_update[1])

                    self.dispatch('member_update', old_member, member)
                else:
                    _log.debug('GUILD_MEMBER_LIST_UPDATE type UPDATE referencing an unknown member ID: %s. Discarding.', user_id)

    def parse_guild_application_command_counts_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_APPLICATION_COMMAND_COUNTS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        guild.command_counts = CommandCounts(data.get(0, 0), data.get(1, 0), data.get(2, 0))

    def parse_guild_emojis_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            self._emojis.pop(emoji.id, None)
        # guild won't be None here
        guild.emojis = tuple(map(lambda d: self.store_emoji(guild, d), data['emojis']))  # type: ignore
        self.dispatch('guild_emojis_update', guild, before_emojis, guild.emojis)

    def parse_guild_stickers_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_STICKERS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_stickers = guild.stickers
        for emoji in before_stickers:
            self._stickers.pop(emoji.id, None)
        # guild won't be None here
        guild.stickers = tuple(map(lambda d: self.store_sticker(guild, d), data['stickers']))  # type: ignore
        self.dispatch('guild_stickers_update', guild, before_stickers, guild.stickers)

    def _get_create_guild(self, data):
        guild = self._get_guild(int(data['id']))
        # Discord being Discord sends a GUILD_CREATE after an OPCode 14 is sent (a la bots)
        # However, we want that if we forced a GUILD_CREATE for an unavailable guild
        if guild is not None:
            guild._from_data(data)
            return

        return self._add_guild_from_data(data)

    def is_guild_evicted(self, guild) -> bool:
        return guild.id not in self._guilds

    async def chunk_guild(self, guild, *, wait=True, cache=None):
        cache = cache or self.member_cache_flags.joined
        request = self._chunk_requests.get(guild.id)
        if request is None:
            self._chunk_requests[guild.id] = request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
            await self.chunker(guild.id, nonce=request.nonce)

        if wait:
            return await request.wait()
        return request.get_future()

    async def _parse_and_dispatch(self, guild, *, chunk, subscribe) -> None:
        self._queued_guilds[guild.id] = guild

        if chunk:
            try:
                await asyncio.wait_for(self.chunk_guild(guild), timeout=60.0)
            except asyncio.TimeoutError:
                _log.info('Somehow timed out waiting for chunks for guild %s.', guild.id)

        if subscribe:
            await guild.subscribe(max_online=self._subscription_options.max_online)

        self._queued_guilds.pop(guild.id)

        # Dispatch available/join depending on circumstances
        if guild.id in self._unavailable_guilds:
            type = self._unavailable_guilds.pop(guild.id)
            if type is UnavailableGuildType.existing:
                self.dispatch('guild_available', guild)
            else:
                self.dispatch('guild_join', guild)
        else:
            self.dispatch('guild_join', guild)

    def parse_guild_create(self, data):
        guild = self._get_create_guild(data)

        if guild is None:
            return

        if self._request_guilds:
            asyncio.ensure_future(self.request_guild(guild.id), loop=self.loop)

        # Chunk/subscribe if needed
        needs_chunking, needs_subscribing = self._guild_needs_chunking(guild), self._guild_needs_subscribing(guild)
        asyncio.ensure_future(self._parse_and_dispatch(guild, chunk=needs_chunking, subscribe=needs_subscribing), loop=self.loop)

    def parse_guild_update(self, data) -> None:
        guild = self._get_guild(int(data['id']))
        if guild is not None:
            old_guild = copy.copy(guild)
            guild._from_data(data)
            self.dispatch('guild_update', old_guild, guild)
        else:
            _log.debug('GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.', data['id'])

    def parse_guild_delete(self, data) -> None:
        guild = self._get_guild(int(data['id']))
        if guild is None:
            _log.debug('GUILD_DELETE referencing an unknown guild ID: %s. Discarding.', data['id'])
            return

        if data.get('unavailable', False):
            # GUILD_DELETE with unavailable being True means that the
            # guild that was available is now currently unavailable
            guild.unavailable = True
            self.dispatch('guild_unavailable', guild)
            return

        # Cleanup the message cache
        if self._messages is not None:
            self._messages: Optional[Deque[Message]] = deque(
                (msg for msg in self._messages if msg.guild != guild), maxlen=self.max_messages
            )

        self._remove_guild(guild)
        self.dispatch('guild_remove', guild)

    def parse_guild_ban_add(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                user = User(data=data['user'], state=self)
            except KeyError:
                pass
            else:
                member = guild.get_member(user.id) or user
                self.dispatch('member_ban', guild, member)

    def parse_guild_ban_remove(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None and 'user' in data:
            user = self.store_user(data['user'])
            self.dispatch('member_unban', guild, user)

    def parse_guild_role_create(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        role_data = data['role']
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.dispatch('guild_role_create', role)

    def parse_guild_role_delete(self, data) -> None:
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
            _log.debug('GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_role_update(self, data) -> None:
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
            _log.debug('GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_members_chunk(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        presences = data.get('presences', [])

        # The guild won't be None here
        members = [Member(guild=guild, data=member, state=self) for member in data.get('members', [])]  # type: ignore
        _log.debug('Processed a chunk for %s members in guild ID %s.', len(members), guild_id)

        if presences:
            member_dict = {str(member.id): member for member in members}
            for presence in presences:
                user = presence['user']
                member_id = user['id']
                member = member_dict.get(member_id)
                if member is not None:
                    member._presence_update(presence, user)

        complete = data.get('chunk_index', 0) + 1 == data.get('chunk_count')
        self.process_chunk_requests(guild_id, data.get('nonce'), members, complete)

    def parse_guild_integrations_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            self.dispatch('guild_integrations_update', guild)
        else:
            _log.debug('GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_integration_create(self, data) -> None:
        guild_id = int(data.pop('guild_id'))
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data['type'])
            integration = cls(data=data, guild=guild)
            self.dispatch('integration_create', integration)
        else:
            _log.debug('INTEGRATION_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_integration_update(self, data) -> None:
        guild_id = int(data.pop('guild_id'))
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data['type'])
            integration = cls(data=data, guild=guild)
            self.dispatch('integration_update', integration)
        else:
            _log.debug('INTEGRATION_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_integration_delete(self, data) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            raw = RawIntegrationDeleteEvent(data)
            self.dispatch('raw_integration_delete', raw)
        else:
            _log.debug('INTEGRATION_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_webhooks_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('WEBHOOKS_UPDATE referencing an unknown guild ID: %s. Discarding', data['guild_id'])
            return

        channel = guild.get_channel(int(data['channel_id']))
        if channel is not None:
            self.dispatch('webhooks_update', channel)
        else:
            _log.debug('WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])

    def parse_stage_instance_create(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            stage_instance = StageInstance(guild=guild, state=self, data=data)
            guild._stage_instances[stage_instance.id] = stage_instance
            self.dispatch('stage_instance_create', stage_instance)
        else:
            _log.debug('STAGE_INSTANCE_CREATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_stage_instance_update(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            stage_instance = guild._stage_instances.get(int(data['id']))
            if stage_instance is not None:
                old_stage_instance = copy.copy(stage_instance)
                stage_instance._update(data)
                self.dispatch('stage_instance_update', old_stage_instance, stage_instance)
            else:
                _log.debug('STAGE_INSTANCE_UPDATE referencing unknown stage instance ID: %s. Discarding.', data['id'])
        else:
            _log.debug('STAGE_INSTANCE_UPDATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_stage_instance_delete(self, data) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                stage_instance = guild._stage_instances.pop(int(data['id']))
            except KeyError:
                pass
            else:
                self.dispatch('stage_instance_delete', stage_instance)
        else:
            _log.debug('STAGE_INSTANCE_DELETE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_call_create(self, data) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        message = self._call_message_cache.pop((int(data['message_id'])), None)
        call = channel._add_call(state=self, message=message, channel=channel, **data)
        self._calls[channel.id] = call
        self.dispatch('call_create', call)

    def parse_call_update(self, data) -> None:
        call = self._calls.get(int(data['channel_id']))
        call._update(**data)
        self.dispatch('call_update', call)

    def parse_call_delete(self, data) -> None:
        call = self._calls.pop(int(data['channel_id']), None)
        if call is not None:
            call._deleteup()
        self.dispatch('call_delete', call)

    def parse_voice_state_update(self, data) -> None:
        guild = self._get_guild(utils._get_as_snowflake(data, 'guild_id'))
        channel_id = utils._get_as_snowflake(data, 'channel_id')
        session_id = data['session_id']
        flags = self.member_cache_flags
        # self.user is *always* cached when this is called
        self_id = self.user.id  # type: ignore

        if int(data['user_id']) == self_id:
            voice = self._get_voice_client(guild.id)
            if voice is not None:
                coro = voice.on_voice_state_update(data)
                asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice state update handler'))

        if guild is not None:
            member, before, after = guild._update_voice_state(data, channel_id)  # type: ignore
            if member is not None:
                if flags.voice:
                    if channel_id is None and flags._voice_only and member.id != self_id:
                        # Member doesn't meet the Snowflake protocol currently
                        guild._remove_member(member)  # type: ignore
                    elif channel_id is not None:
                        guild._add_member(member)

                self.dispatch('voice_state_update', member, before, after)
            else:
                _log.debug('VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', data['user_id'])
        else:
            user, before, after = self._update_voice_state(data)
            self.dispatch('voice_state_update', user, before, after)

    def parse_voice_server_update(self, data) -> None:
        key_id = utils._get_as_snowflake(data, 'guild_id')
        if key_id is None:
            key_id = self.user.id

        vc = self._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_voice_server_update(data)
            asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice server update handler'))

    def parse_typing_start(self, data) -> None:
        channel, guild = self._get_guild_channel(data)
        if channel is not None:
            member = None
            user_id = utils._get_as_snowflake(data, 'user_id')
            if isinstance(channel, DMChannel):
                member = channel.recipient

            elif isinstance(channel, (Thread, TextChannel)) and guild is not None:
                # user_id won't be None
                member = guild.get_member(user_id)  # type: ignore

                if member is None:
                    member_data = data.get('member')
                    if member_data:
                        member = Member(data=member_data, state=self, guild=guild)

            elif isinstance(channel, GroupChannel):
                member = utils.find(lambda x: x.id == user_id, channel.recipients)

            if member is not None:
                timestamp = datetime.datetime.fromtimestamp(data.get('timestamp'), tz=datetime.timezone.utc)
                self.dispatch('typing', channel, member, timestamp)

    def parse_relationship_add(self, data) -> None:
        key = int(data['id'])
        old = self.user.get_relationship(key)
        new = Relationship(state=self, data=data)
        self._relationships[key] = new
        if old is not None:
            self.dispatch('relationship_update', old, new)
        else:
            self.dispatch('relationship_add', new)

    def parse_relationship_remove(self, data) -> None:
        key = int(data['id'])
        try:
            old = self._relationships.pop(key)
        except KeyError:
            pass
        else:
            self.dispatch('relationship_remove', old)

    def parse_interaction_create(self, data) -> None:
        type, name = self._interactions.pop(data['nonce'], (0, None))
        i = Interaction._from_self(type=type, user=self.user, name=name, **data)  # type: ignore
        self._interactions[i.id] = i
        self.dispatch('interaction_create', i)

    def parse_interaction_success(self, data) -> None:
        id = int(data['id'])
        i = self._interactions.pop(id, None)
        if i is None:
            i = Interaction(**data)
        i.successful = True  # type: ignore
        self.dispatch('interaction_finish', i)

    def parse_interaction_failed(self, data) -> None:
        id = int(data['id'])
        i = self._interactions.pop(id, None)
        if i is None:
            i = Interaction(**data)
        i.successful = False
        self.dispatch('interaction_finish', i)

    def _get_reaction_user(self, channel: MessageableChannel, user_id: int) -> Optional[Union[User, Member]]:
        if isinstance(channel, TextChannel):
            return channel.guild.get_member(user_id)
        return self.get_user(user_id)

    def get_reaction_emoji(self, data) -> Union[Emoji, PartialEmoji]:
        emoji_id = utils._get_as_snowflake(data, 'id')

        if not emoji_id:
            return data['name']

        try:
            return self._emojis[emoji_id]
        except KeyError:
            return PartialEmoji.with_state(self, animated=data.get('animated', False), id=emoji_id, name=data['name'])

    def _upgrade_partial_emoji(self, emoji: PartialEmoji) -> Union[Emoji, PartialEmoji, str]:
        emoji_id = emoji.id
        if not emoji_id:
            return emoji.name
        try:
            return self._emojis[emoji_id]
        except KeyError:
            return emoji

    def get_channel(self, id: Optional[int]) -> Optional[Union[Channel, Thread]]:
        if id is None:
            return None

        pm = self._get_private_channel(id)
        if pm is not None:
            return pm

        for guild in self.guilds:
            channel = guild._resolve_channel(id)
            if channel is not None:
                return channel

    def create_message(
        self, *, channel: Union[TextChannel, Thread, DMChannel, GroupChannel, PartialMessageable], data: MessagePayload
    ) -> Message:
        return Message(state=self, channel=channel, data=data)
