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

class User(object):
    """Represents a Discord user.

    Supported Operations:

    +-----------+------------------------------------+
    | Operation |            Description             |
    +===========+====================================+
    | x == y    | Checks if two users are equal.     |
    +-----------+------------------------------------+
    | x != y    | Checks if two users are not equal. |
    +-----------+------------------------------------+
    | str(x)    | Returns the user's name.           |
    +-----------+------------------------------------+

    Attributes
    -----------
    name : str
        The user's username.
    id : str
        The user's unique ID.
    discriminator : str or int
        The user's discriminator. This is given when the username has conflicts.
    avatar : str
        The avatar hash the user has. Could be None.
    """

    def __init__(self, username, id, discriminator, avatar, **kwargs):
        self.name = username
        self.id = id
        self.discriminator = discriminator
        self.avatar = avatar

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, User) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def avatar_url(self):
        """Returns a friendly URL version of the avatar variable the user has. An empty string if
        the user has no avatar."""
        if self.avatar is None:
            return ''
        return 'https://discordapp.com/api/users/{0.id}/avatars/{0.avatar}.jpg'.format(self)

    @property
    def mention(self):
        """Returns a string that allows you to mention the given user."""
        return '<@{0.id}>'.format(self)

