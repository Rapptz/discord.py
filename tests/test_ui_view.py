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


def test_add_item_with_full_row():
    view = discord.ui.View()

    for i in range(5):
        view.add_item(discord.ui.Button(label=str(i), row=0))

    with pytest.raises(ValueError):
        view.add_item(discord.ui.Button(label="6", row=0))

    assert len(view.children) == 5
    assert view.total_children_count == 5


def test_add_item_invalid():
    view = discord.ui.View()

    with pytest.raises(TypeError):
        view.add_item(object())  # type: ignore


def test_remove_item():
    view = discord.ui.View()
    item = discord.ui.Button(label="Test")
    view.add_item(item)

    view.remove_item(item)

    assert view.children == []
    assert view.total_children_count == 0
    assert item.view is None


def test_action_row_add_item_invalid():
    row = discord.ui.ActionRow()

    with pytest.raises(TypeError):
        row.add_item(object())  # type: ignore


def test_layout_view_add_item_with_too_many_children():
    view = discord.ui.LayoutView()
    max_item_limit = 40

    for i in range(max_item_limit - 1):
        view.add_item(discord.ui.TextDisplay(str(i)))

    row = discord.ui.ActionRow(
        discord.ui.Button(label="A"),
        discord.ui.Button(label="B"),
    )

    with pytest.raises(ValueError):
        view.add_item(row)

    assert len(view.children) == max_item_limit - 1
    assert view.total_children_count == max_item_limit - 1
    assert row.view is None
    assert all(item.view is None for item in row.children)
