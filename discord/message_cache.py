# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2015-2018 Rapptz

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

from collections import deque
from itertools import chain

from .. import utils

class MessageCache:

    __slots__ = ('cache', 'max_messages')

    def __init__(self, *, max_messages):
        self.max_messages = max_messages
        self.cache = deque(maxlen=max_messages)

    def get_message(self, msg_id):
        return utils.find(lambda m: m.id == msg_id, self.cache)

    def append(self, message):
        self.cache.append(message)

    def remove(self, element):
        self.cache.remove(element)

    def clear(self):
        self.cache = deque(maxlen=self.max_messages)

    def filter(self, predicate):
        self.cache = deque((i for i in self.important if predicate(i)), maxlen=self.max_messages)

    def __iter__(self):
        return iter(self.cache)
