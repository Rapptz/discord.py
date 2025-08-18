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

from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, TypeVar, Union

from .item import Item
from ..enums import ComponentType
from ..components import UnfurledMediaItem
from ..file import File
from ..utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView
    from ..components import ThumbnailComponent

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('Thumbnail',)


class Thumbnail(Item[V]):
    """Represents a UI Thumbnail. This currently can only be used as a :class:`Section`\'s accessory.

    .. versionadded:: 2.6

    Parameters
    ----------
    media: Union[:class:`str`, :class:`discord.File`, :class:`discord.UnfurledMediaItem`]
        The media of the thumbnail. This can be a URL or a reference
        to an attachment that matches the ``attachment://filename.extension``
        structure.
    description: Optional[:class:`str`]
        The description of this thumbnail. Up to 256 characters. Defaults to ``None``.
    spoiler: :class:`bool`
        Whether to flag this thumbnail as a spoiler. Defaults to ``False``.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __slots__ = (
        '_media',
        'description',
        'spoiler',
    )
    __item_repr_attributes__ = (
        'media',
        'description',
        'spoiler',
        'row',
        'id',
    )

    def __init__(
        self,
        media: Union[str, File, UnfurledMediaItem],
        *,
        description: Optional[str] = MISSING,
        spoiler: bool = MISSING,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()

        if isinstance(media, File):
            description = description if description is not MISSING else media.description
            spoiler = spoiler if spoiler is not MISSING else media.spoiler
            media = media.uri

        self._media: UnfurledMediaItem = UnfurledMediaItem(media) if isinstance(media, str) else media
        self.description: Optional[str] = None if description is MISSING else description
        self.spoiler: bool = bool(spoiler)

        self.id = id

    @property
    def width(self):
        return 5

    @property
    def media(self) -> UnfurledMediaItem:
        """:class:`discord.UnfurledMediaItem`: This thumbnail unfurled media data."""
        return self._media

    @media.setter
    def media(self, value: Union[str, File, UnfurledMediaItem]) -> None:
        if isinstance(value, str):
            self._media = UnfurledMediaItem(value)
        elif isinstance(value, UnfurledMediaItem):
            self._media = value
        elif isinstance(value, File):
            self._media = UnfurledMediaItem(value.uri)
        else:
            raise TypeError(f'expected a str or UnfurledMediaItem, not {value.__class__.__name__!r}')

    @property
    def type(self) -> Literal[ComponentType.thumbnail]:
        return ComponentType.thumbnail

    def _is_v2(self) -> bool:
        return True

    def to_component_dict(self) -> Dict[str, Any]:
        base = {
            'type': self.type.value,
            'spoiler': self.spoiler,
            'media': self.media.to_dict(),
            'description': self.description,
        }
        if self.id is not None:
            base['id'] = self.id
        return base

    @classmethod
    def from_component(cls, component: ThumbnailComponent) -> Self:
        return cls(
            media=component.media.url,
            description=component.description,
            spoiler=component.spoiler,
            id=component.id,
        )
