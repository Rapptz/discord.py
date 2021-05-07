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
from .team import Team
from .user import PartialUser
from typing import List, Optional, TypedDict


class _AppInfoOptional(TypedDict, total=False):
    rpc_origins: List[str]
    terms_of_service_url: str
    privacy_policy_url: str
    guild_id: Snowflake
    primary_sku_id: Snowflake
    slug: str


class AppInfo(_AppInfoOptional):
    id: Snowflake
    name: str
    icon: Optional[str]
    description: str
    bot_public: bool
    bot_require_code_grant: bool
    owner: PartialUser
    summary: str
    verify_key: str
    team: Optional[Team]
    flags: int
