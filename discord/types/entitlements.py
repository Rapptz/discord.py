"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from .payments import PartialPayment
from .promotions import Promotion
from .snowflake import Snowflake
from .store import SKU, StoreListing
from .subscriptions import PartialSubscriptionPlan, SubscriptionPlan, SubscriptionTrial
from .user import PartialUser


class Entitlement(TypedDict):
    id: Snowflake
    type: Literal[1, 2, 3, 4, 5, 6, 7]
    user_id: Snowflake
    sku_id: Snowflake
    application_id: Snowflake
    promotion_id: Optional[Snowflake]
    parent_id: NotRequired[Snowflake]
    guild_id: NotRequired[Snowflake]
    branches: NotRequired[List[Snowflake]]
    gifter_user_id: NotRequired[Snowflake]
    gift_style: NotRequired[Literal[1, 2, 3]]
    gift_batch_id: NotRequired[Snowflake]
    gift_code_flags: NotRequired[int]
    deleted: bool
    consumed: NotRequired[bool]
    starts_at: NotRequired[str]
    ends_at: NotRequired[str]
    subscription_id: NotRequired[Snowflake]
    subscription_plan: NotRequired[PartialSubscriptionPlan]
    sku: NotRequired[SKU]
    payment: NotRequired[PartialPayment]


class GatewayGift(TypedDict):
    code: str
    uses: int
    sku_id: Snowflake
    channel_id: NotRequired[Snowflake]
    guild_id: NotRequired[Snowflake]


class Gift(GatewayGift):
    expires_at: Optional[str]
    application_id: Snowflake
    batch_id: NotRequired[Snowflake]
    entitlement_branches: NotRequired[List[Snowflake]]
    gift_style: NotRequired[Optional[Literal[1, 2, 3]]]
    flags: int
    max_uses: int
    uses: int
    redeemed: bool
    revoked: NotRequired[bool]
    store_listing: NotRequired[StoreListing]
    promotion: NotRequired[Promotion]
    subscription_trial: NotRequired[SubscriptionTrial]
    subscription_plan: NotRequired[SubscriptionPlan]
    user: NotRequired[PartialUser]


class GiftBatch(TypedDict):
    id: Snowflake
    sku_id: Snowflake
    amount: int
    description: NotRequired[str]
    entitlement_branches: NotRequired[List[Snowflake]]
    entitlement_starts_at: NotRequired[str]
    entitlement_ends_at: NotRequired[str]
