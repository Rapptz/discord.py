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
from .colour import Colour

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
