from __future__ import annotations

from typing import Optional, TYPE_CHECKING, List

from . import utils
from .enums import try_enum, SKUType, SKUAccessType, SKUFeature, EntitlementType

__all__ = (
    'SKU',
    'Entitlement'
)

from .flags import SKUFlags

if TYPE_CHECKING:
    from datetime import datetime

    from .guild import Guild
    from .state import ConnectionState
    from .types.sku import (
        SKU as SKUPayload,
        Entitlement as EntitlementPayload,
    )


class SKU:
    """Represents a SKU of an application.

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The SKU's ID.
    type: :class:`SKUType`
        The type of the SKU.
    dependent_sku_id: Optional[:class:`int`]
        The ID of the dependent SKU if any.
    application_id: :class:`int`
        The ID of the application that the SKU belongs to.
    manifest_labels: List[:class:`int`]
        The manifest labels of the SKU.
    access_type: :class:`SKUAccessType`
        The access type of the SKU.
    name: :class:`str`
        The name of the SKU.
    features: List[:class:`SKUFeature`]
        The features of the SKU.
    release_date: Optional[:class:`datetime.datetime`]
        The release date of the SKU.
    premium: :class:`bool`
        Whether the SKU is premium.
    slug: :class:`str`
        The slug of the SKU.
    show_age_gate: :class:`bool`
        Whether the SKU shows an age gate.
    """

    __slots__ = (
        '_state',
        'id',
        'type',
        'dependent_sku_id',
        'application_id',
        'manifest_labels',
        'access_type',
        'name',
        'features',
        'release_date',
        'premium',
        'slug',
        '_flags',
        'show_age_gate',
    )

    def __init__(self, *, state: ConnectionState, data: SKUPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.type = try_enum(SKUType, data['type'])
        self.dependent_sku_id: Optional[int] = utils._get_as_snowflake(data, 'dependent_sku_id')
        self.application_id: int = int(data['application_id'])
        self.manifest_labels: List[int] = [int(label) for label in data['manifest_labels'] or []]
        self.access_type: SKUAccessType = try_enum(SKUAccessType, data['access_type'])
        self.name: str = data['name']
        self.features: List[SKUFeature] = [try_enum(SKUFeature, feature) for feature in data['features'] or []]
        self.release_date: Optional[datetime] = utils.parse_time(data['release_date'])
        self.premium: bool = data['premium']
        self.slug: str = data['slug']
        self._flags: int = data['flags']
        self.show_age_gate: bool = data['show_age_gate']

    def __repr__(self) -> str:
        return f'<SKU id={self.id} name={self.name!r} slug={self.slug!r}>'

    @property
    def flags(self) -> SKUFlags:
        """Returns the flags of the SKU."""
        return SKUFlags._from_value(self._flags)


class Entitlement:
    """Represents an entitlement of a user.

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The entitlement's ID.
    sku_id: :class:`int`
        The ID of the SKU that the entitlement belongs to.
    application_id: :class:`int`
        The ID of the application that the entitlement belongs to.
    user_id: :class:`int`
        The ID of the user that the entitlement belongs to.
    promotion_id: Optional[:class:`int`]
        The ID of the promotion that the entitlement belongs to if any.
    type: :class:`EntitlementType`
        The type of the entitlement.
    deleted: :class:`bool`
        Whether the entitlement has been deleted.
    gift_code_flags: :class:`int`
        The gift code flags of the entitlement.
    consumed: :class:`bool`
        Whether the entitlement has been consumed.
    starts_at: Optional[:class:`datetime.datetime`]
        A naive UTC datetime object representing the start time of the entitlement.
    ends_at: Optional[:class:`datetime.datetime`]
        A naive UTC datetime object representing the end time of the entitlement.
    guild_id: Optional[:class:`int`]
        The ID of the guild that the entitlement belongs to if any.
    subscription_id: Optional[:class:`int`]
        The ID of the subscription that the entitlement belongs to if any.
    """

    __slots__ = (
        '_state',
        'id',
        'sku_id',
        'application_id',
        'user_id',
        'promotion_id',
        'type',
        'deleted',
        'gift_code_flags',
        'consumed',
        'starts_at',
        'ends_at',
        'guild_id',
        'subscription_id',
    )

    def __init__(self, state: ConnectionState, data: EntitlementPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self.user_id: int = int(data['user_id'])
        self.promotion_id: Optional[int] = utils._get_as_snowflake(data, 'promotion_id')
        self.type: EntitlementType = try_enum(EntitlementType, data['type'])
        self.deleted: bool = data['deleted']
        self.gift_code_flags: int = data['gift_code_flags']
        self.consumed: bool = data['consumed']
        self.starts_at: Optional[datetime] = utils.parse_time(data.get('starts_at', None))
        self.ends_at: Optional[datetime] = utils.parse_time(data.get('ends_at', None))
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.subscription_id: Optional[int] = utils._get_as_snowflake(data, 'subscription_id')

    def __repr__(self) -> str:
        return f'<Entitlement id={self.id} type={self.type!r} user_id={self.user_id}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Returns the guild that the entitlement belongs to if any."""
        return self._state._get_guild(self.guild_id)
