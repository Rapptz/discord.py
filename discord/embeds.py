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

import datetime

from . import utils
from .colour import Colour
from .errors import EmbedError

class _EmptyEmbed:
    def __bool__(self):
        return False

    def __repr__(self):
        return 'Embed.Empty'

    def __len__(self):
        return 0

EmptyEmbed = _EmptyEmbed()

class EmbedProxy:
    def __init__(self, layer):
        self.__dict__.update(layer)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return 'EmbedProxy(%s)' % ', '.join(('%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')))

    def __getattr__(self, attr):
        return EmptyEmbed

class Embed:
    """Represents a Discord embed.

    The following attributes can be set during creation
    of the object:

    Certain properties return an ``EmbedProxy``. Which is a type
    that acts similar to a regular :class:`dict` except access the attributes
    via dotted access, e.g. ``embed.author.icon_url``. If the attribute
    is invalid or empty, then a special sentinel value is returned,
    :attr:`Embed.Empty`.

    For ease of use, all parameters that expect a :class:`str` are implicitly
    casted to :class:`str` for you.

    Attributes
    -----------
    title: :class:`str`
        The title of the embed which can not have more than 256 characters.
    type: :class:`str`
        The type of embed. Usually "rich".
    description: :class:`str`
        The description of the embed which can not have more than 2048 characters.
    url: :class:`str`
        The URL of the embed.
    timestamp: `datetime.datetime`
        The timestamp of the embed content. This could be a naive or aware datetime.
    colour: :class:`Colour` or :class:`int`
        The colour code of the embed. Aliased to ``color`` as well.
    Empty
        A special sentinel value used by ``EmbedProxy`` and this class
        to denote that the value or attribute is empty.

    Raises
    ------
    EmbedError
        If title is over 256 limit or description is over 2048 limit.
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
            colour = kwargs.get('color', EmptyEmbed)

        self.colour = colour
        self.title = kwargs.get('title', EmptyEmbed)
        if len(self.title) > 256: raise EmbedError('Embed title is over 256 limit.')
        self.type = kwargs.get('type', 'rich')
        self.url = kwargs.get('url', EmptyEmbed)
        self.description = kwargs.get('description', EmptyEmbed)
        if len(self.description) > 2048: raise EmbedError('Embed description is over 2048 limit.')
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

        self.title = data.get('title', EmptyEmbed)
        self.type = data.get('type', EmptyEmbed)
        self.description = data.get('description', EmptyEmbed)
        self.url = data.get('url', EmptyEmbed)

        # try to fill in the more rich fields

        try:
            self._colour = Colour(value=data['color'])
        except KeyError:
            pass

        try:
            self._timestamp = utils.parse_time(data['timestamp'])
        except KeyError:
            pass

        for attr in ('thumbnail', 'video', 'provider', 'author', 'fields', 'image', 'footer'):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, '_' + attr, value)

        return self

    @property
    def colour(self):
        return getattr(self, '_colour', EmptyEmbed)

    @colour.setter
    def colour(self, value):
        if isinstance(value, (Colour, _EmptyEmbed)):
            self._colour = value
        elif isinstance(value, int):
            self._colour = Colour(value=value)
        else:
            raise TypeError('Expected discord.Colour, int, or Embed.Empty but received %s instead.' % value.__class__.__name__)

    color = colour

    @property
    def timestamp(self):
        return getattr(self, '_timestamp', EmptyEmbed)

    @timestamp.setter
    def timestamp(self, value):
        if isinstance(value, (datetime.datetime, _EmptyEmbed)):
            self._timestamp = value
        else:
            raise TypeError("Expected datetime.datetime or Embed.Empty received %s instead" % value.__class__.__name__)

    @property
    def footer(self):
        """Returns an ``EmbedProxy`` denoting the footer contents.

        See :meth:`set_footer` for possible values you can access.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_footer', {}))

    def set_footer(self, *, text=EmptyEmbed, icon_url=EmptyEmbed):
        """Sets the footer for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        text: str
            The footer text which can not have more than 2048 characters.
        icon_url: str
            The URL of the footer icon. Only HTTP(S) is supported.

        Raises
        ------
        EmbedError
            If text is over 2048 limit.
        """

        self._footer = {}
        if text is not EmptyEmbed:
            if len(text) > 2048: raise EmbedError('Embed footer text is over 2048 limit.')
            self._footer['text'] = str(text)

        if icon_url is not EmptyEmbed:
            self._footer['icon_url'] = str(icon_url)

        return self

    @property
    def image(self):
        """Returns an ``EmbedProxy`` denoting the image contents.

        Possible attributes you can access are:

        - ``url``
        - ``proxy_url``
        - ``width``
        - ``height``

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_image', {}))

    def set_image(self, *, url):
        """Sets the image for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        url: str
            The source URL for the image. Only HTTP(S) is supported.
        """

        self._image = {
            'url': str(url)
        }

        return self

    @property
    def thumbnail(self):
        """Returns an ``EmbedProxy`` denoting the thumbnail contents.

        Possible attributes you can access are:

        - ``url``
        - ``proxy_url``
        - ``width``
        - ``height``

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_thumbnail', {}))

    def set_thumbnail(self, *, url):
        """Sets the thumbnail for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        url: str
            The source URL for the thumbnail. Only HTTP(S) is supported.
        """

        self._thumbnail = {
            'url': str(url)
        }

        return self

    @property
    def video(self):
        """Returns an ``EmbedProxy`` denoting the video contents.

        Possible attributes include:

        - ``url`` for the video URL.
        - ``height`` for the video height.
        - ``width`` for the video width.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_video', {}))

    @property
    def provider(self):
        """Returns an ``EmbedProxy`` denoting the provider contents.

        The only attributes that might be accessed are ``name`` and ``url``.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_provider', {}))

    @property
    def author(self):
        """Returns an ``EmbedProxy`` denoting the author contents.

        See :meth:`set_author` for possible values you can access.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_author', {}))

    def set_author(self, *, name, url=EmptyEmbed, icon_url=EmptyEmbed):
        """Sets the author for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        name: str
            The name of the author which can not have more than 256 characters.
        url: str
            The URL for the author.
        icon_url: str
            The URL of the author icon. Only HTTP(S) is supported.

        Raises
        ------
        EmbedError
            If name is over 256 limit.
        """

        self._author = {
            'name': str(name)
        }
        if len(self.author['name']) > 256: raise EmbedError('Embed author name is over 256 limit.')

        if url is not EmptyEmbed:
            self._author['url'] = str(url)

        if icon_url is not EmptyEmbed:
            self._author['icon_url'] = str(icon_url)

        return self

    @property
    def fields(self):
        """Returns a :class:`list` of ``EmbedProxy`` denoting the field contents.

        See :meth:`add_field` for possible values you can access.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return [EmbedProxy(d) for d in getattr(self, '_fields', [])]

    def add_field(self, *, name, value, inline=True):
        """Adds a field to the embed object. Will get ignored if there are already 25 fields.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        name: str
            The name of the field which can not have more than 256 characters.
        value: str
            The value of the field which can not have more than 1024 characters
        inline: bool
            Whether the field should be displayed inline.

        Raises
        ------
        EmbedError
            If name is over 256 limit or value is over 1024 limit.
        """

        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value)
        }

        if len(self.fields) >= 25: raise EmbedError('Embed fields is at 25 limit.')
        if len(field['name']) > 256: raise EmbedError('Embed field name is over 256 limit.')
        if len(field['value']) > 1024: raise EmbedError('Embed field value is over 1024 limit.')

        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]

        return self

    def clear_fields(self):
        """Removes all fields from this embed."""
        try:
            self._fields.clear()
        except AttributeError:
            self._fields = []

    def remove_field(self, index):
        """Removes a field at a specified index.

        If the index is invalid or out of bounds then the error is
        silently swallowed.

        .. note::
        
            When deleting a field by index, the index of the other fields
            shift to fill the gap just like a regular list.

        Parameters
        -----------
        index: int
            The index of the field to remove.
        """
        try:
            del self._fields[index]
        except (AttributeError, IndexError):
            pass

    def set_field_at(self, index, *, name, value, inline=True):
        """Modifies a field to the embed object.

        The index must point to a valid pre-existing field.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        index: int
            The index of the field to modify.
        name: str
            The name of the field which can not have more than 256 characters.
        value: str
            The value of the field which can not have more than 1024 characters
        inline: bool
            Whether the field should be displayed inline.

        Raises
        -------
        IndexError
            An invalid index was provided
        EmbedError
            If name is over 256 limit or value is over 1024 limit.
        """

        try:
            field = self._fields[index]
        except (TypeError, IndexError, AttributeError):
            raise IndexError('field index out of range')

        if len(field['name']) > 256: raise EmbedError('Embed field name is over 256 limit.')
        if len(field['value']) > 1024: raise EmbedError('Embed field value is over 1024 limit.')

        field['name'] = str(name)
        field['value'] = str(value)
        field['inline'] = inline
        return self

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
            if colour:
                result['color'] = colour.value

        try:
            timestamp = result.pop('timestamp')
        except KeyError:
            pass
        else:
            if timestamp:
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
