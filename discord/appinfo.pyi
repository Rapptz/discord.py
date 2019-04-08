from .asset import Asset
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

    @property
    def icon_url(self) -> Asset: ...
