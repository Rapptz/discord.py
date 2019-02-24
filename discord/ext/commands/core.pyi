from inspect import Parameter

from .context import Context
from .cooldowns import CooldownMapping, BucketType
from .cog import Cog

from typing import Any, Optional, Union, Callable, Dict, Iterator, Coroutine, Type, ValuesView, List, TypeVar, Mapping, Generic, overload

CT = TypeVar('CT', bound=Context)
_CheckType = Union[Callable[[CT], bool],
                   Callable[[CT], Coroutine[Any, Any, bool]]]
_CoroType = Callable[..., Coroutine[Any, Any, Any]]
_C = TypeVar('_C', bound=_CoroType)
_CMD = TypeVar('_CMD', bound=Command)
_F = TypeVar('_F', bound=Union[_CoroType, Command[Any]])

class Command(Generic[CT]):
    name: str
    callback: _CoroType
    help: str
    brief: str
    usage: str
    aliases: List[str]
    enabled: bool
    parent: Optional[Command[CT]]
    checks: List[_CheckType]
    description: str
    hidden: bool
    rest_is_raw: bool
    ignore_extra: bool
    params: Mapping[str, Parameter]
    _buckets: CooldownMapping
    cog: Optional[Cog[CT]]

    def __init__(self, func: _CoroType, *, name: str = ..., enabled: bool = ...,
                 help: Optional[str] = ..., brief: Optional[str] = ..., usage: Optional[str] = ...,
                 aliases: List[str] = ..., description: str = ..., hidden: bool = ...,
                 rest_is_raw: bool = ..., ignore_extra: bool = ...) -> None: ...

    def update(self, name: str = ..., enabled: bool = ..., help: Optional[str] = ..., brief: Optional[str] = ...,
               usage: Optional[str] = ..., aliases: List[str] = ..., description: str = ..., hidden: bool = ...,
               rest_is_raw: bool = ..., ignore_extra: bool = ...) -> None: ...

    def copy(self: _CMD) -> _CMD: ...

    async def dispatch_error(self, ctx: CT, error: Exception) -> None: ...

    async def do_conversion(self, ctx: CT, converter: Any, argument: str, param: Parameter) -> Any: ...

    async def transform(self, ctx: CT, param: Parameter) -> Any: ...

    @property
    def clean_params(self) -> Mapping[str, Parameter]: ...

    @property
    def full_parent_name(self) -> str: ...

    @property
    def root_parent(self) -> Optional[Command[CT]]: ...

    @property
    def qualified_name(self) -> str: ...

    def __str__(self) -> str: ...

    async def call_before_hooks(self, ctx: CT) -> None: ...

    async def call_after_hooks(self, ctx: CT) -> None: ...

    async def prepare(self, ctx: CT) -> None: ...

    def is_on_cooldown(self, ctx: CT) -> bool: ...

    def reset_cooldown(self, ctx: CT) -> None: ...

    async def invoke(self, ctx: CT) -> None: ...

    async def reinvoke(self, ctx: CT, *, call_hooks: bool = ...) -> None: ...

    def error(self, coro: _C) -> _C: ...

    def before_invoke(self, coro: _C) -> _C: ...

    def after_invoke(self, coro: _C) -> _C: ...

    @property
    def cog_name(self) -> Optional[str]: ...

    @property
    def short_doc(self) -> str: ...

    @property
    def signature(self) -> str: ...

    async def can_run(self, ctx: CT) -> bool: ...


class GroupMixin(Generic[CT]):
    all_commands: Dict[str, Command[CT]]
    case_insensitive: bool

    @property
    def commands(self) -> ValuesView[Command[CT]]: ...

    def recursively_remove_all_commands(self) -> None: ...

    def add_command(self, command: Command[CT]) -> None: ...

    def remove_command(self, name: str) -> Optional[Command[CT]]: ...

    def walk_commands(self) -> Iterator[Command[CT]]: ...

    def get_command(self, name: str) -> Optional[Command[CT]]: ...

    def command(self, *args: Any, **kwargs: Any) -> Callable[[_CoroType], Command[CT]]: ...

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., Group[CT]]: ...


_G = TypeVar('_G', bound=Group)


class Group(GroupMixin[CT], Command[CT], Generic[CT]):
    invoke_without_command: bool

    def __init__(self, *, invoke_without_command: bool = ...,
                 case_insensitive: bool = ...) -> None: ...

    def copy(self: _G) -> _G: ...


@overload
def command(name: Optional[str] = ..., *, enabled: bool = ...,
            help: Optional[str] = ..., brief: Optional[str] = ..., usage: Optional[str] = ...,
            rest_is_raw: bool = ..., aliases: List[str] = ..., description: str = ...,
            hidden: bool = ...) -> Callable[[_CoroType], Command[Any]]: ...
@overload
def command(name: Optional[str] = ..., cls: Optional[Type[Command[CT]]] = ..., *, enabled: bool = ...,
            help: Optional[str] = ..., brief: Optional[str] = ..., usage: Optional[str] = ...,
            rest_is_raw: bool = ..., aliases: List[str] = ..., description: str = ...,
            hidden: bool = ...) -> Callable[[_CoroType], Command[CT]]: ...

@overload
def group(name: Optional[str] = ..., invoke_without_command: bool = ...,
          case_insensitive: bool = ..., enabled: bool = ...,
          help: Optional[str] = ..., brief: Optional[str] = ..., usage: Optional[str] = ...,
          rest_is_raw: bool = ..., aliases: List[str] = ..., description: str = ...,
          hidden: bool = ...) -> Callable[[_CoroType], Group[Any]]: ...
@overload
def group(name: Optional[str] = ..., cls: Optional[Type[Group[CT]]] = ..., invoke_without_command: bool = ...,
          case_insensitive: bool = ..., enabled: bool = ...,
          help: Optional[str] = ..., brief: Optional[str] = ..., usage: Optional[str] = ...,
          rest_is_raw: bool = ..., aliases: List[str] = ..., description: str = ...,
          hidden: bool = ...) -> Callable[[_CoroType], Group[CT]]: ...

def check(predicate: _CheckType) -> Callable[[_F], _F]: ...

def has_role(item: Union[int, str]) -> Callable[[_F], _F]: ...

def has_any_role(*items: Union[int, str]) -> Callable[[_F], _F]: ...

def has_permissions(**perms: bool) -> Callable[[_F], _F]: ...

def bot_has_role(item: Union[int, str]) -> Callable[[_F], _F]: ...

def bot_has_any_role(*items: Union[int, str]) -> Callable[[_F], _F]: ...

def bot_has_permissions(**perms: bool) -> Callable[[_F], _F]: ...

def guild_only() -> Callable[[_F], _F]: ...

def is_owner() -> Callable[[_F], _F]: ...

def is_nsfw() -> Callable[[_F], _F]: ...

def cooldown(rate: int, per: float, type: BucketType = ...) -> Callable[[_F], _F]: ...
