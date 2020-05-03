from typing import Any, Iterator, Tuple, ClassVar, Dict, Generic, TypeVar, overload

_F = TypeVar('_F', bound=flag_value)

class flag_value:
    flag: int

    @overload
    def __get__(self: _F, instance: None, owner: Any) -> _F: ...
    @overload
    def __get__(self, instance: Any, owner: Any) -> bool: ...
    def __set__(self, instance: Any, value: bool) -> None: ...

class BaseFlags:
    value: int = ...
    def __init__(self, **kwargs: bool) -> None: ...
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __iter__(self) -> Iterator[Tuple[str, bool]]: ...

class SystemChannelFlags(BaseFlags):
    VALID_FLAGS: ClassVar[Dict[str, int]]

    join_notifications: flag_value
    premium_subscriptions: flag_value

class MessageFlags(BaseFlags):
    VALID_FLAGS: ClassVar[Dict[str, int]]

    crossposted: flag_value
    is_crossposted: flag_value
    suppress_embeds: flag_value
    source_message_deleted: flag_value
    urgent: flag_value
