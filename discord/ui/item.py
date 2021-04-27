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

from typing import Any, Callable, Coroutine, Dict, Generic, Optional, TYPE_CHECKING, Tuple, Type, TypeVar

from ..interactions import Interaction

__all__ = (
    'Item',
)

if TYPE_CHECKING:
    from ..enums import ComponentType
    from .view import View
    from ..components import Component

I = TypeVar('I', bound='Item')
V = TypeVar('V', bound='View', covariant=True)
ItemCallbackType = Callable[[Any, I, Interaction], Coroutine[Any, Any, Any]]


class Item(Generic[V]):
    """Represents the base UI item that all UI components inherit from.

    The current UI items supported are:

    - :class:`discord.ui.Button`
    """

    __item_repr_attributes__: Tuple[str, ...] = ('group_id',)

    def __init__(self):
        self._view: Optional[V] = None
        self.group_id: Optional[int] = None

    def to_component_dict(self) -> Dict[str, Any]:
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
    def view(self) -> Optional[V]:
        """Optional[:class:`View`]: The underlying view for this item."""
        return self._view

    async def callback(self, interaction: Interaction):
        """|coro|

        The callback associated with this UI item.

        This can be overriden by subclasses.

        Parameters
        -----------
        interaction: :class:`Interaction`
            The interaction that triggered this UI item.
        """
        pass
