from .abc import Snowflake
from typing import Any, Union, List, Iterable
from typing_extensions import TypedDict

class _FakeBool:
    def __eq__(self, other: Any) -> bool: ...
    def __bool__(self) -> bool: ...

default: _FakeBool

class _AllowedMentionsDictBase(TypedDict):
    parse: List[str]

class _AllowedMentionsDict(_AllowedMentionsDictBase, total=False):
    users: List[int]
    roles: List[int]

class AllowedMentions:
    everyone: bool
    users: Union[bool, Iterable[Snowflake]]
    roles: Union[bool, Iterable[Snowflake]]
    def __init__(self, *, everyone: Union[bool, _FakeBool] = ..., users: Union[bool, _FakeBool, Iterable[Snowflake]] = ...,
                 roles: Union[bool, _FakeBool, Iterable[Snowflake]] = ...) -> None: ...
    def to_dict(self) -> _AllowedMentionsDict: ...
    def merge(self, other: AllowedMentions) -> AllowedMentions: ...
