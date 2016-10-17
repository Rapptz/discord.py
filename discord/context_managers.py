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

import asyncio

from .compat import create_task

class Typing:
    def __init__(self, channel):
        http = channel._state.http
        self.loop = http.loop
        self.channel = channel
        self.typing = http.send_typing

    @asyncio.coroutine
    def do_typing(self):
        while True:
            yield from self.typing(self.channel.id)
            yield from asyncio.sleep(5)

    def __enter__(self):
        self.task = create_task(self.do_typing(), loop=self.loop)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.task.cancel()
        except:
            pass

    @asyncio.coroutine
    def __aenter__(self):
        return self.__enter__()

    @asyncio.coroutine
    def __aexit__(self, exc_type, exc, tb):
        self.__exit__(exc_type, exc, tb)
