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

import datetime

from .colour import Colour
from . import utils

class _EmptyEmbed:
    def __bool__(self):
        return False

    def __repr__(self):
        return 'Embed.Empty'

EmptyEmbed = _EmptyEmbed()

class EmbedProxy:
    def __init__(self, layer):
        self.__dict__.update(layer)

    def __repr__(self):
        return 'EmbedProxy(%s)' % ', '.join(('%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')))

    def __getattr__(self, attr):
        return EmptyEmbed

class Embed:
    """Represents a Discord embed.

    The following attributes can be set during creation
    of the object:

    Certain properties return an ``EmbedProxy``. Which is a type
    that acts similar to a regular `dict` except access the attributes
    via dotted access, e.g. ``embed.author.icon_url``. If the attribute
    is invalid or empty, then a special sentinel value is returned,
    :attr:`Embed.Empty`.

    Attributes
    -----------
    title: str
        The title of the embed.
    type: str
        The type of embed. Usually "rich".
    description: str
        The description of the embed.
    url: str
        The URL of the embed.
    timestamp: `datetime.datetime`
        The timestamp of the embed content.
    colour: :class:`Colour` or int
        The colour code of the embed. Aliased to ``color`` as well.
    Empty
        A special sentinel value used by ``EmbedProxy`` to denote
        that the value or attribute is empty.
    """

    __slots__ = ('title', 'url', 'type', '_timestamp', '_colour', '_footer',
                 '_image', '_thumbnail', '_video', '_provider', '_author',
                 '_fields', 'description')

    Empty = EmptyEmbed

    def __init__(self, **kwargs):
        # swap the colour/color aliases
        try:
            colour = kwargs['colour']
        except KeyError:
            colour = kwargs.get('color')

        if colour is not None:
            self.colour = colour

        self.title = kwargs.get('title')
        self.type = kwargs.get('type', 'rich')
        self.url = kwargs.get('url')
        self.description = kwargs.get('description')

        try:
            timestamp = kwargs['timestamp']
        except KeyError:
            pass
        else:
            self.timestamp = timestamp

    @classmethod
    def from_data(cls, data):
        # we are bypassing __init__ here since it doesn't apply here
        self = cls.__new__(cls)

        # fill in the basic fields

        self.title = data.get('title')
        self.type  = data.get('type')
        self.description = data.get('description')
        self.url = data.get('url')

        # try to fill in the more rich fields

        try:
            self._colour = Colour(value=data['color'])
        except KeyError:
            pass

        try:
            self._timestamp = utils.parse_time(data['timestamp'])
        except KeyError:
            pass

        for attr in ('thumbnail', 'video', 'provider', 'author', 'fields'):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, '_' + attr, value)

        return self

    @property
    def colour(self):
        return getattr(self, '_colour', None)

    @colour.setter
    def colour(self, value):
        if isinstance(value, Colour):
            self._colour = value
        elif isinstance(value, int):
            self._colour = Colour(value=value)
        else:
            raise TypeError('Expected discord.Colour or int, received %s instead.' % value.__class__.__name__)

    color = colour

    @property
    def timestamp(self):
        return getattr(self, '_timestamp', None)

    @timestamp.setter
    def timestamp(self, value):
        if isinstance(value, datetime.datetime):
            self._timestamp = value
        else:
            raise TypeError("Expected datetime.datetime received %s instead" % value.__class__.__name__)

    @property
    def footer(self):
        """Returns a ``EmbedProxy`` denoting the footer contents.

        See :meth:`set_footer` for possible values you can access.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return EmbedProxy(getattr(self, '_footer', {}))

    def set_footer(self, *, text=None, icon_url=None):
        """Sets the footer for the embed content.

        Parameters
        -----------
        text: str
            The footer text.
        icon_url: str
            The URL of the footer icon. Only HTTP(S) is supported.
        """

        self._footer = {}
        if text is not None:
            self._footer['text'] = text

        if icon_url is not None:
            self._footer['icon_url'] = icon_url

    @property
    def image(self):
        """Returns a ``EmbedProxy`` denoting the image contents.

        See :meth:`set_image` for possible values you can access.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return EmbedProxy(getattr(self, '_image', {}))

    def set_image(self, *, url, height=None, width=None):
        """Sets the image for the embed content.

        Parameters
        -----------
        url: str
            The source URL for the image. Only HTTP(S) is supported.
        height: int
            The height of the image.
        width: int
            The width of the image.
        """

        self._image = {
            'url': url
        }

        if height is not None:
            self._image['height'] = height

        if width is not None:
            self._image['width'] = width

    @property
    def thumbnail(self):
        """Returns a ``EmbedProxy`` denoting the thumbnail contents.

        See :meth:`set_thumbnail` for possible values you can access.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return EmbedProxy(getattr(self, '_thumbnail', {}))

    def set_thumbnail(self, *, url, height=None, width=None):
        """Sets the thumbnail for the embed content.

        Parameters
        -----------
        url: str
            The source URL for the thumbnail. Only HTTP(S) is supported.
        height: int
            The height of the thumbnail.
        width: int
            The width of the thumbnail.
        """

        self._thumbnail = {
            'url': url
        }

        if height is not None:
            self._thumbnail['height'] = height

        if width is not None:
            self._thumbnail['width'] = width

    @property
    def video(self):
        """Returns a ``EmbedProxy`` denoting the video contents.

        Possible attributes include:

        - ``url`` for the video URL.
        - ``height`` for the video height.
        - ``width`` for the video width.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return EmbedProxy(getattr(self, '_video', {}))

    @property
    def provider(self):
        """Returns a ``EmbedProxy`` denoting the provider contents.

        The only attributes that might be accessed are ``name`` and ``url``.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return EmbedProxy(getattr(self, '_provider', {}))

    @property
    def author(self):
        """Returns a ``EmbedProxy`` denoting the author contents.

        See :meth:`set_author` for possible values you can access.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return EmbedProxy(getattr(self, '_author', {}))

    def set_author(self, *, name, url=None, icon_url=None):
        """Sets the author for the embed content.

        Parameters
        -----------
        name: str
            The name of the author.
        url: str
            The URL for the author.
        icon_url: str
            The URL of the author icon. Only HTTP(S) is supported.
        """

        self._author = {
            'name': name
        }

        if url is not None:
            self._author['url'] = url

        if icon_url is not None:
            self._author['icon_url'] = icon_url


    @property
    def fields(self):
        """Returns a list of ``EmbedProxy`` denoting the field contents.

        See :meth:`add_field` for possible values you can access.

        If the attribute cannot be accessed then ``None`` is returned.
        """
        return [EmbedProxy(d) for d in getattr(self, '_fields', [])]

    def add_field(self, *, name=None, value=None, inline=True):
        """Adds a field to the embed object.

        Parameters
        -----------
        name: str
            The name of the field.
        value: str
            The value of the field.
        inline: bool
            Whether the field should be displayed inline.
        """

        field = {
            'inline': inline
        }
        if name is not None:
            field['name'] = name

        if value is not None:
            field['value'] = value

        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]

    def to_dict(self):
        """Converts this embed object into a dict."""

        # add in the raw data into the dict
        result = {
            key[1:]: getattr(self, key)
            for key in self.__slots__
            if key[0] == '_' and hasattr(self, key)
        }

        # deal with basic convenience wrappers

        try:
            colour = result.pop('colour')
        except KeyError:
            pass
        else:
            result['color'] = colour.value

        try:
            timestamp = result.pop('timestamp')
        except KeyError:
            pass
        else:
            result['timestamp'] = timestamp.isoformat()

        # add in the non raw attribute ones
        if self.type:
            result['type'] = self.type

        if self.description:
            result['description'] = self.description

        if self.url:
            result['url'] = self.url

        if self.title:
            result['title'] = self.title

        return result
