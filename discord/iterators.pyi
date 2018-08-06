import datetime
import abc

from .user import User
from .member import Member
from .message import Message
from .emoji import Emoji
from .abc import Messageable
from .guild import Guild
from .audit_logs import AuditLogEntry
from .abc import Snowflake
from .enums import AuditLogAction

from typing import Any, Optional, Union, TypeVar, List, Generic, Coroutine, Callable

IT = TypeVar('IT')
_AIT = TypeVar('_AIT', bound='_AsyncIterator')

class _AsyncIterator(Generic[IT]):
    @abc.abstractmethod
    async def next(self) -> IT: ...

    def get(self, **attrs: Any) -> Coroutine[Any, Any, Optional[IT]]: ...

    async def find(self, predicate: Callable[[IT], bool]) -> Optional[IT]: ...

    def map(self, func: Callable[[IT], Union[IT, Coroutine[Any, Any, IT]]]) -> '_MappedAsyncIterator[IT]': ...

    def filter(self, predicate: Callable[[IT], Union[IT, Coroutine[Any, Any, IT]]]) -> '_FilteredAsyncIterator[IT]': ...

    async def flatten(self) -> List[IT]: ...

    def __aiter__(self) -> _AIT: ...

    async def __anext__(self) -> IT: ...


_VT = TypeVar('_VT')

def _identity(x: _VT) -> _VT: ...

class _MappedAsyncIterator(_AsyncIterator[IT]):
    async def next(self) -> IT: ...


class _FilteredAsyncIterator(_AsyncIterator[IT]):
    async def next(self) -> IT: ...


class ReactionIterator(_AsyncIterator[Union[User, Member]]):
    async def next(self) -> Union[User, Member]: ...

    async def fill_users(self) -> None: ...


class HistoryIterator(_AsyncIterator[Message]):
    async def next(self) -> Message: ...

    async def flatten(self) -> List[Message]: ...

    async def fill_messages(self) -> None: ...


class AuditLogIterator(_AsyncIterator[AuditLogEntry]):
    async def next(self) -> AuditLogEntry: ...
