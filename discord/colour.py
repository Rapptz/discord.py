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

import colorsys
import random

from typing import (
    Any,
    Optional, 
    Tuple,
    Type,
    TypeVar,
    Union,
)

__all__ = (
    'Colour',
    'Color',
)

CT = TypeVar('CT', bound='Colour')


class Colour:
    """Represents a Discord role colour. This class is similar
    to a (red, green, blue) :class:`tuple`.

    There is an alias for this called Color.

    .. container:: operations

        .. describe:: x == y

             Checks if two colours are equal.

        .. describe:: x != y

             Checks if two colours are not equal.

        .. describe:: hash(x)

             Return the colour's hash.

        .. describe:: str(x)

             Returns the hex format for the colour.
             
        .. describe:: int(x)

             Returns the raw colour value.

    Attributes
    ------------
    value: :class:`int`
        The raw integer colour value.
    """

    __slots__ = ('value',)

    def __init__(self, value):
        if not isinstance(value, int):
            raise TypeError(f'Expected int parameter, received {value.__class__.__name__} instead.')

        self.value: int = value

    def _get_byte(self, byte: int) -> int:
        return (self.value >> (8 * byte)) & 0xff

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Colour) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return f'#{self.value:0>6x}'
    
    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f'<Colour value={self.value}>'

    def __hash__(self) -> int:
        return hash(self.value)

    @property
    def r(self) -> int:
        """:class:`int`: Returns the red component of the colour."""
        return self._get_byte(2)

    @property
    def g(self) -> int:
        """:class:`int`: Returns the green component of the colour."""
        return self._get_byte(1)

    @property
    def b(self) -> int:
        """:class:`int`: Returns the blue component of the colour."""
        return self._get_byte(0)

    def to_rgb(self) -> Tuple[int, int, int]:
        """Tuple[:class:`int`, :class:`int`, :class:`int`]: Returns an (r, g, b) tuple representing the colour."""
        return (self.r, self.g, self.b)

    @classmethod
    def from_rgb(cls: Type[CT], r: int, g: int, b: int) -> CT:
        """Constructs a :class:`Colour` from an RGB tuple."""
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hsv(cls: Type[CT], h: float, s: float, v: float) -> CT:
        """Constructs a :class:`Colour` from an HSV tuple."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))

    @classmethod
    def default(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0``."""
        return cls(0)

    @classmethod
    def random(cls: Type[CT], *, seed: Optional[Union[int, str, float, bytes, bytearray]] = None) -> CT:
        """A factory method that returns a :class:`Colour` with a random hue.

        .. note::

            The random algorithm works by choosing a colour with a random hue but
            with maxed out saturation and value.

        .. versionadded:: 1.6

        Parameters
        ------------
        seed: Optional[Union[:class:`int`, :class:`str`, :class:`float`, :class:`bytes`, :class:`bytearray`]]
            The seed to initialize the RNG with. If ``None`` is passed the default RNG is used.

            .. versionadded:: 1.7
        """
        rand = random if seed is None else random.Random(seed)
        return cls.from_hsv(rand.random(), 1, 1)

    @classmethod
    def teal(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x1abc9c``."""
        return cls(0x1abc9c)

    @classmethod
    def dark_teal(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x11806a``."""
        return cls(0x11806a)

    @classmethod
    def green(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x2ecc71``."""
        return cls(0x2ecc71)

    @classmethod
    def dark_green(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x1f8b4c``."""
        return cls(0x1f8b4c)

    @classmethod
    def blue(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x3498db``."""
        return cls(0x3498db)

    @classmethod
    def dark_blue(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x206694``."""
        return cls(0x206694)

    @classmethod
    def purple(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x9b59b6``."""
        return cls(0x9b59b6)

    @classmethod
    def dark_purple(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x71368a``."""
        return cls(0x71368a)

    @classmethod
    def magenta(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xe91e63``."""
        return cls(0xe91e63)

    @classmethod
    def dark_magenta(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xad1457``."""
        return cls(0xad1457)

    @classmethod
    def gold(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xf1c40f``."""
        return cls(0xf1c40f)

    @classmethod
    def dark_gold(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xc27c0e``."""
        return cls(0xc27c0e)

    @classmethod
    def orange(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xe67e22``."""
        return cls(0xe67e22)

    @classmethod
    def dark_orange(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xa84300``."""
        return cls(0xa84300)

    @classmethod
    def red(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0xe74c3c``."""
        return cls(0xe74c3c)

    @classmethod
    def dark_red(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x992d22``."""
        return cls(0x992d22)

    @classmethod
    def lighter_grey(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x95a5a6``."""
        return cls(0x95a5a6)

    lighter_gray = lighter_grey

    @classmethod
    def dark_grey(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x607d8b``."""
        return cls(0x607d8b)

    dark_gray = dark_grey

    @classmethod
    def light_grey(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x979c9f``."""
        return cls(0x979c9f)

    light_gray = light_grey

    @classmethod
    def darker_grey(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x546e7a``."""
        return cls(0x546e7a)

    darker_gray = darker_grey

    @classmethod
    def blurple(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x7289da``."""
        return cls(0x7289da)

    @classmethod
    def greyple(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x99aab5``."""
        return cls(0x99aab5)

    @classmethod
    def dark_theme(cls: Type[CT]) -> CT:
        """A factory method that returns a :class:`Colour` with a value of ``0x36393F``.
        This will appear transparent on Discord's dark theme.

        .. versionadded:: 1.5
        """
        return cls(0x36393F)

Color = Colour
