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

def parse_time(timestamp):
    if timestamp:
        return datetime.datetime(*map(int, re_split(r'[^\d]', timestamp.replace('+00:00', ''))))
    return None

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
    **attrs
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

@asyncio.coroutine
def _verify_successful_response(response):
    code = response.status
    success = code >= 200 and code < 300
    if not success:
        data = yield from response.json()
        message = data.get('message')
        if code == 403:
            raise Forbidden(response, message)
        elif code == 404:
            raise NotFound(response, message)
        raise HTTPException(response, message)

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

try:
    create_task = asyncio.ensure_future
except AttributeError:
    create_task = asyncio.async
