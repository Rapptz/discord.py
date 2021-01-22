# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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


class _EmojiTag:
    __slots__ = ()

class PartialEmoji(_EmojiTag):
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
    name: Optional[:class:`str`]
        The custom emoji name, if applicable, or the unicode codepoint
        of the non-custom emoji. This can be ``None`` if the emoji
        got deleted (e.g. removing a reaction with a deleted emoji).
    animated: :class:`bool`
        Whether the emoji is animated or not.
    id: Optional[:class:`int`]
        The ID of the custom emoji, if applicable.
    """

    __slots__ = ('animated', 'name', 'id', '_state')

    def __init__(self, *, name, animated=False, id=None):
        self.animated = animated
        self.name = name
        self.id = id
        self._state = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            animated=data.get('animated', False),
            id=utils._get_as_snowflake(data, 'id'),
            name=data.get('name'),
        )

    def to_dict(self):
        o = { 'name': self.name }
        if self.id:
            o['id'] = self.id
        if self.animated:
            o['animated'] = self.animated
        return o

    @classmethod
    def with_state(cls, state, *, name, animated=False, id=None):
        self = cls(name=name, animated=animated, id=id)
        self._state = state
        return self

    def __str__(self):
        if self.id is None:
            return self.name
        if self.animated:
            return '<a:%s:%s>' % (self.name, self.id)
        return '<:%s:%s>' % (self.name, self.id)

    def __repr__(self):
        return '<{0.__class__.__name__} animated={0.animated} name={0.name!r} id={0.id}>'.format(self)

    def __eq__(self, other):
        if self.is_unicode_emoji():
            return isinstance(other, PartialEmoji) and self.name == other.name

        if isinstance(other, _EmojiTag):
            return self.id == other.id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.id, self.name))

    def is_custom_emoji(self):
        """:class:`bool`: Checks if this is a custom non-Unicode emoji."""
        return self.id is not None

    def is_unicode_emoji(self):
        """:class:`bool`: Checks if this is a Unicode emoji."""
        return self.id is None

    def _as_reaction(self):
        if self.id is None:
            return self.name
        return '%s:%s' % (self.name, self.id)

    @property
    def created_at(self):
        """Optional[:class:`datetime.datetime`]: Returns the emoji's creation time in UTC, or None if Unicode emoji.

        .. versionadded:: 1.6
        """
        if self.is_unicode_emoji():
            return None

        return utils.snowflake_time(self.id)

    @property
    def url(self):
        """:class:`Asset`: Returns the asset of the emoji, if it is custom.

        This is equivalent to calling :meth:`url_as` with
        the default parameters (i.e. png/gif detection).
        """
        return self.url_as(format=None)

    def url_as(self, *, format=None, static_format="png"):
        """Returns an :class:`Asset` for the emoji's url, if it is custom.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif'.
        'gif' is only valid for animated emojis.

        .. versionadded:: 1.7

        Parameters
        -----------
        format: Optional[:class:`str`]
            The format to attempt to convert the emojis to.
            If the format is ``None``, then it is automatically
            detected as either 'gif' or static_format, depending on whether the
            emoji is animated or not.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated emoji's to.
            Defaults to 'png'

        Raises
        -------
        InvalidArgument
            Bad image format passed to ``format`` or ``static_format``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        if self.is_unicode_emoji():
            return Asset(self._state)

        return Asset._from_emoji(self._state, self, format=format, static_format=static_format)
