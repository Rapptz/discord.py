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

from typing import TYPE_CHECKING, List, Literal, Optional, TypeVar, Union

from .item import Item
from ..enums import ComponentType
from ..utils import MISSING
from ..file import File
from ..components import (
    MediaGalleryItem,
    MediaGalleryComponent,
    UnfurledMediaItem,
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('MediaGallery',)


class MediaGallery(Item[V]):
    r"""Represents a UI media gallery.

    Can contain up to 10 :class:`.MediaGalleryItem`\s.

    This is a top-level layout component that can only be used on :class:`LayoutView`.

    .. versionadded:: 2.6

    Parameters
    ----------
    \*items: :class:`.MediaGalleryItem`
        The initial items of this gallery.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __item_repr_attributes__ = (
        'items',
        'id',
    )

    def __init__(
        self,
        *items: MediaGalleryItem,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()

        self._underlying = MediaGalleryComponent._raw_construct(
            items=list(items),
            id=id,
        )

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} items={len(self._underlying.items)}>'

    @property
    def items(self) -> List[MediaGalleryItem]:
        """List[:class:`.MediaGalleryItem`]: Returns a read-only list of this gallery's items."""
        return self._underlying.items.copy()

    @items.setter
    def items(self, value: List[MediaGalleryItem]) -> None:
        if len(value) > 10:
            raise ValueError('media gallery only accepts up to 10 items')

        self._underlying.items = value

    @property
    def id(self) -> Optional[int]:
        """Optional[:class:`int`]: The ID of this component."""
        return self._underlying.id

    @id.setter
    def id(self, value: Optional[int]) -> None:
        self._underlying.id = value

    def to_component_dict(self):
        return self._underlying.to_dict()

    def _is_v2(self) -> bool:
        return True

    def add_item(
        self,
        *,
        media: Union[str, File, UnfurledMediaItem],
        description: Optional[str] = MISSING,
        spoiler: bool = MISSING,
    ) -> Self:
        """Adds an item to this gallery.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        media: Union[:class:`str`, :class:`discord.File`, :class:`.UnfurledMediaItem`]
            The media item data. This can be a string representing a local
            file uploaded as an attachment in the message, which can be accessed
            using the ``attachment://<filename>`` format, or an arbitrary url.
        description: Optional[:class:`str`]
            The description to show within this item. Up to 256 characters. Defaults
            to ``None``.
        spoiler: :class:`bool`
            Whether this item should be flagged as a spoiler. Defaults to ``False``.

        Raises
        ------
        ValueError
            Maximum number of items has been exceeded (10).
        """

        if len(self._underlying.items) >= 10:
            raise ValueError('maximum number of items has been exceeded')

        item = MediaGalleryItem(media, description=description, spoiler=spoiler)
        self._underlying.items.append(item)
        return self

    def append_item(self, item: MediaGalleryItem) -> Self:
        """Appends an item to this gallery.

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
            raise TypeError(f'expected MediaGalleryItem, not {item.__class__.__name__!r}')

        self._underlying.items.append(item)
        return self

    def insert_item_at(
        self,
        index: int,
        *,
        media: Union[str, File, UnfurledMediaItem],
        description: Optional[str] = MISSING,
        spoiler: bool = MISSING,
    ) -> Self:
        """Inserts an item before a specified index to the media gallery.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        index: :class:`int`
            The index of where to insert the field.
        media: Union[:class:`str`, :class:`discord.File`, :class:`.UnfurledMediaItem`]
            The media item data. This can be a string representing a local
            file uploaded as an attachment in the message, which can be accessed
            using the ``attachment://<filename>`` format, or an arbitrary url.
        description: Optional[:class:`str`]
            The description to show within this item. Up to 256 characters. Defaults
            to ``None``.
        spoiler: :class:`bool`
            Whether this item should be flagged as a spoiler. Defaults to ``False``.

        Raises
        ------
        ValueError
            Maximum number of items has been exceeded (10).
        """

        if len(self._underlying.items) >= 10:
            raise ValueError('maximum number of items has been exceeded')

        item = MediaGalleryItem(
            media,
            description=description,
            spoiler=spoiler,
        )
        self._underlying.items.insert(index, item)
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
            *component.items,
            id=component.id,
        )
