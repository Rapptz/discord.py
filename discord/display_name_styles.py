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

from typing import TYPE_CHECKING, List

from .colour import Colour
from .enums import DisplayNameFont, DisplayNameEffect, try_enum

if TYPE_CHECKING:
    from .types.user import DisplayNameStyles as DisplayNameStylesPayload

# fmt: off
__all__ = (
    'DisplayNameStyles',
)
# fmt: on


class DisplayNameStyles:
    """Represents the display name style of a :class:`User`.

    .. versionadded:: 2.7

    Attributes
    -----------
    font_type: :class:`~discord.DisplayNameFontType`
        The type of the display name font.
    effect_type: :class:`~discord.DisplayNameEffectType`
        The type of the display name effect.
    colors: List[:class:`Colour`]
        A list of the colors that the display name style is consisted of. It may be either a singular color or multiple colors.
    """

    __slots__ = ('font', 'effect', 'colors')

    def __init__(self, *, data: DisplayNameStylesPayload) -> None:
        self._update(data)

    def _update(self, data: DisplayNameStylesPayload):
        self.font: DisplayNameFont = try_enum(DisplayNameFont, data['font_id'])
        self.effect: DisplayNameEffect = try_enum(DisplayNameEffect, data['effect_id'])
        self.colors: List[Colour] = [Colour(c) for c in data.get('colors', [])]

    def __repr__(self) -> str:
        return f'<DisplayNameStyle font={self.font} effect={self.effect} colors={self.colors}>'
