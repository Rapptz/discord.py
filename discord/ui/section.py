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

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypeVar, Union

from .item import Item
from .text_display import TextDisplay
from ..enums import ComponentType

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import View
    from ..components import SectionComponent

V = TypeVar('V', bound='View', covariant=True)


class Section(Item[V]):
    """Represents a UI section.

    .. versionadded:: 2.6

    Parameters
    ----------
    children: List[Union[:class:`str`, :class:`TextDisplay`]]
        The text displays of this section. Up to 3.
    accessory: Optional[:class:`Item`]
        The section accessory. Defaults to ``None``.
    """

    __slots__ = (
        '_children',
        'accessory',
    )

    def __init__(
        self,
        children: List[Union[Item[Any], str]],
        *,
        accessory: Optional[Item[Any]] = None,
    ) -> None:
        super().__init__()
        if len(children) > 3:
            raise ValueError('maximum number of children exceeded')        
        self._children: List[Item[Any]] = [
            c if isinstance(c, Item) else TextDisplay(c) for c in children
        ]
        self.accessory: Optional[Item[Any]] = accessory

    @property
    def type(self) -> Literal[ComponentType.section]:
        return ComponentType.section

    @property
    def width(self):
        return 5

    def _is_v2(self) -> bool:
        return True

    def add_item(self, item: Union[str, Item[Any]]) -> Self:
        """Adds an item to this section.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: Union[:class:`str`, :class:`TextDisplay`]
            The text display to add.

        Raises
        ------
        TypeError
            A :class:`TextDisplay` was not passed.
        ValueError
            Maximum number of children has been exceeded (3).
        """

        if len(self._children) >= 3:
            raise ValueError('maximum number of children exceeded')

        if not isinstance(item, (Item, str)):
            raise TypeError(f'expected Item or str not {item.__class__.__name__}')

        self._children.append(
            item if isinstance(item, Item) else TextDisplay(item),
        )
        return self

    def remove_item(self, item: Item[Any]) -> Self:
        """Removes an item from this section.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`TextDisplay`
            The item to remove from the section.
        """

        try:
            self._children.remove(item)
        except ValueError:
            pass
        return self

    def clear_items(self) -> Self:
        """Removes all the items from the section.

        This function returns the class instance to allow for fluent-style
        chaining.
        """
        self._children.clear()
        return self

    @classmethod
    def from_component(cls, component: SectionComponent) -> Self:
        from .view import _component_to_item # >circular import<
        return cls(
            children=[_component_to_item(c) for c in component.components],
            accessory=_component_to_item(component.accessory) if component.accessory else None,
        )

    def to_component_dict(self) -> Dict[str, Any]:
        data = {
            'components': [c.to_component_dict() for c in self._children],
            'type': self.type.value,
        }
        if self.accessory:
            data['accessory'] = self.accessory.to_component_dict()
        return data
