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

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypeVar

from .item import Item
from ..enums import ComponentType

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import View

    from ..colour import Colour, Color
    from ..components import Container as ContainerComponent

V = TypeVar('V', bound='View', covariant=True)

__all__ = ('Container',)


class Container(Item[V]):
    """Represents a Components V2 Container.

    .. versionadded:: 2.6

    Parameters
    ----------
    children: List[:class:`Item`]
        The initial children of this container.
    accent_colour: Optional[:class:`~discord.Colour`]
        The colour of the container. Defaults to ``None``.
    accent_color: Optional[:class:`~discord.Color`]
        The color of the container. Defaults to ``None``.
    spoiler: :class:`bool`
        Whether to flag this container as a spoiler. Defaults
        to ``False``.
    timeout: Optional[:class:`float`]
        The timeout to set to this container items. Defaults to ``180``.
    """

    __discord_ui_container__ = True

    def __init__(
        self,
        children: List[Item[Any]],
        *,
        accent_colour: Optional[Colour] = None,
        accent_color: Optional[Color] = None,
        spoiler: bool = False,
    ) -> None:
        self._children: List[Item[Any]] = children
        self.spoiler: bool = spoiler
        self._colour = accent_colour or accent_color

    @property
    def children(self) -> List[Item[Any]]:
        """List[:class:`Item`]: The children of this container."""
        return self._children.copy()

    @children.setter
    def children(self, value: List[Item[Any]]) -> None:
        self._children = value

    @property
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`~discord.Colour`]: The colour of the container, or ``None``."""
        return self._colour

    @accent_colour.setter
    def accent_colour(self, value: Optional[Colour]) -> None:
        self._colour = value

    accent_color = accent_colour
    """Optional[:class:`~discord.Color`]: The color of the container, or ``None``."""

    @property
    def type(self) -> Literal[ComponentType.container]:
        return ComponentType.container

    def _is_v2(self) -> bool:
        return True

    def to_component_dict(self) -> Dict[str, Any]:
        base = {
            'type': self.type.value,
            'spoiler': self.spoiler,
            'components': [c.to_component_dict() for c in self._children]
        }
        if self._colour is not None:
            base['accent_color'] = self._colour.value
        return base

    @classmethod
    def from_component(cls, component: ContainerComponent) -> Self:
        from .view import _component_to_item
        return cls(
            children=[_component_to_item(c) for c in component.children],
            accent_colour=component.accent_colour,
            spoiler=component.spoiler,
        )
