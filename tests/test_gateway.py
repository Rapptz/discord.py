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

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading
import traceback
from types import SimpleNamespace
from unittest import mock

from discord.gateway import KeepAliveHandler


def test_keep_alive_block_warning_with_percent_in_stack(monkeypatch, caplog):
    ws = SimpleNamespace(
        HEARTBEAT=1,
        sequence=1,
        loop=None,
        thread_id=threading.get_ident(),
        _max_heartbeat_timeout=60.0,
    )
    handler = KeepAliveHandler(ws=ws, interval=0, shard_id=None)

    def run_coroutine_threadsafe(coro, loop):
        coro.close()
        handler.stop()
        future = mock.Mock()
        future.result.side_effect = [concurrent.futures.TimeoutError(), None]
        return future

    stack = ["  File \"client.py\", line 781, in connect\n    _log.exception('Attempting a reconnect in %.2fs', retry)\n"]

    monkeypatch.setattr(asyncio, 'run_coroutine_threadsafe', run_coroutine_threadsafe)
    monkeypatch.setattr(traceback, 'format_stack', lambda frame: stack)
    caplog.set_level(logging.WARNING, logger='discord.gateway')

    handler.run()

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert message.startswith('Shard ID None heartbeat blocked for more than 10 seconds.')
    assert "_log.exception('Attempting a reconnect in %.2fs', retry)" in message
