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

from .utils import snowflake_time
from .enums import DefaultAvatar

class User:
    """Represents a Discord user.

    Supported Operations:

    +-----------+---------------------------------------------+
    | Operation |                 Description                 |
    +===========+=============================================+
    | x == y    | Checks if two users are equal.              |
    +-----------+---------------------------------------------+
    | x != y    | Checks if two users are not equal.          |
    +-----------+---------------------------------------------+
    | hash(x)   | Return the user's hash.                     |
    +-----------+---------------------------------------------+
    | str(x)    | Returns the user's name with discriminator. |
    +-----------+---------------------------------------------+

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
    bot : bool
        Specifies if the user is a bot account.
    """

    __slots__ = ['name', 'id', 'discriminator', 'avatar', 'bot']

    def __init__(self, **kwargs):
        self.name = kwargs.get('username')
        self.id = kwargs.get('id')
        self.discriminator = kwargs.get('discriminator')
        self.avatar = kwargs.get('avatar')
        self.bot = kwargs.get('bot', False)

    def __str__(self):
        return '{0.name}#{0.discriminator}'.format(self)

    def __eq__(self, other):
        return isinstance(other, User) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    @property
    def avatar_url(self):
        """Returns a friendly URL version of the avatar variable the user has. An empty string if
        the user has no avatar."""
        if self.avatar is None:
            return ''

        url = 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.{1}?size=1024'
        if self.avatar.startswith('a_'):
            return url.format(self, 'gif')
        else:
            return url.format(self, 'webp')

    @property
    def default_avatar(self):
        """Returns the default avatar for a given user. This is calculated by the user's descriminator"""
        return DefaultAvatar(int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self):
        """Returns a URL for a user's default avatar."""
        return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(self.default_avatar.value)

    @property
    def mention(self):
        """Returns a string that allows you to mention the given user."""
        return '<@{0.id}>'.format(self)

    def permissions_in(self, channel):
        """An alias for :meth:`Channel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python

            channel.permissions_for(self)

        Parameters
        -----------
        channel
            The channel to check your permissions for.
        """
        return channel.permissions_for(self)

    @property
    def created_at(self):
        """Returns the user's creation time in UTC.

        This is when the user's discord account was created."""
        return snowflake_time(self.id)

    @property
    def display_name(self):
        """Returns the user's display name.

        For regular users this is just their username, but
        if they have a server specific nickname then that
        is returned instead.
        """
        return getattr(self, 'nick', None) or self.name

    def mentioned_in(self, message):
        """Checks if the user is mentioned in the specified message.

        Parameters
        -----------
        message : :class:`Message`
            The message to check if you're mentioned in.
        """

        if message.mention_everyone:
            return True

        if self in message.mentions:
            return True

        return False
