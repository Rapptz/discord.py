from __future__ import annotations

import inspect
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic, Literal, OrderedDict, Type, TypeVar, Union

from typing_extensions import Self

from ...utils import MISSING, maybe_coroutine

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from .context import Context
    from .converter import Converter, Greedy

__all__ = (
    "Parameter",
    "parameter",
    "param",
)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

if TYPE_CHECKING:
    ConverterType: TypeAlias = "Union[Converter[T], Callable[[str], T], Greedy[T], Type[None], bool]"
    DefaultType: TypeAlias = "Union[T, Callable[[Context], Union[T, Awaitable[T]]]]"
else:

    class ConverterType(Generic[T]):
        pass

    DefaultType = ConverterType


ParamKinds = Union[
    Literal[inspect.Parameter.POSITIONAL_ONLY],
    Literal[inspect.Parameter.POSITIONAL_OR_KEYWORD],
    Literal[inspect.Parameter.VAR_POSITIONAL],
    Literal[inspect.Parameter.KEYWORD_ONLY],
    Literal[inspect.Parameter.VAR_KEYWORD],
]

empty: Any = inspect.Parameter.empty


class Parameter(inspect.Parameter, Generic[T_co]):
    def __init__(
        self,
        name: str = empty,
        kind: ParamKinds = empty,
        default: DefaultType[T_co] = empty,
        annotation: Any = empty,
        displayed_default: str = empty,
    ) -> None:
        super().__init__(name=name, kind=kind, default=default, annotation=annotation)
        self._name = name
        self._kind = kind
        self._default = default
        self._annotation = annotation
        self._displayed_default = displayed_default

    def replace(
        self,
        *,
        name: str = MISSING,  # MISSING here cause empty is valid
        kind: ParamKinds = MISSING,
        default: Any = MISSING,
        annotation: Any = MISSING,
        displayed_default: Any = MISSING,
    ) -> Self:
        if name is MISSING:
            name = self._name
        if kind is MISSING:
            kind = self._kind  # type: ignore  # this assignment is actually safe
        if default is MISSING:
            default = self._default
        if annotation is MISSING:
            annotation = self._annotation
        if displayed_default is MISSING:
            displayed_default = self._displayed_default

        return self.__class__(
            name=name, kind=kind, default=default, annotation=annotation, displayed_default=displayed_default
        )

    if not TYPE_CHECKING:
        name = property(attrgetter("_name"), lambda self, name: setattr(self, "_name", name))
        kind = property(attrgetter("_kind"), lambda self, kind: setattr(self, "_kind", kind))
        default = property(attrgetter("_default"), lambda self, default: setattr(self, "_default", default))
        annotation = property(attrgetter("_annotation"), lambda self, annotation: setattr(self, "_annotation", annotation))

    @property
    def required(self) -> bool:
        return self.default is empty

    @property
    def converter(self) -> ConverterType[T_co]:
        if self.annotation is empty:
            return type(self.default) if self.default not in (empty, None) else str

        return self.annotation

    @property
    def displayed_default(self) -> str:
        if self._displayed_default is not empty:
            return self._displayed_default

        return "" if self.required else str(self.default)

    async def get_default(self, ctx: Context) -> T_co:
        # pre-condition: required is False
        if callable(self.default):
            return await maybe_coroutine(self.default, ctx)
        return self.default


def parameter(
    *,
    converter: ConverterType[T] = empty,
    default: DefaultType[T] = empty,
    displayed_default: str = empty,
) -> Any:
    """Some docs or something"""
    return Parameter(
        name="empty",
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        annotation=converter,
        default=default,
        displayed_default=displayed_default,
    )


param = parameter


class Signature(inspect.Signature):
    _parameter_cls = Parameter
    parameters: OrderedDict[str, Parameter]
