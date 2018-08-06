import datetime

from typing import Any, Union, Optional, List, Dict, Tuple, Iterable, Iterator

from . import enums, utils
from .abc import User as ABCUser
from .guild import Guild
from .member import Member
from .state import ConnectionState
from .user import User


class AuditLogDiff:
    def __len__(self) -> int: ...

    def __iter__(self) -> Iterator[Tuple[str, Any]]: ...

    def __repr__(self) -> str: ...


class AuditLogChanges:
    before: AuditLogDiff
    after: AuditLogDiff

    def __init__(self, entry: 'AuditLogEntry', data: List[Dict[str, Any]]) -> None: ...


class AuditLogEntry:
    id: int
    guild: Guild
    action: enums.AuditLogAction
    user: ABCUser
    reason: Optional[str]
    extra: Any
    _state: ConnectionState

    def __init__(self, *, users: Any, data: Any, guild: Guild) -> None: ...

    def __repr__(self) -> str: ...

    @utils.cached_property
    def created_at(self) -> datetime.datetime: ...

    @utils.cached_property
    def target(self) -> Any: ...

    @utils.cached_property
    def category(self) -> Optional[enums.AuditLogActionCategory]: ...

    @utils.cached_property
    def changes(self) -> AuditLogChanges: ...

    @utils.cached_property
    def before(self) -> AuditLogDiff: ...

    @utils.cached_property
    def after(self) -> AuditLogDiff: ...
