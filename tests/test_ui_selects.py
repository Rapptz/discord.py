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
async def test_add_option():
    select = discord.ui.Select()

    for i in range(1, 25 + 1):
        select.add_option(label=str(i), value=str(i))

    with pytest.raises(ValueError):
        select.add_option(label="26", value="26")


def test_select_rejects_too_many_initial_options():
    options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(26)]

    with pytest.raises(ValueError):
        discord.ui.Select(options=options)


def test_select_rejects_too_many_assigned_options():
    select = discord.ui.Select()
    options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(26)]

    with pytest.raises(ValueError):
        select.options = options


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'min_values': -1}, 'min_values must be between 0 and 25'),
        ({'min_values': 26}, 'min_values must be between 0 and 25'),
        ({'max_values': 0}, 'max_values must be between 1 and 25'),
        ({'max_values': 26}, 'max_values must be between 1 and 25'),
    ],
)
def test_select_rejects_out_of_range_value_counts(kwargs, message):
    with pytest.raises(ValueError, match=message):
        discord.ui.Select(**kwargs)


def test_select_rejects_out_of_range_assigned_value_counts():
    select = discord.ui.Select()

    with pytest.raises(ValueError, match='min_values must be between 0 and 25'):
        select.min_values = -1

    with pytest.raises(ValueError, match='max_values must be between 1 and 25'):
        select.max_values = 26


def test_select_rejects_too_many_initial_default_values():
    values = [discord.Object(i) for i in range(2)]

    with pytest.raises(ValueError, match='default_values must be between min_values and max_values'):
        discord.ui.UserSelect(max_values=1, default_values=values)


def test_select_rejects_too_few_initial_default_values():
    values = [discord.Object(1)]

    with pytest.raises(ValueError, match='default_values must be between min_values and max_values'):
        discord.ui.RoleSelect(min_values=2, default_values=values)


def test_select_rejects_out_of_range_assigned_default_values():
    select = discord.ui.UserSelect(max_values=1)

    with pytest.raises(ValueError, match='default_values must be between min_values and max_values'):
        select.default_values = [discord.Object(1), discord.Object(2)]


def test_select_rejects_value_count_changes_incompatible_with_defaults():
    select = discord.ui.UserSelect(max_values=2, default_values=[discord.Object(1), discord.Object(2)])

    with pytest.raises(ValueError, match='default_values must be between min_values and max_values'):
        select.max_values = 1

    select = discord.ui.RoleSelect(min_values=1, default_values=[discord.Object(1)])

    with pytest.raises(ValueError, match='default_values must be between min_values and max_values'):
        select.min_values = 2
