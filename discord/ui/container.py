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

from typing import TYPE_CHECKING, Any, ClassVar, Coroutine, Dict, List, Literal, Optional, Tuple, Type, TypeVar, Union

from .item import Item, ItemCallbackType
from .view import _component_to_item, LayoutView
from .dynamic import DynamicItem
from ..enums import ComponentType
from ..utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..colour import Colour, Color
    from ..components import Container as ContainerComponent
    from ..interactions import Interaction

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('Container',)


class _ContainerCallback:
    __slots__ = ('container', 'callback', 'item')

    def __init__(self, callback: ItemCallbackType[Any, Any], container: Container, item: Item[Any]) -> None:
        self.callback: ItemCallbackType[Any, Any] = callback
        self.container: Container = container
        self.item: Item[Any] = item

    def __call__(self, interaction: Interaction) -> Coroutine[Any, Any, Any]:
        return self.callback(self.container, interaction, self.item)


class Container(Item[V]):
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
    row: Optional[:class:`int`]
        The relative row this container belongs to. By default
        items are arranged automatically into those rows. If you'd
        like to control the relative positioning of the row then
        passing an index is advised. For example, row=1 will show
        up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 9 (i.e. zero indexed)
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __container_children_items__: ClassVar[List[Union[ItemCallbackType[Any, Any], Item[Any]]]] = []
    __pending_view__: ClassVar[bool] = True
    __discord_ui_container__: ClassVar[bool] = True

    def __init__(
        self,
        children: List[Item[V]] = MISSING,
        *,
        accent_colour: Optional[Colour] = None,
        accent_color: Optional[Color] = None,
        spoiler: bool = False,
        row: Optional[int] = None,
        id: Optional[int] = None,
    ) -> None:
        self._children: List[Item[V]] = self._init_children()

        if children is not MISSING:
            if len(children) + len(self._children) > 10:
                raise ValueError('maximum number of children exceeded')
        self.spoiler: bool = spoiler
        self._colour = accent_colour or accent_color

        self._view: Optional[V] = None
        self.row = row
        self.id = id

    def _init_children(self) -> List[Item[Any]]:
        children = []

        for raw in self.__container_children_items__:
            if isinstance(raw, Item):
                children.append(raw)
            else:
                # action rows can be created inside containers, and then callbacks can exist here
                # so we create items based off them
                item: Item = raw.__discord_ui_model_type__(**raw.__discord_ui_model_kwargs__)
                item.callback = _ContainerCallback(raw, self, item)  # type: ignore
                setattr(self, raw.__name__, item)
                # this should not fail because in order for a function to be here it should be from
                # an action row and must have passed the check in __init_subclass__, but still
                # guarding it
                parent = getattr(raw, '__discord_ui_parent__', None)
                if parent is None:
                    raise RuntimeError(f'{raw.__name__} is not a valid item for a Container')
                parent._children.append(item)
                # we donnot append it to the children list because technically these buttons and
                # selects are not from the container but the action row itself.

        return children

    def is_dispatchable(self) -> bool:
        return True

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, Union[ItemCallbackType[Any, Any], Item[Any]]] = {}
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if isinstance(member, Item):
                    children[name] = member
                if hasattr(member, '__discord_ui_model_type__') and getattr(member, '__discord_ui_parent__', None):
                    children[name] = member

        cls.__container_children_items__ = list(children.values())

    def _update_children_view(self, view) -> None:
        for child in self._children:
            child._view = view
            if getattr(child, '__pending_view__', False):
                # if the item is an action row which child's view can be updated, then update it
                child._update_children_view(view)  # type: ignore

    @property
    def children(self) -> List[Item[V]]:
        """List[:class:`Item`]: The children of this container."""
        return self._children.copy()

    @children.setter
    def children(self, value: List[Item[V]]) -> None:
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

    def to_components(self) -> List[Dict[str, Any]]:
        components = []
        for child in self._children:
            components.append(child.to_component_dict())
        return components

    def to_component_dict(self) -> Dict[str, Any]:
        components = self.to_components()
        base = {
            'type': self.type.value,
            'accent_color': self._colour.value if self._colour else None,
            'spoiler': self.spoiler,
            'components': components,
        }
        if self.id is not None:
            base['id'] = self.id
        return base

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
            id=component.id,
        )
