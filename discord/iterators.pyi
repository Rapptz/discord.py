import abc

from .user import User
from .member import Member
from .message import Message
from .audit_logs import AuditLogEntry

from typing import Any, Optional, Union, TypeVar, List, Generic, Coroutine, Callable

_IT = TypeVar('_IT')
_AIT = TypeVar('_AIT', bound=_AsyncIterator)

class _AsyncIterator(Generic[_IT]):
    @abc.abstractmethod
    async def next(self) -> _IT: ...

    def get(self, **attrs: Any) -> Coroutine[Any, Any, Optional[_IT]]: ...

    async def find(self, predicate: Callable[[_IT], bool]) -> Optional[_IT]: ...

    def map(self, func: Callable[[_IT], Union[_IT, Coroutine[Any, Any, _IT]]]) -> _MappedAsyncIterator[_IT]: ...

    def filter(self, predicate: Callable[[_IT], Union[_IT, Coroutine[Any, Any, _IT]]]) -> _FilteredAsyncIterator[_IT]: ...

    async def flatten(self) -> List[_IT]: ...

    def __aiter__(self: _AIT) -> _AIT: ...

    async def __anext__(self) -> _IT: ...


_VT = TypeVar('_VT')

def _identity(x: _VT) -> _VT: ...

class _MappedAsyncIterator(_AsyncIterator[_IT]):
    async def next(self) -> _IT: ...


class _FilteredAsyncIterator(_AsyncIterator[_IT]):
    async def next(self) -> _IT: ...


class ReactionIterator(_AsyncIterator[Union[User, Member]]):
    async def next(self) -> Union[User, Member]: ...

    async def fill_users(self) -> None: ...


class HistoryIterator(_AsyncIterator[Message]):
    async def next(self) -> Message: ...

    async def flatten(self) -> List[Message]: ...

    async def fill_messages(self) -> None: ...


class AuditLogIterator(_AsyncIterator[AuditLogEntry]):
    async def next(self) -> AuditLogEntry: ...
