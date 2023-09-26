from typing import TypedDict, Optional, List, Literal
from typing_extensions import NotRequired


class SKU(TypedDict):
    id: str
    type: int
    dependent_sku_id: Optional[str]
    application_id: str
    manifest_labels: Optional[List[str]]
    access_type: int
    name: str
    features: List[str]
    release_date: Optional[str]
    premium: bool
    slug: str
    flags: int
    show_age_gate: bool


class Entitlement(TypedDict):
    id: str
    sku_id: str
    application_id: str
    user_id: str
    promotion_id: Optional[str]
    type: int
    deleted: bool
    gift_code_flags: int
    consumed: bool
    starts_at: NotRequired[str]
    ends_at: NotRequired[str]
    guild_id: Optional[str]
    subscription_id: NotRequired[str]


EntitlementType = Literal[1, 2]
