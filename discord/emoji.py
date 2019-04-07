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

from .asset import Asset
from . import utils
from .user import User

class PartialEmoji:
    """Represents a "partial" emoji.

    This model will be given in two scenarios:

    - "Raw" data events such as :func:`on_raw_reaction_add`
    - Custom emoji that the bot cannot see from e.g. :attr:`Message.reactions`

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    -----------
    name: :class:`str`
        The custom emoji name, if applicable, or the unicode codepoint
        of the non-custom emoji.
    animated: :class:`bool`
        Whether the emoji is animated or not.
    id: Optional[:class:`int`]
        The ID of the custom emoji, if applicable.
    """

    __slots__ = ('animated', 'name', 'id', '_state')

    def __init__(self, *, animated, name, id=None):
        self.animated = animated
        self.name = name
        self.id = id
        self._state = None

    @classmethod
    def with_state(cls, state, *, animated, name, id=None):
        self = cls(animated=animated, name=name, id=id)
        self._state = state
        return self

    def __str__(self):
        if self.id is None:
            return self.name
        if self.animated:
            return '<a:%s:%s>' % (self.name, self.id)
        return '<:%s:%s>' % (self.name, self.id)

    def __eq__(self, other):
        if self.is_unicode_emoji():
            return isinstance(other, PartialEmoji) and self.name == other.name

        if isinstance(other, (PartialEmoji, Emoji)):
            return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.id, self.name))

    def is_custom_emoji(self):
        """Checks if this is a custom non-Unicode emoji."""
        return self.id is not None

    def is_unicode_emoji(self):
        """Checks if this is a Unicode emoji."""
        return self.id is None

    def _as_reaction(self):
        if self.id is None:
            return self.name
        return '%s:%s' % (self.name, self.id)

    @property
    def url(self):
        """:class:`Asset`:Returns an asset of the emoji, if it is custom."""
        if self.is_unicode_emoji():
            return Asset(self._state)

        _format = 'gif' if self.animated else 'png'
        url = "https://cdn.discordapp.com/emojis/{0.id}.{1}".format(self, _format)
        return Asset(self._state, url)

class Emoji:
    """Represents a custom emoji.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    -----------
    name: :class:`str`
        The name of the emoji.
    id: :class:`int`
        The emoji's ID.
    require_colons: :class:`bool`
        If colons are required to use this emoji in the client (:PJSalt: vs PJSalt).
    animated: :class:`bool`
        Whether an emoji is animated or not.
    managed: :class:`bool`
        If this emoji is managed by a Twitch integration.
    guild_id: :class:`int`
        The guild ID the emoji belongs to.
    user: Optional[:class:`User`]
        The user that created the emoji. This can only be retrieved using :meth:`Guild.fetch_emoji`.
    """
    __slots__ = ('require_colons', 'animated', 'managed', 'id', 'name', '_roles', 'guild_id',
                 '_state', 'user')

    def __init__(self, *, guild, state, data):
        self.guild_id = guild.id
        self._state = state
        self._from_data(data)

    def _from_data(self, emoji):
        self.require_colons = emoji['require_colons']
        self.managed = emoji['managed']
        self.id = int(emoji['id'])
        self.name = emoji['name']
        self.animated = emoji.get('animated', False)
        self._roles = utils.SnowflakeList(map(int, emoji.get('roles', [])))
        user = emoji.get('user')
        self.user = User(state=self._state, data=user) if user else None

    def _iterator(self):
        for attr in self.__slots__:
            if attr[0] != '_':
                value = getattr(self, attr, None)
                if value is not None:
                    yield (attr, value)

    def __iter__(self):
        return self._iterator()

    def __str__(self):
        if self.animated:
            return '<a:{0.name}:{0.id}>'.format(self)
        return "<:{0.name}:{0.id}>".format(self)

    def __repr__(self):
        return '<Emoji id={0.id} name={0.name!r}>'.format(self)

    def __eq__(self, other):
        return isinstance(other, (PartialEmoji, Emoji)) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.id >> 22

    @property
    def created_at(self):
        """Returns the emoji's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def url(self):
        """Returns a URL version of the emoji."""
        _format = 'gif' if self.animated else 'png'
        url = "https://cdn.discordapp.com/emojis/{0.id}.{1}".format(self, _format)
        return Asset(self._state, url)

    @property
    def roles(self):
        """List[:class:`Role`]: A :class:`list` of roles that is allowed to use this emoji.

        If roles is empty, the emoji is unrestricted.
        """
        guild = self.guild
        if guild is None:
            return []

        return [role for role in guild.roles if self._roles.has(role.id)]

    @property
    def guild(self):
        """:class:`Guild`: The guild this emoji belongs to."""
        return self._state._get_guild(self.guild_id)

    async def delete(self, *, reason=None):
        """|coro|

        Deletes the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_custom_emoji(self.guild.id, self.id, reason=reason)

    async def edit(self, *, name, roles=None, reason=None):
        r"""|coro|

        Edits the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        -----------
        name: :class:`str`
            The new emoji name.
        roles: Optional[list[:class:`Role`]]
            A :class:`list` of :class:`Role`\s that can use this emoji. Leave empty to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for editing this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to edit emojis.
        HTTPException
            An error occurred editing the emoji.
        """

        if roles:
            roles = [role.id for role in roles]
        await self._state.http.edit_custom_emoji(self.guild.id, self.id, name=name, roles=roles, reason=reason)
