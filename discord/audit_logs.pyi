import datetime

from typing import Any, Union, Optional, List, Dict, Tuple, Iterable, Iterator, ClassVar, Callable

from . import enums
from .abc import User as _ABCUser
from .guild import Guild
from .member import Member
from .user import User

class AuditLogDiff:
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Tuple[str, Any]]: ...

class AuditLogChanges:
    TRANSFORMERS: ClassVar[Dict[str, Tuple[Optional[str], Optional[Callable[[Any, Any], AuditLogDiff]]]]]
    before: AuditLogDiff
    after: AuditLogDiff

class AuditLogEntry:
    id: int
    guild: Guild
    action: enums.AuditLogAction
    user: _ABCUser
    reason: Optional[str]
    extra: Any

    def created_at(self) -> datetime.datetime: ...
    def target(self) -> Any: ...
    def category(self) -> Optional[enums.AuditLogActionCategory]: ...
    def changes(self) -> AuditLogChanges: ...
    def before(self) -> AuditLogDiff: ...
    def after(self) -> AuditLogDiff: ...
