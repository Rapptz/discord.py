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

import concurrent.futures
import asyncio

try:
    create_task = asyncio.ensure_future
except AttributeError:
    create_task = asyncio.async

try:
    run_coroutine_threadsafe = asyncio.run_coroutine_threadsafe
except AttributeError:
    # the following code is slightly modified from the
    # official asyncio repository that could be found here:
    # https://github.com/python/asyncio/blob/master/asyncio/futures.py
    # with a commit hash of 5c7efbcdfbe6a5c25b4cd5df22d9a15ab4062c8e
    # this portion is licensed under Apache license 2.0

    def _set_concurrent_future_state(concurrent, source):
        """Copy state from a future to a concurrent.futures.Future."""
        assert source.done()
        if source.cancelled():
            concurrent.cancel()
        if not concurrent.set_running_or_notify_cancel():
            return
        exception = source.exception()
        if exception is not None:
            concurrent.set_exception(exception)
        else:
            result = source.result()
            concurrent.set_result(result)


    def _copy_future_state(source, dest):
        """Internal helper to copy state from another Future.
        The other Future may be a concurrent.futures.Future.
        """
        assert source.done()
        if dest.cancelled():
            return
        assert not dest.done()
        if source.cancelled():
            dest.cancel()
        else:
            exception = source.exception()
            if exception is not None:
                dest.set_exception(exception)
            else:
                result = source.result()
                dest.set_result(result)

    def _chain_future(source, destination):
        """Chain two futures so that when one completes, so does the other.
        The result (or exception) of source will be copied to destination.
        If destination is cancelled, source gets cancelled too.
        Compatible with both asyncio.Future and concurrent.futures.Future.
        """
        if not isinstance(source, (asyncio.Future, concurrent.futures.Future)):
            raise TypeError('A future is required for source argument')

        if not isinstance(destination, (asyncio.Future, concurrent.futures.Future)):
            raise TypeError('A future is required for destination argument')

        source_loop = source._loop if isinstance(source, asyncio.Future) else None
        dest_loop = destination._loop if isinstance(destination, asyncio.Future) else None

        def _set_state(future, other):
            if isinstance(future, asyncio.Future):
                _copy_future_state(other, future)
            else:
                _set_concurrent_future_state(future, other)

        def _call_check_cancel(destination):
            if destination.cancelled():
                if source_loop is None or source_loop is dest_loop:
                    source.cancel()
                else:
                    source_loop.call_soon_threadsafe(source.cancel)

        def _call_set_state(source):
            if dest_loop is None or dest_loop is source_loop:
                _set_state(destination, source)
            else:
                dest_loop.call_soon_threadsafe(_set_state, destination, source)

        destination.add_done_callback(_call_check_cancel)
        source.add_done_callback(_call_set_state)

    def run_coroutine_threadsafe(coro, loop):
        """Submit a coroutine object to a given event loop.

        Return a concurrent.futures.Future to access the result.
        """
        if not asyncio.iscoroutine(coro):
            raise TypeError('A coroutine object is required')

        future = concurrent.futures.Future()

        def callback():
            try:
                _chain_future(create_task(coro, loop=loop), future)
            except Exception as exc:
                if future.set_running_or_notify_cancel():
                    future.set_exception(exc)
                raise
        loop.call_soon_threadsafe(callback)
        return future
