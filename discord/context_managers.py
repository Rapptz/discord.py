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

import asyncio

def _typing_done_callback(fut):
    # just retrieve any exception and call it a day
    try:
        fut.exception()
    except (asyncio.CancelledError, Exception):
        pass

class Typing:
    def __init__(self, messageable):
        self.loop = messageable._state.loop
        self.messageable = messageable

    async def do_typing(self):
        try:
            channel = self._channel
        except AttributeError:
            channel = await self.messageable._get_channel()

        typing = channel._state.http.send_typing

        while True:
            await typing(channel.id)
            await asyncio.sleep(5)

    def __enter__(self):
        self.task = asyncio.ensure_future(self.do_typing(), loop=self.loop)
        self.task.add_done_callback(_typing_done_callback)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.task.cancel()

    async def __aenter__(self):
        self._channel = channel = await self.messageable._get_channel()
        await channel._state.http.send_typing(channel.id)
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb):
        self.task.cancel()
