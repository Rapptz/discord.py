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

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Type, TypeVar

from .item import Item
from .view import View, _component_to_item, LayoutView
from .dynamic import DynamicItem
from ..enums import ComponentType
from ..utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..colour import Colour, Color
    from ..components import Container as ContainerComponent

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('Container',)


class Container(View, Item[V]):
    """Represents a UI container.

    .. versionadded:: 2.6

    Parameters
    ----------
    children: List[:class:`Item`]
        The initial children or :class:`View` s of this container. Can have up to 10
        items.
    accent_colour: Optional[:class:`.Colour`]
        The colour of the container. Defaults to ``None``.
    accent_color: Optional[:class:`.Colour`]
        The color of the container. Defaults to ``None``.
    spoiler: :class:`bool`
        Whether to flag this container as a spoiler. Defaults
        to ``False``.
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    row: Optional[:class:`int`]
        The relative row this container belongs to. By default
        items are arranged automatically into those rows. If you'd
        like to control the relative positioning of the row then
        passing an index is advised. For example, row=1 will show
        up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 9 (i.e. zero indexed)
    id: Optional[:class:`str`]
        The ID of this component. This must be unique across the view.
    """

    __discord_ui_container__ = True

    def __init__(
        self,
        children: List[Item[Any]] = MISSING,
        *,
        accent_colour: Optional[Colour] = None,
        accent_color: Optional[Color] = None,
        spoiler: bool = False,
        timeout: Optional[float] = 180,
        row: Optional[int] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        if children is not MISSING:
            if len(children) + len(self._children) > 10:
                raise ValueError('maximum number of components exceeded')
            self._children.extend(children)
        self.spoiler: bool = spoiler
        self._colour = accent_colour or accent_color

        self._view: Optional[V] = None
        self._row: Optional[int] = None
        self._rendered_row: Optional[int] = None
        self.row: Optional[int] = row
        self.id: Optional[str] = id

    @property
    def children(self) -> List[Item[Self]]:
        """List[:class:`Item`]: The children of this container."""
        return self._children.copy()

    @children.setter
    def children(self, value: List[Item[Any]]) -> None:
        self._children = value

    @property
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`discord.Colour`]: The colour of the container, or ``None``."""
        return self._colour

    @accent_colour.setter
    def accent_colour(self, value: Optional[Colour]) -> None:
        self._colour = value

    accent_color = accent_colour

    @property
    def type(self) -> Literal[ComponentType.container]:
        return ComponentType.container

    @property
    def width(self):
        return 5

    def _is_v2(self) -> bool:
        return True

    def is_dispatchable(self) -> bool:
        return any(c.is_dispatchable() for c in self.children)

    def to_component_dict(self) -> Dict[str, Any]:
        components = super().to_components()
        return {
            'type': self.type.value,
            'accent_color': self._colour.value if self._colour else None,
            'spoiler': self.spoiler,
            'components': components,
        }

    def _update_store_data(
        self,
        dispatch_info: Dict[Tuple[int, str], Item[Any]],
        dynamic_items: Dict[Any, Type[DynamicItem]],
    ) -> bool:
        is_fully_dynamic = True
        for item in self._children:
            if isinstance(item, DynamicItem):
                pattern = item.__discord_ui_compiled_template__
                dynamic_items[pattern] = item.__class__
            elif item.is_dispatchable():
                dispatch_info[(item.type.value, item.custom_id)] = item  # type: ignore
                is_fully_dynamic = False
        return is_fully_dynamic

    @classmethod
    def from_component(cls, component: ContainerComponent) -> Self:
        return cls(
            children=[_component_to_item(c) for c in component.children],
            accent_colour=component.accent_colour,
            spoiler=component.spoiler,
        )
