# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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

from .permissions import Permissions

def create_colour_constants(cls):
    cls.DEFAULT        = cls(0)
    cls.CYAN           = cls(0x1abc9c)
    cls.GREEN          = cls(0x2ecc71)
    cls.BLUE           = cls(0x3498db)
    cls.PURPLE         = cls(0x9b59b6)
    cls.YELLOW         = cls(0xf1c40f)
    cls.ORANGE         = cls(0xe67e22)
    cls.RED            = cls(0xe74c3c)
    cls.GREY           = cls(0x95a5a6)
    cls.DARK_GREY      = cls(0x7f8c8d)
    cls.NAVY_BLUE      = cls(0x34495e)
    cls.DARK_CYAN      = cls(0x11806a)
    cls.DARK_GREEN     = cls(0x1f8b4c)
    cls.DARK_BLUE      = cls(0x206694)
    cls.DARK_PURPLE    = cls(0x71368a)
    cls.STRONG_ORANGE  = cls(0xc27c0e)
    cls.DARK_ORANGE    = cls(0xa84300)
    cls.DARK_RED       = cls(0x992d22)
    cls.DARK_GREY_BLUE = cls(0x979c9f)
    cls.LIGHT_GREY     = cls(0xbcc0c0)
    cls.DARK_NAVY_BLUE = cls(0x2c3e50)
    return cls

@create_colour_constants
class Colour(object):
    """Represents a Discord role colour. This class is similar
    to an (red, green, blue) tuple.

    There is an alias for this called Color.

    Supported operations:

    +-----------+--------------------------------------+
    | Operation |             Description              |
    +===========+======================================+
    | x == y    | Checks if two colours are equal.     |
    +-----------+--------------------------------------+
    | x != y    | Checks if two colours are not equal. |
    +-----------+--------------------------------------+

    Class attributes:

    .. attribute:: DEFAULT

        A constant representing the equivalent of ``Colour(0)``.
    .. attribute:: CYAN

        A constant representing the equivalent of ``Colour(0x1abc9c)``.
    .. attribute:: GREEN

        A constant representing the equivalent of ``Colour(0x2ecc71)``.
    .. attribute:: BLUE

        A constant representing the equivalent of ``Colour(0x3498db)``.
    .. attribute:: PURPLE

        A constant representing the equivalent of ``Colour(0x9b59b6)``.
    .. attribute:: YELLOW

        A constant representing the equivalent of ``Colour(0xf1c40f)``.
    .. attribute:: ORANGE

        A constant representing the equivalent of ``Colour(0xe67e22)``.
    .. attribute:: RED

        A constant representing the equivalent of ``Colour(0xe74c3c)``.
    .. attribute:: GREY

        A constant representing the equivalent of ``Colour(0x95a5a6)``.
    .. attribute:: DARK_GREY

        A constant representing the equivalent of ``Colour(0x7f8c8d)``.
    .. attribute:: NAVY_BLUE

        A constant representing the equivalent of ``Colour(0x34495e)``.
    .. attribute:: DARK_CYAN

        A constant representing the equivalent of ``Colour(0x11806a)``.
    .. attribute:: DARK_GREEN

        A constant representing the equivalent of ``Colour(0x1f8b4c)``.
    .. attribute:: DARK_BLUE

        A constant representing the equivalent of ``Colour(0x206694)``.
    .. attribute:: DARK_PURPLE

        A constant representing the equivalent of ``Colour(0x71368a)``.
    .. attribute:: STRONG_ORANGE

        A constant representing the equivalent of ``Colour(0xc27c0e)``.
    .. attribute:: DARK_ORANGE

        A constant representing the equivalent of ``Colour(0xa84300)``.
    .. attribute:: DARK_RED

        A constant representing the equivalent of ``Colour(0x992d22)``.
    .. attribute:: DARK_GREY_BLUE

        A constant representing the equivalent of ``Colour(0x979c9f)``.
    .. attribute:: LIGHT_GREY

        A constant representing the equivalent of ``Colour(0xbcc0c0)``.
    .. attribute:: DARK_NAVY_BLUE

        A constant representing the equivalent of ``Colour(0x2c3e50)``.

    Instance attributes:

    .. attribute:: value

        The raw integer colour value.
    """

    def __init__(self, value):
        self.value = value

    def _get_byte(self, byte):
        return (self.value >> (8 * byte)) & 0xff

    def __eq__(self, other):
        return self.value == getattr(other, 'value', None)

    def __ne__(self, other):
        return isinstance(other, Colour) and self.value != other.value

    @property
    def red(self):
        """Returns the red component of the colour."""
        return self._get_byte(2)

    @property
    def green(self):
        """Returns the green component of the colour."""
        return self._get_byte(1)

    @property
    def blue(self):
        """Returns the blue component of the colour."""
        return self._get_byte(0)

    def to_tuple(self):
        """Returns an (r, g, b) tuple representing the colour."""
        return (self.red, self.green, self.blue)


Color = Colour

class Role(object):
    """Represents a Discord role in a :class:`Server`.

    Instance attributes:

    .. attribute:: id

        The ID for the role.
    .. attribute:: name

        The name of the role.
    .. attribute:: permissions

        A :class:`Permissions` that represents the role's permissions.
    .. attribute:: color
                   colour

        A :class:`Colour` representing the role colour.
    .. attribute:: hoist

        A boolean representing if the role will be displayed separately from other members.
    .. attribute:: position

        The position of the role. This number is usually positive.
    .. attribute:: managed

        A boolean indicating if the role is managed by the server through some form of integration
        such as Twitch.
    """

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.permissions = Permissions(kwargs.get('permissions', 0))
        self.position = kwargs.get('position', 0)
        self.colour = Colour(kwargs.get('color', 0))
        self.hoist = kwargs.get('hoist', False)
        self.managed = kwargs.get('managed', False)
        self.color = self.colour
        self._is_everyone = kwargs.get('everyone', False)

    def is_everyone(self):
        """Checks if the role is the @everyone role."""
        return self.position == -1
