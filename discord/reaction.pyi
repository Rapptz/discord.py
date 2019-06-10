from .member import Member
from .message import Message
from .emoji import Emoji
from .iterators import ReactionIterator
from .abc import Snowflake

from typing import Any, Union, Optional
from typing_extensions import Protocol
from mypy_extensions import TypedDict

class _RequiredReactionData(TypedDict):
    me: bool

class _ReactionData(_RequiredReactionData, total=False):
    count: int

class _UserProtocol(Protocol):
    id: int

class Reaction:
    emoji: Union[Emoji, str]
    count: int
    me: bool
    message: Message

    @property
    def custom_emoji(self) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
    async def remove(self, user: _UserProtocol) -> None: ...
    def users(self, limit: Optional[int] = ..., after: Optional[Snowflake] = ...) -> ReactionIterator: ...
