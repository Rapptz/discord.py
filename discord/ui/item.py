"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, Optional, TYPE_CHECKING, Tuple, Type, TypeVar, Union
import inspect

from ..interactions import Interaction

__all__ = (
    'Item',
)

if TYPE_CHECKING:
    from ..enums import ComponentType
    from .view import View
    from ..components import Component

I = TypeVar('I', bound='Item')
ItemCallbackType = Callable[[Any, I, Interaction], Coroutine[Any, Any, Any]]


class Item:
    """Represents the base UI item that all UI components inherit from.

    The current UI items supported are:

    - :class:`discord.ui.Button`
    """

    __slots__: Tuple[str, ...] = (
        '_callback',
        '_pass_view_arg',
        'group_id',
    )

    __item_repr_attributes__: Tuple[str, ...] = ('group_id',)

    def __init__(self):
        self._callback: Optional[ItemCallbackType] = None
        self._pass_view_arg = True
        self.group_id: Optional[int] = None

    def to_component_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def copy(self: I) -> I:
        raise NotImplementedError

    def refresh_state(self, component: Component) -> None:
        return None

    @classmethod
    def from_component(cls: Type[I], component: Component) -> I:
        return cls()

    @property
    def type(self) -> ComponentType:
        raise NotImplementedError

    def is_dispatchable(self) -> bool:
        return False

    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__item_repr_attributes__)
        return f'<{self.__class__.__name__} {attrs}>'

    @property
    def callback(self) -> Optional[ItemCallbackType]:
        """Returns the underlying callback associated with this interaction."""
        return self._callback

    @callback.setter
    def callback(self, value: Optional[ItemCallbackType]):
        if value is None:
            self._callback = None
            return

        # Check if it's a partial function
        try:
            partial = value.func
        except AttributeError:
            pass
        else:
            if not inspect.iscoroutinefunction(value.func):
                raise TypeError(f'inner partial function must be a coroutine')

            # Check if the partial is bound
            try:
                bound_partial = partial.__self__
            except AttributeError:
                pass
            else:
                self._pass_view_arg = not hasattr(bound_partial, '__discord_ui_view__')

            self._callback = value
            return

        try:
            func_self = value.__self__
        except AttributeError:
            pass
        else:
            if not isinstance(func_self, Item):
                raise TypeError(f'callback bound method must be from Item not {func_self!r}')
            else:
                value = value.__func__

        if not inspect.iscoroutinefunction(value):
            raise TypeError(f'callback must be a coroutine not {value!r}')

        self._callback = value

    async def _do_call(self, view: View, interaction: Interaction):
        if self._pass_view_arg:
            await self._callback(view, self, interaction)
        else:
            await self._callback(self, interaction)  # type: ignore
