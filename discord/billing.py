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
from typing import TYPE_CHECKING, Optional, Union

from .enums import (
    PaymentGateway,
    PaymentSourceType,
    try_enum,
)
from .flags import PaymentSourceFlags
from .mixins import Hashable
from .utils import MISSING

if TYPE_CHECKING:
    from datetime import date
    from typing_extensions import Self

    from .state import ConnectionState
    from .types.billing import (
        BillingAddress as BillingAddressPayload,
        PartialPaymentSource as PartialPaymentSourcePayload,
        PaymentSource as PaymentSourcePayload,
        PremiumUsage as PremiumUsagePayload,
    )

__all__ = (
    'BillingAddress',
    'PaymentSource',
    'PremiumUsage',
)


class BillingAddress:
    """Represents a billing address.

    .. container:: operations

        .. describe:: x == y

            Checks if two billing addresses are equal.

        .. describe:: x != y

            Checks if two billing addresses are not equal.

        .. describe:: hash(x)

            Returns the address' hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    name: :class:`str`
        The payment source's name.
    address: :class:`str`
        The location's address.
    postal_code: Optional[:class:`str`]
        The location's postal code.
    city: :class:`str`
        The location's city.
    state: Optional[:class:`str`]
        The location's state or province.
    country: :class:`str`
        The location's country.
    email: Optional[:class:`str`]
        The email address associated with the payment source, if any.
    """

    __slots__ = ('_state', 'name', 'address', 'postal_code', 'city', 'state', 'country', 'email')

    def __init__(
        self,
        *,
        name: str,
        address: str,
        city: str,
        country: str,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        email: Optional[str] = None,
        _state: Optional[ConnectionState] = None,
    ) -> None:
        self._state = _state

        self.name = name
        self.address = address
        self.postal_code = postal_code
        self.city = city
        self.state = state
        self.country = country
        self.email = email

    def __repr__(self) -> str:
        return f'<BillingAddress name={self.name!r} address={self.address!r} city={self.city!r} country={self.country!r}>'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BillingAddress) and self.to_dict() == other.to_dict()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, BillingAddress):
            return True
        return self.to_dict() != other.to_dict()

    def __hash__(self) -> int:
        return hash(self.to_dict())

    @classmethod
    def from_dict(cls, data: BillingAddressPayload, state: ConnectionState) -> Self:
        address = '\n'.join(filter(None, (data['line_1'], data.get('line_2'))))
        return cls(
            _state=state,
            name=data['name'],
            address=address,
            postal_code=data.get('postal_code'),
            city=data['city'],
            state=data.get('state'),
            country=data['country'],
            email=data.get('email'),
        )

    def to_dict(self) -> dict:
        line1, _, line2 = self.address.partition('\n')
        data = {
            'name': self.name,
            'line_1': line1,
            'line_2': line2 or '',
            'city': self.city,
            'country': self.country,
        }
        if self.postal_code:
            data['postal_code'] = self.postal_code
        if self.state:
            data['state'] = self.state
        if self.email:
            data['email'] = self.email
        return data

    async def validate(self) -> str:
        """|coro|

        Validates the billing address.

        Raises
        ------
        TypeError
            The billing address does not have state attached.
        HTTPException
            The billing address is invalid.

        Returns
        -------
        :class:`str`
            The billing address token.
        """
        if self._state is None:
            raise TypeError('BillingAddress does not have state available')

        data = await self._state.http.validate_billing_address(self.to_dict())
        return data['token']


class PaymentSource(Hashable):
    """Represents a payment source.

    .. container:: operations

        .. describe:: x == y

            Checks if two payment sources are equal.

        .. describe:: x != y

            Checks if two payment sources are not equal.

        .. describe:: hash(x)

            Returns the source's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the payment source.
    brand: Optional[:class:`str`]
        The brand of the payment source. This is only available for cards.
    country: Optional[:class:`str`]
        The country of the payment source. Not available in all contexts.
    partial_card_number: Optional[:class:`str`]
        The last four digits of the payment source. This is only available for cards.
    billing_address: Optional[:class:`BillingAddress`]
        The billing address of the payment source. Not available in all contexts.
    type: :class:`PaymentSourceType`
        The type of the payment source.
    payment_gateway: :class:`PaymentGateway`
        The payment gateway of the payment source.
    default: :class:`bool`
        Whether the payment source is the default payment source.
    invalid: :class:`bool`
        Whether the payment source is invalid.
    expires_at: Optional[:class:`datetime.date`]
        When the payment source expires. This is only available for cards.
    email: Optional[:class:`str`]
        The email address associated with the payment source, if any.
        This is only available for PayPal.
    bank: Optional[:class:`str`]
        The bank associated with the payment source, if any.
        This is only available for certain payment sources.
    username: Optional[:class:`str`]
        The username associated with the payment source, if any.
        This is only available for Venmo.
    """

    __slots__ = (
        '_state',
        'id',
        'brand',
        'country',
        'partial_card_number',
        'billing_address',
        'type',
        'payment_gateway',
        'default',
        'invalid',
        'expires_at',
        'email',
        'bank',
        'username',
        '_flags',
    )

    def __init__(self, *, data: Union[PaymentSourcePayload, PartialPaymentSourcePayload], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<PaymentSource id={self.id} type={self.type!r} country={self.country!r}>'

    def _update(self, data: Union[PaymentSourcePayload, PartialPaymentSourcePayload]) -> None:
        self.id: int = int(data['id'])
        self.brand: Optional[str] = data.get('brand')
        self.country: Optional[str] = data.get('country')
        self.partial_card_number: Optional[str] = data.get('last_4')
        self.billing_address: Optional[BillingAddress] = (
            BillingAddress.from_dict(data['billing_address'], state=self._state) if 'billing_address' in data else None  # type: ignore # ???
        )

        self.type: PaymentSourceType = try_enum(PaymentSourceType, data['type'])
        self.payment_gateway: PaymentGateway = try_enum(PaymentGateway, data['payment_gateway'])
        self.default: bool = data.get('default', False)
        self.invalid: bool = data['invalid']
        self._flags: int = data.get('flags', 0)

        month = data.get('expires_month')
        year = data.get('expires_year')
        self.expires_at: Optional[date] = datetime(year=year, month=month or 1, day=1).date() if year else None

        self.email: Optional[str] = data.get('email')
        self.bank: Optional[str] = data.get('bank')
        self.username: Optional[str] = data.get('username')

        if not self.country and self.billing_address:
            self.country = self.billing_address.country

        if not self.email and self.billing_address:
            self.email = self.billing_address.email

    @property
    def flags(self) -> PaymentSourceFlags:
        """:class:`PaymentSourceFlags`: Returns the payment source's flags."""
        return PaymentSourceFlags._from_value(self._flags)

    async def edit(
        self, *, billing_address: BillingAddress = MISSING, default: bool = MISSING, expires_at: date = MISSING
    ) -> None:
        """|coro|

        Edits the payment source.

        Parameters
        ----------
        billing_address: :class:`BillingAddress`
            The billing address of the payment source.
        default: :class:`bool`
            Whether the payment source is the default payment source.
        expires_at: :class:`datetime.date`
            When the payment source expires. This is only applicable to cards.

        Raises
        ------
        HTTPException
            Editing the payment source failed.
        """
        payload = {}
        if billing_address is not MISSING:
            payload['billing_address'] = billing_address.to_dict()
        if default is not MISSING:
            payload['default'] = default
        if expires_at is not MISSING:
            payload['expires_month'] = expires_at.month
            payload['expires_year'] = expires_at.year

        data = await self._state.http.edit_payment_source(self.id, payload)
        self._update(data)

    async def delete(self) -> None:
        """|coro|

        Deletes the payment source.

        Raises
        ------
        HTTPException
            Deleting the payment source failed.
        """
        await self._state.http.delete_payment_source(self.id)


class PremiumUsage:
    """Represents the usage of a user's premium perks.

    .. versionadded:: 2.0

    Attributes
    ----------
    sticker_sends: :class:`int`
        The number of premium sticker sends.
    animated_emojis: :class:`int`
        The number of animated emojis used.
    global_emojis: :class:`int`
        The number of global emojis used.
    large_uploads: :class:`int`
        The number of large uploads made.
    hd_streams: :class:`int`
        The number of HD streams.
    hd_hours_streamed: :class:`int`
        The number of hours streamed in HD.
    """

    __slots__ = (
        'sticker_sends',
        'animated_emojis',
        'global_emojis',
        'large_uploads',
        'hd_streams',
        'hd_hours_streamed',
    )

    def __init__(self, *, data: PremiumUsagePayload) -> None:
        self.sticker_sends: int = data['nitro_sticker_sends']['value']
        self.animated_emojis: int = data['total_animated_emojis']['value']
        self.global_emojis: int = data['total_global_emojis']['value']
        self.large_uploads: int = data['total_large_uploads']['value']
        self.hd_streams: int = data['total_hd_streams']['value']
        self.hd_hours_streamed: int = data['hd_hours_streamed']['value']
