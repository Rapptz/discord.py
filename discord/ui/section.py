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

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypeVar, Union, ClassVar

from .item import Item
from .text_display import TextDisplay
from ..enums import ComponentType
from ..utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView
    from ..components import SectionComponent

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('Section',)


class Section(Item[V]):
    """Represents a UI section.

    .. versionadded:: 2.6

    Parameters
    ----------
    children: List[Union[:class:`str`, :class:`TextDisplay`]]
        The text displays of this section. Up to 3.
    accessory: :class:`Item`
        The section accessory.
    row: Optional[:class:`int`]
        The relative row this section belongs to. By default
        items are arranged automatically into those rows. If you'd
        like to control the relative positioning of the row then
        passing an index is advised. For example, row=1 will show
        up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 9 (i.e. zero indexed)
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __discord_ui_section__: ClassVar[bool] = True

    __slots__ = (
        '_children',
        'accessory',
    )

    def __init__(
        self,
        children: List[Union[Item[Any], str]] = MISSING,
        *,
        accessory: Item[Any],
        row: Optional[int] = None,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._children: List[Item[Any]] = []
        if children is not MISSING:
            if len(children) > 3:
                raise ValueError('maximum number of children exceeded')
            self._children.extend(
                [c if isinstance(c, Item) else TextDisplay(c) for c in children],
            )
        self.accessory: Item[Any] = accessory

        self.row = row
        self.id = id

    @property
    def type(self) -> Literal[ComponentType.section]:
        return ComponentType.section

    @property
    def width(self):
        return 5

    def _is_v2(self) -> bool:
        return True

    # Accessory can be a button, and thus it can have a callback so, maybe
    # allow for section to be dispatchable and make the callback func
    # be accessory component callback, only called if accessory is
    # dispatchable?
    def is_dispatchable(self) -> bool:
        if self.accessory:
            return self.accessory.is_dispatchable()
        return False

    def add_item(self, item: Union[str, Item[Any]]) -> Self:
        """Adds an item to this section.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: Union[:class:`str`, :class:`Item`]
            The items to append, if it is a string it automatically wrapped around
            :class:`TextDisplay`.

        Raises
        ------
        TypeError
            An :class:`Item` or :class:`str` was not passed.
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
        from .view import _component_to_item  # >circular import<

        return cls(
            children=[_component_to_item(c) for c in component.components],
            accessory=_component_to_item(component.accessory),
            id=component.id,
        )

    def to_component_dict(self) -> Dict[str, Any]:
        data = {
            'type': self.type.value,
            'components': [c.to_component_dict() for c in self._children],
            'accessory': self.accessory.to_component_dict(),
        }
        if self.id is not None:
            data['id'] = self.id
        return data
