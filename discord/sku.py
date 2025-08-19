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

from typing import AsyncIterator, Optional, TYPE_CHECKING

from datetime import datetime

from . import utils
from .enums import try_enum, SKUType, EntitlementType
from .flags import SKUFlags
from .object import Object
from .subscription import Subscription

if TYPE_CHECKING:
    from .abc import SnowflakeTime, Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.sku import (
        SKU as SKUPayload,
        Entitlement as EntitlementPayload,
    )
    from .user import User

__all__ = (
    'SKU',
    'Entitlement',
)


class SKU:
    """Represents a premium offering as a stock-keeping unit (SKU).

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The SKU's ID.
    type: :class:`SKUType`
        The type of the SKU.
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
        'type',
        'application_id',
        'name',
        'slug',
        '_flags',
    )

    def __init__(self, *, state: ConnectionState, data: SKUPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.type: SKUType = try_enum(SKUType, data['type'])
        self.application_id: int = int(data['application_id'])
        self.name: str = data['name']
        self.slug: str = data['slug']
        self._flags: int = data['flags']

    def __repr__(self) -> str:
        return f'<SKU id={self.id} name={self.name!r} slug={self.slug!r}>'

    @property
    def flags(self) -> SKUFlags:
        """:class:`SKUFlags`: Returns the flags of the SKU."""
        return SKUFlags._from_value(self._flags)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the sku's creation time in UTC."""
        return utils.snowflake_time(self.id)

    async def fetch_subscription(self, subscription_id: int, /) -> Subscription:
        """|coro|

        Retrieves a :class:`.Subscription` with the specified ID.

        .. versionadded:: 2.5

        Parameters
        -----------
        subscription_id: :class:`int`
            The subscription's ID to fetch from.

        Raises
        -------
        NotFound
            An subscription with this ID does not exist.
        HTTPException
            Fetching the subscription failed.

        Returns
        --------
        :class:`.Subscription`
            The subscription you requested.
        """
        data = await self._state.http.get_sku_subscription(self.id, subscription_id)
        return Subscription(data=data, state=self._state)

    async def subscriptions(
        self,
        *,
        limit: Optional[int] = 50,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        user: Snowflake,
    ) -> AsyncIterator[Subscription]:
        """Retrieves an :term:`asynchronous iterator` of the :class:`.Subscription` that SKU has.

        .. versionadded:: 2.5

        Examples
        ---------

        Usage ::

            async for subscription in sku.subscriptions(limit=100, user=user):
                print(subscription.user_id, subscription.current_period_end)

        Flattening into a list ::

            subscriptions = [subscription async for subscription in sku.subscriptions(limit=100, user=user)]
            # subscriptions is now a list of Subscription...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of subscriptions to retrieve. If ``None``, it retrieves every subscription for this SKU.
            Note, however, that this would make it a slow operation. Defaults to ``100``.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve subscriptions before this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve subscriptions after this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        user: :class:`~discord.abc.Snowflake`
            The user to filter by.

        Raises
        -------
        HTTPException
            Fetching the subscriptions failed.
        TypeError
            Both ``after`` and ``before`` were provided, as Discord does not
            support this type of pagination.

        Yields
        --------
        :class:`.Subscription`
            The subscription with the SKU.
        """

        if before is not None and after is not None:
            raise TypeError('subscriptions pagination does not support both before and after')

        # This endpoint paginates in ascending order.
        endpoint = self._state.http.list_sku_subscriptions

        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await endpoint(self.id, before=before_id, limit=retrieve, user_id=user.id)

            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[0]['id']))

            return data, before, limit

        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await endpoint(
                self.id,
                after=after_id,
                limit=retrieve,
                user_id=user.id,
            )

            if data:
                if limit is not None:
                    limit -= len(data)

                after = Object(id=int(data[-1]['id']))

            return data, after, limit

        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))

        if before:
            strategy, state = _before_strategy, before
        else:
            strategy, state = _after_strategy, after

        while True:
            retrieve = 100 if limit is None else min(limit, 100)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            # Terminate loop on next iteration; there's no data left after this
            if len(data) < 100:
                limit = 0

            for e in data:
                yield Subscription(data=e, state=self._state)


class Entitlement:
    """Represents an entitlement from user or guild which has been granted access to a premium offering.

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The entitlement's ID.
    sku_id: :class:`int`
        The ID of the SKU that the entitlement belongs to.
    application_id: :class:`int`
        The ID of the application that the entitlement belongs to.
    user_id: Optional[:class:`int`]
        The ID of the user that is granted access to the entitlement.
    type: :class:`EntitlementType`
        The type of the entitlement.
    deleted: :class:`bool`
        Whether the entitlement has been deleted.
    starts_at: Optional[:class:`datetime.datetime`]
        A UTC start date which the entitlement is valid. Not present when using test entitlements.
    ends_at: Optional[:class:`datetime.datetime`]
        A UTC date which entitlement is no longer valid. Not present when using test entitlements.
    guild_id: Optional[:class:`int`]
        The ID of the guild that is granted access to the entitlement
    consumed: :class:`bool`
        For consumable items, whether the entitlement has been consumed.
    """

    __slots__ = (
        '_state',
        'id',
        'sku_id',
        'application_id',
        'user_id',
        'type',
        'deleted',
        'starts_at',
        'ends_at',
        'guild_id',
        'consumed',
    )

    def __init__(self, state: ConnectionState, data: EntitlementPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self.user_id: Optional[int] = utils._get_as_snowflake(data, 'user_id')
        self.type: EntitlementType = try_enum(EntitlementType, data['type'])
        self.deleted: bool = data['deleted']
        self.starts_at: Optional[datetime] = utils.parse_time(data.get('starts_at', None))
        self.ends_at: Optional[datetime] = utils.parse_time(data.get('ends_at', None))
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.consumed: bool = data.get('consumed', False)

    def __repr__(self) -> str:
        return f'<Entitlement id={self.id} type={self.type!r} user_id={self.user_id}>'

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`User`]: The user that is granted access to the entitlement."""
        if self.user_id is None:
            return None
        return self._state.get_user(self.user_id)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild that is granted access to the entitlement."""
        return self._state._get_guild(self.guild_id)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the entitlement's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def is_expired(self) -> bool:
        """:class:`bool`: Returns ``True`` if the entitlement is expired. Will be always False for test entitlements."""
        if self.ends_at is None:
            return False
        return utils.utcnow() >= self.ends_at

    async def consume(self) -> None:
        """|coro|

        Marks a one-time purchase entitlement as consumed.

        Raises
        -------
        NotFound
            The entitlement could not be found.
        HTTPException
            Consuming the entitlement failed.
        """

        await self._state.http.consume_entitlement(self.application_id, self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the entitlement.

        Raises
        -------
        NotFound
            The entitlement could not be found.
        HTTPException
            Deleting the entitlement failed.
        """

        await self._state.http.delete_entitlement(self.application_id, self.id)
