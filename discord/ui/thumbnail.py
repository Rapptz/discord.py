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

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import View
    from ..components import ThumbnailComponent

V = TypeVar('V', bound='View', covariant=True)

__all__ = (
    'Thumbnail',
)

class Thumbnail(Item[V]):
    """Represents a UI Thumbnail.

    .. versionadded:: 2.6

    Parameters
    ----------
    media: Union[:class:`str`, :class:`UnfurledMediaItem`]
        The media of the thumbnail. This can be a string that points to a local
        attachment uploaded within this item. URLs must match the ``attachment://file-name.extension``
        structure.
    description: Optional[:class:`str`]
        The description of this thumbnail. Defaults to ``None``.
    spoiler: :class:`bool`
        Whether to flag this thumbnail as a spoiler. Defaults to ``False``.
    """

    def __init__(self, media: Union[str, UnfurledMediaItem], *, description: Optional[str] = None, spoiler: bool = False) -> None:
        self.media: UnfurledMediaItem = UnfurledMediaItem(media) if isinstance(media, str) else media
        self.description: Optional[str] = description
        self.spoiler: bool = spoiler

        self._underlying = ThumbnailComponent._raw_construct()

    @property
    def type(self) -> Literal[ComponentType.thumbnail]:
        return ComponentType.thumbnail

    def _is_v2(self) -> bool:
        return True

    def to_component_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'spoiler': self.spoiler,
            'media': self.media.to_dict(),
            'description': self.description,
        }

    @classmethod
    def from_component(cls, component: ThumbnailComponent) -> Self:
        return cls(
            media=component.media.url,
            description=component.description,
            spoiler=component.spoiler,
        )
