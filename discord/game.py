# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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

class Game:
    """Represents a Discord game.

    .. container:: operations

        .. describe:: x == y

            Checks if two games are equal.

        .. describe:: x != y

            Checks if two games are not equal.

        .. describe:: hash(x)

            Returns the game's hash.

        .. describe:: str(x)

            Returns the game's name.

    Attributes
    -----------
    name : str
        The game's name.
    url : str
        The game's URL. Usually used for twitch streaming.
    type : int
        The type of game being played. 1 indicates "Streaming".
    """

    __slots__ = ('name', 'type', 'url')

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.url = kwargs.get('url')
        self.type = kwargs.get('type')

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Game name={0.name!r} type={0.type!r} url={0.url!r}>'.format(self)

    def _iterator(self):
        for attr in self.__slots__:
            value = getattr(self, attr, None)
            if value is not None:
                yield (attr, value)

    def __iter__(self):
        return self._iterator()

    def __eq__(self, other):
        return isinstance(other, Game) and other.name == self.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)
