import datetime
from .mixins import Hashable
from .role import Role
from .guild import Guild

from typing import Any, Optional, List, Iterator, Tuple, NamedTuple

class PartialEmoji(NamedTuple):
    animated: bool
    name: str
    id: Optional[int]

    def __str__(self) -> str: ...

    def is_custom_emoji(self) -> bool: ...

    def is_unicode_emoji(self) -> bool: ...

    @property
    def url(self) -> Optional[str]: ...


class Emoji(Hashable):
    name: str
    id: int
    require_colons: bool
    animated: bool
    managed: bool
    guild_id: int

    def __iter__(self) -> Iterator[Tuple[str, Any]]: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    @property
    def url(self) -> str: ...

    @property
    def roles(self) -> List[Role]: ...

    @property
    def guild(self) -> Guild: ...

    async def delete(self, *, reason: Optional[str] = ...) -> None: ...

    async def edit(self, *, name: str, reason: Optional[str] = ...) -> None: ...
