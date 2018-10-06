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

class MessageCache:

	__slots__ = ('mixed', 'important', 'max_mixed_messages', 'max_important_messages')

	def __init__(self, *, max_mixed_messages, max_important_messages):
		self.max_mixed_messages = max_mixed_messages
		self.max_important_messages = max_important_messages
		self.mixed = deque(maxlen = max_mixed_messages)
		self.important = deque(maxlen=max_important_messages)

	def append(self, message):
		if len(self.mixed) >= self.max_mixed_messages:
			dropped = self.mixed.popLeft()
			if dropped.important:
				self.important.append(dropped)
		self.mixed.append(message)

	def remove(self, element):
		try:
			self.mixed.remove(element)
		except ValueError:
			self.important.remove(element)

	def filter(self, predicate):
		new = MessageCache(
			max_mixed_messages=self.max_mixed_messages,
			max_important_messages=self.max_important_messages
		)
		new.mixed = deque((i for i in self.mixed if predicate(i)), maxlen=self.max_mixed_messages)
		new.important = deque((i for i in self.important if predicate(i)), maxlen=self.max_important_messages)
		return new

	def __iter__(self):
		return chain(self.mixed, self.important)
