import enum

from .context import Context
from ...message import Message

from typing import Optional, TypeVar, Type

class BucketType(enum.Enum):
    default: int
    user: int
    guild: int
    channel: int
    member: int
    category: int

class Cooldown:
    rate: int
    per: float
    type: BucketType

    def __init__(self, rate: int, per: float, type: BucketType) -> None: ...

    def get_tokens(self, current: Optional[int] = ...) -> int: ...

    def update_rate_limit(self) -> Optional[float]: ...

    def reset(self) -> None: ...

    def copy(self) -> Cooldown: ...

    def __repr__(self) -> str: ...

_T = TypeVar('_T', bound=CooldownMapping)

class CooldownMapping:
    def __init__(self, original: Cooldown) -> None: ...

    def copy(self) -> CooldownMapping: ...

    @property
    def valid(self) -> bool: ...

    @classmethod
    def from_cooldown(cls: Type[_T], rate: int, per: float, type: BucketType) -> _T: ...

    def get_bucket(self, message: Message) -> Cooldown: ...
