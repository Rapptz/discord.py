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

from typing import TYPE_CHECKING, Literal, Optional, TypeVar

from .item import Item
from ..components import TextDisplay as TextDisplayComponent
from ..enums import ComponentType

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('TextDisplay',)


class TextDisplay(Item[V]):
    """Represents a UI text display.

    This is a top-level layout component that can only be used on :class:`LayoutView` or :class:`Section`.

    .. versionadded:: 2.6

    Parameters
    ----------
    content: :class:`str`
        The content of this text display. Up to 4000 characters.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __slots__ = ('content',)

    def __init__(self, content: str, *, id: Optional[int] = None) -> None:
        super().__init__()
        self.content: str = content
        self.id = id

    def to_component_dict(self):
        base = {
            'type': self.type.value,
            'content': self.content,
        }
        if self.id is not None:
            base['id'] = self.id
        return base

    @property
    def width(self):
        return 5

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        return ComponentType.text_display

    def _is_v2(self) -> bool:
        return True

    @classmethod
    def from_component(cls, component: TextDisplayComponent) -> Self:
        return cls(
            content=component.content,
            id=component.id,
        )
