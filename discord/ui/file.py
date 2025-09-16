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

from typing import TYPE_CHECKING, Literal, Optional, TypeVar, Union


from .item import Item
from ..components import FileComponent, UnfurledMediaItem
from ..enums import ComponentType
from ..utils import MISSING
from ..file import File as SendableFile

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('File',)


class File(Item[V]):
    """Represents a UI file component.

    This is a top-level layout component that can only be used on :class:`LayoutView`.

    .. versionadded:: 2.6

    Example
    -------

    .. code-block:: python3

        import discord
        from discord import ui

        class MyView(ui.LayoutView):
            file = ui.File('attachment://file.txt')
            # attachment://file.txt points to an attachment uploaded alongside this view

    Parameters
    ----------
    media: Union[:class:`str`, :class:`.UnfurledMediaItem`, :class:`discord.File`]
        This file's media. If this is a string it must point to a local
        file uploaded within the parent view of this item, and must
        meet the ``attachment://<filename>`` format.
    spoiler: :class:`bool`
        Whether to flag this file as a spoiler. Defaults to ``False``.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __item_repr_attributes__ = (
        'media',
        'spoiler',
        'id',
    )

    def __init__(
        self,
        media: Union[str, UnfurledMediaItem, SendableFile],
        *,
        spoiler: bool = MISSING,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        if isinstance(media, SendableFile):
            self._underlying = FileComponent._raw_construct(
                media=UnfurledMediaItem(media.uri),
                spoiler=media.spoiler if spoiler is MISSING else spoiler,
                id=id,
            )
        else:
            self._underlying = FileComponent._raw_construct(
                media=UnfurledMediaItem(media) if isinstance(media, str) else media,
                spoiler=bool(spoiler),
                id=id,
            )
        self.id = id

    def _is_v2(self):
        return True

    @property
    def width(self):
        return 5

    @property
    def type(self) -> Literal[ComponentType.file]:
        return self._underlying.type

    @property
    def media(self) -> UnfurledMediaItem:
        """:class:`.UnfurledMediaItem`: Returns this file media."""
        return self._underlying.media

    @media.setter
    def media(self, value: Union[str, SendableFile, UnfurledMediaItem]) -> None:
        if isinstance(value, str):
            self._underlying.media = UnfurledMediaItem(value)
        elif isinstance(value, UnfurledMediaItem):
            self._underlying.media = value
        elif isinstance(value, SendableFile):
            self._underlying.media = UnfurledMediaItem(value.uri)
        else:
            raise TypeError(f'expected a str or UnfurledMediaItem or File, not {value.__class__.__name__!r}')

    @property
    def url(self) -> str:
        """:class:`str`: Returns this file's url."""
        return self._underlying.media.url

    @url.setter
    def url(self, value: str) -> None:
        self._underlying.media = UnfurledMediaItem(value)

    @property
    def spoiler(self) -> bool:
        """:class:`bool`: Returns whether this file should be flagged as a spoiler."""
        return self._underlying.spoiler

    @spoiler.setter
    def spoiler(self, value: bool) -> None:
        self._underlying.spoiler = value

    def to_component_dict(self):
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: FileComponent) -> Self:
        return cls(
            media=component.media,
            spoiler=component.spoiler,
            id=component.id,
        )
