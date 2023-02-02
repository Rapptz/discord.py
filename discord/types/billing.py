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

from typing import Literal, TypedDict
from typing_extensions import NotRequired


class BillingAddress(TypedDict):
    line_1: str
    line_2: NotRequired[str]
    name: str
    postal_code: NotRequired[str]
    city: str
    state: NotRequired[str]
    country: str
    email: NotRequired[str]


class BillingAddressToken(TypedDict):
    token: str


class PartialPaymentSource(TypedDict):
    id: str
    brand: NotRequired[str]
    country: NotRequired[str]
    last_4: NotRequired[str]
    type: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    payment_gateway: Literal[1, 2, 3, 4, 5, 6]
    invalid: bool
    flags: int
    expires_month: NotRequired[int]
    expires_year: NotRequired[int]
    email: NotRequired[str]
    bank: NotRequired[str]
    username: NotRequired[str]
    screen_status: int  # TODO: Figure this out


class PaymentSource(PartialPaymentSource):
    billing_address: BillingAddress
    default: bool


class PremiumUsageValue(TypedDict):
    value: int


class PremiumUsage(TypedDict):
    nitro_sticker_sends: PremiumUsageValue
    total_animated_emojis: PremiumUsageValue
    total_global_emojis: PremiumUsageValue
    total_large_uploads: PremiumUsageValue
    total_hd_streams: PremiumUsageValue
    hd_hours_streamed: PremiumUsageValue
