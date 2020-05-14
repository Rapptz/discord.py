from .mixins import Hashable
from .permissions import Permissions
from .member import Member
from .colour import Colour
from .guild import Guild

import datetime
from typing import Any, List, Optional, Union, overload

class Role(Hashable):
    id: int
    name: str
    guild: Guild
    hoist: bool
    position: int
    managed: bool
    mentionable: bool

    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...
    def is_default(self) -> bool: ...
    @property
    def permissions(self) -> Permissions: ...
    @property
    def colour(self) -> Colour: ...
    @property
    def color(self) -> Colour: ...
    @property
    def created_at(self) -> datetime.datetime: ...
    @property
    def mention(self) -> str: ...
    @property
    def members(self) -> List[Member]: ...
    @overload
    async def edit(self, *, name: str = ..., permissions: Permissions = ..., colour: Union[Colour, int] = ...,
                   hoist: bool = ..., mentionable: bool = ..., position: int = ...,
                   reason: Optional[str] = ...) -> None: ...
    @overload
    async def edit(self, *, name: str = ..., permissions: Permissions = ..., color: Union[Colour, int] = ...,
                   hoist: bool = ..., mentionable: bool = ..., position: int = ...,
                   reason: Optional[str] = ...) -> None: ...
    async def delete(self, *, reason: Optional[str] = ...) -> None: ...
