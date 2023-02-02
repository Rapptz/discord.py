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

from typing import List, Optional, TypedDict
from typing_extensions import NotRequired

from .snowflake import Snowflake
from .subscriptions import SubscriptionTrial


class Promotion(TypedDict):
    id: Snowflake
    trial_id: NotRequired[Snowflake]
    start_date: str
    end_date: str
    flags: int
    outbound_title: str
    outbound_redemption_modal_body: str
    outbound_redemption_page_link: NotRequired[str]
    outbound_redemption_url_format: NotRequired[str]
    outbound_restricted_countries: NotRequired[List[str]]
    outbound_terms_and_conditions: str
    inbound_title: NotRequired[str]
    inbound_body_text: NotRequired[str]
    inbound_help_center_link: NotRequired[str]
    inbound_restricted_countries: NotRequired[List[str]]


class ClaimedPromotion(TypedDict):
    promotion: Promotion
    code: str
    claimed_at: str


class TrialOffer(TypedDict):
    id: Snowflake
    expires_at: str
    trial_id: Snowflake
    subscription_trial: SubscriptionTrial


class PromotionalPrice(TypedDict):
    amount: int
    currency: str


class PricingPromotion(TypedDict):
    plan_id: Snowflake
    country_code: str
    payment_source_types: List[str]
    price: PromotionalPrice


class WrappedPricingPromotion(TypedDict):
    country_code: str
    localized_pricing_promo: Optional[PricingPromotion]
