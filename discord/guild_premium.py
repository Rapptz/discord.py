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
from typing import TYPE_CHECKING, Optional

from .mixins import Hashable
from .subscriptions import Subscription
from .utils import parse_time, utcnow

if TYPE_CHECKING:
    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.subscriptions import (
        PremiumGuildSubscription as PremiumGuildSubscriptionPayload,
        PremiumGuildSubscriptionSlot as PremiumGuildSubscriptionSlotPayload,
        PremiumGuildSubscriptionCooldown as PremiumGuildSubscriptionCooldownPayload,
    )

__all__ = (
    'PremiumGuildSubscription',
    'PremiumGuildSubscriptionSlot',
    'PremiumGuildSubscriptionCooldown',
)


class PremiumGuildSubscription(Hashable):
    """Represents a premium guild subscription (boost).

    .. container:: operations

        .. describe:: x == y

            Checks if two premium guild subscriptions are equal.

        .. describe:: x != y

            Checks if two premium guild subscriptions are not equal.

        .. describe:: hash(x)

            Returns the premium guild subscription's hash.

    .. versionadded:: 2.0

    Attributes
    ------------
    id: :class:`int`
        The ID of the guild premium subscription.
    guild_id: :class:`int`
        The ID of the guild this guild premium subscription belongs to.
    user_id: :class:`int`
        The ID of the user this guild premium subscription belongs to.
    user: :class:`User`
        The user this guild premium subscription belongs to.
    ended: :class:`bool`
        Whether the guild premium subscription has ended.
    ends_at: Optional[:class:`datetime.datetime`]
        When the guild premium subscription ends.
    """

    def __init__(self, *, state: ConnectionState, data: PremiumGuildSubscriptionPayload):
        self._state = state
        self._update(data)

    def _update(self, data: PremiumGuildSubscriptionPayload):
        state = self._state

        self.id = int(data['id'])
        self.guild_id = int(data['guild_id'])
        self.user_id = int(data['user_id'])
        self.user = state.store_user(data['user']) if 'user' in data else state.user
        self.ended = data.get('ended', False)
        self.ends_at: Optional[datetime] = parse_time(data.get('ends_at'))

    def __repr__(self) -> str:
        return f'<PremiumGuildSubscription id={self.id} guild_id={self.guild_id} user_id={self.user_id} ended={self.ended}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this guild premium subscription belongs to, if available."""
        return self._state._get_guild(self.guild_id)

    @property
    def remaining(self) -> Optional[timedelta]:
        """Optional[:class:`datetime.timedelta`]: The remaining time for this guild premium subscription.

        This is ``None`` if the subscription is not ending.
        """
        if self.ends_at is None or self.ends_at <= utcnow():
            return None

        return self.ends_at - utcnow()

    async def delete(self) -> None:
        """|coro|

        Deletes this guild premium subscription.

        Raises
        -------
        Forbidden
            You do not have permissions to delete this guild premium subscription.
        HTTPException
            Deleting the guild premium subscription failed.
        """
        await self._state.http.delete_guild_subscription(self.guild_id, self.id)


class PremiumGuildSubscriptionSlot(Hashable):
    """Represents a premium guild subscription (boost) slot.

    This is a slot that can be used on a guild (to boost it).

    .. container:: operations

        .. describe:: x == y

            Checks if two subscription slots are equal.

        .. describe:: x != y

            Checks if two subscription slots are not equal.

        .. describe:: hash(x)

            Returns the subscription slot's hash.

    .. versionadded:: 2.0

    Attributes
    ------------
    id: :class:`int`
        The ID of the guild subscription slot.
    subscription_id: :class:`int`
        The ID of the guild subscription this slot belongs to.
    canceled: :class:`bool`
        Whether the slot is canceled.
    cooldown_ends_at: Optional[:class:`datetime.datetime`]
        When the cooldown for this guild subscription slot ends.
    premium_guild_subscription: Optional[:class:`PremiumGuildSubscription`]
        The subscription this slot belongs to.
    """

    __slots__ = (
        'id',
        'subscription_id',
        'canceled',
        'cooldown_ends_at',
        'premium_guild_subscription',
        '_state',
    )

    def __init__(self, *, state: ConnectionState, data: PremiumGuildSubscriptionSlotPayload):
        self._state = state
        self._update(data)

    def _update(self, data: PremiumGuildSubscriptionSlotPayload):
        self.id = int(data['id'])
        self.subscription_id = int(data['subscription_id'])
        self.canceled = data.get('canceled', False)
        self.cooldown_ends_at: Optional[datetime] = parse_time(data.get('cooldown_ends_at'))

        premium_guild_subscription = data.get('premium_guild_subscription')
        self.premium_guild_subscription: Optional[PremiumGuildSubscription] = (
            PremiumGuildSubscription(state=self._state, data=premium_guild_subscription)
            if premium_guild_subscription is not None
            else None
        )

    def __repr__(self) -> str:
        return f'<PremiumGuildSubscriptionSlot id={self.id} subscription_id={self.subscription_id} canceled={self.canceled}>'

    def is_available(self) -> bool:
        """:class:`bool`: Indicates if the slot is available for use."""
        return not self.premium_guild_subscription and not self.is_on_cooldown()

    def is_on_cooldown(self) -> bool:
        """:class:`bool`: Indicates if the slot is on cooldown."""
        return self.cooldown_ends_at is not None and self.cooldown_ends_at > utcnow()

    @property
    def cancelled(self) -> bool:
        """:class:`bool`: Whether the slot is cancelled.

        This is an alias of :attr:`canceled`.
        """
        return self.canceled

    @property
    def cooldown_remaining(self) -> Optional[timedelta]:
        """Optional[:class:`datetime.timedelta`]: The cooldown remaining for this boost slot.

        This is ``None`` if the cooldown has ended.
        """
        if self.cooldown_ends_at is None or self.cooldown_ends_at <= utcnow():
            return None

        return self.cooldown_ends_at - utcnow()

    async def subscription(self) -> Subscription:
        """|coro|

        Retrieves the subscription this guild subscription slot is attached to.

        Raises
        ------
        NotFound
            You cannot access this subscription.
        HTTPException
            Fetching the subscription failed.

        Returns
        -------
        :class:`Subscription`
            The retrieved subscription, if applicable.
        """
        data = await self._state.http.get_subscription(self.subscription_id)
        return Subscription(data=data, state=self._state)

    async def apply(self, guild: Snowflake) -> PremiumGuildSubscription:
        """|coro|

        Applies the premium guild subscription slot to a guild.

        Parameters
        -----------
        guild: :class:`Guild`
            The guild to apply the slot to.

        Raises
        -------
        HTTPException
            Applying the slot failed.

        Returns
        --------
        :class:`PremiumGuildSubscription`
            The premium guild subscription that was created.
        """
        state = self._state
        data = await state.http.apply_guild_subscription_slots(guild.id, (self.id,))
        return PremiumGuildSubscription(state=state, data=data[0])

    async def cancel(self) -> None:
        """|coro|

        Cancels the guild subscription slot.

        Raises
        -------
        HTTPException
            Cancelling the slot failed.
        """
        data = await self._state.http.cancel_guild_subscription_slot(self.id)
        self._update(data)

    async def uncancel(self) -> None:
        """|coro|

        Uncancels the guild subscription slot.

        Raises
        -------
        HTTPException
            Uncancelling the slot failed.
        """
        data = await self._state.http.uncancel_guild_subscription_slot(self.id)
        self._update(data)


class PremiumGuildSubscriptionCooldown:
    """Represents a premium guild subscription cooldown.

    This is a cooldown that is applied to your guild subscription slot changes (boosting and unboosting).

    .. versionadded:: 2.0

    Attributes
    ------------
    ends_at: :class:`datetime.datetime`
        When the cooldown resets.
    limit: :class:`int`
        The maximum number of changes that can be made before the cooldown is applied.
    remaining: :class:`int`
        The number of changes remaining before the cooldown is applied.
    """

    def __init__(self, *, state: ConnectionState, data: PremiumGuildSubscriptionCooldownPayload):
        self._state = state
        self._update(data)

    def _update(self, data: PremiumGuildSubscriptionCooldownPayload):
        self.ends_at: datetime = parse_time(data['ends_at'])
        self.limit = data['limit']
        self.remaining = data.get('remaining', 0)
