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

from .snowflake import Snowflake
from typing import Literal, Optional, TypedDict
from typing_extensions import NotRequired


class AvatarDecorationData(TypedDict):
    asset: str
    sku_id: Snowflake


class PartialUser(TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    avatar: Optional[str]
    global_name: Optional[str]
    avatar_decoration_data: NotRequired[AvatarDecorationData]


PremiumType = Literal[0, 1, 2, 3]


class User(PartialUser, total=False):
    bot: bool
    system: bool
    mfa_enabled: bool
    locale: str
    verified: bool
    email: Optional[str]
    flags: int
    premium_type: PremiumType
    public_flags: int
