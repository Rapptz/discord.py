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

import datetime
from typing import List, Optional, TYPE_CHECKING

from . import utils
from .enums import try_enum, SubscriptionStatus

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.subscription import Subscription as SubscriptionPayload

__all__ = (
    'Subscription',
)


class Subscription:
    """Represents a premium offering as a stock-keeping unit (SKU).

    .. versionadded:: 2.5

    Attributes
    -----------
    id: :class:`int`
        The subscription's ID.
    status: :class:`SubscriptionStatus`
        The status of the subscription.
    application_id: :class:`int`
        The ID of the application that the SKU belongs to.
    name: :class:`str`
        The consumer-facing name of the premium offering.
    slug: :class:`str`
        A system-generated URL slug based on the SKU name.
    """

    __slots__ = (
        '_state',
        'id',
        'user_id',
        'sku_ids',
        'entitlement_ids',
        'current_period_start',
        'current_period_end',
        'status',
        'canceled_at',
    )

    def __init__(self, *, state: ConnectionState, data: SubscriptionPayload):
        self._state = state
        
        self.id: int = int(data['id'])
        self.user_id: int = int(data['user_id'])
        self.sku_ids: List[int] = list(map(int, data['sku_ids']))
        self.entitlement_ids: List[int] = list(map(int, data['entitlement_ids']))
        self.current_period_start: datetime.datetime = utils.parse_time(data['current_period_start'])
        self.current_period_end: datetime.datetime = utils.parse_time(data['current_period_end'])
        self.status: SubscriptionStatus = try_enum(SubscriptionStatus, data['status'])
        self.canceled_at: Optional[datetime.datetime] = utils.parse_time(data['canceled_at'])
