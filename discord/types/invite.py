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

from .scheduled_event import GuildScheduledEvent
from .snowflake import Snowflake
from .guild import InviteGuild, _GuildPreviewUnique
from .channel import PartialChannel
from .user import PartialUser
from .application import PartialApplication

InviteTargetType = Literal[1, 2]


class _InviteMetadata(TypedDict, total=False):
    uses: int
    max_uses: int
    max_age: int
    temporary: bool
    created_at: str
    expires_at: Optional[str]


class VanityInvite(_InviteMetadata):
    code: Optional[str]
    revoked: NotRequired[bool]


class IncompleteInvite(_InviteMetadata):
    code: str
    channel: PartialChannel


class Invite(IncompleteInvite, total=False):
    guild: InviteGuild
    inviter: PartialUser
    target_user: PartialUser
    target_type: InviteTargetType
    target_application: PartialApplication
    guild_scheduled_event: GuildScheduledEvent


class InviteWithCounts(Invite, _GuildPreviewUnique):
    ...


class GatewayInviteCreate(TypedDict):
    channel_id: Snowflake
    code: str
    created_at: str
    max_age: int
    max_uses: int
    temporary: bool
    uses: bool
    guild_id: Snowflake
    inviter: NotRequired[PartialUser]
    target_type: NotRequired[InviteTargetType]
    target_user: NotRequired[PartialUser]
    target_application: NotRequired[PartialApplication]


class GatewayInviteDelete(TypedDict):
    channel_id: Snowflake
    code: str
    guild_id: NotRequired[Snowflake]


GatewayInvite = Union[GatewayInviteCreate, GatewayInviteDelete]
