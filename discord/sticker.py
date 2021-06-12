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

from .mixins import Hashable
from .asset import Asset
from .utils import snowflake_time
from .enums import StickerType, try_enum

class Sticker(Hashable):
    """Represents a sticker.

    .. versionadded:: 1.6

    .. container:: operations

        .. describe:: str(x)

            Returns the name of the sticker.

        .. describe:: x == y

           Checks if the sticker is equal to another sticker.

        .. describe:: x != y

           Checks if the sticker is not equal to another sticker.

    Attributes
    ----------
    name: :class:`str`
        The sticker's name.
    id: :class:`int`
        The id of the sticker.
    description: :class:`str`
        The description of the sticker.
    pack_id: :class:`int`
        The id of the sticker's pack.
    format: :class:`StickerType`
        The format for the sticker's image.
    image: :class:`str`
        The sticker's image.
    tags: List[:class:`str`]
        A list of tags for the sticker.
    preview_image: Optional[:class:`str`]
        The sticker's preview asset hash.
    """
    __slots__ = ('_state', 'id', 'name', 'description', 'pack_id', 'format', 'image', 'tags', 'preview_image')

    def __init__(self, *, state, data):
        self._state = state
        self.id = int(data['id'])
        self.name = data['name']
        self.description = data['description']
        self.pack_id = int(data.get('pack_id', 0))
        self.format = try_enum(StickerType, data['format_type'])
        self.image = data['asset']

        try:
            self.tags = [tag.strip() for tag in data['tags'].split(',')]
        except KeyError:
            self.tags = []

        self.preview_image = data.get('preview_asset')

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name!r}>'.format(self)

    def __str__(self):
        return self.name

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the sticker's creation time in UTC as a naive datetime."""
        return snowflake_time(self.id)

    @property
    def image_url(self):
        """Returns an :class:`Asset` for the sticker's image.

        .. note::
            This will return ``None`` if the format is ``StickerType.lottie``.

        Returns
        -------
        Optional[:class:`Asset`]
            The resulting CDN asset.
        """
        return self.image_url_as()

    def image_url_as(self, *, size=1024):
        """Optionally returns an :class:`Asset` for the sticker's image.

        The size must be a power of 2 between 16 and 4096.

        .. note::
            This will return ``None`` if the format is ``StickerType.lottie``.

        Parameters
        -----------
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Invalid ``size``.

        Returns
        -------
        Optional[:class:`Asset`]
            The resulting CDN asset or ``None``.
        """
        if self.format is StickerType.lottie:
            return None

        return Asset._from_sticker_url(self._state, self, size=size)
