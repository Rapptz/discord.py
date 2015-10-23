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
    def r(self):
        """Returns the red component of the colour."""
        return self._get_byte(2)

    @property
    def g(self):
        """Returns the green component of the colour."""
        return self._get_byte(1)

    @property
    def b(self):
        """Returns the blue component of the colour."""
        return self._get_byte(0)

    def to_tuple(self):
        """Returns an (r, g, b) tuple representing the colour."""
        return (self.r, self.g, self.b)

    @classmethod
    def default(cls):
        """A factory method that returns a :class:`Colour` with a value of 0."""
        return cls(0)

    @classmethod
    def cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x1abc9c."""
        return cls(0x1abc9c)

    @classmethod
    def green(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x2ecc71."""
        return cls(0x2ecc71)

    @classmethod
    def blue(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x3498db."""
        return cls(0x3498db)

    @classmethod
    def purple(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x9b59b6."""
        return cls(0x9b59b6)

    @classmethod
    def yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of 0xf1c40f."""
        return cls(0xf1c40f)

    @classmethod
    def orange(cls):
        """A factory method that returns a :class:`Colour` with a value of 0xe67e22."""
        return cls(0xe67e22)

    @classmethod
    def red(cls):
        """A factory method that returns a :class:`Colour` with a value of 0xe74c3c."""
        return cls(0xe74c3c)

    @classmethod
    def grey(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x95a5a6."""
        return cls(0x95a5a6)

    @classmethod
    def dark_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x7f8c8d."""
        return cls(0x7f8c8d)

    @classmethod
    def navy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x34495e."""
        return cls(0x34495e)

    @classmethod
    def dark_cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x11806a."""
        return cls(0x11806a)

    @classmethod
    def dark_green(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x1f8b4c."""
        return cls(0x1f8b4c)

    @classmethod
    def dark_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x206694."""
        return cls(0x206694)

    @classmethod
    def dark_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x71368a."""
        return cls(0x71368a)

    @classmethod
    def strong_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of 0xc27c0e."""
        return cls(0xc27c0e)

    @classmethod
    def dark_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of 0xa84300."""
        return cls(0xa84300)

    @classmethod
    def dark_red(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x992d22."""
        return cls(0x992d22)

    @classmethod
    def dark_grey_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x979c9f."""
        return cls(0x979c9f)

    @classmethod
    def light_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of 0xbcc0c0."""
        return cls(0xbcc0c0)

    @classmethod
    def dark_navy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of 0x2c3e50."""
        return cls(0x2c3e50)


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
