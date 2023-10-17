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

from typing import Optional, TypedDict
from .snowflake import SnowflakeList
from .user import User


class Nickname(TypedDict):
    nick: str


class PartialMember(TypedDict):
    roles: SnowflakeList
    joined_at: str
    deaf: bool
    mute: bool
    flags: int


class Member(PartialMember, total=False):
    avatar: str
    user: User
    nick: str
    premium_since: Optional[str]
    pending: bool
    permissions: str
    communication_disabled_until: str


class _OptionalMemberWithUser(PartialMember, total=False):
    avatar: str
    nick: str
    premium_since: Optional[str]
    pending: bool
    permissions: str
    communication_disabled_until: str


class MemberWithUser(_OptionalMemberWithUser):
    user: User


class UserWithMember(User, total=False):
    member: _OptionalMemberWithUser
