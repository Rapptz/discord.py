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

from typing import TYPE_CHECKING, Any, List, Optional

from .enums import EntitlementType, GiftStyle, PremiumType, try_enum
from .flags import GiftFlags
from .mixins import Hashable
from .payments import EntitlementPayment
from .promotions import Promotion
from .store import SKU, StoreListing, SubscriptionPlan
from .subscriptions import Subscription, SubscriptionTrial
from .utils import _get_as_snowflake, parse_time, utcnow

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.entitlements import (
        Entitlement as EntitlementPayload,
        Gift as GiftPayload,
        GiftBatch as GiftBatchPayload,
    )
    from .user import User

__all__ = (
    'Entitlement',
    'Gift',
    'GiftBatch',
)


class Entitlement(Hashable):
    """Represents a Discord entitlement.

    .. container:: operations

        .. describe:: x == y

            Checks if two entitlements are equal.

        .. describe:: x != y

            Checks if two entitlements are not equal.

        .. describe:: hash(x)

            Returns the entitlement's hash.

        .. describe:: bool(x)

            Checks if the entitlement is active.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the entitlement.
    type: :class:`EntitlementType`
        The type of entitlement.
    user_id: :class:`int`
        The ID of the user the entitlement is for.
    sku_id: :class:`int`
        The ID of the SKU the entitlement grants.
    application_id: :class:`int`
        The ID of the application that owns the SKU the entitlement grants.
    promotion_id: Optional[:class:`int`]
        The ID of the promotion the entitlement is from.
    parent_id: Optional[:class:`int`]
        The ID of the entitlement's parent.
    guild_id: Optional[:class:`int`]
        The ID of the guild the entitlement is for.
    branches: List[:class:`int`]
        The IDs of the branches the entitlement grants.
    gifter_id: Optional[:class:`int`]
        The ID of the user that gifted the entitlement.
    gift_style: Optional[:class:`GiftStyle`]
        The style of the gift attached to this entitlement.
    gift_batch_id: Optional[:class:`int`]
        The ID of the batch the gift attached to this entitlement is from.
    deleted: :class:`bool`
        Whether the entitlement is deleted.
    consumed: :class:`bool`
        Whether the entitlement is consumed.
    starts_at: Optional[:class:`datetime.datetime`]
        When the entitlement period starts.
    ends_at: Optional[:class:`datetime.datetime`]
        When the entitlement period ends.
    subscription_id: Optional[:class:`int`]
        The ID of the subscription the entitlement is from.
    subscription_plan: Optional[:class:`SubscriptionPlan`]
        The subscription plan the entitlement is for.

        .. note::

            This is a partial object without price information.
    sku: Optional[:class:`SKU`]
        The SKU the entitlement grants.
    payment: Optional[:class:`EntitlementPayment`]
        The payment made for the entitlement.
        Not available in some contexts.
    """

    __slots__ = (
        'id',
        'type',
        'user_id',
        'sku_id',
        'application_id',
        'promotion_id',
        'parent_id',
        'guild_id',
        'branches',
        'gifter_id',
        'gift_style',
        'gift_batch_id',
        '_gift_flags',
        'deleted',
        'consumed',
        'starts_at',
        'ends_at',
        'subscription_id',
        'subscription_plan',
        'sku',
        'payment',
        '_state',
    )

    def __init__(self, *, data: EntitlementPayload, state: ConnectionState):
        self._state = state
        self._update(data)

    def _update(self, data: EntitlementPayload):
        state = self._state

        self.id: int = int(data['id'])
        self.type: EntitlementType = try_enum(EntitlementType, data['type'])
        self.user_id: int = int(data.get('user_id') or state.self_id)  # type: ignore
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self.promotion_id: Optional[int] = _get_as_snowflake(data, 'promotion_id')
        self.parent_id: Optional[int] = _get_as_snowflake(data, 'parent_id')
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.branches: List[int] = [int(branch) for branch in data.get('branches', [])]
        self.gifter_id: Optional[int] = _get_as_snowflake(data, 'gifter_user_id')
        self.gift_style: Optional[GiftStyle] = try_enum(GiftStyle, data.get('gift_style'))
        self.gift_batch_id: Optional[int] = _get_as_snowflake(data, 'gift_code_batch_id')
        self._gift_flags: int = data.get('gift_code_flags', 0)

        self.deleted: bool = data.get('deleted', False)
        self.consumed: bool = data.get('consumed', False)
        self.starts_at: Optional[datetime] = parse_time(data.get('starts_at'))
        self.ends_at: Optional[datetime] = parse_time(data.get('ends_at'))

        self.subscription_id: Optional[int] = _get_as_snowflake(data, 'subscription_id')
        self.subscription_plan: Optional[SubscriptionPlan] = (
            SubscriptionPlan(data=data['subscription_plan'], state=state) if 'subscription_plan' in data else None
        )
        self.sku: Optional[SKU] = SKU(data=data['sku'], state=state) if 'sku' in data else None
        self.payment: Optional[EntitlementPayment] = (
            EntitlementPayment(data=data['payment'], entitlement=self) if 'payment' in data else None
        )

    def __repr__(self) -> str:
        return f'<Entitlement id={self.id} type={self.type!r} sku_id={self.sku_id} application_id={self.application_id}>'

    def __bool__(self) -> bool:
        return self.is_active()

    @property
    def guild(self) -> Optional[Guild]:
        """:class:`Guild`: Returns the guild the entitlement is for, if accessible."""
        return self._state._get_guild(self.guild_id)

    @property
    def premium_type(self) -> Optional[PremiumType]:
        """Optional[:class:`PremiumType`]: The premium type this entitlement grants, if it is for a premium subscription."""
        return PremiumType.from_sku_id(self.sku_id)

    @property
    def gift_flags(self) -> GiftFlags:
        """:class:`GiftFlags`: Returns the flags for the gift this entitlement is attached to."""
        return GiftFlags._from_value(self._gift_flags)

    def is_giftable(self) -> bool:
        """:class:`bool`: Whether the entitlement is giftable."""
        return self.type == EntitlementType.user_gift and not self.gifter_id

    def is_active(self) -> bool:
        """:class:`bool`: Whether the entitlement is active and offering perks."""
        # This is a copy of the logic used in the client

        if self.is_giftable() or self.deleted:
            return False  # Giftable entitlements have not yet been gifted therefore are not active
        if self.starts_at and self.starts_at > utcnow():
            return False  # Entitlement has not started yet
        if self.ends_at and self.ends_at < utcnow():
            return False  # Entitlement has ended

        if self.type == EntitlementType.premium_subscription:
            # Premium subscription entitlements are only active
            # if the SKU is offered for free to premium subscribers
            # and the user is a premium subscriber
            sku = self.sku
            if sku and not sku.premium:
                return False
            if self._state.user and not self._state.user.premium_type == PremiumType.nitro:
                return False

        return True

    async def subscription(self) -> Optional[Subscription]:
        """|coro|

        Retrieves the subscription this entitlement is attached to, if applicable.

        Raises
        ------
        NotFound
            You cannot access this subscription.
        HTTPException
            Fetching the subscription failed.

        Returns
        -------
        Optional[:class:`Subscription`]
            The retrieved subscription, if applicable.
        """
        if not self.subscription_id:
            return

        data = await self._state.http.get_subscription(self.subscription_id)
        return Subscription(data=data, state=self._state)

    async def consume(self) -> None:
        """|coro|

        Consumes the entitlement. This marks a given user entitlement as expended,
        and removes the entitlement from the user's active entitlements.

        This should be called after the user has received the relevant item,
        and only works on entitlements for SKUs of type :attr:`SKUType.consumable`.

        Raises
        ------
        Forbidden
            You do not have permissions to access this application.
        HTTPException
            Consuming the entitlement failed.
        """
        await self._state.http.consume_app_entitlement(self.application_id, self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the entitlement. This removes the entitlement from the user's
        entitlements, and is irreversible.

        This is only useable on entitlements of type :attr:`EntitlementType.test_mode_purchase`.

        Raises
        ------
        Forbidden
            You do not have permissions to access this application.
        HTTPException
            Deleting the entitlement failed.
        """
        await self._state.http.delete_app_entitlement(self.application_id, self.id)


class Gift:
    """Represents a Discord gift.

    .. container:: operations

        .. describe:: x == y

            Checks if two gifts are equal.

        .. describe:: x != y

            Checks if two gifts are not equal.

        .. describe:: hash(x)

            Returns the gift's hash.

    .. versionadded:: 2.0

    Attributes
    ----------
    code: :class:`str`
        The gift's code.
    expires_at: Optional[:class:`datetime.datetime`]
        When the gift expires.
    application_id: Optional[:class:`int`]
        The ID of the application that owns the SKU the gift is for.
        Not available in all contexts.
    batch_id: Optional[:class:`int`]
        The ID of the batch the gift is from.
    sku_id: :class:`int`
        The ID of the SKU the gift is for.
    entitlement_branches: List[:class:`int`]
        A list of entitlements the gift is for.
    gift_style: Optional[:class:`GiftStyle`]
        The style of the gift.
    max_uses: :class:`int`
        The maximum number of times the gift can be used.
    uses: :class:`int`
        The number of times the gift has been used.
    redeemed: :class:`bool`
        Whether the user has redeemed the gift.
    revoked: :class:`bool`
        Whether the gift has been revoked.
    guild_id: Optional[:class:`int`]
        The ID of the guild the gift was redeemed in.
        Not available in all contexts.
    channel_id: Optional[:class:`int`]
        The ID of the channel the gift was redeemed in.
        Not available in all contexts.
    store_listing: Optional[:class:`StoreListing`]
        The store listing for the SKU the gift is for.
        Not available in all contexts.
    promotion: Optional[:class:`Promotion`]
        The promotion the gift is a part of, if any.
    subscription_trial: Optional[:class:`SubscriptionTrial`]
        The subscription trial the gift is a part of, if any.
    subscription_plan_id: Optional[:class:`int`]
        The ID of the subscription plan the gift is for, if any.
    subscription_plan: Optional[:class:`SubscriptionPlan`]
        The subscription plan the gift is for, if any.
    user: Optional[:class:`User`]
        The user who created the gift, if applicable.
    """

    __slots__ = (
        'code',
        'expires_at',
        'application_id',
        'batch_id',
        'sku_id',
        'entitlement_branches',
        'gift_style',
        '_flags',
        'max_uses',
        'uses',
        'redeemed',
        'revoked',
        'guild_id',
        'channel_id',
        'store_listing',
        'promotion',
        'subscription_trial',
        'subscription_plan_id',
        'subscription_plan',
        'user',
        '_state',
    )

    def __init__(self, *, data: GiftPayload, state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def _update(self, data: GiftPayload) -> None:
        state = self._state

        self.code: str = data['code']
        self.expires_at: Optional[datetime] = parse_time(data.get('expires_at'))
        self.application_id: Optional[int] = _get_as_snowflake(data, 'application_id')
        self.batch_id: Optional[int] = _get_as_snowflake(data, 'batch_id')
        self.subscription_plan_id: Optional[int] = _get_as_snowflake(data, 'subscription_plan_id')
        self.sku_id: int = int(data['sku_id'])
        self.entitlement_branches: List[int] = [int(x) for x in data.get('entitlement_branches', [])]
        self.gift_style: Optional[GiftStyle] = try_enum(GiftStyle, data['gift_style']) if data.get('gift_style') else None  # type: ignore
        self._flags: int = data.get('flags', 0)

        self.max_uses: int = data.get('max_uses', 0)
        self.uses: int = data.get('uses', 0)
        self.redeemed: bool = data.get('redeemed', False)
        self.revoked: bool = data.get('revoked', False)

        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.channel_id: Optional[int] = _get_as_snowflake(data, 'channel_id')

        self.store_listing: Optional[StoreListing] = (
            StoreListing(data=data['store_listing'], state=state) if 'store_listing' in data else None
        )
        self.promotion: Optional[Promotion] = Promotion(data=data['promotion'], state=state) if 'promotion' in data else None
        self.subscription_trial: Optional[SubscriptionTrial] = (
            SubscriptionTrial(data['subscription_trial']) if 'subscription_trial' in data else None
        )
        self.subscription_plan: Optional[SubscriptionPlan] = (
            SubscriptionPlan(data=data['subscription_plan'], state=state) if 'subscription_plan' in data else None
        )
        self.user: Optional[User] = self._state.create_user(data['user']) if 'user' in data else None

    def __repr__(self) -> str:
        return f'<Gift code={self.code!r} sku_id={self.sku_id} uses={self.uses} max_uses={self.max_uses} redeemed={self.redeemed}>'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Gift) and other.code == self.code

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, Gift):
            return other.code != self.code
        return True

    def __hash__(self) -> int:
        return hash(self.code)

    @property
    def id(self) -> str:
        """:class:`str`: Returns the code portion of the gift."""
        return self.code

    @property
    def url(self) -> str:
        """:class:`str`: Returns the gift's URL."""
        return f'https://discord.gift/{self.code}'

    @property
    def remaining_uses(self) -> int:
        """:class:`int`: Returns the number of remaining uses for the gift."""
        return self.max_uses - self.uses

    @property
    def flags(self) -> GiftFlags:
        """:class:`GiftFlags`: Returns the gift's flags."""
        return GiftFlags._from_value(self._flags)

    @property
    def premium_type(self) -> Optional[PremiumType]:
        """Optional[:class:`PremiumType`]: The premium type this gift grants, if it is for a premium subscription."""
        return PremiumType.from_sku_id(self.sku_id) if self.is_subscription() else None

    def is_claimed(self) -> bool:
        """:class:`bool`: Checks if the gift has been used up."""
        return self.uses >= self.max_uses if self.max_uses else False

    def is_expired(self) -> bool:
        """:class:`bool`: Checks if the gift has expired."""
        return self.expires_at < utcnow() if self.expires_at else False

    def is_subscription(self) -> bool:
        """:class:`bool`: Checks if the gift is for a subscription."""
        return self.subscription_plan_id is not None

    def is_premium_subscription(self) -> bool:
        """:class:`bool`: Checks if the gift is for a premium subscription."""
        return self.is_subscription() and self.application_id == self._state.premium_subscriptions_application.id

    async def redeem(
        self,
        payment_source: Optional[Snowflake] = None,
        *,
        channel: Optional[Snowflake] = None,
        gateway_checkout_context: Optional[str] = None,
    ) -> Entitlement:
        """|coro|

        Redeems the gift.

        Parameters
        ----------
        payment_source: Optional[:class:`PaymentSource`]
            The payment source to use for the redemption.
            Only required if the gift's :attr:`flags` have :attr:`GiftFlags.payment_source_required` set to ``True``.
        channel: Optional[Union[:class:`TextChannel`, :class:`VoiceChannel`, :class:`StageChannel`, :class:`Thread`, :class:`DMChannel`, :class:`GroupChannel`]]
            The channel to redeem the gift in. This is usually the channel the gift was sent in.
            While this is optional, it is recommended to pass this in.
        gateway_checkout_context: Optional[:class:`str`]
            The current checkout context.

        Raises
        ------
        HTTPException
            The gift failed to redeem.

        Returns
        -------
        :class:`Entitlement`
            The entitlement that was created from redeeming the gift.
        """
        data = await self._state.http.redeem_gift(
            self.code,
            payment_source.id if payment_source else None,
            channel.id if channel else None,
            gateway_checkout_context,
        )
        return Entitlement(data=data, state=self._state)

    async def delete(self) -> None:
        """|coro|

        Revokes the gift.

        This is only possible for gifts the current account has created.

        Raises
        ------
        NotFound
            The owned gift was not found.
        HTTPException
            The gift failed to delete.
        """
        await self._state.http.delete_gift(self.code)


class GiftBatch(Hashable):
    """Represents a batch of gifts for an SKU.

    .. container:: operations

        .. describe:: x == y

            Checks if two gift batches are equal.

        .. describe:: x != y

            Checks if two gift batches are not equal.

        .. describe:: hash(x)

            Returns the gift batch's hash.

        .. describe:: str(x)

            Returns the gift batch's description.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The ID of the gift batch.
    application_id: :class:`int`
        The ID of the application the gift batch is for.
    sku_id: :class:`int`
        The ID of the SKU the gift batch is for.
    amount: :class:`int`
        The amount of gifts in the batch.
    description: :class:`str`
        The description of the gift batch.
    entitlement_branches: List[:class:`int`]
        The entitlement branches the gift batch is for.
    entitlement_starts_at: Optional[:class:`datetime.datetime`]
        When the entitlement is valid from.
    entitlement_ends_at: Optional[:class:`datetime.datetime`]
        When the entitlement is valid until.
    """

    __slots__ = (
        'id',
        'application_id',
        'sku_id',
        'amount',
        'description',
        'entitlement_branches',
        'entitlement_starts_at',
        'entitlement_ends_at',
        '_state',
    )

    def __init__(self, *, data: GiftBatchPayload, state: ConnectionState, application_id: int) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.application_id = application_id
        self.sku_id: int = int(data['sku_id'])
        self.amount: int = data['amount']
        self.description: str = data.get('description', '')
        self.entitlement_branches: List[int] = [int(branch) for branch in data.get('entitlement_branches', [])]
        self.entitlement_starts_at: Optional[datetime] = parse_time(data.get('entitlement_starts_at'))
        self.entitlement_ends_at: Optional[datetime] = parse_time(data.get('entitlement_ends_at'))

    def __repr__(self) -> str:
        return f'<GiftBatch id={self.id} sku_id={self.sku_id} amount={self.amount} description={self.description!r}>'

    def __str__(self) -> str:
        return self.description

    def is_valid(self) -> bool:
        """:class:`bool`: Checks if the gift batch is valid."""
        if self.entitlement_starts_at and self.entitlement_starts_at > utcnow():
            return False
        if self.entitlement_ends_at and self.entitlement_ends_at < utcnow():
            return False
        return True

    async def download(self) -> bytes:
        """|coro|

        Returns the gifts in the gift batch in CSV format.

        Raises
        -------
        Forbidden
            You do not have permissions to download the batch.
        HTTPException
            Downloading the batch failed.

        Returns
        -------
        :class:`bytes`
            The report content.
        """
        return await self._state.http.get_gift_batch_csv(self.application_id, self.id)
