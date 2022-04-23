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

from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    from typing import Optional, Sequence

    from discord import Emoji, Guild, GuildSticker, Integration, Invite, RawIntegrationDeleteEvent, User
    from discord.abc import GroupChannel, GuildChannel

__all__ = (
    'Event',
    'GuildChannelDelete',
    'GuildChannelCreate',
    'GuildChannelUpdate',
    'GroupJoin',
    'GroupRemove',
    'GuildChannelPinsUpdate',
    'PrivateChannelUpdate',
    'PrivateChannelPinsUpdate',
    'Typing',
    'Connect',
    'Disconnect',
    'ShardConnect',
    'ShardDisconnect',
    'Error',
    'SocketEventType',
    'SocketRawReceive',
    'SocketRawSend',
    'Ready',
    'Resumed',
    'ShardReady',
    'ShardResumed',
    'GuildAvailable',
    'GuildUnavailable',
    'GuildJoin',
    'GuildRemove',
    'GuildUpdate',
    'GuildEmojisUpdate',
    'GuildStickersUpdate',
    'InviteCreate',
    'InviteDelete',
    'IntegrationCreate',
    'IntegrationUpdate',
    'GuildIntegrationUpdate',
    'WekhooksUpdate',
    'RawIntegrationDelete',
    'Interaction',
)


class Event(ABC):
    pass


@dataclass(frozen=True)
class GuildChannelDelete(Event):
    channel: GuildChannel


@dataclass(frozen=True)
class GuildChannelCreate(Event):
    channel: GuildChannel


@dataclass(frozen=True)
class GuildChannelUpdate(Event):
    before: GuildChannel
    after: GuildChannel


@dataclass(frozen=True)
class GroupJoin(Event):
    channel: GroupChannel
    user: User


@dataclass(frozen=True)
class GroupRemove(Event):
    channel: GroupChannel
    user: User


@dataclass(frozen=True)
class GuildChannelPinsUpdate(Event):
    channel: GuildChannel
    last_pin: Optional[datetime.datetime]


@dataclass(frozen=True)
class PrivateChannelUpdate(Event):
    before: GroupChannel
    after: GroupChannel


@dataclass(frozen=True)
class PrivateChannelPinsUpdate(Event):
    channel: GroupChannel
    last_pin: Optional[datetime.datetime]


@dataclass(frozen=True)
class Typing(Event):
    pass


@dataclass(frozen=True)
class Connect(Event):
    pass


@dataclass(frozen=True)
class Disconnect(Event):
    pass


@dataclass(frozen=True)
class ShardConnect(Event):
    shard_id: int


@dataclass(frozen=True)
class ShardDisconnect(Event):
    shard_id: int


@dataclass(frozen=True)
class Error(Event):
    event: Event


@dataclass(frozen=True)
class SocketEventType(Event):
    event_type: str


@dataclass(frozen=True)
class SocketRawReceive(Event):
    msg: str


@dataclass(frozen=True)
class SocketRawSend(Event):
    payload: str | bytes


@dataclass(frozen=True)
class Ready(Event):
    pass


@dataclass(frozen=True)
class Resumed(Event):
    pass


@dataclass(frozen=True)
class ShardReady(Event):
    shard_id: int


@dataclass(frozen=True)
class ShardResumed(Event):
    shard_id: int


@dataclass(frozen=True)
class GuildAvailable(Event):
    guild: Guild


@dataclass(frozen=True)
class GuildUnavailable(Event):
    guild: Guild


@dataclass(frozen=True)
class GuildJoin(Event):
    guild: Guild


@dataclass(frozen=True)
class GuildRemove(Event):
    guild: Guild


@dataclass(frozen=True)
class GuildUpdate(Event):
    before: Guild
    after: Guild


@dataclass(frozen=True)
class GuildEmojisUpdate(Event):
    guild: Guild
    before: Sequence[Emoji]
    after: Sequence[Emoji]


@dataclass(frozen=True)
class GuildStickersUpdate(Event):
    guild: Guild
    before: Sequence[GuildSticker]
    after: Sequence[GuildSticker]


@dataclass(frozen=True)
class InviteCreate(Event):
    invite: Invite


@dataclass(frozen=True)
class InviteDelete(Event):
    invite: Invite


@dataclass(frozen=True)
class IntegrationCreate(Event):
    integration: Integration


@dataclass(frozen=True)
class IntegrationUpdate(Event):
    # TODO isn't it before / after ?
    integration: Integration


@dataclass(frozen=True)
class GuildIntegrationUpdate(Event):
    guild: Guild


@dataclass(frozen=True)
class WekhooksUpdate(Event):
    channel: GuildChannel


@dataclass(frozen=True)
class RawIntegrationDelete(Event):
    # TODO seems redundant
    payload: RawIntegrationDeleteEvent


@dataclass(frozen=True)
class Interaction(Event):
    interaction: Interaction
