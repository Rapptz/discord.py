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


def test_checkbox_group_rejects_too_many_initial_options():
    options = [discord.CheckboxGroupOption(label=str(i), value=str(i)) for i in range(11)]

    with pytest.raises(ValueError):
        discord.ui.CheckboxGroup(options=options)


def test_checkbox_group_rejects_too_many_assigned_options():
    group = discord.ui.CheckboxGroup()
    options = [discord.CheckboxGroupOption(label=str(i), value=str(i)) for i in range(11)]

    with pytest.raises(ValueError):
        group.options = options


def test_radio_group_rejects_too_many_initial_options():
    options = [discord.RadioGroupOption(label=str(i), value=str(i)) for i in range(11)]

    with pytest.raises(ValueError):
        discord.ui.RadioGroup(options=options)


def test_radio_group_rejects_too_many_assigned_options():
    group = discord.ui.RadioGroup()
    options = [discord.RadioGroupOption(label=str(i), value=str(i)) for i in range(11)]

    with pytest.raises(ValueError):
        group.options = options


def test_radio_group_rejects_too_few_initial_options():
    options = [discord.RadioGroupOption(label='One', value='one')]

    with pytest.raises(ValueError, match='radio group must have at least 2 options'):
        discord.ui.RadioGroup(options=options)


def test_radio_group_rejects_too_few_assigned_options():
    group = discord.ui.RadioGroup()
    options = [discord.RadioGroupOption(label='One', value='one')]

    with pytest.raises(ValueError, match='radio group must have at least 2 options'):
        group.options = options


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'min_values': -1}, 'min_values must be between 0 and 10'),
        ({'min_values': 11}, 'min_values must be between 0 and 10'),
        ({'max_values': 0}, 'max_values must be between 1 and 10'),
        ({'max_values': 11}, 'max_values must be between 1 and 10'),
    ],
)
def test_checkbox_group_rejects_out_of_range_value_counts(kwargs, message):
    with pytest.raises(ValueError, match=message):
        discord.ui.CheckboxGroup(**kwargs)


def test_checkbox_group_rejects_out_of_range_assigned_value_counts():
    group = discord.ui.CheckboxGroup()

    with pytest.raises(ValueError, match='min_values must be between 0 and 10'):
        group.min_values = -1

    with pytest.raises(ValueError, match='max_values must be between 1 and 10'):
        group.max_values = 11


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'min_values': -1}, 'min_values must be between 0 and 10'),
        ({'min_values': 11}, 'min_values must be between 0 and 10'),
        ({'max_values': 0}, 'max_values must be between 1 and 10'),
        ({'max_values': 11}, 'max_values must be between 1 and 10'),
    ],
)
def test_file_upload_rejects_out_of_range_value_counts(kwargs, message):
    with pytest.raises(ValueError, match=message):
        discord.ui.FileUpload(**kwargs)


def test_file_upload_rejects_out_of_range_assigned_value_counts():
    upload = discord.ui.FileUpload()

    with pytest.raises(ValueError, match='min_values must be between 0 and 10'):
        upload.min_values = -1

    with pytest.raises(ValueError, match='max_values must be between 1 and 10'):
        upload.max_values = 11


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'min_length': -1}, 'min_length must be between 0 and 4000'),
        ({'min_length': 4001}, 'min_length must be between 0 and 4000'),
        ({'max_length': 0}, 'max_length must be between 1 and 4000'),
        ({'max_length': 4001}, 'max_length must be between 1 and 4000'),
        ({'min_length': 10, 'max_length': 1}, 'min_length cannot be greater than max_length'),
    ],
)
def test_text_input_rejects_out_of_range_lengths(kwargs, message):
    with pytest.raises(ValueError, match=message):
        discord.ui.TextInput(**kwargs)


def test_text_input_rejects_out_of_range_assigned_lengths():
    input = discord.ui.TextInput()

    with pytest.raises(ValueError, match='min_length must be between 0 and 4000'):
        input.min_length = -1

    with pytest.raises(ValueError, match='max_length must be between 1 and 4000'):
        input.max_length = 4001

    input.max_length = 5
    with pytest.raises(ValueError, match='min_length cannot be greater than max_length'):
        input.min_length = 6
