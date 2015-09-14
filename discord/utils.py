# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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
import datetime


def parse_time(timestamp):
    if timestamp:
        return datetime.datetime(*map(int, re_split(r'[^\d]', timestamp.replace('+00:00', ''))))
    return None

def find(predicate, seq):
    """A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = find(lambda m: m.name == 'Mighty', channel.server.members)

    would find the first :class:`Member` whose name is 'Mighty' and return it.

    This is different from `filter`_ due to the fact it stops the moment it finds
    a valid entry.

    .. _filter: https://docs.python.org/3.6/library/functions.html#filter

    :param predicate: A function that returns a boolean-like result.
    :param seq: The sequence to iterate through.
    :return: The first result of the predicate that returned a ``True``-like value or ``None`` if nothing was found.
    """

    for element in seq:
        if predicate(element):
            return element
    return None
