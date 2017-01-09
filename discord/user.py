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

import discord.abc
import asyncio

class User(discord.abc.Messageable):
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
    name: str
        The user's username.
    id: int
        The user's unique ID.
    discriminator: str
        The user's discriminator. This is given when the username has conflicts.
    avatar: str
        The avatar hash the user has. Could be None.
    bot: bool
        Specifies if the user is a bot account.
    """

    __slots__ = ('name', 'id', 'discriminator', 'avatar', 'bot', '_state', '__weakref__')

    def __init__(self, *, state, data):
        self._state = state
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self.avatar = data['avatar']
        self.bot = data.get('bot', False)

    def __str__(self):
        return '{0.name}#{0.discriminator}'.format(self)

    def __eq__(self, other):
        return isinstance(other, User) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return '<User id={0.id} name={0.name!r} discriminator={0.discriminator!r} bot={0.bot}>'.format(self)

    @asyncio.coroutine
    def _get_channel(self):
        ch = yield from self.create_dm()
        return ch

    def _get_guild_id(self):
        return None

    @property
    def dm_channel(self):
        """Returns the :class:`DMChannel` associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @asyncio.coroutine
    def create_dm(self):
        """Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data = yield from state.http.start_private_message(self.id)
        return state.add_dm_channel(data)

    @property
    def avatar_url(self):
        """Returns a friendly URL version of the avatar the user has.

        If the user does not have a traditional avatar, their default
        avatar URL is returned instead.
        """
        if self.avatar is None:
            return self.default_avatar_url

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
        if they have a guild specific nickname then that
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
