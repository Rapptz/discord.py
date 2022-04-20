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

import colorsys
import random
import re

from typing import TYPE_CHECKING, Optional, Tuple, Union

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    'Colour',
    'Color',
)

RGB_REGEX = re.compile(r'rgb\s*\((?P<r>[0-9.]+%?)\s*,\s*(?P<g>[0-9.]+%?)\s*,\s*(?P<b>[0-9.]+%?)\s*\)')


def parse_hex_number(argument: str) -> Colour:
    arg = ''.join(i * 2 for i in argument) if len(argument) == 3 else argument
    try:
        value = int(arg, base=16)
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError('hex number out of range for 24-bit colour')
    except ValueError:
        raise ValueError('invalid hex digit given') from None
    else:
        return Color(value=value)


def parse_rgb_number(number: str) -> int:
    if number[-1] == '%':
        value = float(number[:-1])
        if not (0 <= value <= 100):
            raise ValueError('rgb percentage can only be between 0 to 100')
        return round(255 * (value / 100))

    value = int(number)
    if not (0 <= value <= 255):
        raise ValueError('rgb number can only be between 0 to 255')
    return value


def parse_rgb(argument: str, *, regex: re.Pattern[str] = RGB_REGEX) -> Colour:
    match = regex.match(argument)
    if match is None:
        raise ValueError('invalid rgb syntax found')

    red = parse_rgb_number(match.group('r'))
    green = parse_rgb_number(match.group('g'))
    blue = parse_rgb_number(match.group('b'))
    return Color.from_rgb(red, green, blue)


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

    def __init__(self, value: int):
        if not isinstance(value, int):
            raise TypeError(f'Expected int parameter, received {value.__class__.__name__} instead.')

        self.value: int = value

    def _get_byte(self, byte: int) -> int:
        return (self.value >> (8 * byte)) & 0xFF

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Colour) and self.value == other.value

    def __ne__(self, other: object) -> bool:
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
    def from_rgb(cls, r: int, g: int, b: int) -> Self:
        """Constructs a :class:`Colour` from an RGB tuple."""
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> Self:
        """Constructs a :class:`Colour` from an HSV tuple."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Constructs a :class:`Colour` from a string.

        The following formats are accepted:

        - ``0x<hex>``
        - ``#<hex>``
        - ``0x#<hex>``
        - ``rgb(<number>, <number>, <number>)``

        Like CSS, ``<number>`` can be either 0-255 or 0-100% and ``<hex>`` can be
        either a 6 digit hex number or a 3 digit hex shortcut (e.g. #fff).

        .. versionadded:: 2.0

        Raises
        -------
        ValueError
            The string could not be converted into a colour.
        """

        if value[0] == '#':
            return parse_hex_number(value[1:])

        if value[0:2] == '0x':
            rest = value[2:]
            # Legacy backwards compatible syntax
            if rest.startswith('#'):
                return parse_hex_number(rest[1:])
            return parse_hex_number(rest)

        arg = value.lower()
        if arg[0:3] == 'rgb':
            return parse_rgb(arg)

        raise ValueError('unknown colour format given')

    @classmethod
    def default(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0``."""
        return cls(0)

    @classmethod
    def random(cls, *, seed: Optional[Union[int, str, float, bytes, bytearray]] = None) -> Self:
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
    def teal(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x1abc9c``."""
        return cls(0x1ABC9C)

    @classmethod
    def dark_teal(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x11806a``."""
        return cls(0x11806A)

    @classmethod
    def brand_green(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x57F287``.

        .. versionadded:: 2.0
        """
        return cls(0x57F287)

    @classmethod
    def green(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x2ecc71``."""
        return cls(0x2ECC71)

    @classmethod
    def dark_green(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x1f8b4c``."""
        return cls(0x1F8B4C)

    @classmethod
    def blue(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x3498db``."""
        return cls(0x3498DB)

    @classmethod
    def dark_blue(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x206694``."""
        return cls(0x206694)

    @classmethod
    def purple(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x9b59b6``."""
        return cls(0x9B59B6)

    @classmethod
    def dark_purple(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x71368a``."""
        return cls(0x71368A)

    @classmethod
    def magenta(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xe91e63``."""
        return cls(0xE91E63)

    @classmethod
    def dark_magenta(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xad1457``."""
        return cls(0xAD1457)

    @classmethod
    def gold(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xf1c40f``."""
        return cls(0xF1C40F)

    @classmethod
    def dark_gold(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xc27c0e``."""
        return cls(0xC27C0E)

    @classmethod
    def orange(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xe67e22``."""
        return cls(0xE67E22)

    @classmethod
    def dark_orange(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xa84300``."""
        return cls(0xA84300)

    @classmethod
    def brand_red(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xED4245``.

        .. versionadded:: 2.0
        """
        return cls(0xED4245)

    @classmethod
    def red(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xe74c3c``."""
        return cls(0xE74C3C)

    @classmethod
    def dark_red(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x992d22``."""
        return cls(0x992D22)

    @classmethod
    def lighter_grey(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x95a5a6``."""
        return cls(0x95A5A6)

    lighter_gray = lighter_grey

    @classmethod
    def dark_grey(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x607d8b``."""
        return cls(0x607D8B)

    dark_gray = dark_grey

    @classmethod
    def light_grey(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x979c9f``."""
        return cls(0x979C9F)

    light_gray = light_grey

    @classmethod
    def darker_grey(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x546e7a``."""
        return cls(0x546E7A)

    darker_gray = darker_grey

    @classmethod
    def og_blurple(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x7289da``."""
        return cls(0x7289DA)

    @classmethod
    def blurple(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x5865F2``."""
        return cls(0x5865F2)

    @classmethod
    def greyple(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x99aab5``."""
        return cls(0x99AAB5)

    @classmethod
    def dark_theme(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0x36393F``.
        This will appear transparent on Discord's dark theme.

        .. versionadded:: 1.5
        """
        return cls(0x36393F)

    @classmethod
    def fuchsia(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xEB459E``.

        .. versionadded:: 2.0
        """
        return cls(0xEB459E)

    @classmethod
    def yellow(cls) -> Self:
        """A factory method that returns a :class:`Colour` with a value of ``0xFEE75C``.

        .. versionadded:: 2.0
        """
        return cls(0xFEE75C)


Color = Colour
