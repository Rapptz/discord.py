from .asset import Asset
from .guild import Guild
from .team import Team
from .user import User
from typing import Any, Optional, List

class AppInfo:
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    rpc_origins: Optional[List[str]]
    bot_public: bool
    bot_require_code_grant: bool
    owner: User
    team: Team
    summary: str
    verify_key: str
    guild_id: Optional[int]
    primary_sku_id: Optional[int]
    slug: Optional[str]
    cover_image: Optional[str]

    @property
    def icon_url(self) -> Asset: ...
    @property
    def cover_image_url(self) -> Asset: ...
    @property
    def guild(self) -> Optional[Guild]: ...
