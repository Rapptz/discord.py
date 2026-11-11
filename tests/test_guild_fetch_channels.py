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

from unittest import mock

import pytest

import discord


def make_guild():
    state = mock.Mock()
    state.http.get_all_guild_channels = mock.AsyncMock(
        return_value=[
            {'id': '1', 'type': 0, 'name': 'general', 'position': 0, 'permission_overwrites': []},
            {'id': '2', 'type': 20, 'name': 'unknown', 'position': 1, 'permission_overwrites': []},
        ]
    )
    return discord.Guild(data={'id': '9'}, state=state)  # type: ignore


@pytest.mark.asyncio
async def test_fetch_channels_raises_on_unknown_types():
    with pytest.raises(discord.InvalidData):
        await make_guild().fetch_channels()


@pytest.mark.asyncio
async def test_fetch_channels_skips_unknown_types_when_asked():
    channels = await make_guild().fetch_channels(ignore_unhandled_types=True)

    assert [(channel.id, channel.name) for channel in channels] == [(1, 'general')]
