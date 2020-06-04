from typing import Any, Iterator, Tuple, ClassVar, Dict, List, Generic, TypeVar, overload

from .enums import UserFlags

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

class PublicUserFlags(BaseFlags):
    VALID_FLAGS: ClassVar[Dict[str, int]]

    staff: flag_value
    partner: flag_value
    hypesquad: flag_value
    bug_hunter: flag_value
    hypesquad_bravery: flag_value
    hypesquad_brilliance: flag_value
    hypesquad_balance: flag_value
    early_supporter: flag_value
    team_user: flag_value
    system: flag_value
    bug_hunter_level_2: flag_value
    verified_bot: flag_value
    verified_bot_developer: flag_value

    def all(self) -> List[UserFlags]: ...
