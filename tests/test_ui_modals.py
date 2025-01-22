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

import discord
import pytest


@pytest.mark.asyncio
async def test_modal_init():
    modal = discord.ui.Modal(
        title="Temp Title",
    )
    assert modal.title == "Temp Title"
    assert modal.timeout == None


@pytest.mark.asyncio
async def test_no_title():
    with pytest.raises(ValueError) as excinfo:
        discord.ui.Modal()

    assert str(excinfo.value) == "Modal must have a title"


@pytest.mark.asyncio
async def test_to_dict():
    modal = discord.ui.Modal(
        title="Temp Title",
    )
    data = modal.to_dict()
    assert data["custom_id"] is not None
    assert data["title"] == "Temp Title"
    assert data["components"] == []


@pytest.mark.asyncio
async def test_add_item():
    modal = discord.ui.Modal(
        title="Temp Title",
    )
    item = discord.ui.TextInput(label="Test")
    modal.add_item(item)

    assert modal.children == [item]


@pytest.mark.asyncio
async def test_add_item_invalid():
    modal = discord.ui.Modal(
        title="Temp Title",
    )
    with pytest.raises(TypeError):
        modal.add_item("Not an item")  # type: ignore


@pytest.mark.asyncio
async def test_maximum_items():
    modal = discord.ui.Modal(
        title="Temp Title",
    )
    max_item_limit = 5

    for i in range(max_item_limit):
        modal.add_item(discord.ui.TextInput(label=f"Test {i}"))

    with pytest.raises(ValueError):
        modal.add_item(discord.ui.TextInput(label="Test"))


@pytest.mark.asyncio
async def test_modal_setters():
    modal = discord.ui.Modal(
        title="Temp Title",
    )
    modal.title = "New Title"
    assert modal.title == "New Title"

    modal.timeout = 120
    assert modal.timeout == 120
