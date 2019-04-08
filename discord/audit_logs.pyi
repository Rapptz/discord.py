import datetime

from typing import Any, Union, Optional, List, Dict, Tuple, Iterable, Iterator

from . import enums
from .abc import User as ABCUser
from .guild import Guild
from .member import Member
from .user import User

class AuditLogDiff:
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Tuple[str, Any]]: ...
    def __repr__(self) -> str: ...

class AuditLogChanges:
    before: AuditLogDiff
    after: AuditLogDiff

class AuditLogEntry:
    id: int
    guild: Guild
    action: enums.AuditLogAction
    user: ABCUser
    reason: Optional[str]
    extra: Any

    def __repr__(self) -> str: ...
    def created_at(self) -> datetime.datetime: ...
    def target(self) -> Any: ...
    def category(self) -> Optional[enums.AuditLogActionCategory]: ...
    def changes(self) -> AuditLogChanges: ...
    def before(self) -> AuditLogDiff: ...
    def after(self) -> AuditLogDiff: ...
