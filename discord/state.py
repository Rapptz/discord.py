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
from collections import deque, OrderedDict
import copy
import datetime
import logging
from typing import (
    Dict,
    Final,
    Optional,
    TYPE_CHECKING,
    Union,
    Callable,
    Any,
    List,
    TypeVar,
    Coroutine,
    Tuple,
    Deque,
    Literal,
    overload,
    Sequence,
    Set,
)
import weakref
import inspect
from math import ceil

from discord_protos import UserSettingsType

from .errors import ClientException, InvalidData, NotFound
from .guild import ApplicationCommandCounts, Guild
from .activity import BaseActivity, create_activity, Session
from .user import User, ClientUser, Note
from .emoji import Emoji
from .mentions import AllowedMentions
from .partial_emoji import PartialEmoji
from .message import Message
from .channel import *
from .channel import _channel_factory, _private_channel_factory
from .raw_models import *
from .member import Member
from .relationship import Relationship, FriendSuggestion
from .role import Role
from .enums import (
    ChannelType,
    MessageType,
    PaymentSourceType,
    ReadStateType,
    RelationshipType,
    RequiredActionType,
    Status,
    try_enum,
)
from . import utils
from .flags import MemberCacheFlags
from .invite import Invite
from .integrations import _integration_factory
from .scheduled_event import ScheduledEvent
from .stage_instance import StageInstance
from .threads import Thread, ThreadMember
from .sticker import GuildSticker
from .settings import UserSettings, GuildSettings, ChannelSettings, TrackingSettings
from .interactions import Interaction
from .permissions import Permissions, PermissionOverwrite
from .modal import Modal
from .member import VoiceState
from .application import IntegrationApplication, PartialApplication, Achievement
from .connections import Connection
from .payments import Payment
from .entitlements import Entitlement, Gift
from .guild_premium import PremiumGuildSubscriptionSlot
from .library import LibraryApplication
from .automod import AutoModRule, AutoModAction
from .audit_logs import AuditLogEntry
from .read_state import ReadState
from .tutorial import Tutorial
from .experiment import UserExperiment, GuildExperiment

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake as abcSnowflake
    from .activity import ActivityTypes
    from .message import MessageableChannel
    from .guild import GuildChannel
    from .http import HTTPClient
    from .voice_client import VoiceProtocol
    from .client import Client
    from .gateway import DiscordWebSocket
    from .calls import Call

    from .types.automod import AutoModerationRule, AutoModerationActionExecution
    from .types.snowflake import Snowflake
    from .types.activity import Activity as ActivityPayload
    from .types.application import (
        Achievement as AchievementPayload,
        IntegrationApplication as IntegrationApplicationPayload,
    )
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import User as UserPayload, PartialUser as PartialUserPayload
    from .types.emoji import Emoji as EmojiPayload, PartialEmoji as PartialEmojiPayload
    from .types.sticker import GuildSticker as GuildStickerPayload
    from .types.guild import BaseGuild as BaseGuildPayload, Guild as GuildPayload
    from .types.message import (
        Message as MessagePayload,
        MessageSearchResult as MessageSearchResultPayload,
        PartialMessage as PartialMessagePayload,
    )
    from .types import gateway as gw
    from .types.voice import BaseVoiceState as VoiceStatePayload
    from .types.activity import ClientStatus as ClientStatusPayload

    T = TypeVar('T')
    PrivateChannel = Union[DMChannel, GroupChannel]
    Channel = Union[GuildChannel, PrivateChannel, PartialMessageable]

MISSING = utils.MISSING
_log = logging.getLogger(__name__)


class ChunkRequest:
    __slots__ = (
        'guild_id',
        'resolver',
        'loop',
        'limit',
        'remaining',
        'cache',
        'oneshot',
        'nonce',
        'buffer',
        'last_buffer',
        'waiters',
    )

    def __init__(
        self,
        guild_id: int,
        loop: asyncio.AbstractEventLoop,
        resolver: Callable[[int], Any],
        *,
        limit: Optional[int] = None,
        cache: bool = True,
        oneshot: bool = True,
        nonce: Optional[str] = None,
    ) -> None:
        self.guild_id: int = guild_id
        self.resolver: Callable[[int], Any] = resolver
        self.loop: asyncio.AbstractEventLoop = loop
        self.limit: Optional[int] = limit
        self.remaining: int = limit or 0
        self.cache: bool = cache
        self.oneshot: bool = oneshot
        self.nonce: str = nonce or utils._generate_nonce()
        self.buffer: List[Member] = []
        self.last_buffer: Optional[List[Member]] = None
        self.waiters: List[asyncio.Future[List[Member]]] = []

    def add_members(self, members: List[Member]) -> None:
        unique_members = set(members)
        if self.limit is not None:
            if self.remaining <= 0:
                return

            members = list(unique_members)[: self.remaining]
            self.remaining -= len(unique_members)
        else:
            members = list(unique_members)

        self.buffer.extend(members)

        if self.cache:
            guild = self.resolver(self.guild_id)
            if guild is None:
                return

            for member in members:
                guild._add_member(member)

        if not self.oneshot:
            self.last_buffer = members

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
        result = self.buffer if self.oneshot else self.last_buffer or self.buffer
        for future in self.waiters:
            if not future.done():
                future.set_result(result)


class MemberSidebar:
    __slots__ = (
        'guild',
        'channels',
        'chunk',
        'delay',
        'cache',
        'loop',
        'safe_override',
        'ranges',
        'subscribing',
        'buffer',
        'exception',
        'waiters',
    )

    def __init__(
        self,
        guild: Guild,
        channels: List[abcSnowflake],
        *,
        chunk: bool,
        delay: Union[int, float],
        cache: bool,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.guild = guild
        self.cache = cache
        self.chunk = chunk
        self.delay = delay
        self.loop = loop
        self.safe_override = False  # >.<

        self.channels = [str(channel.id) for channel in (channels or self.get_channels(1 if chunk else 5))]
        self.ranges = self.get_ranges()
        self.subscribing: bool = False
        self.buffer: List[Member] = []
        self.exception: Optional[Exception] = None
        self.waiters: List[asyncio.Future[Optional[List[Member]]]] = []

    @property
    def limit(self) -> int:
        guild = self.guild
        members = guild._presence_count if guild._offline_members_hidden else guild._member_count or 0
        # Ensure groups are accounted for
        return (members or 0) + len([role for role in guild.roles if role.hoist]) + 2

    @property
    def state(self) -> ConnectionState:
        return self.guild._state

    @property
    def safe(self):
        return self.safe_override or (self.guild._member_count or 0) >= 75000

    @staticmethod
    def amalgamate(original: Tuple[int, int], value: Tuple[int, int]) -> Tuple[int, int]:
        return original[0], value[1] - 99

    def get_ranges(self) -> List[Tuple[int, int]]:
        chunk = 100
        end = 99
        amount = self.limit
        if amount is None:
            raise RuntimeError('Member/presence count required to compute ranges')

        ceiling = ceil(amount / chunk) * chunk
        ranges = []
        for i in range(0, int(ceiling / chunk)):
            min = i * chunk
            max = min + end
            ranges.append((min, max))

        return ranges

    def get_current_ranges(self) -> List[Tuple[int, int]]:
        ranges = self.ranges
        ret = []

        for _ in range(3):
            if self.safe:
                try:
                    ret.append(ranges.pop(0))
                except IndexError:
                    break
            else:
                try:
                    current = ranges.pop(0)
                except IndexError:
                    break
                for _ in range(3):
                    try:
                        current = self.amalgamate(current, ranges.pop(0))
                    except IndexError:
                        break
                ret.append(current)

        return ret

    def get_channels(self, amount: int) -> List[abcSnowflake]:
        guild = self.guild
        ret = set()

        channels = [
            channel
            for channel in self.guild.channels
            if channel.permissions_for(guild.default_role).read_messages  # "everyone" id
            and channel.permissions_for(guild.me).read_messages  # type: ignore
        ]
        if guild.rules_channel is not None:  # micro-optimization
            channels.insert(0, guild.rules_channel)

        while len(ret) < amount and channels:
            channel = channels.pop()
            for role in guild.roles:
                if not channel.permissions_for(role).read_messages:
                    break
            else:
                for ow in channel._overwrites:
                    if ow.is_member():
                        allow = Permissions(ow.allow)
                        deny = Permissions(ow.deny)
                        overwrite = PermissionOverwrite.from_pair(allow, deny)
                        if not overwrite.read_messages:
                            break
                ret.add(channel)

        return list(ret)

    def add_members(self, members: List[Member]) -> None:
        members = list(set(members))
        self.buffer.extend(members)
        if self.cache:
            guild = self.guild
            for member in members:
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
                if self.exception:
                    future.set_exception(self.exception)
                else:
                    future.set_result(self.buffer)

        try:
            del self.state._scrape_requests[self.guild.id]
        except KeyError:
            pass

    def start(self):
        self.loop.create_task(self.wrapper())

    async def wrapper(self):
        try:
            await self.scrape()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            _log.warning('Member list scraping failed for guild ID %s (%s).', self.guild.id, exc)
            self.exception = exc
        finally:
            self.done()

    async def scrape(self):
        self.subscribing = True
        delay = self.delay
        channels = self.channels
        guild = self.guild
        state = guild._state

        while self.subscribing:
            requests = {}
            for channel in channels:
                ranges = self.get_current_ranges()
                if not ranges:
                    self.subscribing = False
                    break
                requests[channel] = ranges
            if not self.subscribing and not requests:
                break

            if not requests:
                raise ClientException('Failed to automatically choose channels; please specify them manually')

            def predicate(data):
                return int(data['guild_id']) == guild.id and any(op['op'] == 'SYNC' for op in data['ops'])

            await state.subscriptions.subscribe_to_channels(guild, requests, replace=True)

            try:
                await asyncio.wait_for(
                    state.ws.wait_for('GUILD_MEMBER_LIST_UPDATE', predicate), timeout=state._chunk_timeout(guild)
                )
            except asyncio.TimeoutError:
                r = tuple(requests.values())[-1][-1]
                if self.limit in range(r[0], r[1]) or self.limit < r[1]:
                    self.subscribing = False
                    break
                else:
                    if self.safe:
                        raise InvalidData('Did not receive a response from Discord')

                    # Sometimes servers require safe mode (they used to have 75k+ members)
                    # so if we don't get a response we force safe mode and try again
                    self.safe_override = True
                    self.ranges = self.get_ranges()
                    await self.scrape()
                    return

            await asyncio.sleep(delay)

            r = tuple(requests.values())[-1][-1]
            if self.limit in range(r[0], r[1]) or self.limit < r[1]:
                self.subscribing = False
                break

        state.loop.create_task(state.subscriptions.subscribe_to_channels(guild, {}, replace=True))


class GuildSubscriptions:
    """A bit of documentation on guild subscriptions:

    Client can subscribe to the following "features":
    - ``typing``: whether the client receives TYPING_START events
    - ``threads``: whether the client receives thread events for threads the user is not in -- probably wrong
      - The client immediately receives a THREAD_LIST_SYNC event with all the threads in the guild
    - ``activities``: not sure what this does yet
    - ``member_updates``: whether the client receives member events (GUILD_MEMBER_ADD, GUILD_MEMBER_UPDATE, GUILD_MEMBER_REMOVE)

    The client is automatically subscribed to all guilds with < 75k members on connect. For guilds the client is not subscribed to,
    it will not receive non-stateful events (e.g. MESSAGE_CREATE, MESSAGE_UPDATE, MESSAGE_DELETE, etc.).
    Additionally, it will receive the PASSIVE_UPDATE_V1 event to keep voice states and channel unreads up-to-date.

    Once a client subscribes to the ``typing`` feature, it is considered subscribed to that guild indefinitely. On the first subscribe,
    it will receive a GUILD_CREATE event (for some reason). If subscribing to other features/members without having subscribed to the
    guild, they will have no effect until the client subscribes to it. This comes with the drawback of not receiving a THREAD_LIST_SYNC
    event if the client is not subscribed to the guild, even if it subscribes to it later. It must first unsubscribe from the ``threads``
    event and then resubscribe to it.

    Clients can also subscribe to specific members within a guild using the ``members`` parameter. This is a list of user IDs that
    the client will receive GUILD_MEMBER_ & PRESENCE_ UPDATEs for. This field has no cap except for the max payload size.

    Clients can also subscribe to specific threads' member lists using the ``thread_member_lists`` parameter. After subscribing to a thread
    member list, the client will immediately receive a THREAD_MEMBER_LIST_UPDATE event (sent regardless of whether the client is subscribed
    to the guild) with all the members in the thread. Note that the members received are guild member objects, not thread member objects.
    There is no way for user accounts to request thread member objects. After subscribing to a thread member list, the client will be
    subscribed to all members in the thread, akin to using ``members``. This field has no cap except for the max payload size.

    The client is automatically subscribed to the members of all friends, implicit relationships, and users with open DMs (that it has a mutual guild with)
    for all guilds with less than 75k members at startup. Additionally, the Gateway will repeat this process and subscribe you to a specific DM recipient every time a new DM is opened.
    The above triggers a GUILD_MEMBER_REMOVE event for every guild you do not share with the DM recipient (this behavior used to exist for the ``members`` parameter too).

    Irrespective of subscribed members, clients will always receive GUILD_MEMBER_UPDATE and GUILD_MEMBER_REMOVE events for actions they perform
    (e.g. changing a user's nickname, kicking a user, banning a user, etc.). Additionally, you will also receive GUILD_MEMBER_UPDATE for members
    with an active voice state. This requires that the client is subscribed to the guild.

    Remember that you get presence updates for the overall user presence for all friends and implicit relationships.

    # TODO: there's some weird behavior here that needs to be further investigated:
    a) joining new guilds
    b) adding new friends - I believe you are NOT automatically subscribed to them in every guild (however you still get the overall user presence)
    c) opening new DMs - I'm almost sure this just universally subscribes you
    d) 75k member+ guilds are fucking weird
    """

    # I thought it was 4096 bytes, but this is taken from the client
    MAX_PAYLOAD_SIZE: Final[int] = 15360  # 15 KiB
    TICK_TIMEOUT: Final[float] = 0.5

    __slots__ = (
        '_state',
        '_pending',
        '_task',
        '_blocked',
        '_subscribed',
        '_typing',
        '_threads',
        '_activities',
        '_member_updates',
        '_members',
        '_thread_member_lists',
        '_channels',
    )

    def __init__(self, state: ConnectionState, /) -> None:
        self._state = state
        self._pending: gw.BulkGuildSubscribePayload = {}
        self._task: Optional[asyncio.Task[None]] = None
        self._blocked: bool = False
        self.clear()

    def clear(self) -> None:
        # Feature subscriptions
        self._subscribed: utils.SnowflakeList = utils.SnowflakeList()
        self._typing: utils.SnowflakeList = utils.SnowflakeList()
        self._threads: utils.SnowflakeList = utils.SnowflakeList()
        self._activities: utils.SnowflakeList = utils.SnowflakeList()  # TODO: wtf does this do
        self._member_updates: utils.SnowflakeList = utils.SnowflakeList()

        # Member subscriptions
        self._members: Dict[int, utils.SnowflakeList] = {}
        self._thread_member_lists: Dict[int, utils.SnowflakeList] = {}
        self._channels: Dict[int, Dict[int, List[Tuple[int, int]]]] = {}

    def _initial_update(self, guilds: List[Guild]):
        # The client is subscribed to all guilds with < 75k members on connect
        # This function is currently unused because I don't want to rely on this behavior
        for guild in guilds:
            if guild._member_count and guild._member_count < 75000:
                self._subscribed.add(guild.id)

    def _cancel(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    async def _tick_task(self) -> None:
        try:
            await asyncio.sleep(self.TICK_TIMEOUT)
            await self._flush()
            self._task = None
        except asyncio.CancelledError:
            pass

    def _tick(self) -> None:
        self._cancel()
        if not self._blocked:
            self._task = self._state.loop.create_task(self._tick_task())

    @property
    def empty(self) -> bool:
        return not self._subscribed and not self._pending

    @property
    def blocked(self) -> bool:
        return self._blocked

    @blocked.setter
    def blocked(self, value: bool, /) -> None:
        if self._blocked == value:
            return
        self._blocked = value
        if value:
            self._cancel()
        else:
            self._tick()

    async def _requeue_subscriptions(self):
        # We need to send all our subscriptions again if we reconnect
        pending = self._pending
        subscribed = self._subscribed
        typing = self._typing
        threads = self._threads
        activities = self._activities
        member_updates = self._member_updates
        members = self._members
        thread_member_lists = self._thread_member_lists
        channels = self._channels
        self.clear()

        for guild_id in self._state._guilds:
            if guild_id not in subscribed:
                continue

            key = str(guild_id)
            payload: gw.BaseGuildSubscribePayload = {
                # Ensure we are subscribed to the guild
                'typing': guild_id in typing or guild_id in subscribed,
                'threads': guild_id in threads,
                'activities': guild_id in activities,
                'member_updates': guild_id in member_updates,
                'members': list(members.get(guild_id, ())),
                'thread_member_lists': list(thread_member_lists.get(guild_id, ())),
                'channels': channels.get(guild_id, {}),  # type: ignore
            }
            if key in pending:
                payload.update(pending[key])
            if payload:
                await self._checked_add({key: payload})

    def is_subscribed(self, guild: abcSnowflake, /) -> bool:
        return guild.id in self._subscribed

    def _is_pending_subscribe(self, guild_id: int, /) -> bool:
        key = str(guild_id)
        return guild_id in self._subscribed or (key in self._pending and self._pending[key].get('typing') is True)

    def has_feature(
        self, guild: abcSnowflake, feature: Literal['typing', 'threads', 'activities', 'member_updates'], /
    ) -> bool:
        # getattr is less performant
        if feature == 'typing':
            return self._typing.has(guild.id)
        elif feature == 'threads':
            return self._threads.has(guild.id)
        elif feature == 'activities':
            return self._activities.has(guild.id)
        elif feature == 'member_updates':
            return self._member_updates.has(guild.id)

    def members_for(self, guild: abcSnowflake, /) -> Sequence[int]:
        return utils.SequenceProxy(self._members.get(guild.id, ()))

    def threads_for(self, guild: abcSnowflake, /) -> Sequence[int]:
        return utils.SequenceProxy(self._thread_member_lists.get(guild.id, ()))

    def channels_for(self, guild: abcSnowflake, /) -> Dict[int, List[Tuple[int, int]]]:
        return self._channels.get(guild.id, {}).copy()

    async def _checked_add(self, changes: gw.BulkGuildSubscribePayload, /) -> None:
        # n.b. changes should have a single key
        # We need to check if the new payload is larger than MAX_PAYLOAD_SIZE bytes
        # If it is, we need to flush the old payload and start a new one
        # If there isn't an old payload and the new payload is larger, this is impossible
        EMPTY: Any = {}
        new_payload = self._pending.copy()
        for guild_id, subscriptions in changes.items():
            old = new_payload.get(guild_id, EMPTY)
            new_payload[guild_id] = {**old, **subscriptions}  # type: ignore # ???

        if len(utils._to_json(new_payload)) > self.MAX_PAYLOAD_SIZE:
            if len(utils._to_json(changes)) > self.MAX_PAYLOAD_SIZE:
                raise ValueError('Guild subscription payload too large to send')
            await self._flush()
            self._pending = changes
        else:
            self._pending = new_payload

        self._tick()

    async def _flush(self) -> None:
        payload = self._pending
        if not payload:
            return

        # Only keys that are present in the payload are updated on the backend
        await self._state.ws.bulk_guild_subscribe(payload)
        self._pending = {}
        for key, subscriptions in payload.items():
            guild_id = int(key)
            if subscriptions.get('typing'):
                self._subscribed.add(guild_id)
            for attr, value in subscriptions.items():
                if isinstance(value, bool):
                    record = getattr(self, f'_{attr}')
                    if value:
                        record.add(guild_id)
                    else:
                        record.discard(guild_id)
                elif attr == 'channels':
                    record = self._channels
                    if value:
                        record[guild_id] = value  # type: ignore
                    else:
                        record.pop(guild_id, None)
                else:
                    record = getattr(self, f'_{attr}')
                    if value:
                        record[guild_id] = utils.SnowflakeList(value)  # type: ignore
                    else:
                        record.pop(guild_id, None)

    async def send(self) -> None:
        should_tick = self._task is not None
        await self._flush()
        if should_tick:
            self._tick()

    async def subscribe_to(
        self,
        guild: abcSnowflake,
        /,
        *,
        typing: bool = MISSING,
        threads: bool = MISSING,
        activities: bool = MISSING,
        member_updates: bool = MISSING,
    ):
        # Sanity check
        if not self._is_pending_subscribe(guild.id):
            if typing is MISSING:
                typing = True
            if not typing:
                raise TypeError('Cannot subscribe to guild without subscribing to typing')

        payload: gw.BaseGuildSubscribePayload = {}
        if typing is not MISSING:
            payload['typing'] = typing
        if threads is not MISSING:
            payload['threads'] = threads
        if activities is not MISSING:
            payload['activities'] = activities
        if member_updates is not MISSING:
            payload['member_updates'] = member_updates

        if payload:
            await self._checked_add({str(guild.id): payload})

    async def subscribe_to_members(self, guild: abcSnowflake, /, *members: abcSnowflake, replace: bool = False) -> None:
        if not replace and not members:
            return

        # Sanity check
        if not self._is_pending_subscribe(guild.id):
            raise TypeError('Cannot subscribe to guild without subscribing to typing')

        payload: gw.BaseGuildSubscribePayload = {}
        values: Set[Snowflake] = {member.id for member in members}
        if not replace:
            existing = self._members.get(guild.id)
            if existing:
                values.update(existing)

        payload['members'] = list(values)
        await self._checked_add({str(guild.id): payload})

    async def unsubscribe_from_members(self, guild: abcSnowflake, /, *members: abcSnowflake) -> None:
        # Sanity check
        if not self._is_pending_subscribe(guild.id):
            return

        payload: gw.BaseGuildSubscribePayload = {}
        existing = self._members.get(guild.id)
        to_remove = [member.id for member in members]

        if existing:
            payload['members'] = [member for member in existing if member not in to_remove]
        await self._checked_add({str(guild.id): payload})

    async def subscribe_to_threads(self, guild: abcSnowflake, /, *threads: abcSnowflake, replace: bool = False) -> None:
        if not replace and not threads:
            return

        # Sanity check
        if not self._is_pending_subscribe(guild.id):
            raise TypeError('Cannot subscribe to guild without subscribing to typing')

        payload: gw.BaseGuildSubscribePayload = {}
        values: set[Snowflake] = {thread.id for thread in threads}
        if not replace:
            existing = self._thread_member_lists.get(guild.id)
            if existing:
                values.update(existing)

        payload['thread_member_lists'] = list(values)
        await self._checked_add({str(guild.id): payload})

    async def unsubscribe_from_threads(self, guild: abcSnowflake, /, *threads: abcSnowflake) -> None:
        # Sanity check
        if not self._is_pending_subscribe(guild.id):
            return

        payload: gw.BaseGuildSubscribePayload = {}
        existing = self._thread_member_lists.get(guild.id)
        to_remove = [thread.id for thread in threads]

        if existing:
            payload['thread_member_lists'] = [thread for thread in existing if thread not in to_remove]
        await self._checked_add({str(guild.id): payload})

    async def subscribe_to_channels(
        self, guild: abcSnowflake, /, channels: Dict[Snowflake, List[Tuple[int, int]]], replace: bool = False
    ) -> None:
        if not replace and not channels:
            return

        # Sanity check
        if not self._is_pending_subscribe(guild.id):
            raise TypeError('Cannot subscribe to guild without subscribing to typing')

        payload: gw.BaseGuildSubscribePayload = {}
        values = channels.copy()
        if not replace:
            existing = self._channels.get(guild.id)
            if existing:
                values = {**existing, **channels}

        for channel_id, ranges in channels.items():
            values[channel_id] = ranges

        payload['channels'] = values
        await self._checked_add({str(guild.id): payload})


class ClientStatus:
    __slots__ = ('status', 'desktop', 'mobile', 'web')

    def __init__(self, status: Optional[str] = None, data: Optional[ClientStatusPayload] = None, /) -> None:
        self.status: str = 'offline'
        self.desktop: Optional[str] = None
        self.mobile: Optional[str] = None
        self.web: Optional[str] = None

        if status is not None or data is not None:
            self._update(status or 'offline', data or {})

    def __repr__(self) -> str:
        attrs = [
            ('status', self.status),
            ('desktop', self.desktop),
            ('mobile', self.mobile),
            ('web', self.web),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'

    def _update(self, status: str, data: ClientStatusPayload, /) -> None:
        self.status = status
        self.desktop = data.get('desktop')
        self.mobile = data.get('mobile')
        self.web = data.get('web')

    @classmethod
    def _copy(cls, client_status: Self, /) -> Self:
        self = cls.__new__(cls)  # bypass __init__
        self.status = client_status.status
        self.desktop = client_status.desktop
        self.mobile = client_status.mobile
        self.web = client_status.web
        return self


class Presence:
    __slots__ = ('client_status', 'activities')

    def __init__(self, data: gw.BasePresenceUpdate, state: ConnectionState, /) -> None:
        self.client_status: ClientStatus = ClientStatus(data['status'], data.get('client_status'))
        self.activities: Tuple[ActivityTypes, ...] = tuple(create_activity(d, state) for d in data['activities'])

    def __repr__(self) -> str:
        attrs = [
            ('client_status', self.client_status),
            ('activities', self.activities),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Presence):
            return False
        return self.client_status == other.client_status and self.activities == other.activities

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, Presence):
            return True
        return self.client_status != other.client_status or self.activities != other.activities

    def _update(self, data: gw.BasePresenceUpdate, state: ConnectionState, /) -> None:
        self.client_status._update(data['status'], data.get('client_status'))
        self.activities = tuple(create_activity(d, state) for d in data['activities'])

    @classmethod
    def _offline(cls) -> Self:
        self = cls.__new__(cls)  # bypass __init__
        self.client_status = ClientStatus()
        self.activities = ()
        return self

    @classmethod
    def _copy(cls, presence: Self, /) -> Self:
        self = cls.__new__(cls)  # bypass __init__
        self.client_status = ClientStatus._copy(presence.client_status)
        self.activities = presence.activities
        return self


class FakeClientPresence(Presence):
    __slots__ = ('_state',)

    def __init__(self, state: ConnectionState, /) -> None:
        self._state = state

    def _update(self, data: gw.PresenceUpdateEvent, state: ConnectionState, /) -> None:
        return

    @property
    def client_status(self) -> ClientStatus:
        state = self._state
        status = str(getattr(state.current_session, 'status', 'offline'))
        client_status = {str(session.client): str(session.status) for session in state._sessions.values()}
        return ClientStatus(status, client_status)  # type: ignore

    @property
    def activities(self) -> Tuple[ActivityTypes, ...]:
        return getattr(self._state.current_session, 'activities', ())


async def logging_coroutine(coroutine: Coroutine[Any, Any, T], *, info: str) -> Optional[T]:
    try:
        await coroutine
    except Exception:
        _log.exception('Exception occurred during %s.', info)


class ConnectionState:
    def __init__(
        self,
        *,
        dispatch: Callable[..., Any],
        handlers: Dict[str, Callable[..., Any]],
        hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]],
        http: HTTPClient,
        client: Client,
        **options: Any,
    ) -> None:
        # Set later, after Client.login
        self.loop: asyncio.AbstractEventLoop = utils.MISSING
        self.http: HTTPClient = http
        self.client = client
        self.max_messages: Optional[int] = options.get('max_messages', 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.dispatch: Callable[..., Any] = dispatch
        self.handlers: Dict[str, Callable[..., Any]] = handlers
        self.hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = hooks
        self._ready_task: Optional[asyncio.Task] = None
        self.heartbeat_timeout: float = options.get('heartbeat_timeout', 60.0)

        allowed_mentions = options.get('allowed_mentions')
        if allowed_mentions is not None and not isinstance(allowed_mentions, AllowedMentions):
            raise TypeError('allowed_mentions parameter must be AllowedMentions')

        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions
        self._chunk_requests: Dict[Union[str, int], ChunkRequest] = {}
        self._scrape_requests: Dict[Union[str, int], MemberSidebar] = {}

        activities = options.get('activities', [])
        if not activities:
            activity = options.get('activity')
            if activity is not None:
                activities = [activity]

        if not all(isinstance(activity, BaseActivity) for activity in activities):
            raise TypeError('activity parameter must derive from BaseActivity')
        activities = [activity.to_dict() for activity in activities]

        status = options.get('status', None)
        if status:
            if status is Status.offline:
                status = 'invisible'
            else:
                status = str(status)

        idle_since = options.get('idle_since', None)
        if idle_since:
            if not isinstance(idle_since, datetime.datetime):
                raise TypeError('idle_since parameter must be a datetime.datetime')
            since = int(idle_since.timestamp() * 1000)
        else:
            since = 0

        chunk_guilds = options.get('chunk_guilds_at_startup', MISSING)
        subscribe_guilds = options.get('guild_subscriptions', options.get('request_guilds', True))

        cache_flags = options.get('member_cache_flags', None)
        if cache_flags is None:
            cache_flags = MemberCacheFlags.all()
        else:
            if not isinstance(cache_flags, MemberCacheFlags):
                raise TypeError(f'member_cache_flags parameter must be MemberCacheFlags not {type(cache_flags)!r}')

        if not cache_flags.joined and chunk_guilds:
            raise ClientException('Cannot chunk guilds at startup without a member cache')
        if chunk_guilds and not subscribe_guilds:
            raise ClientException('Cannot chunk guilds at startup without subscribing to them')

        self._chunk_guilds: bool = chunk_guilds if chunk_guilds is not MISSING else (subscribe_guilds and cache_flags.joined)
        self._subscribe_guilds: bool = subscribe_guilds
        self.member_cache_flags: MemberCacheFlags = cache_flags
        self._activities: List[ActivityPayload] = activities
        self._status: Optional[str] = status
        self._afk: bool = options.get('afk', False)
        self._idle_since: int = since

        if cache_flags._empty:
            self.store_user = self.create_user

        self.parsers: Dict[str, Callable[[Any], None]]
        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func

        self.clear(full=True)

    def clear(self, *, full: bool = False) -> None:
        self.user: Optional[ClientUser] = None
        self._users: weakref.WeakValueDictionary[int, User] = weakref.WeakValueDictionary()
        self.settings: Optional[UserSettings] = None
        self.consents: Optional[TrackingSettings] = None
        self.connections: Dict[str, Connection] = {}
        self.pending_payments: Dict[int, Payment] = {}
        self.analytics_token: Optional[str] = None
        self.preferred_rtc_regions: List[str] = []
        self.country_code: Optional[str] = None
        self.api_code_version: int = 0
        self.session_type: Optional[str] = None
        self.auth_session_id: Optional[str] = None
        self.required_action: Optional[RequiredActionType] = None
        self.friend_suggestion_count: int = 0
        self.disclose: List[str] = []
        self._emojis: Dict[int, Emoji] = {}
        self._stickers: Dict[int, GuildSticker] = {}
        self._guilds: Dict[int, Guild] = {}
        self.tutorial: Tutorial = Tutorial.default(self)

        self._read_states: Dict[int, Dict[int, ReadState]] = {}
        self.read_state_version: int = 0

        self.guild_settings: Dict[Optional[int], GuildSettings] = {}
        self.guild_settings_version: int = 0

        self._calls: Dict[int, Call] = {}
        self._call_message_cache: Dict[int, Message] = {}  # Hopefully this won't be a memory leak
        self._voice_clients: Dict[int, VoiceProtocol] = {}
        self._voice_states: Dict[int, VoiceState] = {}

        self._interaction_cache: Dict[Union[int, str], Tuple[int, Optional[str], MessageableChannel]] = {}
        self._interactions: OrderedDict[Union[int, str], Interaction] = OrderedDict()  # LRU of max size 15
        self._relationships: Dict[int, Relationship] = {}
        self._private_channels: Dict[int, PrivateChannel] = {}
        self._private_channels_by_user: Dict[int, DMChannel] = {}

        self._guild_presences: Dict[int, Dict[int, Presence]] = {}
        self._presences: Dict[int, Presence] = {}
        self._sessions: Dict[str, Session] = {}

        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages)
        else:
            self._messages: Optional[Deque[Message]] = None

        self.experiments: Dict[int, UserExperiment] = {}
        self.guild_experiments: Dict[int, GuildExperiment] = {}

        if full:
            self.subscriptions: GuildSubscriptions = GuildSubscriptions(self)

    def process_chunk_requests(self, guild_id: int, nonce: Optional[str], members: List[Member], complete: bool) -> None:
        removed = []
        for key, request in self._chunk_requests.items():
            if request.guild_id == guild_id and request.nonce == nonce:
                request.add_members(members)
                if complete:
                    request.done()
                    if request.oneshot:
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

    async def async_setup(self) -> None:
        pass

    @property
    def session_id(self) -> Optional[str]:
        if self.ws:
            return self.ws.session_id

    @property
    def ws(self):
        return self.client.ws

    @property
    def self_id(self) -> Optional[int]:
        u = self.user
        return u.id if u else None

    @property
    def locale(self) -> str:
        return str(getattr(self.user, 'locale', 'en-US'))

    @property
    def preferred_rtc_region(self) -> str:
        return self.preferred_rtc_regions[0] if self.preferred_rtc_regions else 'us-central'

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        return list(self._voice_clients.values())

    def _update_voice_state(
        self, data: VoiceStatePayload, channel_id: Optional[int]
    ) -> Tuple[Optional[User], VoiceState, VoiceState]:
        user_id = int(data['user_id'])
        user = self.get_user(user_id)
        channel: Optional[Union[DMChannel, GroupChannel]] = self._get_private_channel(channel_id)

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
            vc.main_ws = ws  # type: ignore # Silencing the unknown attribute (ok at runtime).

    def _add_interaction(self, interaction: Interaction) -> None:
        self._interactions[interaction.id] = interaction
        if len(self._interactions) > 15:
            self._interactions.popitem(last=False)

    def store_user(self, data: Union[UserPayload, PartialUserPayload], *, cache: bool = True) -> User:
        # this way is 300% faster than `dict.setdefault`.
        user_id = int(data['id'])
        try:
            return self._users[user_id]
        except KeyError:
            user = User(state=self, data=data)
            if cache:
                self._users[user_id] = user
            return user

    def create_user(self, data: Union[UserPayload, PartialUserPayload], cache: bool = False) -> User:
        user_id = int(data['id'])
        if user_id == self.self_id:
            return self.user  # type: ignore
        return User(state=self, data=data)

    def get_user(self, id: int) -> Optional[User]:
        return self._users.get(id)

    def store_emoji(self, guild: Guild, data: EmojiPayload) -> Emoji:
        # The id will be present here
        emoji_id = int(data['id'])  # type: ignore
        emoji = Emoji(guild=guild, state=self, data=data)
        if not self.is_guild_evicted(guild):
            self._emojis[emoji_id] = emoji
        return emoji

    def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        sticker_id = int(data['id'])
        sticker = GuildSticker(state=self, data=data)
        if not self.is_guild_evicted(guild):
            self._stickers[sticker_id] = sticker
        return sticker

    @property
    def guilds(self) -> Sequence[Guild]:
        return utils.SequenceProxy(self._guilds.values())

    def _get_guild(self, guild_id: Optional[int], /) -> Optional[Guild]:
        # The keys of self._guilds are ints
        return self._guilds.get(guild_id)  # type: ignore

    def _get_or_create_unavailable_guild(self, guild_id: int, /) -> Guild:
        return self._guilds.get(guild_id) or Guild._create_unavailable(state=self, guild_id=guild_id)

    def _add_guild(self, guild: Guild, /) -> None:
        self._guilds[guild.id] = guild

    def _remove_guild(self, guild: Guild, /) -> None:
        self._guilds.pop(guild.id, None)
        self._guild_presences.pop(guild.id, None)

        # Nuke all read states
        for state_type in (ReadStateType.scheduled_events, ReadStateType.guild_home, ReadStateType.onboarding):
            read_state = self.get_read_state(guild.id, state_type, if_exists=True)
            if read_state is not None:
                self.remove_read_state(read_state)

        # Nuke guild expressions
        for emoji in guild.emojis:
            self._emojis.pop(emoji.id, None)

        for sticker in guild.stickers:
            self._stickers.pop(sticker.id, None)

        del guild

    def create_guild(self, guild: BaseGuildPayload, /) -> Guild:
        return Guild(data=guild, state=self)

    @property
    def emojis(self) -> Sequence[Emoji]:
        return utils.SequenceProxy(self._emojis.values())

    @property
    def stickers(self) -> Sequence[GuildSticker]:
        return utils.SequenceProxy(self._stickers.values())

    def get_emoji(self, emoji_id: Optional[int]) -> Optional[Emoji]:
        # the keys of self._emojis are ints
        return self._emojis.get(emoji_id)  # type: ignore

    def get_sticker(self, sticker_id: Optional[int]) -> Optional[GuildSticker]:
        # the keys of self._stickers are ints
        return self._stickers.get(sticker_id)  # type: ignore

    @property
    def private_channels(self) -> Sequence[PrivateChannel]:
        return utils.SequenceProxy(self._private_channels.values())

    async def call_connect(self, channel_id: int) -> None:
        # This is now no longer needed with the AUTO_CALL_CONNECT capability
        if self.ws is None:
            return

        await self.ws.call_connect(channel_id)

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
        return (
            utils.find(lambda m: m.id == msg_id, reversed(self._messages))
            if self._messages
            else utils.find(lambda m: m.id == msg_id, reversed(self._call_message_cache.values()))
        )

    def _add_guild_from_data(self, data: GuildPayload) -> Guild:
        guild = self.create_guild(data)
        self._add_guild(guild)
        return guild

    def _guild_needs_chunking(self, guild: Guild) -> bool:
        return self._chunk_guilds and not guild.chunked and not guild.unavailable

    async def _can_chunk_guild(self, guild: Guild) -> bool:
        if not guild.me:
            await guild.query_members(user_ids=[self.self_id], cache=True)  # type: ignore # self_id is always present here

        return guild.me is not None and any(
            (
                guild.me.guild_permissions.kick_members,
                guild.me.guild_permissions.ban_members,
                guild.me.guild_permissions.manage_roles,
            )
        )

    def _get_guild_channel(
        self, data: PartialMessagePayload, guild_id: Optional[int] = None
    ) -> Tuple[Union[Channel, Thread], Optional[Guild]]:
        channel_id = int(data['channel_id'])
        try:
            guild_id = guild_id or int(data['guild_id'])
            guild = self._get_guild(guild_id)
        except KeyError:
            channel = self.get_channel(channel_id)
            guild = None
        else:
            channel = guild and guild._resolve_channel(channel_id)

        return channel or PartialMessageable(state=self, guild_id=guild_id, id=channel_id), guild

    async def _delete_messages(self, channel_id, messages, reason: Optional[str] = None) -> None:
        delete_message = self.http.delete_message
        for msg in messages:
            try:
                await delete_message(channel_id, msg.id, reason=reason)
            except NotFound:
                pass

    def subscribe_guild(
        self, guild: Guild, typing: bool = True, activities: bool = True, threads: bool = True, member_updates: bool = True
    ) -> Coroutine:
        return self.subscriptions.subscribe_to(
            guild, typing=typing, activities=activities, threads=threads, member_updates=member_updates
        )

    def chunker(
        self,
        guild_ids: List[Snowflake],
        query: Optional[str] = '',
        limit: int = 0,
        presences: bool = True,
        *,
        user_ids: Optional[List[Snowflake]] = None,
        nonce: Optional[str] = None,
    ):
        return self.ws.request_chunks(
            guild_ids, query=query, limit=limit, presences=presences, user_ids=user_ids, nonce=nonce
        )

    async def query_members(
        self,
        guild: Guild,
        query: Optional[str],
        limit: int,
        user_ids: Optional[List[Snowflake]],
        cache: bool,
        presences: bool,
    ) -> List[Member]:
        guild_id = guild.id
        request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
        self._chunk_requests[request.nonce] = request

        try:
            await self.chunker(
                [guild_id], query=query, limit=limit, presences=presences, user_ids=user_ids, nonce=request.nonce
            )
            return await asyncio.wait_for(request.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            _log.warning('Timed out waiting for chunks with query %r and limit %d for guild ID %d.', query, limit, guild_id)
            raise

    async def search_recent_members(
        self,
        guild: Guild,
        query: str = '',
        limit: Optional[int] = None,
        cache: bool = False,
    ) -> List[Member]:
        guild_id = guild.id
        request = ChunkRequest(guild.id, self.loop, self._get_guild, limit=limit, cache=cache, oneshot=False)
        self._chunk_requests[request.nonce] = request

        # Unlike query members, this OP is paginated
        old_continuation_token = None
        continuation_token = None
        while True:
            try:
                await self.ws.search_recent_members(guild_id, query=query, nonce=request.nonce, after=continuation_token)
                returned = await asyncio.wait_for(request.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                _log.warning(
                    'Timed out waiting for search chunks with query %r and limit %d for guild ID %d.',
                    query,
                    limit,
                    guild_id,
                )
                raise

            if (limit is not None and request.remaining < 1) or len(returned) < 1:
                break

            # Sort the members by joined_at timestamp and grab the oldest one
            request.buffer.sort(key=lambda m: m.joined_at or utils.utcnow())
            old_continuation_token = continuation_token
            continuation_token = request.buffer[0].id
            if continuation_token == old_continuation_token:
                break

        self._chunk_requests.pop(request.nonce, None)
        return list(set(request.buffer))

    async def _delay_ready(self) -> None:
        manager = self.subscriptions
        manager.blocked = True

        try:
            # Try to only send one OP each
            member_nonce = utils._generate_nonce()
            states = []
            to_chunk = []

            if not manager.empty:
                await manager._requeue_subscriptions()

            for guild in self._guilds.values():
                if self._subscribe_guilds:
                    await self.subscribe_guild(guild)

                if self._guild_needs_chunking(guild):
                    if await self._can_chunk_guild(guild):
                        future = await self.chunk_guild(guild, wait=False, nonce=member_nonce)
                        to_chunk.append(guild.id)
                        states.append((guild, future))
                    elif not guild._offline_members_hidden:
                        request = MemberSidebar(guild, MISSING, chunk=True, cache=True, loop=self.loop, delay=0)
                        if not request.channels:
                            # Not possible to scrape here
                            continue

                        self._scrape_requests[guild.id] = request
                        request.start()
                        states.append((guild, request.get_future()))

            manager.blocked = False
            await self.chunker(to_chunk, nonce=member_nonce)

            for guild, future in states:
                timeout = self._chunk_timeout(guild)

                try:
                    await asyncio.wait_for(future, timeout=timeout)
                except asyncio.TimeoutError:
                    _log.warning('Timed out waiting for chunks for guild ID %s.', guild.id)
                except (ClientException, InvalidData):
                    pass
        except asyncio.CancelledError:
            pass
        else:
            # Dispatch the event
            self.call_handlers('ready')
            self.dispatch('ready')
        finally:
            # Make sure we don't block it forever
            manager.blocked = False
            self._ready_task = None

    def parse_ready(self, data: gw.ReadyEvent) -> None:
        if self._ready_task is not None:
            self._ready_task.cancel()
        self.clear()
        self._ready_data = data

        # Clear the ACK token
        self.http.ack_token = None

        # Self parsing
        self.user = user = ClientUser(state=self, data=data['user'])
        self._users[user.id] = user  # type: ignore

        # Read state parsing
        read_states = data.get('read_state', {})
        for read_state in read_states['entries']:
            item = ReadState(state=self, data=read_state)
            self.store_read_state(item)
        self.read_state_version = read_states.get('version', 0)

        # Guild settings parsing
        guild_settings = data.get('user_guild_settings', {})
        self.guild_settings = {
            utils._get_as_snowflake(entry, 'guild_id'): GuildSettings(data=entry, state=self)
            for entry in guild_settings.get('entries', [])
        }
        self.guild_settings_version = guild_settings.get('version', 0)

        # Experiments
        self.experiments = {exp[0]: UserExperiment(state=self, data=exp) for exp in data.get('experiments', [])}
        self.guild_experiments = {exp[0]: GuildExperiment(state=self, data=exp) for exp in data.get('guild_experiments', [])}

        # Extras
        self.analytics_token = data.get('analytics_token')
        self.preferred_rtc_regions = data.get('geo_ordered_rtc_regions', ['us-central'])
        self.settings = UserSettings(self, data.get('user_settings_proto', ''))
        self.consents = TrackingSettings(data=data.get('consents', {}), state=self)
        self.country_code = data.get('country_code', 'US')
        self.api_code_version = data.get('api_code_version', 1)
        self.session_type = data.get('session_type', 'normal')
        self.auth_session_id = data.get('auth_session_id_hash')
        self.connections = {c['id']: Connection(state=self, data=c) for c in data.get('connected_accounts', [])}
        self.pending_payments = {int(p['id']): Payment(state=self, data=p) for p in data.get('pending_payments', [])}
        self.required_action = try_enum(RequiredActionType, data['required_action']) if 'required_action' in data else None
        self.friend_suggestion_count = data.get('friend_suggestion_count', 0)

        if 'sessions' in data:
            self.parse_sessions_replace(data['sessions'], from_ready=True)

        if 'auth_token' in data:
            self.http._token(data['auth_token'])

        if 'tutorial' in data and data['tutorial']:
            self.tutorial = Tutorial(state=self, data=data['tutorial'])

        # Before parsing the rest, we wait for READY_SUPPLEMENTAL
        # This has voice state objects, as well as an initial member cache

    def parse_ready_supplemental(self, extra_data: gw.ReadySupplementalEvent) -> None:
        data = self._ready_data

        # Temp user parsing
        user = self.user
        temp_users: Dict[int, PartialUserPayload] = {int(data['user']['id']): data['user']}
        for u in data.get('users', []):
            u_id = int(u['id'])
            temp_users[u_id] = u

        # Discord bad
        for guild_data, guild_extra, merged_members, merged_me, merged_presences in zip(
            data.get('guilds', []),
            extra_data.get('guilds', []),
            extra_data.get('merged_members', []),
            data.get('merged_members', []),
            extra_data['merged_presences'].get('guilds', []),
        ):
            for presence in merged_presences:
                presence['user'] = {'id': presence['user_id']}  # type: ignore

            if 'properties' in guild_data:
                guild_data.update(guild_data.pop('properties'))  # type: ignore

            voice_states = guild_data.setdefault('voice_states', [])
            voice_states.extend(guild_extra.get('voice_states', []))
            members = guild_data.setdefault('members', [])
            members.extend(merged_me)
            members.extend(merged_members)
            presences = guild_data.setdefault('presences', [])
            presences.extend(merged_presences)

            for member in members:
                if 'user' not in member:
                    member['user'] = temp_users.get(int(member.pop('user_id')))

            for voice_state in voice_states:
                if 'member' not in voice_state:
                    member = utils.find(lambda m: m['user']['id'] == voice_state['user_id'], members)
                    if member:
                        voice_state['member'] = member

        # Guild parsing
        for guild_data in data.get('guilds', []):
            self._add_guild_from_data(guild_data)

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

        # Relationship presence parsing
        for presence in extra_data['merged_presences'].get('friends', []):
            user_id = int(presence.pop('user_id'))  # type: ignore
            self.store_presence(user_id, self.create_presence(presence))

        # Private channel parsing
        for pm in data.get('private_channels', []) + extra_data.get('lazy_private_channels', []):
            factory, _ = _private_channel_factory(pm['type'])
            if 'recipients' not in pm:
                pm['recipients'] = [temp_users[int(u_id)] for u_id in pm.pop('recipient_ids')]  # type: ignore
            self._add_private_channel(factory(me=user, data=pm, state=self))  # type: ignore

        # Disloses
        self.disclose = data.get('disclose', [])

        # We're done
        del self._ready_data
        self.call_handlers('connect')
        self.dispatch('connect')
        self._ready_task = asyncio.create_task(self._delay_ready())

    def parse_resumed(self, data: gw.ResumedEvent) -> None:
        self.dispatch('resumed')

    def parse_passive_update_v1(self, data: gw.PassiveUpdateEvent) -> None:
        # PASSIVE_UPDATE_V1 is sent for large guilds you are not subscribed to
        # in order to keep their read and voice states up-to-date; it replaces CHANNEL_UNREADS_UPDATE
        guild = self._get_guild(int(data['guild_id']))
        if not guild:
            _log.debug('PASSIVE_UPDATE_V1 referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        for channel_data in data.get('channels', []):
            channel = guild.get_channel(int(channel_data['id']))
            if not channel:
                continue
            channel.last_message_id = utils._get_as_snowflake(channel_data, 'last_message_id')  # type: ignore
            if 'last_pin_timestamp' in channel_data and hasattr(channel, 'last_pin_timestamp'):
                channel.last_pin_timestamp = utils.parse_time(channel_data['last_pin_timestamp'])  # type: ignore

        # Apparently, voice states not being in the payload means there are no longer any voice states
        guild._voice_states = {}
        members = {int(m['user']['id']): m for m in data.get('members', [])}
        for voice_state in data.get('voice_states', []):
            user_id = int(voice_state['user_id'])
            member = members.get(user_id)
            if member:
                voice_state['member'] = member
            guild._update_voice_state(voice_state, utils._get_as_snowflake(voice_state, 'channel_id'))

    def parse_message_create(self, data: gw.MessageCreateEvent) -> None:
        channel, _ = self._get_guild_channel(data)

        # channel will be the correct type here
        message = Message(channel=channel, data=data, state=self)  # type: ignore
        self.dispatch('message', message)
        if self._messages is not None:
            self._messages.append(message)
        if message.call is not None:
            self._call_message_cache[message.id] = message
        if channel:
            channel.last_message_id = message.id  # type: ignore

        read_state = self.get_read_state(channel.id)
        if message.author.id == self.self_id:
            # Implicitly mark our own messages as read
            read_state.last_acked_id = message.id
        if (
            not message.author.is_blocked()
            and not (channel.type == ChannelType.group and message.type == MessageType.recipient_remove)
            and message._is_self_mentioned()
        ):
            # Increment mention count if applicable
            read_state.badge_count += 1

    def parse_message_delete(self, data: gw.MessageDeleteEvent) -> None:
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(raw.message_id)
        raw.cached_message = found
        self.dispatch('raw_message_delete', raw)
        if self._messages is not None and found is not None:
            self.dispatch('message_delete', found)
            self._messages.remove(found)

    def parse_message_delete_bulk(self, data: gw.MessageDeleteBulkEvent) -> None:
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

    def parse_message_update(self, data: gw.MessageUpdateEvent) -> None:
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

    def parse_message_ack(self, data: gw.MessageAckEvent) -> None:
        self.read_state_version = data.get('version', self.read_state_version)
        channel_id = int(data['channel_id'])
        channel = self.get_channel(channel_id)
        if channel is None:
            _log.debug('MESSAGE_ACK referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        raw = RawMessageAckEvent(data)
        message_id = int(data['message_id'])
        message = self._get_message(message_id)
        raw.cached_message = message

        read_state = self.get_read_state(channel_id)
        read_state.last_acked_id = message_id
        if 'mention_count' in data:
            read_state.badge_count = data['mention_count']
        if 'flags' in data and data['flags'] is not None:
            read_state._flags = data['flags']
        if 'last_viewed' in data and data['last_viewed']:
            read_state.last_viewed = read_state.unpack_last_viewed(data['last_viewed'])

        self.dispatch('raw_message_ack', raw)
        if message is not None:
            self.dispatch('message_ack', message, raw.manual)

    def parse_message_reaction_add(self, data: gw.MessageReactionAddEvent) -> None:
        emoji = data['emoji']
        emoji_id = utils._get_as_snowflake(emoji, 'id')
        emoji = PartialEmoji.with_state(self, id=emoji_id, animated=emoji.get('animated', False), name=emoji['name'])  # type: ignore
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

    def parse_message_reaction_remove_all(self, data: gw.MessageReactionRemoveAllEvent) -> None:
        raw = RawReactionClearEvent(data)
        self.dispatch('raw_reaction_clear', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch('reaction_clear', message, old_reactions)

    def parse_message_reaction_remove(self, data: gw.MessageReactionRemoveEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
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

    def parse_message_reaction_remove_emoji(self, data: gw.MessageReactionRemoveEmojiEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
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

    def parse_recent_mention_delete(self, data: gw.RecentMentionDeleteEvent) -> None:
        message_id = int(data['message_id'])
        message = self._get_message(message_id)
        if message is not None:
            self.dispatch('recent_mention_delete', message)
        self.dispatch('raw_recent_mention_delete', message_id)

    def parse_presences_replace(self, data: List[gw.PartialPresenceUpdate]) -> None:
        for presence in data:
            self.parse_presence_update(presence)

    def _handle_presence_update(self, guild: Optional[Guild], data: gw.BasePresenceUpdate):
        guild_id = guild.id if guild else None
        user = data['user']
        user_id = int(user['id'])

        presence = self.get_presence(user_id, guild_id)
        if presence is not None:
            old_presence = Presence._copy(presence)
            presence._update(data, self)
        else:
            old_presence = Presence._offline()
            presence = self.store_presence(user_id, self.create_presence(data), guild_id)

        if not guild:
            try:
                relationship = self.create_implicit_relationship(self.store_user(user))
            except (KeyError, ValueError):
                # User object is partial, so we can't continue
                _log.debug('PRESENCE_UPDATE referencing an unknown relationship ID: %s. Discarding.', user_id)
                return

            user_update = relationship.user._update_self(user)
            if old_presence != presence:
                old_relationship = Relationship._copy(relationship, old_presence)
                self.dispatch('presence_update', old_relationship, relationship)
        else:
            member = guild.get_member(user_id)
            if member is None:
                _log.debug('PRESENCE_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)
                return

            user_update = member._user._update_self(user)
            if old_presence != presence:
                old_member = Member._copy(member)
                old_member._presence = old_presence
                self.dispatch('presence_update', old_member, member)

        if user_update:
            self.dispatch('user_update', user_update[0], user_update[1])

    def parse_presence_update(self, data: gw.PresenceUpdateEvent) -> None:
        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild_id and not guild:
            _log.debug('PRESENCE_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        self._handle_presence_update(guild, data)

    def parse_user_update(self, data: gw.UserUpdateEvent) -> None:
        # Clear the ACK token
        self.http.ack_token = None
        if self.user:
            self.user._full_update(data)

    def parse_user_note_update(self, data: gw.UserNoteUpdateEvent) -> None:
        # The gateway does not provide note objects on READY with our default capabilities
        # so we cannot have (old, new) event dispatches
        user_id = int(data['id'])
        text = data['note']
        user = self.get_user(user_id)
        if user:
            note = user.note
            note._value = text
        else:
            note = Note(self, user_id, note=text)

        self.dispatch('note_update', note)

    # def parse_user_settings_update(self, data) -> None:
    #     new_settings = self.settings
    #     old_settings = copy.copy(new_settings)
    #     new_settings._update(data)
    #     self.dispatch('settings_update', old_settings, new_settings)
    #     self.dispatch('internal_settings_update', old_settings, new_settings)

    def parse_user_settings_proto_update(self, data: gw.ProtoSettingsEvent):
        type = UserSettingsType(data['settings']['type'])
        if type == UserSettingsType.preloaded_user_settings:
            settings = self.settings
            if settings:
                old_settings = UserSettings._copy(settings)
                settings._update(data['settings']['proto'], partial=data.get('partial', False))
                self.dispatch('settings_update', old_settings, settings)
                self.dispatch('internal_settings_update', old_settings, settings)
        elif type == UserSettingsType.frecency_user_settings:
            ...
        elif type == UserSettingsType.test_settings:
            _log.debug('Received test settings proto update. Data: %s', data['settings']['proto'])
        else:
            _log.warning('Unknown user settings proto type: %s', type.value)

    def parse_user_guild_settings_update(self, data: gw.UserGuildSettingsEvent) -> None:
        guild_id = utils._get_as_snowflake(data, 'guild_id')

        settings = self.guild_settings.get(guild_id)
        if settings is not None:
            old_settings = copy.copy(settings)
            settings._update(data)
        else:
            old_settings = None
            settings = GuildSettings(data=data, state=self)
        self.guild_settings_version = data.get('version', self.guild_settings_version)
        self.dispatch('guild_settings_update', old_settings, settings)

    def parse_user_required_action_update(self, data: gw.RequiredActionEvent) -> None:
        required_action = try_enum(RequiredActionType, data['required_action']) if data['required_action'] else None
        self.required_action = required_action
        self.dispatch('required_action_update', required_action)

    def parse_user_non_channel_ack(self, data: gw.NonChannelAckEvent) -> None:
        self.read_state_version = data.get('version', self.read_state_version)

        raw = RawUserFeatureAckEvent(data)
        read_state = self.get_read_state(self.self_id, raw.type)  # type: ignore
        read_state.last_acked_id = int(data['entity_id'])
        self.dispatch('user_feature_ack', raw)

    def parse_user_connections_update(self, data: Union[gw.ConnectionEvent, gw.PartialConnectionEvent]) -> None:
        self.dispatch('connections_update')

        id = data.get('id')
        if id is None or 'user_id' in data:
            return

        if id not in self.connections:
            self.connections[id] = connection = Connection(state=self, data=data)
            self.dispatch('connection_create', connection)
        else:
            # TODO: We can also get to this point if the connection has been deleted
            # We can detect that by checking if the payload is identical to the previous payload
            # However, certain events can also trigger updates with identical payloads, so we can't rely on that
            # For now, we assume everything is an update; thanks Discord
            connection = self.connections[id]
            old_connection = copy.copy(connection)
            connection._update(data)
            self.dispatch('connection_update', old_connection, connection)

    def parse_user_connections_link_callback(self, data: gw.ConnectionsLinkCallbackEvent) -> None:
        self.dispatch('connections_link_callback', data['provider'], data['callback_code'], data['callback_state'])

    def parse_user_payment_sources_update(self, data: gw.NoEvent) -> None:
        self.dispatch('payment_sources_update')

    def parse_user_subscriptions_update(self, data: gw.NoEvent) -> None:
        self.dispatch('subscriptions_update')

    def parse_user_payment_client_add(self, data: gw.PaymentClientAddEvent) -> None:
        self.dispatch('payment_client_add', data['purchase_token_hash'], utils.parse_time(data['expires_at']))

    def parse_user_premium_guild_subscription_slot_create(self, data: gw.PremiumGuildSubscriptionSlotEvent) -> None:
        slot = PremiumGuildSubscriptionSlot(state=self, data=data)
        self.dispatch('premium_guild_subscription_slot_create', slot)

    def parse_user_premium_guild_subscription_slot_update(self, data: gw.PremiumGuildSubscriptionSlotEvent) -> None:
        slot = PremiumGuildSubscriptionSlot(state=self, data=data)
        self.dispatch('premium_guild_subscription_slot_update', slot)

    def parse_user_achievement_update(self, data: gw.AchievementUpdatePayload) -> None:
        achievement: AchievementPayload = data.get('achievement')  # type: ignore
        application_id = data.get('application_id')
        if not achievement or not application_id:
            _log.warning('USER_ACHIEVEMENT_UPDATE payload has invalid data: %s. Discarding.', list(data.keys()))
            return

        achievement['application_id'] = application_id
        model = Achievement(state=self, data=achievement)
        self.dispatch('achievement_update', model, data.get('percent_complete', 0))

    def parse_billing_popup_bridge_callback(self, data: gw.BillingPopupBridgeCallbackEvent) -> None:
        self.dispatch(
            'billing_popup_bridge_callback',
            try_enum(PaymentSourceType, data.get('payment_source_type', 0)),
            data.get('path'),
            data.get('query'),
            data.get('state'),
        )

    def parse_oauth2_token_revoke(self, data: gw.OAuth2TokenRevokeEvent) -> None:
        if 'access_token' not in data:
            _log.warning('OAUTH2_TOKEN_REVOKE payload has invalid data: %s. Discarding.', list(data.keys()))
        self.dispatch('oauth2_token_revoke', data['access_token'])

    def parse_auth_session_change(self, data: gw.AuthSessionChangeEvent) -> None:
        self.auth_session_id = auth_session_id = data['auth_session_id_hash']
        self.dispatch('auth_session_change', auth_session_id)

    def parse_payment_update(self, data: gw.PaymentUpdateEvent) -> None:
        id = int(data['id'])
        payment = self.pending_payments.get(id)
        if payment is not None:
            payment._update(data)
        else:
            payment = Payment(state=self, data=data)

        self.dispatch('payment_update', payment)

    def parse_library_application_update(self, data: gw.LibraryApplicationUpdateEvent) -> None:
        entry = LibraryApplication(state=self, data=data)
        self.dispatch('library_application_update', entry)

    def parse_sessions_replace(self, payload: gw.SessionsReplaceEvent, *, from_ready: bool = False) -> None:
        data = {s['session_id']: s for s in payload}

        for session_id, session in data.items():
            existing = self._sessions.get(session_id)
            if existing is not None:
                old = copy.copy(existing)
                existing._update(session)
                if not from_ready and (
                    old.status != existing.status or old.active != existing.active or old.activities != existing.activities
                ):
                    self.dispatch('session_update', old, existing)
            else:
                existing = Session(state=self, data=session)
                self._sessions[session_id] = existing
                if not from_ready:
                    self.dispatch('session_create', existing)

        old_all = None
        if not from_ready:
            removed_sessions = [s for s in self._sessions if s not in data]
            for session_id in removed_sessions:
                if session_id == 'all':
                    old_all = self._sessions.pop('all')
                else:
                    session = self._sessions.pop(session_id)
                    self.dispatch('session_delete', session)

        if 'all' not in self._sessions:
            # The "all" session does not always exist...
            # This usually happens if there is only a single session (us)
            # In the case it is "removed", we try to update the old one
            # Else, we create a new one with fake data
            if len(data) > 1:
                # We have more than one session, this should not happen
                fake = data[self.session_id]  # type: ignore
            else:
                fake = list(data.values())[0]
            if old_all is not None:
                old = copy.copy(old_all)
                old_all._update(fake)
                if old.status != old_all.status or old.active != old_all.active or old.activities != old_all.activities:
                    self.dispatch('session_update', old, old_all)
            else:
                old_all = Session._fake_all(state=self, data=fake)
            self._sessions['all'] = old_all

    def parse_entitlement_create(self, data: gw.EntitlementEvent) -> None:
        entitlement = Entitlement(state=self, data=data)
        self.dispatch('entitlement_create', entitlement)

    def parse_entitlement_update(self, data: gw.EntitlementEvent) -> None:
        entitlement = Entitlement(state=self, data=data)
        self.dispatch('entitlement_update', entitlement)

    def parse_entitlement_delete(self, data: gw.EntitlementEvent) -> None:
        entitlement = Entitlement(state=self, data=data)
        self.dispatch('entitlement_delete', entitlement)

    def parse_gift_code_create(self, data: gw.GiftCreateEvent) -> None:
        # Should be fine:tm:
        gift = Gift(state=self, data=data)  # type: ignore
        self.dispatch('gift_create', gift)

    def parse_gift_code_update(self, data: gw.GiftUpdateEvent) -> None:
        # Should be fine:tm:
        gift = Gift(state=self, data=data)  # type: ignore
        self.dispatch('gift_update', gift)

    def parse_invite_create(self, data: gw.InviteCreateEvent) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch('invite_create', invite)

    def parse_invite_delete(self, data: gw.InviteDeleteEvent) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch('invite_delete', invite)

    def parse_channel_delete(self, data: gw.ChannelDeleteEvent) -> None:
        guild = self._get_guild(utils._get_as_snowflake(data, 'guild_id'))
        channel_id = int(data['id'])
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                guild._remove_channel(channel)
                self.dispatch('guild_channel_delete', channel)

                if channel.type in (ChannelType.voice, ChannelType.stage_voice):
                    for s in guild.scheduled_events:
                        if s.channel_id == channel.id:
                            guild._scheduled_events.pop(s.id)
                            self.dispatch('scheduled_event_delete', s)
        else:
            channel = self._get_private_channel(channel_id)
            if channel is not None:
                self._remove_private_channel(channel)
                self.dispatch('private_channel_delete', channel)

        # Nuke read state
        read_state = self.get_read_state(channel_id)
        if read_state is not None:
            self.remove_read_state(read_state)

    def parse_channel_update(self, data: gw.ChannelUpdateEvent) -> None:
        channel_type = try_enum(ChannelType, data.get('type'))
        channel_id = int(data['id'])
        if channel_type in (ChannelType.private, ChannelType.group):
            channel = self._get_private_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                channel._update(data)  # type: ignore # the data payload varies based on the channel type
                self.dispatch('private_channel_update', old_channel, channel)
                return
            else:
                _log.debug('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)

        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                channel._update(guild, data)  # type: ignore # the data payload varies based on the channel type
                self.dispatch('guild_channel_update', old_channel, channel)
            else:
                _log.debug('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
        else:
            _log.debug('CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_channel_create(self, data: gw.ChannelCreateEvent) -> None:
        factory, ch_type = _channel_factory(data['type'])
        if factory is None:
            _log.debug('CHANNEL_CREATE referencing an unknown channel type %s. Discarding.', data['type'])
            return

        if ch_type in (ChannelType.group, ChannelType.private):
            channel_id = int(data['id'])
            if self._get_private_channel(channel_id) is None:
                channel = factory(me=self.user, data=data, state=self)  # type: ignore # user is always present when logged in
                self._add_private_channel(channel)  # type: ignore # channel will always be a private channel
                self.dispatch('private_channel_create', channel)
        else:
            guild_id = utils._get_as_snowflake(data, 'guild_id')
            guild = self._get_guild(guild_id)
            if guild is not None:
                # The factory can't be a DMChannel or GroupChannel here
                channel = factory(guild=guild, state=self, data=data)  # type: ignore
                guild._add_channel(channel)  # type: ignore
                self.dispatch('guild_channel_create', channel)
            else:
                _log.debug('CHANNEL_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
                return

    def parse_channel_pins_update(self, data: gw.ChannelPinsUpdateEvent) -> None:
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

        last_pin = utils.parse_time(data.get('last_pin_timestamp'))
        if hasattr(channel, 'last_pin_timestamp'):
            channel.last_pin_timestamp = last_pin  # type: ignore # Handled above

        if guild is None:
            self.dispatch('private_channel_pins_update', channel, last_pin)
        else:
            self.dispatch('guild_channel_pins_update', channel, last_pin)

    def parse_channel_pins_ack(self, data: gw.ChannelPinsAckEvent) -> None:
        self.read_state_version = data.get('version', self.read_state_version)
        channel_id = int(data['channel_id'])
        channel = self.get_channel(channel_id)
        if channel is None:
            _log.debug('CHANNEL_PINS_ACK referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        read_state = self.get_read_state(channel_id)
        last_pin = utils.parse_time(data.get('last_pin'))
        read_state.acked_pin_timestamp = last_pin

        if channel.guild is None:
            self.dispatch('private_channel_pins_ack', channel, last_pin)
        else:
            self.dispatch('guild_channel_pins_ack', channel, last_pin)

    def parse_channel_recipient_add(self, data: gw.ChannelRecipientEvent) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        if channel is None:
            _log.debug('CHANNEL_RECIPIENT_ADD referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        user = self.store_user(data['user'])
        channel.recipients.append(user)  # type: ignore
        self.dispatch('group_join', channel, user)

    def parse_channel_recipient_remove(self, data: gw.ChannelRecipientEvent) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        if channel is None:
            _log.debug('CHANNEL_RECIPIENT_REMOVE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        user = self.store_user(data['user'])
        try:
            channel.recipients.remove(user)  # type: ignore
        except ValueError:
            pass
        else:
            self.dispatch('group_remove', channel, user)

    def parse_thread_create(self, data: gw.ThreadCreateEvent) -> None:
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

    def parse_thread_update(self, data: gw.ThreadUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_UPDATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        existing = guild.get_thread(int(data['id']))
        if existing is not None:
            old = existing._update(data)
            if existing.archived:
                guild._remove_thread(existing)
            if old is not None:
                self.dispatch('thread_update', old, existing)
        else:  # Shouldn't happen
            thread = Thread(guild=guild, state=self, data=data)
            guild._add_thread(thread)

    def parse_thread_delete(self, data: gw.ThreadDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_DELETE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        raw = RawThreadDeleteEvent(data)
        raw.thread = thread = guild.get_thread(raw.thread_id)
        self.dispatch('raw_thread_delete', raw)

        if thread is not None:
            guild._remove_thread(thread)
            self.dispatch('thread_delete', thread)

        # Nuke read state
        read_state = self.get_read_state(raw.thread_id)
        if read_state is not None:
            self.remove_read_state(read_state)

    def parse_thread_list_sync(self, data: gw.ThreadListSyncEvent) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_LIST_SYNC referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        try:
            channel_ids = {int(i) for i in data['channel_ids']}
        except KeyError:
            channel_ids = None
            threads = guild._threads.copy()
        else:
            threads = guild._filter_threads(channel_ids)

        new_threads = {}
        for d in data.get('threads', []):
            thread = threads.pop(int(d['id']), None)
            if thread is not None:
                old = thread._update(d)
                if old is not None:
                    self.dispatch('thread_update', old, thread)  # Honestly not sure if this is right
            else:
                thread = Thread(guild=guild, state=self, data=d)
                new_threads[thread.id] = thread
        old_threads = [t for t in threads.values() if t.id not in new_threads]

        for member in data.get('members', []):
            try:  # Note: member['id'] is the thread_id
                thread = threads[int(member['id'])]
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

            # channel will be the correct type here
            message = Message(channel=channel, data=message, state=self)  # type: ignore
            if self._messages is not None:
                self._messages.append(message)

    def parse_thread_member_update(self, data: gw.ThreadMemberUpdate) -> None:
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

    def parse_thread_members_update(self, data: gw.ThreadMembersUpdate) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_MEMBERS_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        raw = RawThreadMembersUpdate(data)
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
                self.dispatch('raw_thread_member_remove', raw)
                if member is not None:
                    self.dispatch('thread_member_remove', member)
                else:
                    self.dispatch('raw_thread_member_remove', thread, member_id)
            else:
                self.dispatch('thread_remove', thread)

    def parse_thread_member_list_update(self, data: gw.ThreadMemberListUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_MEMBER_LIST_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        thread_id = int(data['thread_id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.debug('THREAD_MEMBER_LIST_UPDATE referencing an unknown thread ID: %s. Discarding.', thread_id)
            return

        members = [ThreadMember(thread, member) for member in data['members']]
        for m in members:
            thread._add_member(m)

    def parse_guild_member_add(self, data: gw.GuildMemberAddEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = Member(guild=guild, data=data, state=self)
        presence = None
        if 'presence' in data:
            presence = self.create_presence(data['presence'])

        if self.member_cache_flags.joined or member.id == self.self_id:
            if presence is not None:
                self.store_presence(member.id, presence, guild.id)
            guild._add_member(member)
        else:
            member._presence = presence  # Save the presence

        if guild._member_count is not None:
            guild._member_count += 1

        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data: gw.GuildMemberRemoveEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        user_data = data['user']
        if len(user_data) <= 1:
            # Fake event here, so no event
            member = guild.get_member(int(user_data['id']))
            if member is not None:
                guild._remove_member(member)
            else:
                _log.debug('GUILD_MEMBER_REMOVE referencing an unknown member ID: %s. Discarding.', user_data['id'])
            return

        try:
            user = self.store_user(user_data)  # type: ignore
            raw = RawMemberRemoveEvent(data, user)
        except KeyError:
            _log.debug('GUILD_MEMBER_REMOVE referencing an unknown user ID: %s. Discarding.', data['user']['id'])
            return

        guild = self._get_guild(raw.guild_id)
        if guild is not None:
            if guild._member_count is not None:
                guild._member_count -= 1

            member = guild.get_member(user.id)
            if member is not None:
                raw.user = member
                guild._remove_member(member)
                self.dispatch('member_remove', member)
        else:
            _log.debug('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

        self.dispatch('raw_member_remove', raw)

    def _handle_member_update(self, guild: Guild, data: Union[gw.GuildMemberUpdateEvent, gw.MemberWithUser]):
        user = data['user']
        user_id = int(user['id'])
        member = guild.get_member(user_id)
        if member is not None:
            old_member = member._update(data)
            if old_member is not None:
                self.dispatch('member_update', old_member, member)
        else:
            if self.member_cache_flags.joined:
                member = Member(data=data, guild=guild, state=self)  # type: ignore # The data is close enough
                guild._add_member(member)
            _log.debug('GUILD_MEMBER_UPDATE referencing an unknown member ID: %s.', user_id)

        if member is not None:
            # Force an update on the inner user if necessary
            user_update = member._user._update_self(user)
            if user_update:
                self.dispatch('user_update', user_update[0], user_update[1])

    def parse_guild_member_update(self, data: gw.GuildMemberUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        self._handle_member_update(guild, data)

    def parse_guild_member_list_update(self, data: gw.GuildMemberListUpdateEvent) -> None:
        # The below code used to hackily emit guild member events from the member list
        # This is no longer necessary, but is kept here commented out for reference
        self.dispatch('raw_member_list_update', data)
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_LIST_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        request = self._scrape_requests.get(guild.id)
        # should_parse = guild.chunked or getattr(request, 'chunk', False)

        if data['member_count'] > 0:
            guild._member_count = data['member_count']
        if data['online_count'] > 0:
            guild._presence_count = data['online_count']
        guild._true_online_count = sum(group['count'] for group in data['groups'] if group['id'] != 'offline')

        empty_tuple = tuple()

        # to_add = []
        # to_remove = []
        # disregard = []
        members = []

        # if should_parse:  # The SYNCs need to be first and in order for indexes to not crap a brick
        #     syncs = [opdata for opdata in data['ops'] if opdata['op'] == 'SYNC']
        #     syncs.sort(key=lambda op: op['range'][0])
        #     ops = syncs + [opdata for opdata in data['ops'] if opdata['op'] != 'SYNC']
        # else:
        ops = data['ops']

        for opdata in ops:
            # The OPs are as follows:
            # SYNC: Provides member/presence data for a 100 member range of the member list
            # UPDATE: Dispatched when a member is updated and stays in the same range
            # INSERT: Dispatched when a member is inserted into a range
            # DELETE: Dispatched when a member is removed from a range
            # INVALIDATE: Sent when you're unsubscribed from a range

            if opdata['op'] == 'SYNC':
                for item in opdata['items']:
                    if 'group' in item:  # Hoisted role
                        # (
                        #     guild._member_list.append(None) if should_parse else None
                        # )  # Insert blank so indexes don't fuck up
                        continue

                    mdata = item['member']
                    member = Member(data=mdata, guild=guild, state=self)
                    if mdata.get('presence') is not None:
                        member._presence_update(mdata['presence'], empty_tuple)

                    members.append(member)
                    # guild._member_list.append(member) if should_parse else None

            # elif opdata['op'] == 'INSERT':
            #     index = opdata['index']
            #     item = opdata['item']
            #     if 'group' in item:  # Hoisted role
            #         (
            #             guild._member_list.insert(index, None) if should_parse else None
            #         )  # Insert blank so indexes don't fuck up
            #         continue

            #     mdata = item['member']
            #     user = mdata['user']
            #     user_id = int(user['id'])

            #     member = guild.get_member(user_id)
            #     if member is not None:  # INSERTs are also sent when a user changes range
            #         old_member = Member._copy(member)
            #         dispatch = bool(member._update(mdata))

            #         if mdata.get('presence') is not None:
            #             pdata = mdata['presence']
            #             presence = self.get_presence(user_id, guild.id)
            #             if presence is not None:
            #                 old_presence = Presence._copy(presence)
            #                 presence._update(pdata, self)
            #             else:
            #                 old_presence = Presence._offline()
            #                 presence = self.store_presence(user_id, self.create_presence(pdata), guild.id)

            #             old_member._presence = old_presence
            #             if should_parse and old_presence != presence:
            #                 self.dispatch('presence_update', old_member, member)

            #         user_update = member._user._update_self(user)
            #         if user_update:
            #             self.dispatch('user_update', user_update[0], user_update[1])

            #         if should_parse and dispatch:
            #             self.dispatch('member_update', old_member, member)

            #         disregard.append(member)
            #     else:
            #         member = Member(data=mdata, guild=guild, state=self)
            #         if mdata.get('presence') is not None:
            #             member._presence_update(mdata['presence'], empty_tuple)

            #         to_add.append(member)

            #     guild._member_list.insert(index, member) if should_parse else None

            # elif opdata['op'] == 'UPDATE' and should_parse:
            #     item = opdata['item']
            #     if 'group' in item:  # Hoisted role
            #         continue

            #     mdata = item['member']
            #     user = mdata['user']
            #     user_id = int(user['id'])

            #     member = guild.get_member(user_id)
            #     if member is not None:
            #         old_member = Member._copy(member)
            #         dispatch = bool(member._update(mdata))

            #         if mdata.get('presence') is not None:
            #             pdata = mdata['presence']
            #             presence = self.get_presence(user_id, guild.id)
            #             if presence is not None:
            #                 old_presence = Presence._copy(presence)
            #                 presence._update(pdata, self)
            #             else:
            #                 old_presence = Presence._offline()
            #                 presence = self.store_presence(user_id, self.create_presence(pdata), guild.id)

            #             old_member._presence = old_presence
            #             if should_parse and old_presence != presence:
            #                 self.dispatch('presence_update', old_member, member)

            #         user_update = member._user._update_self(user)
            #         if user_update:
            #             self.dispatch('user_update', user_update[0], user_update[1])

            #         if should_parse and dispatch:
            #             self.dispatch('member_update', old_member, member)
            #     else:
            #         _log.debug(
            #             'GUILD_MEMBER_LIST_UPDATE type UPDATE referencing an unknown member ID %s index %s in %s. Discarding.',
            #             user_id,
            #             opdata['index'],
            #             guild.id,
            #         )

            #         member = Member(data=mdata, guild=guild, state=self)
            #         if mdata.get('presence') is not None:
            #             self.store_presence(user_id, self.create_presence(mdata['presence']), guild.id)

            #         guild._member_list.insert(opdata['index'], member)  # Race condition?

            # elif opdata['op'] == 'DELETE' and should_parse:
            #     index = opdata['index']
            #     try:
            #         item = guild._member_list.pop(index)
            #     except IndexError:
            #         _log.debug(
            #             'GUILD_MEMBER_LIST_UPDATE type DELETE referencing an unknown member index %s in %s. Discarding.',
            #             index,
            #             guild.id,
            #         )
            #         continue

            #     if item is not None:
            #         to_remove.append(item)

        if request:
            if request.chunk and not (
                any(group['id'] == 'offline' for group in data['groups']) or data['member_count'] == data['online_count']
            ):
                # The guild has offline members hidden
                print(f'Detected guild {guild} with erroneous offline members')
                return
            request.add_members(members)
            # request.add_members(members + to_add)
        else:
            for member in members:  # + to_add:
                guild._add_member(member)

        # if should_parse:
        #     actually_remove = [member for member in to_remove if member not in to_add and member not in disregard]
        #     actually_add = [member for member in to_add if member not in to_remove]
        #     for member in actually_remove:
        #         guild._remove_member(member)
        #         self.dispatch('member_remove', member)
        #     for member in actually_add:
        #         self.dispatch('member_join', member)

    def parse_guild_application_command_index_update(self, data: gw.GuildApplicationCommandIndexUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug(
                'GUILD_APPLICATION_COMMAND_INDEX_UPDATE referencing an unknown guild ID: %s. Discarding.',
                data['guild_id'],
            )
            return

        counts = data['application_command_counts']
        old_counts = guild.application_command_counts or ApplicationCommandCounts(0, 0, 0)
        guild.application_command_counts = new_counts = ApplicationCommandCounts(
            counts.get(1, 0), counts.get(2, 0), counts.get(3, 0)
        )
        self.dispatch('application_command_counts_update', guild, old_counts, new_counts)

    def parse_guild_emojis_update(self, data: gw.GuildEmojisUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            self._emojis.pop(emoji.id, None)
        guild.emojis = tuple(map(lambda d: self.store_emoji(guild, d), data['emojis']))
        self.dispatch('guild_emojis_update', guild, before_emojis, guild.emojis)

    def parse_guild_stickers_update(self, data: gw.GuildStickersUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_STICKERS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_stickers = guild.stickers
        for emoji in before_stickers:
            self._stickers.pop(emoji.id, None)
        guild.stickers = tuple(map(lambda d: self.store_sticker(guild, d), data['stickers']))
        self.dispatch('guild_stickers_update', guild, before_stickers, guild.stickers)

    def parse_guild_audit_log_entry_create(self, data: gw.GuildAuditLogEntryCreate) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_AUDIT_LOG_ENTRY_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        entry = AuditLogEntry(
            users=self._users,
            automod_rules={},
            webhooks={},
            data=data,
            guild=guild,
        )
        self.dispatch('audit_log_entry_create', entry)

    # AutoMod events are not actually dispatched for user accounts...

    def parse_auto_moderation_rule_create(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_RULE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)
        self.dispatch('automod_rule_create', rule)

    def parse_auto_moderation_rule_update(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_RULE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)
        self.dispatch('automod_rule_update', rule)

    def parse_auto_moderation_rule_delete(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_RULE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)
        self.dispatch('automod_rule_delete', rule)

    def parse_auto_moderation_action_execution(self, data: AutoModerationActionExecution) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_ACTION_EXECUTION referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        execution = AutoModAction(data=data, state=self)
        self.dispatch('automod_action', execution)

    def _get_create_guild(self, data: gw.GuildCreateEvent) -> Optional[Guild]:
        guild = self._get_guild(int(data['id']))
        unavailable = data.get('unavailable')

        # Discord being Discord sometimes sends a GUILD_CREATE after subscribing to a guild
        # In this case, we just update it and return None to avoid a double dispatch
        if guild is not None:
            guild._from_data(data)
            if unavailable is not False:
                return

        return guild or self._add_guild_from_data(data)

    def _chunk_timeout(self, guild: Guild) -> float:
        return max(5.0, (guild._member_count or 0) / 10000)

    def is_guild_evicted(self, guild: Guild) -> bool:
        return guild.id not in self._guilds

    async def assert_guild_presence_count(self, guild: Guild):
        if not guild._offline_members_hidden or guild._presence_count:
            return

        channel = None
        for channel in guild.channels:
            if channel.permissions_for(guild.default_role).read_messages and channel.permissions_for(guild.me).read_messages:  # type: ignore
                break
        else:
            raise RuntimeError('No channels viewable')

        requests: Dict[Snowflake, List[Tuple[int, int]]] = {str(channel.id): [(0, 99)]}

        def predicate(data):
            return int(data['guild_id']) == guild.id

        await self.subscriptions.subscribe_to_channels(guild, requests)

        try:
            await asyncio.wait_for(self.ws.wait_for('GUILD_MEMBER_LIST_UPDATE', predicate), timeout=10)
        except asyncio.TimeoutError:
            pass

        if not guild._presence_count:
            data = await self.http.get_guild_preview(guild.id)
            guild._presence_count = data['approximate_presence_count']

    @overload
    async def scrape_guild(
        self,
        guild: Guild,
        *,
        wait: Literal[True] = ...,
        cache: bool,
        force_scraping: bool = ...,
        chunk: bool = ...,
        channels: List[abcSnowflake] = ...,
        delay: Union[int, float] = ...,
    ) -> List[Member]:
        ...

    @overload
    async def scrape_guild(
        self,
        guild: Guild,
        *,
        wait: Literal[False] = ...,
        cache: bool,
        force_scraping: bool = ...,
        chunk: bool = ...,
        channels: List[abcSnowflake] = ...,
        delay: Union[int, float] = ...,
    ) -> asyncio.Future[List[Member]]:
        ...

    async def scrape_guild(
        self,
        guild: Guild,
        *,
        wait: bool = True,
        cache: bool,
        force_scraping: bool = False,
        chunk: bool = False,
        channels: List[abcSnowflake] = MISSING,
        delay: Union[int, float] = MISSING,
    ) -> Union[List[Member], asyncio.Future[List[Member]]]:
        if not guild.me:
            await guild.query_members(user_ids=[self.self_id], cache=True)  # type: ignore # self_id is always present here

        if (
            not chunk
            and not force_scraping
            and guild.me
            and any(
                {
                    guild.me.guild_permissions.kick_members,
                    guild.me.guild_permissions.ban_members,
                    guild.me.guild_permissions.manage_roles,
                }
            )
        ):
            request = self._chunk_requests.get(guild.id)
            if request is None:
                self._chunk_requests[guild.id] = request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
                await self.chunker([guild.id], nonce=request.nonce)
        else:
            if not chunk:
                await self.assert_guild_presence_count(guild)

            request = self._scrape_requests.get(guild.id)
            if request is None:
                self._scrape_requests[guild.id] = request = MemberSidebar(
                    guild, channels, chunk=chunk, cache=cache, loop=self.loop, delay=delay or 0
                )
                if not request.channels:
                    del self._scrape_requests[guild.id]
                    if chunk:
                        raise ClientException('Guild cannot be chunked: no channels viewable by @everyone')
                    raise ClientException('Failed to automatically choose channels; please specify them manually')
                request.start()

        if wait:
            return await request.wait()
        return request.get_future()

    @overload
    async def chunk_guild(
        self, guild: Guild, *, nonce: Optional[str] = ..., wait: Literal[True] = ..., cache: Optional[bool] = ...
    ) -> List[Member]:
        ...

    @overload
    async def chunk_guild(
        self, guild: Guild, *, nonce: Optional[str] = ..., wait: Literal[False] = ..., cache: Optional[bool] = ...
    ) -> asyncio.Future[List[Member]]:
        ...

    async def chunk_guild(
        self, guild: Guild, *, nonce: Optional[str] = None, wait: bool = True, cache: Optional[bool] = None
    ) -> Union[List[Member], asyncio.Future[List[Member]]]:
        cache = cache or self.member_cache_flags.joined
        request = self._chunk_requests.get(guild.id)
        if request is None:
            self._chunk_requests[guild.id] = request = ChunkRequest(
                guild.id, self.loop, self._get_guild, cache=cache, nonce=nonce
            )
            if not nonce:
                await self.chunker([guild.id], nonce=request.nonce)

        if wait:
            return await request.wait()
        return request.get_future()

    async def _chunk_and_dispatch(self, guild: Guild, chunk: bool, unavailable: Optional[bool]) -> None:
        timeout = self._chunk_timeout(guild)

        if chunk:
            coro = None
            if await self._can_chunk_guild(guild):
                coro = self.chunk_guild(guild)
            elif not guild._offline_members_hidden:
                try:
                    coro = await self.scrape_guild(guild, wait=False, cache=True, chunk=True)
                except ClientException:
                    pass

            if coro is not None:
                try:
                    await asyncio.wait_for(coro, timeout=timeout)
                except asyncio.TimeoutError:
                    _log.warning('Somehow timed out waiting for chunks for guild %s.', guild.id)
                except (ClientException, InvalidData):
                    pass

        if unavailable is False:
            self.dispatch('guild_available', guild)
        else:
            self.dispatch('guild_join', guild)

    def parse_guild_create(self, data: gw.GuildCreateEvent):
        if 'properties' in data:
            data.update(data.pop('properties'))  # type: ignore

        guild = self._get_create_guild(data)
        if guild is None:
            return

        if self._subscribe_guilds and not guild.unavailable:
            asyncio.ensure_future(self.subscribe_guild(guild), loop=self.loop)

        # Chunk if needed
        needs_chunking = self._guild_needs_chunking(guild)
        asyncio.ensure_future(self._chunk_and_dispatch(guild, needs_chunking, data.get('unavailable')), loop=self.loop)

    def parse_guild_update(self, data: gw.GuildUpdateEvent) -> None:
        guild = self._get_guild(int(data['id']))
        if guild is not None:
            old_guild = copy.copy(guild)
            guild._from_data(data)
            self.dispatch('guild_update', old_guild, guild)
        else:
            _log.debug('GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.', data['id'])

    def parse_guild_delete(self, data: gw.GuildDeleteEvent) -> None:
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

    def parse_guild_feature_ack(self, data: gw.NonChannelAckEvent) -> None:
        self.read_state_version = data.get('version', self.read_state_version)
        guild = self._get_guild(int(data['resource_id']))
        if guild is None:
            _log.debug('GUILD_FEATURE_ACK referencing an unknown guild ID: %s. Discarding.', data['resource_id'])
            return

        raw = RawGuildFeatureAckEvent(data, self)
        read_state = self.get_read_state(guild.id, raw.type)
        read_state.last_acked_id = int(data['entity_id'])
        self.dispatch('guild_feature_ack', raw)

        # Rich events here
        if read_state.type == ReadStateType.scheduled_events:
            event = guild.get_scheduled_event(read_state.last_acked_id)
            if event is not None:
                self.dispatch('scheduled_event_ack', event)

    def parse_guild_ban_add(self, data: gw.GuildBanAddEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                user = User(data=data['user'], state=self)
            except KeyError:
                pass
            else:
                member = guild.get_member(user.id) or user
                self.dispatch('member_ban', guild, member)

    def parse_guild_ban_remove(self, data: gw.GuildBanRemoveEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None and 'user' in data:
            user = self.store_user(data['user'])
            self.dispatch('member_unban', guild, user)

    def parse_guild_role_create(self, data: gw.GuildRoleCreateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        role_data = data['role']
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.dispatch('guild_role_create', role)

    def parse_guild_role_delete(self, data: gw.GuildRoleDeleteEvent) -> None:
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

    def parse_guild_role_update(self, data: gw.GuildRoleUpdateEvent) -> None:
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

    def parse_guild_members_chunk(self, data: gw.GuildMembersChunkEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        presences = data.get('presences', [])

        if guild is None:
            return

        members = [Member(guild=guild, data=member, state=self) for member in data.get('members', [])]
        _log.debug('Processed a chunk for %s members in guild ID %s.', len(members), guild_id)

        if presences:
            empty_tuple = ()
            member_dict: Dict[Snowflake, Member] = {str(member.id): member for member in members}
            for presence in presences:
                user = presence['user']
                member_id = user['id']
                member = member_dict.get(member_id)
                if member is not None:
                    member._presence_update(presence, empty_tuple)

        complete = data.get('chunk_index', 0) + 1 == data.get('chunk_count')
        self.process_chunk_requests(guild_id, data.get('nonce'), members, complete)

    def parse_guild_integrations_update(self, data: gw.GuildIntegrationsUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            self.dispatch('guild_integrations_update', guild)
        else:
            _log.debug('GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_integration_create(self, data: gw.IntegrationCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data['type'])
            integration = cls(data=data, guild=guild)
            self.dispatch('integration_create', integration)
        else:
            _log.debug('INTEGRATION_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_integration_update(self, data: gw.IntegrationUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data['type'])
            integration = cls(data=data, guild=guild)
            self.dispatch('integration_update', integration)
        else:
            _log.debug('INTEGRATION_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_integration_delete(self, data: gw.IntegrationDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            raw = RawIntegrationDeleteEvent(data)
            self.dispatch('raw_integration_delete', raw)
        else:
            _log.debug('INTEGRATION_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_webhooks_update(self, data: gw.WebhooksUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('WEBHOOKS_UPDATE referencing an unknown guild ID: %s. Discarding', data['guild_id'])
            return

        channel_id = utils._get_as_snowflake(data, 'channel_id')
        channel = guild.get_channel(channel_id)  # type: ignore # None is okay here
        if channel is not None:
            self.dispatch('webhooks_update', channel)
        else:
            _log.debug('WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])

    def parse_stage_instance_create(self, data: gw.StageInstanceCreateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            stage_instance = StageInstance(guild=guild, state=self, data=data)
            guild._stage_instances[stage_instance.id] = stage_instance
            self.dispatch('stage_instance_create', stage_instance)
        else:
            _log.debug('STAGE_INSTANCE_CREATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_stage_instance_update(self, data: gw.StageInstanceUpdateEvent) -> None:
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

    def parse_stage_instance_delete(self, data: gw.StageInstanceDeleteEvent) -> None:
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

    def parse_guild_scheduled_event_create(self, data: gw.GuildScheduledEventCreateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = ScheduledEvent(state=self, data=data)
            guild._scheduled_events[scheduled_event.id] = scheduled_event
            self.dispatch('scheduled_event_create', scheduled_event)

            read_state = self.get_read_state(guild.id, ReadStateType.scheduled_events)
            if scheduled_event.creator_id == self.self_id:
                # Implicitly ack created events
                read_state.last_acked_id = scheduled_event.id
            if not guild.notification_settings.mute_scheduled_events:
                # Increment badge count if we're not muted
                read_state.badge_count += 1
        else:
            _log.debug('SCHEDULED_EVENT_CREATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_update(self, data: gw.GuildScheduledEventUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.get(int(data['id']))
            if scheduled_event is not None:
                old_scheduled_event = copy.copy(scheduled_event)
                scheduled_event._update(data)
                self.dispatch('scheduled_event_update', old_scheduled_event, scheduled_event)
            else:
                _log.debug('SCHEDULED_EVENT_UPDATE referencing unknown scheduled event ID: %s. Discarding.', data['id'])
        else:
            _log.debug('SCHEDULED_EVENT_UPDATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_delete(self, data: gw.GuildScheduledEventDeleteEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                scheduled_event = guild._scheduled_events.pop(int(data['id']))
            except KeyError:
                pass
            else:
                self.dispatch('scheduled_event_delete', scheduled_event)
        else:
            _log.debug('SCHEDULED_EVENT_DELETE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_user_add(self, data: gw.GuildScheduledEventUserAdd) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.get(int(data['guild_scheduled_event_id']))
            if scheduled_event is not None:
                user_id = int(data['user_id'])
                user = self.get_user(user_id)
                if user is not None:
                    scheduled_event._add_user(user)
                    self.dispatch('scheduled_event_user_add', scheduled_event, user)
                self.dispatch('raw_scheduled_event_user_add', scheduled_event, user_id)
            else:
                _log.debug(
                    'SCHEDULED_EVENT_USER_ADD referencing unknown scheduled event ID: %s. Discarding.',
                    data['guild_scheduled_event_id'],
                )
        else:
            _log.debug('SCHEDULED_EVENT_USER_ADD referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_user_remove(self, data: gw.GuildScheduledEventUserRemove) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.get(int(data['guild_scheduled_event_id']))
            if scheduled_event is not None:
                user_id = int(data['user_id'])
                user = self.get_user(user_id)
                if user is not None:
                    scheduled_event._pop_user(user.id)
                    self.dispatch('scheduled_event_user_remove', scheduled_event, user)
                self.dispatch('raw_scheduled_event_user_remove', scheduled_event, user_id)
            else:
                _log.debug(
                    'SCHEDULED_EVENT_USER_REMOVE referencing unknown scheduled event ID: %s. Discarding.',
                    data['guild_scheduled_event_id'],
                )
        else:
            _log.debug('SCHEDULED_EVENT_USER_REMOVE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_call_create(self, data: gw.CallCreateEvent) -> None:
        channel_id = int(data['channel_id'])
        channel = self._get_private_channel(channel_id)
        if channel is None:
            _log.debug('CALL_CREATE referencing unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        call = self._calls.get(channel_id)
        if call is not None:
            # Should only happen for unavailable calls
            old_call = copy.copy(call)
            call._update(data)
            self.dispatch('call_update', old_call, call)

        message = self._get_message(int(data['message_id']))
        call = channel._add_call(data=data, state=self, message=message, channel=channel)
        self._calls[channel.id] = call
        self.dispatch('call_create', call)

    def parse_call_update(self, data: gw.CallUpdateEvent) -> None:
        call = self._calls.get(int(data['channel_id']))
        if call is None:
            _log.debug('CALL_UPDATE referencing unknown call (channel ID: %s). Discarding.', data['channel_id'])
            return
        old_call = copy.copy(call)
        call._update(data)
        self.dispatch('call_update', old_call, call)

    def parse_call_delete(self, data: gw.CallDeleteEvent) -> None:
        call = self._calls.pop(int(data['channel_id']), None)
        if call is not None:
            if data.get('unavailable'):
                old_call = copy.copy(call)
                call.unavailable = True
                self.dispatch('call_update', old_call, call)
                return

            call._delete()
            self._call_message_cache.pop(call._message_id, None)
            self.dispatch('call_delete', call)

    def parse_voice_state_update(self, data: gw.VoiceStateUpdateEvent) -> None:
        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        channel_id = utils._get_as_snowflake(data, 'channel_id')
        flags = self.member_cache_flags
        self_id = self.self_id

        if guild_id is not None and guild is None:
            _log.debug('VOICE_STATE_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        if int(data['user_id']) == self_id:
            voice = self._get_voice_client(guild.id if guild else self_id)
            if voice is not None:
                coro = voice.on_voice_state_update(data)
                asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice state update handler'))

        if guild is not None:
            member, before, after = guild._update_voice_state(data, channel_id)
            if member is not None:
                if flags.voice:
                    if channel_id is None and flags._voice_only and member.id != self_id:
                        guild._remove_member(member)
                    elif channel_id is not None:
                        guild._add_member(member)

                self.dispatch('voice_state_update', member, before, after)
            else:
                _log.debug('VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', data['user_id'])
        else:
            user, before, after = self._update_voice_state(data, channel_id)
            self.dispatch('voice_state_update', user, before, after)

    def parse_voice_server_update(self, data: gw.VoiceServerUpdateEvent) -> None:
        key_id = utils._get_as_snowflake(data, 'guild_id')
        if key_id is None:
            key_id = self.self_id

        vc = self._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_voice_server_update(data)
            asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice server update handler'))

    def parse_typing_start(self, data: gw.TypingStartEvent) -> None:
        channel, guild = self._get_guild_channel(data)
        if channel is not None:
            member = None
            user_id = int(data['user_id'])
            if isinstance(channel, DMChannel):
                member = channel.recipient

            elif isinstance(channel, (Thread, TextChannel)) and guild is not None:
                member = guild.get_member(user_id)

                if member is None:
                    member_data = data.get('member')
                    if member_data:
                        member = Member(data=member_data, state=self, guild=guild)

            elif isinstance(channel, GroupChannel):
                member = utils.find(lambda x: x.id == user_id, channel.recipients)

            if member is not None:
                timestamp = datetime.datetime.fromtimestamp(data['timestamp'], tz=datetime.timezone.utc)
                self.dispatch('typing', channel, member, timestamp)

    def parse_relationship_add(self, data: gw.RelationshipAddEvent) -> None:
        key = int(data['id'])
        new = self._relationships.get(key)
        if new is None:
            relationship = Relationship(state=self, data=data)
            self._relationships[key] = relationship
            self.dispatch('relationship_add', relationship)
        else:
            old = copy.copy(new)
            new._update(data)
            self.dispatch('relationship_update', old, new)

    def parse_relationship_remove(self, data: gw.RelationshipEvent) -> None:
        key = int(data['id'])
        try:
            old = self._relationships.pop(key)
        except KeyError:
            _log.warning('RELATIONSHIP_REMOVE referencing unknown relationship ID: %s. Discarding.', key)
        else:
            self.dispatch('relationship_remove', old)

    def parse_relationship_update(self, data: gw.RelationshipEvent) -> None:
        key = int(data['id'])
        new = self._relationships.get(key)
        if new is None:
            relationship = Relationship(state=self, data=data)  # type: ignore
            self._relationships[key] = relationship
        else:
            old = copy.copy(new)
            new._update(data)
            self.dispatch('relationship_update', old, new)

    def parse_friend_suggestion_create(self, data: gw.FriendSuggestionCreateEvent):
        self.friend_suggestion_count += 1
        self.dispatch('friend_suggestion_add', FriendSuggestion(state=self, data=data))

    def parse_friend_suggestion_delete(self, data: gw.FriendSuggestionDeleteEvent):
        self.friend_suggestion_count -= 1
        user_id = int(data['suggested_user_id'])
        user = self.get_user(user_id)
        if user:
            self.dispatch('friend_suggestion_remove', user)
        self.dispatch('raw_friend_suggestion_remove', user_id)

    def parse_interaction_create(self, data: gw.InteractionEvent) -> None:
        if 'nonce' not in data:  # Sometimes interactions seem to be missing the nonce
            return

        type, name, channel = self._interaction_cache.pop(data['nonce'], (0, None, None))
        i = Interaction._from_self(channel, type=type, user=self.user, name=name, **data)  # type: ignore # self.user is always present here
        self._interactions[i.id] = i
        self.dispatch('interaction', i)

    def parse_interaction_success(self, data: gw.InteractionEvent) -> None:
        id = int(data['id'])
        i = self._interactions.get(id, None)
        if i is None:
            _log.warning('INTERACTION_SUCCESS referencing an unknown interaction ID: %s. Discarding.', id)
            return

        i.successful = True
        self.dispatch('interaction_finish', i)

    def parse_interaction_failed(self, data: gw.InteractionEvent) -> None:
        id = int(data['id'])
        i = self._interactions.pop(id, None)
        if i is None:
            _log.warning('INTERACTION_FAILED referencing an unknown interaction ID: %s. Discarding.', id)
            return

        i.successful = False
        self.dispatch('interaction_finish', i)

    def parse_interaction_modal_create(self, data: gw.InteractionModalCreateEvent) -> None:
        id = int(data['id'])
        interaction = self._interactions.pop(id, None)
        if interaction is not None:
            modal = Modal(data=data, interaction=interaction)
            interaction.modal = modal
            self.dispatch('modal', modal)

    # Silence "unknown event" warnings for events parsed elsewhere
    parse_nothing = lambda *_: None
    # parse_guild_application_commands_update = parse_nothing  # Grabbed directly in command iterators

    def _get_reaction_user(self, channel: MessageableChannel, user_id: int) -> Optional[Union[User, Member]]:
        if isinstance(channel, (TextChannel, Thread, VoiceChannel, StageChannel)):
            return channel.guild.get_member(user_id)
        return self.get_user(user_id)

    def get_reaction_emoji(self, data: PartialEmojiPayload) -> Union[Emoji, PartialEmoji, str]:
        emoji_id = utils._get_as_snowflake(data, 'id')

        if not emoji_id:
            # the name key will be a str
            return data['name']  # type: ignore

        try:
            return self._emojis[emoji_id]
        except KeyError:
            return PartialEmoji.with_state(
                self, animated=data.get('animated', False), id=emoji_id, name=data['name']  # type: ignore
            )

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

    def _get_or_create_partial_messageable(self, id: Optional[int]) -> Optional[Union[Channel, Thread]]:
        if id is None:
            return None

        return self.get_channel(id) or PartialMessageable(state=self, id=id)

    def create_message(
        self,
        *,
        channel: MessageableChannel,
        data: MessagePayload,
        search_result: Optional[MessageSearchResultPayload] = None,
    ) -> Message:
        return Message(state=self, channel=channel, data=data, search_result=search_result)

    def _update_message_references(self) -> None:
        # self._messages won't be None when this is called
        for msg in self._messages:  # type: ignore
            if not msg.guild:
                continue

            new_guild = self._get_guild(msg.guild.id)
            if new_guild is not None and new_guild is not msg.guild:
                channel_id = msg.channel.id
                channel = new_guild._resolve_channel(channel_id) or PartialMessageable(
                    state=self, id=channel_id, guild_id=new_guild.id
                )
                msg._rebind_cached_references(new_guild, channel)

    def create_integration_application(self, data: IntegrationApplicationPayload) -> IntegrationApplication:
        return IntegrationApplication(state=self, data=data)

    def default_guild_settings(self, guild_id: Optional[int]) -> GuildSettings:
        return GuildSettings(data={'guild_id': guild_id}, state=self)  # type: ignore

    def default_channel_settings(self, guild_id: Optional[int], channel_id: int) -> ChannelSettings:
        return ChannelSettings(guild_id, data={'channel_id': channel_id}, state=self)  # type: ignore

    def create_implicit_relationship(self, user: User) -> Relationship:
        relationship = self._relationships.get(user.id)
        if relationship is not None:
            if relationship.type.value == 0:
                relationship.type = RelationshipType.implicit
        else:
            relationship = Relationship._from_implicit(state=self, user=user)
            self._relationships[relationship.id] = relationship
        return relationship

    @property
    def all_session(self) -> Optional[Session]:
        return self._sessions.get('all')

    @property
    def current_session(self) -> Optional[Session]:
        return self._sessions.get(self.session_id)  # type: ignore

    @utils.cached_property
    def client_presence(self) -> FakeClientPresence:
        return FakeClientPresence(self)

    def create_presence(self, data: gw.BasePresenceUpdate) -> Presence:
        return Presence(data, self)

    def create_offline_presence(self) -> Presence:
        return Presence._offline()

    def get_presence(self, user_id: int, guild_id: Optional[int] = None) -> Optional[Presence]:
        if user_id == self.self_id:
            # Our own presence is unified
            return self.client_presence

        if guild_id is not None:
            guild = self._guild_presences.get(guild_id)
            if guild is not None:
                return guild.get(user_id)
            return
        return self._presences.get(user_id)

    def remove_presence(self, user_id: int, guild_id: Optional[int] = None) -> None:
        if guild_id is not None:
            guild = self._guild_presences.get(guild_id)
            if guild is not None:
                guild.pop(user_id, None)
        else:
            self._presences.pop(user_id, None)

    def store_presence(self, user_id: int, presence: Presence, guild_id: Optional[int] = None) -> Presence:
        if presence.client_status.status == Status.offline.value and not presence.activities:
            # We don't store empty presences
            self.remove_presence(user_id, guild_id)
            return presence

        if user_id == self.self_id:
            # We don't store our own presence
            return presence

        if guild_id is not None:
            guild = self._guild_presences.get(guild_id)
            if guild is None:
                guild = self._guild_presences[guild_id] = {}
            guild[user_id] = presence
        else:
            self._presences[user_id] = presence
        return presence

    @overload
    def get_read_state(self, id: int, type: ReadStateType = ..., *, if_exists: Literal[False] = ...) -> ReadState:
        ...

    @overload
    def get_read_state(self, id: int, type: ReadStateType = ..., *, if_exists: Literal[True]) -> Optional[ReadState]:
        ...

    def get_read_state(
        self, id: int, type: ReadStateType = ReadStateType.channel, *, if_exists: bool = False
    ) -> Optional[ReadState]:
        try:
            return self._read_states[type.value][id]
        except KeyError:
            if not if_exists:
                # Create and store a default read state
                state = ReadState.default(id, type, state=self)
                self.store_read_state(state)
                return state

    def remove_read_state(self, read_state: ReadState) -> None:
        try:
            group = self._read_states[read_state.type.value]
        except KeyError:
            return
        group.pop(read_state.id, None)

    def store_read_state(self, read_state: ReadState):
        try:
            group = self._read_states[read_state.type.value]
        except KeyError:
            group = self._read_states[read_state.type.value] = {}
        group[read_state.id] = read_state

    @utils.cached_property
    def premium_subscriptions_application(self) -> PartialApplication:
        # Hardcoded application for premium subscriptions, highly unlikely to change
        return PartialApplication(
            state=self,
            data={
                'id': 521842831262875670,
                'name': 'Nitro',
                'icon': None,
                'description': '',
                'verify_key': '93661a9eefe452d12f51e129e8d9340e7ca53a770158c0ec7970e701534b7420',
                'type': None,
            },
        )

    @utils.cached_property
    def premium_subscriptions_sku_ids(self) -> Dict[str, Snowflake]:
        return {
            'none': 628379670982688768,
            'basic': 978380684370378762,
            'legacy': 521842865731534868,
            'classic': 521846918637420545,
            'full': 521847234246082599,
            'guild': 590663762298667008,
        }
