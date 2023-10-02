from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from . import utils
from .app_commands import MissingApplicationID
from .enums import try_enum, SKUType, EntitlementType
from .flags import SKUFlags

if TYPE_CHECKING:
    from datetime import datetime

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
        """Returns the flags of the SKU."""
        return SKUFlags._from_value(self._flags)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the sku's creation time in UTC."""
        return utils.snowflake_time(self.id)


class Entitlement:
    """Represents an entitlement from user or guild which has been granted access to a premium offering.

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The entitlement's ID.
    sku_id: :class:`int`
        The ID of the SKU that the entitlement belongs to.
    user_id: Optional[:class:`int`]
        The ID of the user that is granted access to the entitlement.
    guild_id: Optional[:class:`int`]
        The ID of the guild that is granted access to the entitlement
    application_id: :class:`int`
        The ID of the application that the entitlement belongs to.
    type: :class:`EntitlementType`
        The type of the entitlement.
    consumed: :class:`bool`
        Whether the entitlement has been consumed. Not applicable to app subscriptions so will typically be ``False``.
    starts_at: Optional[:class:`datetime.datetime`]
        A UTC start date which the entitlement is valid. Not present when using test entitlements.
    ends_at: Optional[:class:`datetime.datetime`]
        A UTC date which entitlement is no longer valid. Not present when using test entitlements.
    """

    __slots__ = (
        '_state',
        'id',
        'sku_id',
        'user_id',
        'guild_id',
        'application_id',
        'type',
        'consumed',
        'starts_at',
        'ends_at',
    )

    def __init__(self, state: ConnectionState, data: EntitlementPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.sku_id: int = int(data['sku_id'])
        self.user_id: Optional[int] = utils._get_as_snowflake(data, 'user_id')
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.application_id: int = int(data['application_id'])
        self.type: EntitlementType = try_enum(EntitlementType, data['type'])
        self.consumed: bool = data.get('consumed', False)
        self.starts_at: Optional[datetime] = utils.parse_time(data.get('starts_at', None))
        self.ends_at: Optional[datetime] = utils.parse_time(data.get('ends_at', None))

    def __repr__(self) -> str:
        return f'<Entitlement id={self.id} type={self.type!r} user_id={self.user_id}>'

    @property
    def user(self) -> Optional[User]:
        """The user that is granted access to the entitlement"""
        if self.user_id is None:
            return None
        return self._state.get_user(self.user_id)

    @property
    def guild(self) -> Optional[Guild]:
        """The guild that is granted access to the entitlement"""
        return self._state._get_guild(self.guild_id)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the entitlement's creation time in UTC."""
        return utils.snowflake_time(self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the entitlement.

        Raises
        -------
        MissingApplicationID
            The application ID could not be found.
        NotFound
            The entitlement could not be found.
        HTTPException
            Deleting the entitlement failed.
        """

        if self.application_id is None:
            raise MissingApplicationID

        await self._state.http.delete_entitlement(self.application_id, self.id)
