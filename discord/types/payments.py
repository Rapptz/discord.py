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

from typing import List, Literal, TypedDict
from typing_extensions import NotRequired

from .billing import PartialPaymentSource
from .snowflake import Snowflake
from .store import SKU
from .subscriptions import PartialSubscription


class PartialPayment(TypedDict):
    # TODO: There might be more, but I don't have an example payload
    id: Snowflake
    amount: int
    tax: int
    tax_inclusive: bool
    currency: str


class Payment(PartialPayment):
    amount_refunded: int
    description: str
    status: Literal[0, 1, 2, 3, 4, 5]
    created_at: str
    sku_id: NotRequired[Snowflake]
    sku_price: NotRequired[int]
    sku_subscription_plan_id: NotRequired[Snowflake]
    payment_gateway: NotRequired[Literal[1, 2, 3, 4, 5, 6]]
    payment_gateway_payment_id: NotRequired[str]
    downloadable_invoice: NotRequired[str]
    downloadable_refund_invoices: NotRequired[List[str]]
    refund_disqualification_reasons: NotRequired[List[str]]
    flags: int
    sku: NotRequired[SKU]
    payment_source: NotRequired[PartialPaymentSource]
    subscription: NotRequired[PartialSubscription]
