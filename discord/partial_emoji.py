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

import io

from .asset import Asset, AssetMixin
from .errors import DiscordException, InvalidArgument
from . import utils

__all__ = (
    'PartialEmoji',
)

class _EmojiTag:
    __slots__ = ()

class PartialEmoji(_EmojiTag, AssetMixin):
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
            return f'<a:{self.name}:{self.id}>'
        return f'<:{self.name}:{self.id}>'

    def __repr__(self):
        return f'<{self.__class__.__name__} animated={self.animated} name={self.name!r} id={self.id}>'

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
        return f'{self.name}:{self.id}'

    @property
    def created_at(self):
        """Optional[:class:`datetime.datetime`]: Returns the emoji's creation time in UTC, or None if Unicode emoji.

        .. versionadded:: 1.6
        """
        if self.is_unicode_emoji():
            return None

        return utils.snowflake_time(self.id)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the emoji, if it is custom.

        If this isn't a custom emoji then an empty string is returned
        """
        if self.is_unicode_emoji():
            return ''

        fmt = 'gif' if self.animated else 'png'
        return f'{Asset.BASE}/emojis/{self.id}.{fmt}'

    async def read(self) -> bytes:
        if self.is_unicode_emoji():
            raise InvalidArgument('PartialEmoji is not a custom emoji')

        return await super().read()
