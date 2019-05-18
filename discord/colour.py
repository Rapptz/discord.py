# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

class Colour:
    """Represents a Discord role colour. This class is similar
    to an (red, green, blue) :class:`tuple`.

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

    Attributes
    ------------
    value: :class:`int`
        The raw integer colour value.
    """

    __slots__ = ('value',)

    def __init__(self, value):
        if not isinstance(value, int):
            raise TypeError('Expected int parameter, received %s instead.' % value.__class__.__name__)

        self.value = value

    def _get_byte(self, byte):
        return (self.value >> (8 * byte)) & 0xff

    def __eq__(self, other):
        return isinstance(other, Colour) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '#{:0>6x}'.format(self.value)

    def __repr__(self):
        return '<Colour value=%s>' % self.value

    def __hash__(self):
        return hash(self.value)

    @property
    def r(self):
        """:class:`int`: Returns the red component of the colour."""
        return self._get_byte(2)

    @property
    def g(self):
        """:class:`int`: Returns the green component of the colour."""
        return self._get_byte(1)

    @property
    def b(self):
        """:class:`int`: Returns the blue component of the colour."""
        return self._get_byte(0)

    def to_rgb(self):
        """Tuple[:class:`int`, :class:`int`, :class:`int`]: Returns an (r, g, b) tuple representing the colour."""
        return (self.r, self.g, self.b)

    @classmethod
    def from_rgb(cls, r, g, b):
        """Constructs a :class:`Colour` from an RGB tuple."""
        return cls((r << 16) + (g << 8) + b)

    @classmethod
    def from_hsv(cls, h, s, v):
        """Constructs a :class:`Colour` from an HSV tuple."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(*(int(x * 255) for x in rgb))

    @classmethod
    def default(cls):
        """A factory method that returns a :class:`Colour` with a value of 0."""
        return cls(0)

    @classmethod
    def teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1abc9c``."""
        return cls(0x1abc9c)

    @classmethod
    def dark_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x11806a``."""
        return cls(0x11806a)

    @classmethod
    def green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2ecc71``."""
        return cls(0x2ecc71)

    @classmethod
    def dark_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1f8b4c``."""
        return cls(0x1f8b4c)

    @classmethod
    def blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3498db``."""
        return cls(0x3498db)

    @classmethod
    def dark_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x206694``."""
        return cls(0x206694)

    @classmethod
    def purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9b59b6``."""
        return cls(0x9b59b6)

    @classmethod
    def dark_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x71368a``."""
        return cls(0x71368a)

    @classmethod
    def magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe91e63``."""
        return cls(0xe91e63)

    @classmethod
    def dark_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xad1457``."""
        return cls(0xad1457)

    @classmethod
    def gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf1c40f``."""
        return cls(0xf1c40f)

    @classmethod
    def dark_gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc27c0e``."""
        return cls(0xc27c0e)

    @classmethod
    def orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe67e22``."""
        return cls(0xe67e22)

    @classmethod
    def dark_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa84300``."""
        return cls(0xa84300)

    @classmethod
    def red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe74c3c``."""
        return cls(0xe74c3c)

    @classmethod
    def dark_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x992d22``."""
        return cls(0x992d22)

    @classmethod
    def lighter_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x95a5a6``."""
        return cls(0x95a5a6)

    @classmethod
    def dark_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x607d8b``."""
        return cls(0x607d8b)

    @classmethod
    def light_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x979c9f``."""
        return cls(0x979c9f)

    @classmethod
    def darker_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x546e7a``."""
        return cls(0x546e7a)

    @classmethod
    def blurple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7289da``."""
        return cls(0x7289da)

    @classmethod
    def greyple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x99aab5``."""
        return cls(0x99aab5)

Color = Colour
