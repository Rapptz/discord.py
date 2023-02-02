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

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from .billing import PaymentSource
from .enums import (
    PaymentGateway,
    SubscriptionDiscountType,
    SubscriptionInterval,
    SubscriptionInvoiceStatus,
    SubscriptionStatus,
    SubscriptionType,
    try_enum,
)
from .metadata import Metadata
from .mixins import Hashable
from .utils import MISSING, _get_as_snowflake, parse_time, snowflake_time, utcnow

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.subscriptions import (
        SubscriptionDiscount as SubscriptionDiscountPayload,
        SubscriptionInvoice as SubscriptionInvoicePayload,
        SubscriptionInvoiceItem as SubscriptionInvoiceItemPayload,
        SubscriptionItem as SubscriptionItemPayload,
        SubscriptionRenewalMutations as SubscriptionRenewalMutationsPayload,
        PartialSubscription as PartialSubscriptionPayload,
        Subscription as SubscriptionPayload,
        SubscriptionTrial as SubscriptionTrialPayload,
    )

__all__ = (
    'SubscriptionItem',
    'SubscriptionDiscount',
    'SubscriptionInvoiceItem',
    'SubscriptionInvoice',
    'SubscriptionRenewalMutations',
    'Subscription',
    'SubscriptionTrial',
)


class SubscriptionItem(Hashable):
    """Represents a Discord subscription item.

    .. container:: operations

        .. describe:: x == y

            Checks if two subscription items are equal.

        .. describe:: x != y

            Checks if two subscription items are not equal.

        .. describe:: hash(x)

            Returns the item's hash.

        .. describe:: len(x)

            Returns the quantity of the subscription item.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of the subscription item. Always available when received from the API.
    quantity: :class:`int`
        How many of the item have been/are being purchased.
    plan_id: :class:`int`
        The ID of the plan the item is for.
    """

    __slots__ = ('id', 'quantity', 'plan_id')

    def __init__(self, *, id: Optional[int] = None, plan_id: int, quantity: int = 1) -> None:
        self.id: Optional[int] = id
        self.quantity: int = quantity
        self.plan_id: int = plan_id

    def __repr__(self) -> str:
        return f'<SubscriptionItem {f"id={self.id} " if self.id else ""}plan_id={self.plan_id} quantity={self.quantity}>'

    def __len__(self) -> int:
        return self.quantity

    @classmethod
    def from_dict(cls, data: SubscriptionItemPayload) -> Self:
        return cls(id=int(data['id']), plan_id=int(data['plan_id']), quantity=int(data.get('quantity', 1)))

    def to_dict(self, with_id: bool = True) -> dict:
        data = {
            'quantity': self.quantity,
            'plan_id': self.plan_id,
        }
        if self.id and with_id:
            data['id'] = self.id

        return data


class SubscriptionDiscount:
    """Represents a discount on a Discord subscription item.

    .. container:: operations

        .. describe:: int(x)

            Returns the discount's amount.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`SubscriptionDiscountType`
        The type of the discount.
    amount: :class:`int`
        How much the discount is.
    """

    __slots__ = ('type', 'amount')

    def __init__(self, data: SubscriptionDiscountPayload) -> None:
        self.type: SubscriptionDiscountType = try_enum(SubscriptionDiscountType, data['type'])
        self.amount: int = data['amount']

    def __repr__(self) -> str:
        return f'<SubscriptionDiscount type={self.type!r} amount={self.amount}>'

    def __int__(self) -> int:
        return self.amount


class SubscriptionInvoiceItem(Hashable):
    """Represents an invoice item.

    .. container:: operations

        .. describe:: x == y

            Checks if two invoice items are equal.

        .. describe:: x != y

            Checks if two invoice items are not equal.

        .. describe:: hash(x)

            Returns the invoice's hash.

        .. describe:: len(x)

            Returns the quantity of the invoice item.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the invoice item.
    quantity: :class:`int`
        How many of the item have been/are being purchased.
    amount: :class:`int`
        The price of the item. This includes discounts.
    proration: :class:`bool`
        Whether the item is prorated.
    plan_id: :class:`int`
        The ID of the subscription plan the item represents.
    plan_price: :class:`int`
        The price of the subscription plan the item represents. This does not include discounts.
    discounts: List[:class:`SubscriptionDiscount`]
        A list of discounts applied to the item.
    """

    __slots__ = ('id', 'quantity', 'amount', 'proration', 'plan_id', 'plan_price', 'discounts')

    def __init__(self, data: SubscriptionInvoiceItemPayload) -> None:
        self.id: int = int(data['id'])
        self.quantity: int = data['quantity']
        self.amount: int = data['amount']
        self.proration: bool = data.get('proration', False)
        self.plan_id: int = int(data['subscription_plan_id'])
        self.plan_price: int = data['subscription_plan_price']
        self.discounts: List[SubscriptionDiscount] = [SubscriptionDiscount(d) for d in data['discounts']]

    def __repr__(self) -> str:
        return f'<SubscriptionInvoiceItem id={self.id} quantity={self.quantity} amount={self.amount}>'

    def __len__(self) -> int:
        return self.quantity

    @property
    def savings(self) -> int:
        """:class:`int`: The total amount of discounts on the invoice item."""
        return self.plan_price - self.amount

    def is_discounted(self) -> bool:
        """:class:`bool`: Indicates if the invoice item has a discount."""
        return bool(self.discounts)

    def is_trial(self) -> bool:
        """:class:`bool`: Indicates if the invoice item is a trial."""
        return not self.amount or any(discount.type is SubscriptionDiscountType.premium_trial for discount in self.discounts)


class SubscriptionInvoice(Hashable):
    """Represents an invoice for a Discord subscription.

    .. container:: operations

        .. describe:: x == y

            Checks if two invoices are equal.

        .. describe:: x != y

            Checks if two invoices are not equal.

        .. describe:: hash(x)

            Returns the invoice's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    subscription: Optional[:class:`Subscription`]
        The subscription the invoice is for. Not available for new subscription previews.
    id: :class:`int`
        The ID of the invoice.
    status: Optional[:class:`SubscriptionInvoiceStatus`]
        The status of the invoice. Not available for subscription previews.
    currency: :class:`str`
        The currency the invoice is in.
    subtotal: :class:`int`
        The subtotal of the invoice.
    tax: :class:`int`
        The tax applied to the invoice.
    total: :class:`int`
        The total of the invoice.
    tax_inclusive: :class:`bool`
        Whether the subtotal is inclusive of all taxes.
    items: List[:class:`SubscriptionInvoiceItem`]
        The items in the invoice.
    current_period_start: :class:`datetime.datetime`
        When the current billing period started.
    current_period_end: :class:`datetime.datetime`
        When the current billing period ends.
    """

    __slots__ = (
        '_state',
        'subscription',
        'id',
        'status',
        'currency',
        'subtotal',
        'tax',
        'total',
        'tax_inclusive',
        'items',
        'current_period_start',
        'current_period_end',
    )

    def __init__(
        self, subscription: Optional[Subscription], *, data: SubscriptionInvoicePayload, state: ConnectionState
    ) -> None:
        self._state = state
        self.subscription = subscription
        self._update(data)

    def _update(self, data: SubscriptionInvoicePayload) -> None:
        self.id: int = int(data['id'])
        self.status: Optional[SubscriptionInvoiceStatus] = (
            try_enum(SubscriptionInvoiceStatus, data['status']) if 'status' in data else None
        )
        self.currency: str = data['currency']
        self.subtotal: int = data['subtotal']
        self.tax: int = data.get('tax', 0)
        self.total: int = data['total']
        self.tax_inclusive: bool = data['tax_inclusive']
        self.items: List[SubscriptionInvoiceItem] = [SubscriptionInvoiceItem(d) for d in data.get('invoice_items', [])]

        self.current_period_start: datetime = parse_time(data['subscription_period_start'])  # type: ignore # Should always be a datetime
        self.current_period_end: datetime = parse_time(data['subscription_period_end'])  # type: ignore # Should always be a datetime

    def __repr__(self) -> str:
        return f'<SubscriptionInvoice id={self.id} status={self.status!r} total={self.total}>'

    def is_discounted(self) -> bool:
        """:class:`bool`: Indicates if the invoice has a discount."""
        return any(item.discounts for item in self.items)

    def is_preview(self) -> bool:
        """:class:`bool`: Indicates if the invoice is a preview and not real."""
        return self.subscription is None or self.status is None

    async def pay(
        self,
        payment_source: Optional[Snowflake] = None,
        currency: str = 'usd',
        *,
        payment_source_token: Optional[str] = None,
        return_url: Optional[str] = None,
    ) -> None:
        """|coro|

        Pays the invoice.

        Parameters
        ----------
        payment_source: Optional[:class:`PaymentSource`]
            The payment source the invoice should be paid with.
        currency: :class:`str`
            The currency to pay with.
        payment_source_token: Optional[:class:`str`]
            The token used to authorize with the payment source.
        return_url: Optional[:class:`str`]
            The URL to return to after the payment is complete.

        Raises
        ------
        TypeError
            The invoice is a preview and not real.
        NotFound
            The invoice is not open or found.
        HTTPException
            Paying the invoice failed.
        """
        if self.is_preview() or not self.subscription:
            raise TypeError('Cannot pay a nonexistant invoice')

        data = await self._state.http.pay_invoice(
            self.subscription.id,
            self.id,
            payment_source.id if payment_source else None,
            payment_source_token,
            currency,
            return_url,
        )
        self.subscription._update(data)


class SubscriptionRenewalMutations:
    """Represents a subscription renewal mutation.

    This represents changes to a subscription that will occur after renewal.

    .. container:: operations

        .. describe:: len(x)

            Returns the number of items in the changed subscription, including quantity.

        .. describe:: bool(x)

            Returns whether any mutations are present.

    .. versionadded:: 2.0

    Attributes
    ----------
    payment_gateway_plan_id: Optional[:class:`str`]
        The payment gateway's new plan ID for the subscription.
        This signifies an external plan change.
    items: Optional[List[:class:`SubscriptionItem`]]
        The new items of the subscription.
    """

    __slots__ = ('payment_gateway_plan_id', 'items')

    def __init__(self, data: SubscriptionRenewalMutationsPayload) -> None:
        self.payment_gateway_plan_id: Optional[str] = data.get('payment_gateway_plan_id')
        self.items: Optional[List[SubscriptionItem]] = (
            [SubscriptionItem.from_dict(item) for item in data['items']] if 'items' in data else None
        )

    def __repr__(self) -> str:
        return (
            f'<SubscriptionRenewalMutations payment_gateway_plan_id={self.payment_gateway_plan_id!r} items={self.items!r}>'
        )

    def __len__(self) -> int:
        return sum(item.quantity for item in self.items) if self.items else 0

    def __bool__(self) -> bool:
        return self.is_mutated()

    def is_mutated(self) -> bool:
        """:class:`bool`: Checks if any renewal mutations exist."""
        return self.payment_gateway_plan_id is not None or self.items is not None


class Subscription(Hashable):
    """Represents a Discord subscription.

    .. container:: operations

        .. describe:: x == y

            Checks if two premium subscriptions are equal.

        .. describe:: x != y

            Checks if two premium subscriptions are not equal.

        .. describe:: hash(x)

            Returns the subscription's hash.

        .. describe:: len(x)

            Returns the number of items in the subscription, including quantity.

        .. describe:: bool(x)

            Checks if the subscription is currently active and offering perks.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the subscription.
    type: :class:`SubscriptionType`
        The type of the subscription.
    status: Optional[:class:`SubscriptionStatus`]
        The status of the subscription. This is ``None`` for fake subscriptions.
    payment_gateway: Optional[:class:`PaymentGateway`]
        The payment gateway used to bill the subscription.
    currency: :class:`str`
        The currency the subscription is billed in.
    items: List[:class:`SubscriptionItem`]
        The items in the subscription.
    renewal_mutations: :class:`SubscriptionRenewalMutations`
        The mutations to the subscription that will occur after renewal.
    trial_id: Optional[:class:`int`]
        The ID of the trial the subscription is from, if applicable.
    payment_source_id: Optional[:class:`int`]
        The ID of the payment source the subscription is paid with, if applicable.
    payment_gateway_plan_id: Optional[:class:`str`]
        The payment gateway's plan ID for the subscription, if applicable.
    payment_gateway_subscription_id: Optional[:class:`str`]
        The payment gateway's subscription ID for the subscription, if applicable.
    created_at: :class:`datetime.datetime`
        When the subscription was created.
    canceled_at: Optional[:class:`datetime.datetime`]
        When the subscription was canceled.
        This is only available for subscriptions with a :attr:`status` of :attr:`SubscriptionStatus.canceled`.
    current_period_start: :class:`datetime.datetime`
        When the current billing period started.
    current_period_end: :class:`datetime.datetime`
        When the current billing period ends.
    trial_ends_at: Optional[:class:`datetime.datetime`]
        When the trial ends, if applicable.
    streak_started_at: Optional[:class:`datetime.datetime`]
        When the current subscription streak started.
    ended_at: Optional[:class:`datetime.datetime`]
        When the subscription finally ended.
    metadata: :class:`Metadata`
        Extra metadata about the subscription.
    latest_invoice: Optional[:class:`SubscriptionInvoice`]
        The latest invoice for the subscription, if applicable.
    """

    __slots__ = (
        '_state',
        'id',
        'type',
        'status',
        'payment_gateway',
        'currency',
        'items',
        'renewal_mutations',
        'trial_id',
        'payment_source_id',
        'payment_gateway_plan_id',
        'payment_gateway_subscription_id',
        'created_at',
        'canceled_at',
        'current_period_start',
        'current_period_end',
        'trial_ends_at',
        'streak_started_at',
        'ended_at',
        'metadata',
        'latest_invoice',
    )

    def __init__(self, *, data: Union[PartialSubscriptionPayload, SubscriptionPayload], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<Subscription id={self.id} currency={self.currency!r} items={self.items!r}>'

    def __len__(self) -> int:
        return sum(item.quantity for item in self.items)

    def __bool__(self) -> bool:
        return self.is_active()

    def _update(self, data: PartialSubscriptionPayload) -> None:
        self.id: int = int(data['id'])
        self.type: SubscriptionType = try_enum(SubscriptionType, data['type'])
        self.status: Optional[SubscriptionStatus] = (
            try_enum(SubscriptionStatus, data['status']) if 'status' in data else None  # type: ignore # ???
        )
        self.payment_gateway: Optional[PaymentGateway] = (
            try_enum(PaymentGateway, data['payment_gateway']) if 'payment_gateway' in data else None
        )
        self.currency: str = data.get('currency', 'usd')
        self.items: List[SubscriptionItem] = [SubscriptionItem.from_dict(item) for item in data.get('items', [])]
        self.renewal_mutations: SubscriptionRenewalMutations = SubscriptionRenewalMutations(
            data.get('renewal_mutations') or {}
        )

        self.trial_id: Optional[int] = _get_as_snowflake(data, 'trial_id')
        self.payment_source_id: Optional[int] = _get_as_snowflake(data, 'payment_source_id')
        self.payment_gateway_plan_id: Optional[str] = data.get('payment_gateway_plan_id')
        self.payment_gateway_subscription_id: Optional[str] = data.get('payment_gateway_subscription_id')

        self.created_at: datetime = parse_time(data.get('created_at')) or snowflake_time(self.id)
        self.canceled_at: Optional[datetime] = parse_time(data.get('canceled_at'))

        self.current_period_start: datetime = parse_time(data['current_period_start'])
        self.current_period_end: datetime = parse_time(data['current_period_end'])
        self.trial_ends_at: Optional[datetime] = parse_time(data.get('trial_ends_at'))
        self.streak_started_at: Optional[datetime] = parse_time(data.get('streak_started_at'))

        metadata = data.get('metadata') or {}
        self.ended_at: Optional[datetime] = parse_time(metadata.get('ended_at', None))
        self.metadata: Metadata = Metadata(metadata)

        self.latest_invoice: Optional[SubscriptionInvoice] = (
            SubscriptionInvoice(self, data=data['latest_invoice'], state=self._state) if 'latest_invoice' in data else None  # type: ignore # ???
        )

    @property
    def cancelled_at(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: When the subscription was canceled.
        This is only available for subscriptions with a :attr:`status` of :attr:`SubscriptionStatus.canceled`.

        This is an alias of :attr:`canceled_at`.
        """
        return self.canceled_at

    @property
    def guild(self) -> Optional[Guild]:
        """:class:`Guild`: The guild the subscription's entitlements apply to, if applicable."""
        return self._state._get_guild(self.metadata.guild_id)

    @property
    def grace_period(self) -> int:
        """:class:`int`: How many days past the renewal date the user has available to pay outstanding invoices.

        .. note::

            This is a static value and does not change based on the subscription's status.
            For that, see :attr:`remaining`.
        """
        return 7 if self.payment_source_id else 3

    @property
    def remaining(self) -> timedelta:
        """:class:`datetime.timedelta`: The remaining time until the subscription ends."""
        if self.status in (SubscriptionStatus.active, SubscriptionStatus.cancelled):
            return self.current_period_end - utcnow()
        elif self.status == SubscriptionStatus.past_due:
            if self.payment_gateway == PaymentGateway.google and self.metadata.google_grace_period_expires_date:
                return self.metadata.google_grace_period_expires_date - utcnow()
            return (self.current_period_start + timedelta(days=self.grace_period)) - utcnow()
        elif self.status == SubscriptionStatus.account_hold:
            # Max hold time is 30 days
            return (self.current_period_start + timedelta(days=30)) - utcnow()
        return timedelta()

    @property
    def trial_remaining(self) -> timedelta:
        """:class:`datetime.timedelta`: The remaining time until the trial applied to the subscription ends."""
        if not self.trial_id:
            return timedelta()
        if not self.trial_ends_at:
            # Infinite trial?
            return self.remaining
        return self.trial_ends_at - utcnow()

    def is_active(self) -> bool:
        """:class:`bool`: Indicates if the subscription is currently active and providing perks."""
        return self.remaining > timedelta()

    def is_trial(self) -> bool:
        """:class:`bool`: Indicates if the subscription is a trial."""
        return self.trial_id is not None

    async def edit(
        self,
        items: List[SubscriptionItem] = MISSING,
        payment_source: Snowflake = MISSING,
        currency: str = MISSING,
        *,
        status: SubscriptionStatus = MISSING,
        payment_source_token: Optional[str] = None,
    ) -> None:
        """|coro|

        Edits the subscription.

        All parameters are optional.

        Parameters
        ----------
        items: List[:class:`SubscriptionItem`]
            The new subscription items to use.
        payment_source: :class:`int`
            The new payment source for payment.
        currency: :class:`str`
            The new currency to use for payment.
        status: :class:`SubscriptionStatus`
            The new status of the subscription.
        payment_source_token: Optional[:class:`str`]
            The token used to authorize with the payment source.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the subscription.
        HTTPException
            Editing the subscription failed.
        """
        payload = {}
        if items is not MISSING:
            payload['items'] = [item.to_dict() for item in items] if items else []
        if payment_source is not MISSING:
            payload['payment_source_id'] = payment_source.id
            payload['payment_source_token'] = payment_source_token
        if currency is not MISSING:
            payload['currency'] = currency
        if status is not MISSING:
            payload['status'] = int(status)

        data = await self._state.http.edit_subscription(self.id, **payload)
        self._update(data)

    async def delete(self) -> None:
        """|coro|

        Deletes the subscription.

        There is an alias of this called :meth:`cancel`.

        Raises
        ------
        HTTPException
            Deleting the subscription failed.
        """
        await self._state.http.delete_subscription(self.id)

    async def cancel(self) -> None:
        """|coro|

        Deletes the subscription.

        Alias of :meth:`delete`.

        Raises
        ------
        HTTPException
            Deleting the subscription failed.
        """
        await self.delete()

    async def preview_invoice(
        self,
        *,
        items: List[SubscriptionItem] = MISSING,
        payment_source: Snowflake = MISSING,
        currency: str = MISSING,
        apply_entitlements: bool = MISSING,
        renewal: bool = MISSING,
    ) -> SubscriptionInvoice:
        """|coro|

        Preview an invoice for the subscription with the given parameters.

        All parameters are optional and default to the current subscription values.

        Parameters
        ----------
        items: List[:class:`SubscriptionItem`]
            The items the previewed invoice should have.
        payment_source: :class:`.PaymentSource`
            The payment source the previewed invoice should be paid with.
        currency: :class:`str`
            The currency the previewed invoice should be paid in.
        apply_entitlements: :class:`bool`
            Whether to apply entitlements (credits) to the previewed invoice.
        renewal: :class:`bool`
            Whether the previewed invoice should be a renewal.

        Raises
        ------
        HTTPException
            Failed to preview the invoice.

        Returns
        -------
        :class:`SubscriptionInvoice`
            The previewed invoice.
        """
        payload: Dict[str, Any] = {}
        if items is not MISSING:
            payload['items'] = [item.to_dict() for item in items] if items else []
        if payment_source:
            payload['payment_source_id'] = payment_source.id
        if currency:
            payload['currency'] = currency
        if apply_entitlements is not MISSING:
            payload['apply_entitlements'] = apply_entitlements
        if renewal is not MISSING:
            payload['renewal'] = renewal

        if payload:
            data = await self._state.http.preview_subscription_update(self.id, **payload)
        else:
            data = await self._state.http.get_subscription_preview(self.id)

        return SubscriptionInvoice(self, data=data, state=self._state)

    async def payment_source(self) -> Optional[PaymentSource]:
        """|coro|

        Retrieves the payment source the subscription is paid with, if applicable.

        Raises
        ------
        NotFound
            The payment source could not be found.
        HTTPException
            Retrieving the payment source failed.

        Returns
        -------
        Optional[:class:`PaymentSource`]
            The payment source the subscription is paid with, if applicable.
        """
        if not self.payment_source_id:
            return

        data = await self._state.http.get_payment_source(self.payment_source_id)
        return PaymentSource(data=data, state=self._state)

    async def invoices(self):
        """|coro|

        Retrieves all invoices for the subscription.

        Raises
        ------
        NotFound
            The payment source or invoices could not be found.
        HTTPException
            Retrieving the invoices failed.

        Returns
        -------
        List[:class:`SubscriptionInvoice`]
            The invoices.
        """
        state = self._state
        data = await state.http.get_subscription_invoices(self.id)
        return [SubscriptionInvoice(self, data=d, state=state) for d in data]


class SubscriptionTrial(Hashable):
    """Represents a subscription trial.

    .. container:: operations

        .. describe:: x == y

            Checks if two trials are equal.

        .. describe:: x != y

            Checks if two trials are not equal.

        .. describe:: hash(x)

            Returns the trial's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the trial.
    interval: :class:`SubscriptionInterval`
        The interval of the trial.
    interval_count: :class:`int`
        How many counts of the interval the trial provides.
    """

    __slots__ = ('id', 'interval', 'interval_count', 'sku_id')

    _INTERVAL_TABLE = {
        SubscriptionInterval.day: 1,
        SubscriptionInterval.month: 30,
        SubscriptionInterval.year: 365,
    }

    def __init__(self, data: SubscriptionTrialPayload):
        self.id: int = int(data['id'])
        self.interval: SubscriptionInterval = try_enum(SubscriptionInterval, data['interval'])
        self.interval_count: int = data['interval_count']
        self.sku_id: int = int(data['sku_id'])

    def __repr__(self) -> str:
        return (
            f'<SubscriptionTrial id={self.id} interval={self.interval} '
            f'interval_count={self.interval_count} sku_id={self.sku_id}>'
        )

    @property
    def duration(self) -> timedelta:
        """:class:`datetime.timedelta`: How long the trial lasts."""
        return timedelta(days=self.interval_count * self._INTERVAL_TABLE[self.interval])
