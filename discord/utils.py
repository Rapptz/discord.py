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

from re import split as re_split
from .errors import HTTPException, Forbidden, NotFound, InvalidArgument
import datetime
from base64 import b64encode
import asyncio
import json
import warnings, functools

DISCORD_EPOCH = 1420070400000

class cached_property:
    def __init__(self, function):
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value

class CachedSlotProperty:
    def __init__(self, name, function):
        self.name = name
        self.function = function
        self.__doc__ = getattr(function, '__doc__')

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return getattr(instance, self.name)
        except AttributeError:
            value = self.function(instance)
            setattr(instance, self.name, value)
            return value

def cached_slot_property(name):
    def decorator(func):
        return CachedSlotProperty(name, func)
    return decorator

def parse_time(timestamp):
    if timestamp:
        return datetime.datetime(*map(int, re_split(r'[^\d]', timestamp.replace('+00:00', ''))))
    return None

def deprecated(instead=None):
    def actual_decorator(func):
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning) # turn off filter
            if instead:
                fmt = "{0.__name__} is deprecated, use {1} instead."
            else:
                fmt = '{0.__name__} is deprecated.'

            warnings.warn(fmt.format(func, instead), stacklevel=3, category=DeprecationWarning)
            warnings.simplefilter('default', DeprecationWarning) # reset filter
            return func(*args, **kwargs)
        return decorated
    return actual_decorator

def oauth_url(client_id, permissions=None, server=None, redirect_uri=None):
    """A helper function that returns the OAuth2 URL for inviting the bot
    into servers.

    Parameters
    -----------
    client_id : str
        The client ID for your bot.
    permissions : :class:`Permissions`
        The permissions you're requesting. If not given then you won't be requesting any
        permissions.
    server : :class:`Server`
        The server to pre-select in the authorization screen, if available.
    redirect_uri : str
        An optional valid redirect URI.
    """
    url = 'https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(client_id)
    if permissions is not None:
        url = url + '&permissions=' + str(permissions.value)
    if server is not None:
        url = url + "&guild_id=" + server.id
    if redirect_uri is not None:
        from urllib.parse import urlencode
        url = url + "&response_type=code&" + urlencode({'redirect_uri': redirect_uri})
    return url


def snowflake_time(id):
    """Returns the creation date in UTC of a discord id."""
    return datetime.datetime.utcfromtimestamp(((int(id) >> 22) + DISCORD_EPOCH) / 1000)

def time_snowflake(datetime_obj, high=False):
    """Returns a numeric snowflake pretending to be created at the given date.

    When using as the lower end of a range, use time_snowflake(high=False) - 1 to be inclusive, high=True to be exclusive
    When using as the higher end of a range, use time_snowflake(high=True) + 1 to be inclusive, high=False to be exclusive

    Parameters
    -----------
    datetime_obj
        A timezone-naive datetime object representing UTC time.
    high
        Whether or not to set the lower 22 bit to high or low.
    """
    unix_seconds = (datetime_obj - type(datetime_obj)(1970, 1, 1)).total_seconds()
    discord_millis = int(unix_seconds * 1000 - DISCORD_EPOCH)

    return (discord_millis << 22) + (2**22-1 if high else 0)

def find(predicate, seq):
    """A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = find(lambda m: m.name == 'Mighty', channel.server.members)

    would find the first :class:`Member` whose name is 'Mighty' and return it.
    If an entry is not found, then ``None`` is returned.

    This is different from `filter`_ due to the fact it stops the moment it finds
    a valid entry.


    .. _filter: https://docs.python.org/3.6/library/functions.html#filter

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    seq : iterable
        The iterable to search through.
    """

    for element in seq:
        if predicate(element):
            return element
    return None

def get(iterable, **attrs):
    """A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``. This is an alternative for
    :func:`discord.utils.find`.

    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.

    If nothing is found that matches the attributes passed, then
    ``None`` is returned.

    Examples
    ---------

    Basic usage:

    .. code-block:: python

        member = discord.utils.get(message.server.members, name='Foo')

    Multiple attribute matching:

    .. code-block:: python

        channel = discord.utils.get(server.channels, name='Foo', type=ChannelType.voice)

    Nested attribute matching:

    .. code-block:: python

        channel = discord.utils.get(client.get_all_channels(), server__name='Cool', name='general')

    Parameters
    -----------
    iterable
        An iterable to search through.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """

    def predicate(elem):
        for attr, val in attrs.items():
            nested = attr.split('__')
            obj = elem
            for attribute in nested:
                obj = getattr(obj, attribute)

            if obj != val:
                return False
        return True

    return find(predicate, iterable)


def _unique(iterable):
    seen = set()
    adder = seen.add
    return [x for x in iterable if not (x in seen or adder(x))]

def _null_event(*args, **kwargs):
    pass

def _get_mime_type_for_image(data):
    if data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        return 'image/png'
    elif data.startswith(b'\xFF\xD8') and data.endswith(b'\xFF\xD9'):
        return 'image/jpeg'
    else:
        raise InvalidArgument('Unsupported image type given')

def _bytes_to_base64_data(data):
    fmt = 'data:{mime};base64,{data}'
    mime = _get_mime_type_for_image(data)
    b64 = b64encode(data).decode('ascii')
    return fmt.format(mime=mime, data=b64)

def to_json(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=True)

