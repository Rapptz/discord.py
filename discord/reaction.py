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

from .emoji import Emoji

class Reaction:
    """Represents a reaction to a message.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    Similar to members, the same reaction to a different message are equal.

    Supported Operations:

    +-----------+-------------------------------------------+
    | Operation |               Description                 |
    +===========+===========================================+
    | x == y    | Checks if two reactions are the same.     |
    +-----------+-------------------------------------------+
    | x != y    | Checks if two reactions are not the same. |
    +-----------+-------------------------------------------+
    | hash(x)   | Return the emoji's hash.                  |
    +-----------+-------------------------------------------+

    Attributes
    -----------
    emoji : :class:`Emoji` or str
        The reaction emoji. May be a custom emoji, or a unicode emoji.
    custom_emoji : bool
        If this is a custom emoji.
    count : int
        Number of times this reaction was made
    me : bool
        If the user sent this reaction.
    message: :class:`Message`
        Message this reaction is for.
    """
    __slots__ = ['message', 'count', 'emoji', 'me', 'custom_emoji']

    def __init__(self, **kwargs):
        self.message = kwargs.get('message')
        self.emoji = kwargs['emoji']
        self.count = kwargs.get('count', 1)
        self.me = kwargs.get('me')
        self.custom_emoji = isinstance(self.emoji, Emoji)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.emoji == self.emoji

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True

    def __hash__(self):
        return hash(self.emoji)
