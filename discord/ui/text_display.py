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

from typing import TYPE_CHECKING, Literal, TypeVar

from .item import Item
from ..components import TextDisplay as TextDisplayComponent
from ..enums import ComponentType

if TYPE_CHECKING:
    from .view import View

V = TypeVar('V', bound='View', covariant=True)

__all__ = ('TextDisplay',)


class TextDisplay(Item[V]):
    """Represents a UI text display.

    .. versionadded:: 2.6

    Parameters
    ----------
    content: :class:`str`
        The content of this text display.
    """

    def __init__(self, content: str) -> None:
        super().__init__()
        self.content: str = content

        self._underlying = TextDisplayComponent._raw_construct(
            content=content,
        )

    def to_component_dict(self):
        return self._underlying.to_dict()

    @property
    def width(self):
        return 5

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        return self._underlying.type

    def _is_v2(self) -> bool:
        return True
