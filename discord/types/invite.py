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

from typing import Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

from .application import PartialApplication
from .channel import InviteStageInstance, PartialChannel
from .gateway import InviteCreateEvent, InviteDeleteEvent
from .guild import InviteGuild, _GuildCounts
from .scheduled_event import GuildScheduledEvent
from .snowflake import Snowflake
from .user import PartialUser

InviteTargetType = Literal[1, 2]


class _InviteMetadata(TypedDict):
    uses: NotRequired[int]
    max_uses: NotRequired[int]
    max_age: NotRequired[int]
    temporary: NotRequired[bool]
    created_at: str


class _InviteTargetType(TypedDict, total=False):
    target_type: InviteTargetType
    target_user: PartialUser
    target_application: PartialApplication


class VanityInvite(TypedDict):
    code: Optional[str]
    uses: int


class PartialInvite(_InviteTargetType):
    code: str
    type: Literal[0, 1, 2]
    channel: Optional[PartialChannel]
    guild_id: NotRequired[Snowflake]
    guild: NotRequired[InviteGuild]
    inviter: NotRequired[PartialUser]
    flags: NotRequired[int]
    expires_at: Optional[str]
    guild_scheduled_event: NotRequired[GuildScheduledEvent]
    stage_instance: NotRequired[InviteStageInstance]


class InviteWithCounts(PartialInvite, _GuildCounts):
    ...


class InviteWithMetadata(PartialInvite, _InviteMetadata):
    ...


class AcceptedInvite(InviteWithCounts):
    new_member: bool
    show_verification_form: bool


Invite = Union[PartialInvite, InviteWithCounts, InviteWithMetadata, AcceptedInvite]
GatewayInvite = Union[InviteCreateEvent, InviteDeleteEvent]
