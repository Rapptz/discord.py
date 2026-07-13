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

from typing import List, Sequence, Union, TYPE_CHECKING
from .enums import BaseTheme, try_enum
from .colour import Colour
from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.message import SharedClientTheme as SharedClientThemePayload


__all__ = ('SharedClientTheme',)


class SharedClientTheme:
    """Represents a shared client theme from a :class:`~discord.Message`.

    This can be constructed by users to create a new shared client theme for sending and
    is received using :attr:`Message.shared_client_theme` when a message contains a shared client theme.

    .. versionadded:: 2.8

    Parameters
    -----------
    colours: Sequence[Union[:class:`Colour`, :class:`int`]]
        An iterable of the theme's colours. Must be between 1 and 5 colours.
    colors: Sequence[Union[:class:`Colour`, :class:`int`]]
        An alias for ``colours``.
    gradient_angle: :class:`int`
        The direction of the theme's gradient in degrees. Must be between 0 and 360.
        This is only applicable if there are at least 2 colours.
    intensity: :class:`int`
        The intensity of the theme's colors. Must be between 0 and 100.
    theme: :class:`BaseTheme`
        The base theme to use for this client theme. Defaults to :attr:`BaseTheme.dark`.

    Raises
    -------
    ValueError
        - If the number of colours is not between 1 and 5.
        - If ``colours`` is empty.
        - If ``colours`` contains more than 5 colours.
        - If ``gradient_angle`` is set but there are less than 2 colours.
        - If ``gradient_angle`` is not between 0 and 360.
        - If ``intensity`` is not between 0 and 100.
        - If ``theme`` is not an instance of :class:`BaseTheme`.
    """

    __slots__ = ('_colours', '_gradient_angle', '_intensity', '_theme')

    def __init__(
        self,
        *,
        colours: Sequence[Union[Colour, int]] = MISSING,
        colors: Sequence[Union[Colour, int]] = MISSING,
        gradient_angle: int = 0,
        intensity: int = 0,
        theme: BaseTheme = BaseTheme.dark,
    ) -> None:
        self.colours = colours if colours is not MISSING else colors
        self.gradient_angle = gradient_angle
        self.intensity = intensity
        self.theme = theme

    @classmethod
    def from_dict(cls, data: SharedClientThemePayload) -> Self:
        """Creates a :class:`SharedClientTheme` from a dictionary.

        Possible keys can be found in the
        :ddocs:`api docs <resources/message#shared-client-theme-object>`.
        """
        return cls(
            colours=[Colour(int(colour, 16)) for colour in data.get('colors', [])],
            gradient_angle=data.get('gradient_angle', 0),
            intensity=data.get('base_mix', 0),
            theme=try_enum(BaseTheme, data.get('base_theme', 'dark')),
        )

    def to_dict(self) -> SharedClientThemePayload:
        return {
            'colors': [str(colour).lstrip('#') for colour in self._colours],
            'gradient_angle': self.gradient_angle,
            'base_mix': self.intensity,
            'base_theme': self.theme.value,
        }

    def __repr__(self) -> str:
        return f'<SharedClientTheme colours={self.colours!r} gradient_angle={self.gradient_angle} intensity={self.intensity} theme={self.theme!r}>'

    @property
    def colours(self) -> List[Colour]:
        """List[:class:`Colour`]: A list of the theme's colours."""
        return self._colours

    colors = colours

    @colours.setter
    def colours(self, value: Sequence[Union[Colour, int]]) -> None:
        if not value:
            raise ValueError('colours cannot be empty')

        if len(value) > 5:
            raise ValueError('cannot have more than 5 colours')

        if len(value) < 2:
            self.intensity = 0

        self._colours = [colour if isinstance(colour, Colour) else Colour(colour) for colour in value]

    @property
    def gradient_angle(self) -> int:
        """:class:`int`: The direction of the theme's gradient in degrees.

        This is only applicable if there are at least 2 colours.
        """
        return self._gradient_angle

    @gradient_angle.setter
    def gradient_angle(self, value: int) -> None:
        if len(self.colours) < 2 and value != 0:
            raise ValueError('gradient_angle may only be set if there are at least 2 colours')

        if not 0 <= value <= 360:
            raise ValueError('gradient_angle must be between 0 and 360')
        self._gradient_angle = value

    @property
    def intensity(self) -> int:
        """:class:`int`: The intensity of the theme's colors."""
        return self._intensity

    @intensity.setter
    def intensity(self, value: int) -> None:
        if not 0 <= value <= 100:
            raise ValueError('intensity must be between 0 and 100')
        self._intensity = value

    @property
    def theme(self) -> BaseTheme:
        """:class:`BaseTheme`: The base theme to use for this client theme."""
        if not isinstance(self._theme, BaseTheme):
            raise ValueError('theme must be an instance of BaseTheme')

        return self._theme

    @theme.setter
    def theme(self, value: BaseTheme) -> None:
        if not isinstance(value, BaseTheme):
            raise ValueError('theme must be an instance of BaseTheme')
        self._theme = value
