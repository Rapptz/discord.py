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

from typing import TYPE_CHECKING, List, Literal, Optional, TypeVar

from .item import Item
from ..enums import ComponentType
from ..components import (
    MediaGalleryItem,
    MediaGalleryComponent,
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('MediaGallery',)


class MediaGallery(Item[V]):
    """Represents a UI media gallery.

    This can contain up to 10 :class:`.MediaGalleryItem` s.

    .. versionadded:: 2.6

    Parameters
    ----------
    items: List[:class:`.MediaGalleryItem`]
        The initial items of this gallery.
    row: Optional[:class:`int`]
        The relative row this media gallery belongs to. By default
        items are arranged automatically into those rows. If you'd
        like to control the relative positioning of the row then
        passing an index is advised. For example, row=1 will show
        up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 9 (i.e. zero indexed)
    id: Optional[:class:`str`]
        The ID of this component. This must be unique across the view.
    """

    def __init__(
        self,
        items: List[MediaGalleryItem],
        *,
        row: Optional[int] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__()

        self._underlying = MediaGalleryComponent._raw_construct(
            items=items,
        )

        self.row = row
        self.id = id

    @property
    def items(self) -> List[MediaGalleryItem]:
        """List[:class:`.MediaGalleryItem`]: Returns a read-only list of this gallery's items."""
        return self._underlying.items.copy()

    @items.setter
    def items(self, value: List[MediaGalleryItem]) -> None:
        if len(value) > 10:
            raise ValueError('media gallery only accepts up to 10 items')

        self._underlying.items = value

    def to_component_dict(self):
        return self._underlying.to_dict()

    def _is_v2(self) -> bool:
        return True

    def add_item(self, item: MediaGalleryItem) -> Self:
        """Adds an item to this gallery.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`.MediaGalleryItem`
            The item to add to the gallery.

        Raises
        ------
        TypeError
            A :class:`.MediaGalleryItem` was not passed.
        ValueError
            Maximum number of items has been exceeded (10).
        """

        if len(self._underlying.items) >= 10:
            raise ValueError('maximum number of items has been exceeded')

        if not isinstance(item, MediaGalleryItem):
            raise TypeError(f'expected MediaGalleryItem not {item.__class__.__name__}')

        self._underlying.items.append(item)
        return self

    def remove_item(self, item: MediaGalleryItem) -> Self:
        """Removes an item from the gallery.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`.MediaGalleryItem`
            The item to remove from the gallery.
        """

        try:
            self._underlying.items.remove(item)
        except ValueError:
            pass
        return self

    def insert_item_at(self, index: int, item: MediaGalleryItem) -> Self:
        """Inserts an item before a specified index to the gallery.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        index: :class:`int`
            The index of where to insert the item.
        item: :class:`.MediaGalleryItem`
            The item to insert.
        """

        self._underlying.items.insert(index, item)
        return self

    def clear_items(self) -> Self:
        """Removes all items from the gallery.

        This function returns the class instance to allow for fluent-style
        chaining.
        """

        self._underlying.items.clear()
        return self

    @property
    def type(self) -> Literal[ComponentType.media_gallery]:
        return self._underlying.type

    @property
    def width(self):
        return 5

    @classmethod
    def from_component(cls, component: MediaGalleryComponent) -> Self:
        return cls(
            items=component.items,
        )
