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

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Union

from .enums import PaymentSourceType, try_enum
from .flags import PromotionFlags
from .mixins import Hashable
from .subscriptions import SubscriptionTrial
from .utils import _get_as_snowflake, parse_time, utcnow

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.promotions import (
        ClaimedPromotion as ClaimedPromotionPayload,
        Promotion as PromotionPayload,
        TrialOffer as TrialOfferPayload,
        PricingPromotion as PricingPromotionPayload,
    )

__all__ = (
    'Promotion',
    'TrialOffer',
    'PricingPromotion',
)


class Promotion(Hashable):
    """Represents a Discord promotion.

    .. container:: operations

        .. describe:: x == y

            Checks if two promotions are equal.

        .. describe:: x != y

            Checks if two promotions are not equal.

        .. describe:: hash(x)

            Returns the promotion's hash.

        .. describe:: str(x)

            Returns the outbound promotion's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The promotion ID.
    trial_id: Optional[:class:`int`]
        The trial ID of the inbound promotion, if applicable.
    starts_at: :class:`datetime.datetime`
        When the promotion starts.
    ends_at: :class:`datetime.datetime`
        When the promotion ends.
    claimed_at: Optional[:class:`datetime.datetime`]
        When the promotion was claimed.
        Only available for claimed promotions.
    code: Optional[:class:`str`]
        The promotion's claim code. Only available for claimed promotions.
    outbound_title: :class:`str`
        The title of the outbound promotion.
    outbound_description: :class:`str`
        The description of the outbound promotion.
    outbound_link: :class:`str`
        The redemption page of the outbound promotion, used to claim it.
    outbound_restricted_countries: List[:class:`str`]
        The countries that the outbound promotion is not available in.
    inbound_title: Optional[:class:`str`]
        The title of the inbound promotion. This is usually Discord Nitro.
    inbound_description: Optional[:class:`str`]
        The description of the inbound promotion.
    inbound_link: Optional[:class:`str`]
        The Discord help center link of the inbound promotion.
    inbound_restricted_countries: List[:class:`str`]
        The countries that the inbound promotion is not available in.
    terms_and_conditions: :class:`str`
        The terms and conditions of the promotion.
    """

    __slots__ = (
        'id',
        'trial_id',
        'starts_at',
        'ends_at',
        'claimed_at',
        'code',
        'outbound_title',
        'outbound_description',
        'outbound_link',
        'outbound_restricted_countries',
        'inbound_title',
        'inbound_description',
        'inbound_link',
        'inbound_restricted_countries',
        'terms_and_conditions',
        '_flags',
        '_state',
    )

    def __init__(self, *, data: Union[PromotionPayload, ClaimedPromotionPayload], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __str__(self) -> str:
        return self.outbound_title

    def __repr__(self) -> str:
        return f'<Promotion id={self.id} title={self.outbound_title!r}>'

    def _update(self, data: Union[PromotionPayload, ClaimedPromotionPayload]) -> None:
        promotion: PromotionPayload = data.get('promotion', data)  # type: ignore

        self.id: int = int(promotion['id'])
        self.trial_id: Optional[int] = _get_as_snowflake(promotion, 'trial_id')
        self.starts_at: datetime = parse_time(promotion['start_date'])
        self.ends_at: datetime = parse_time(promotion['end_date'])
        self.claimed_at: Optional[datetime] = parse_time(data.get('claimed_at'))
        self.code: Optional[str] = data.get('code')
        self._flags: int = promotion.get('flags', 0)

        self.outbound_title: str = promotion['outbound_title']
        self.outbound_description: str = promotion['outbound_redemption_modal_body']
        self.outbound_link: str = promotion.get(
            'outbound_redemption_page_link',
            promotion.get('outbound_redemption_url_format', '').replace('{code}', self.code or '{code}'),
        )
        self.outbound_restricted_countries: List[str] = promotion.get('outbound_restricted_countries', [])
        self.inbound_title: Optional[str] = promotion.get('inbound_header_text')
        self.inbound_description: Optional[str] = promotion.get('inbound_body_text')
        self.inbound_link: Optional[str] = promotion.get('inbound_help_center_link')
        self.inbound_restricted_countries: List[str] = promotion.get('inbound_restricted_countries', [])
        self.terms_and_conditions: str = promotion['outbound_terms_and_conditions']

    @property
    def flags(self) -> PromotionFlags:
        """:class:`PromotionFlags`: Returns the promotion's flags."""
        return PromotionFlags._from_value(self._flags)

    def is_claimed(self) -> bool:
        """:class:`bool`: Checks if the promotion has been claimed.

        Only accurate if the promotion was fetched from :meth:`Client.promotions` with ``claimed`` set to ``True`` or :meth:`claim` was just called.
        """
        return self.claimed_at is not None

    def is_active(self) -> bool:
        """:class:`bool`: Checks if the promotion is active."""
        return self.starts_at <= utcnow() <= self.ends_at

    async def claim(self) -> str:
        """|coro|

        Claims the promotion.

        Sets :attr:`claimed_at` and :attr:`code`.

        Raises
        ------
        Forbidden
            You are not allowed to claim the promotion.
        HTTPException
            Claiming the promotion failed.

        Returns
        -------
        :class:`str`
            The claim code for the outbound promotion.
        """
        data = await self._state.http.claim_promotion(self.id)
        self._update(data)
        return data['code']


class TrialOffer(Hashable):
    """Represents a Discord user trial offer.

    .. container:: operations

        .. describe:: x == y

            Checks if two trial offers are equal.

        .. describe:: x != y

            Checks if two trial offers are not equal.

        .. describe:: hash(x)

            Returns the trial offer's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the trial offer.
    expires_at: :class:`datetime.datetime`
        When the trial offer expires.
    trial_id: :class:`int`
        The ID of the trial.
    trial: :class:`SubscriptionTrial`
        The trial offered.
    """

    __slots__ = (
        'id',
        'expires_at',
        'trial_id',
        'trial',
        '_state',
    )

    def __init__(self, *, data: TrialOfferPayload, state: ConnectionState) -> None:
        self._state = state

        self.id: int = int(data['id'])
        self.expires_at: datetime = parse_time(data['expires_at'])
        self.trial_id: int = int(data['trial_id'])
        self.trial: SubscriptionTrial = SubscriptionTrial(data['subscription_trial'])

    def __repr__(self) -> str:
        return f'<TrialOffer id={self.id} trial={self.trial!r}>'

    async def ack(self) -> None:
        """|coro|

        Acknowledges the trial offer.

        Raises
        ------
        HTTPException
            Acknowledging the trial offer failed.
        """
        await self._state.http.ack_trial_offer(self.id)


class PricingPromotion:
    """Represents a Discord localized pricing promotion.

    .. versionadded:: 2.0

    Attributes
    ----------
    subscription_plan_id: :class:`int`
        The ID of the subscription plan the promotion is for.
    country_code: :class:`str`
        The country code the promotion applies to.
    payment_source_types: List[:class:`PaymentSourceType`]
        The payment source types the promotion is restricted to.
    amount: :class:`int`
        The discounted price of the subscription plan.
    currency: :class:`str`
        The currency of the discounted price.
    """

    __slots__ = (
        'subscription_plan_id',
        'country_code',
        'payment_source_types',
        'amount',
        'currency',
    )

    def __init__(self, *, data: PricingPromotionPayload) -> None:
        self.subscription_plan_id: int = int(data['plan_id'])
        self.country_code: str = data['country_code']
        self.payment_source_types: List[PaymentSourceType] = [
            try_enum(PaymentSourceType, t) for t in data['payment_source_types']
        ]

        price = data['price']
        self.amount: int = price['amount']
        self.currency: str = price['currency']

    def __repr__(self) -> str:
        return f'<PricingPromotion plan_id={self.subscription_plan_id} country_code={self.country_code!r} amount={self.amount} currency={self.currency!r}>'
