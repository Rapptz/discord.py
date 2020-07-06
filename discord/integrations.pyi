import datetime
from typing import Any, Optional, NamedTuple

from .enums import ExpireBehaviour
from .user import User
from .guild import Guild
from .role import Role

class IntegrationAccount(NamedTuple):
    id: int
    name: str

class Integration:
    id: int
    name: str
    guild: Guild
    type: str
    enabled: bool
    syncing: bool
    role: Role
    enable_emoticons: Optional[bool]
    expire_behaviour: ExpireBehaviour
    expire_behavior: ExpireBehaviour
    expire_grace_period: int
    user: User
    account: IntegrationAccount
    synced_at: datetime.datetime
    async def edit(self, *, expire_behaviour: ExpireBehaviour = ..., expire_behavior: ExpireBehaviour = ...,
                   expire_grace_period: int = ..., enable_emoticons: bool = ...) -> None: ...
    async def sync(self) -> None: ...
    async def delete(self) -> None: ...
