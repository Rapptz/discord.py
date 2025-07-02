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
from .._types import ClientT

# fmt: off
__all__ = (
    'Item',
)
# fmt: on

if TYPE_CHECKING:
    from ..enums import ComponentType
    from .view import BaseView
    from ..components import Component

I = TypeVar('I', bound='Item[Any]')
V = TypeVar('V', bound='BaseView', covariant=True)
ItemCallbackType = Callable[[Any, Interaction[Any], I], Coroutine[Any, Any, Any]]


class Item(Generic[V]):
    """Represents the base UI item that all UI components inherit from.

    The current UI items supported are:

    - :class:`discord.ui.Button`
    - :class:`discord.ui.Select`
    - :class:`discord.ui.TextInput`
    - :class:`discord.ui.ActionRow`
    - :class:`discord.ui.Container`
    - :class:`discord.ui.File`
    - :class:`discord.ui.MediaGallery`
    - :class:`discord.ui.Section`
    - :class:`discord.ui.Separator`
    - :class:`discord.ui.TextDisplay`
    - :class:`discord.ui.Thumbnail`

    .. versionadded:: 2.0
    """

    __item_repr_attributes__: Tuple[str, ...] = ('row', 'id')

    def __init__(self):
        self._view: Optional[V] = None
        self._row: Optional[int] = None
        self._rendered_row: Optional[int] = None
        # This works mostly well but there is a gotcha with
        # the interaction with from_component, since that technically provides
        # a custom_id most dispatchable items would get this set to True even though
        # it might not be provided by the library user. However, this edge case doesn't
        # actually affect the intended purpose of this check because from_component is
        # only called upon edit and we're mainly interested during initial creation time.
        self._provided_custom_id: bool = False
        self._id: Optional[int] = None
        self._max_row: int = 5 if not self._is_v2() else 40
        self._parent: Optional[Item] = None

    def to_component_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def _refresh_component(self, component: Component) -> None:
        return None

    def _refresh_state(self, interaction: Interaction, data: Dict[str, Any]) -> None:
        return None

    def _is_v2(self) -> bool:
        return False

    @classmethod
    def from_component(cls: Type[I], component: Component) -> I:
        return cls()

    @property
    def type(self) -> ComponentType:
        raise NotImplementedError

    def is_dispatchable(self) -> bool:
        return False

    def is_persistent(self) -> bool:
        if self.is_dispatchable():
            return self._provided_custom_id
        return True

    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__item_repr_attributes__)
        return f'<{self.__class__.__name__} {attrs}>'

    @property
    def row(self) -> Optional[int]:
        return self._row

    @row.setter
    def row(self, value: Optional[int]) -> None:
        if value is None:
            self._row = None
        elif self._max_row > value >= 0:
            self._row = value
        else:
            raise ValueError(f'row cannot be negative or greater than or equal to {self._max_row}')

        if self._rendered_row is None:
            self._rendered_row = value

    @property
    def width(self) -> int:
        return 1

    @property
    def view(self) -> Optional[V]:
        """Optional[:class:`View`]: The underlying view for this item."""
        return self._view

    @property
    def id(self) -> Optional[int]:
        """Optional[:class:`int`]: The ID of this component."""
        return self._id

    @id.setter
    def id(self, value: Optional[int]) -> None:
        self._id = value

    async def _run_checks(self, interaction: Interaction[ClientT]) -> bool:
        can_run = await self.interaction_check(interaction)

        if can_run and self._parent:
            can_run = await self._parent._run_checks(interaction)

        return can_run

    def _can_be_dynamic(self) -> bool:
        # if an item can be dynamic then it must override this, this is mainly used
        # by DynamicItem's so a user cannot set, for example, a Container with a dispatchable
        # button as a dynamic item, and cause errors where Container can't be dispatched
        # or lost interactions
        return False

    async def callback(self, interaction: Interaction[ClientT]) -> Any:
        """|coro|

        The callback associated with this UI item.

        This can be overridden by subclasses.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The interaction that triggered this UI item.
        """
        pass

    async def interaction_check(self, interaction: Interaction[ClientT], /) -> bool:
        """|coro|

        A callback that is called when an interaction happens within this item
        that checks whether the callback should be processed.

        This is useful to override if, for example, you want to ensure that the
        interaction author is a given user.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check
            is considered a failure and :meth:`discord.ui.View.on_error` is called.

            For :class:`~discord.ui.DynamicItem` this does not call the ``on_error``
            handler.

        .. versionadded:: 2.4

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that occurred.

        Returns
        ---------
        :class:`bool`
            Whether the callback should be called.
        """
        return True
