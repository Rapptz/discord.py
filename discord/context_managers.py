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

import asyncio

from .compat import create_task

def _typing_done_callback(fut):
    # just retrieve any exception and call it a day
    try:
        fut.exception()
    except:
        pass

class Typing:
    def __init__(self, messageable):
        self.loop = messageable._state.loop
        self.messageable = messageable

    @asyncio.coroutine
    def do_typing(self):
        try:
            channel = self._channel
        except AttributeError:
            channel = yield from self.messageable._get_channel()

        typing = channel._state.http.send_typing

        while True:
            yield from typing(channel.id)
            yield from asyncio.sleep(5)

    def __enter__(self):
        self.task = create_task(self.do_typing(), loop=self.loop)
        self.task.add_done_callback(_typing_done_callback)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.task.cancel()

    @asyncio.coroutine
    def __aenter__(self):
        self._channel = channel = yield from self.messageable._get_channel()
        yield from channel._state.http.send_typing(channel.id)
        return self.__enter__()

    @asyncio.coroutine
    def __aexit__(self, exc_type, exc, tb):
        self.task.cancel()
