# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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
from .colour import Colour
from .mixins import Hashable
from .utils import snowflake_time

class Role(Hashable):
    """Represents a Discord role in a :class:`Server`.

    Supported Operations:

    +-----------+------------------------------------------------------------------+
    | Operation |                           Description                            |
    +===========+==================================================================+
    | x == y    | Checks if two roles are equal.                                   |
    +-----------+------------------------------------------------------------------+
    | x != y    | Checks if two roles are not equal.                               |
    +-----------+------------------------------------------------------------------+
    | x > y     | Checks if a role is higher than another in the hierarchy.        |
    +-----------+------------------------------------------------------------------+
    | x < y     | Checks if a role is lower than another in the hierarchy.         |
    +-----------+------------------------------------------------------------------+
    | x >= y    | Checks if a role is higher or equal to another in the hierarchy. |
    +-----------+------------------------------------------------------------------+
    | x <= y    | Checks if a role is lower or equal to another in the hierarchy.  |
    +-----------+------------------------------------------------------------------+
    | hash(x)   | Return the role's hash.                                          |
    +-----------+------------------------------------------------------------------+
    | str(x)    | Returns the role's name.                                         |
    +-----------+------------------------------------------------------------------+

    Attributes
    ----------
    id : str
        The ID for the role.
    name : str
        The name of the role.
    permissions : :class:`Permissions`
        Represents the role's permissions.
    server : :class:`Server`
        The server the role belongs to.
    colour : :class:`Colour`
        Represents the role colour. An alias exists under ``color``.
    hoist : bool
         Indicates if the role will be displayed separately from other members.
    position : int
        The position of the role. This number is usually positive. The bottom
        role has a position of 0.
    managed : bool
        Indicates if the role is managed by the server through some form of
        integrations such as Twitch.
    mentionable : bool
        Indicates if the role can be mentioned by users.
    """

    __slots__ = ['id', 'name', 'permissions', 'color', 'colour', 'position',
                 'managed', 'mentionable', 'hoist', 'server' ]

    def __init__(self, **kwargs):
        self.server = kwargs.pop('server')
        self._update(**kwargs)

    def __str__(self):
        return self.name

    def __lt__(self, other):
        if not isinstance(other, Role) or  not isinstance(self, Role):
            return NotImplemented

        if self.server != other.server:
            raise RuntimeError('cannot compare roles from two different servers.')

        if self.position < other.position:
            return True

        if self.position == other.position:
            return int(self.id) > int(other.id)

        return False

    def __le__(self, other):
        r = Role.__lt__(other, self)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def __gt__(self, other):
        return Role.__lt__(other, self)

    def __ge__(self, other):
        r = Role.__lt__(self, other)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def _update(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.permissions = Permissions(kwargs.get('permissions', 0))
        self.position = kwargs.get('position', 0)
        self.colour = Colour(kwargs.get('color', 0))
        self.hoist = kwargs.get('hoist', False)
        self.managed = kwargs.get('managed', False)
        self.mentionable = kwargs.get('mentionable', False)
        self.color = self.colour

    @property
    def is_everyone(self):
        """Checks if the role is the @everyone role."""
        return self.server.id == self.id

    @property
    def created_at(self):
        """Returns the role's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def mention(self):
        """Returns a string that allows you to mention a role."""
        return '<@&{}>'.format(self.id)
