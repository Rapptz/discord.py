from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Generic, TypeVar, Union

from ...utils import MISSING, maybe_coroutine

if TYPE_CHECKING:
    from typing_extensions import TypeAlias
    from .context import Context
    from .converter import Converter

__all__ = (
    "Parameter",
    "parameter",
    "param",
)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

ConverterType: TypeAlias = "Union[Converter[T], Callable[[str], T]]"
DefaultType: TypeAlias = "Union[T, Callable[[Context], Union[T, Awaitable[T]]]]"


@dataclass
class Parameter(Generic[T_co]):
    converter: ConverterType[T_co] = MISSING
    default: DefaultType[T_co] = MISSING
    _displayed_default: str = MISSING

    @property
    def required(self) -> bool:
        return self.default is MISSING

    @property
    def displayed_default(self) -> str:
        if self._displayed_default is not MISSING:
            return self._displayed_default
        if self.required:
            return ""
        else:
            return str(self.default)

    async def get_default(self, ctx: Context) -> T_co:
        # pre-condition: required is False
        if callable(self.default):
            return await maybe_coroutine(self.default, ctx)
        return self.default


def parameter(
    *,
    converter: ConverterType[T] = MISSING,
    default: DefaultType[T] = MISSING,
    displayed_default: str = MISSING,
) -> Any:
    """Some docs or something"""
    return Parameter(converter, default, displayed_default)


param = parameter
