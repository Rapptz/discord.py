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
from io import BytesIO
from typing import Any
from unittest.mock import patch

import aiohttp
import discord
import pytest

from discord.http import HTTPClient, Route, handle_message_parameters
from discord.webhook.async_ import interaction_message_response_params


def make_file(index: int) -> discord.File:
    return discord.File(BytesIO(b'test'), filename=f'test-{index}.txt')


def test_handle_message_parameters_rejects_too_many_files():
    files = [make_file(index) for index in range(11)]

    with pytest.raises(ValueError, match='files has a maximum of 10 elements'):
        handle_message_parameters(content='test', files=files)


def test_interaction_message_response_params_rejects_too_many_files():
    files = [make_file(index) for index in range(11)]

    with pytest.raises(ValueError, match='files has a maximum of 10 elements'):
        interaction_message_response_params(type=4, content='test', files=files)


class FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.headers = {'Via': '1.1 google', 'content-type': 'application/json'}
        self.body = body

    async def text(self, encoding: str) -> str:
        return self.body

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


def fake_request(session: aiohttp.ClientSession, method: str, url: str, **kwargs: Any) -> FakeResponse:
    if url.endswith('/gateway'):
        return FakeResponse(429, '{"message": "You are being rate limited.", "retry_after": 60.0, "global": true}')
    return FakeResponse(200, '{}')


@pytest.mark.asyncio
async def test_global_rate_limit_is_released_when_request_is_cancelled():
    http = HTTPClient(asyncio.get_running_loop())

    with patch.object(aiohttp.ClientSession, 'request', fake_request):
        await http.static_login('token')
        try:
            # the request is cancelled while sleeping on the global rate limit
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(http.request(Route('GET', '/gateway')), timeout=0.1)

            # later requests would wait forever if the global rate limit was never released
            await asyncio.wait_for(http.request(Route('GET', '/users/@me')), timeout=1)
        finally:
            await http.close()
