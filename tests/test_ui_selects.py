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


def test_select_init():
    select = discord.ui.Select(placeholder="Choose an option")
    assert select.placeholder == "Choose an option"
    assert select.min_values == 1
    assert select.max_values == 1
    assert select.disabled is False
    assert select.options == []


def test_select_init_with_options():
    options = [
        discord.SelectOption(label="Option 1", value="opt1"),
        discord.SelectOption(label="Option 2", value="opt2"),
    ]
    select = discord.ui.Select(options=options)
    assert len(select.options) == 2
    assert select.options[0].label == "Option 1"
    assert select.options[1].value == "opt2"


def test_select_min_max_values():
    select = discord.ui.Select(min_values=2, max_values=5)
    assert select.min_values == 2
    assert select.max_values == 5


def test_select_disabled():
    select = discord.ui.Select(disabled=True)
    assert select.disabled is True


def test_select_custom_id():
    select = discord.ui.Select(custom_id="my_select")
    assert select.custom_id == "my_select"


def test_select_invalid_custom_id():
    with pytest.raises(TypeError):
        discord.ui.Select(custom_id=12345)  # type: ignore


def test_select_custom_id_setter():
    select = discord.ui.Select()
    select.custom_id = "new_custom_id"
    assert select.custom_id == "new_custom_id"

    with pytest.raises(TypeError):
        select.custom_id = 12345  # type: ignore


def test_select_placeholder_setter():
    select = discord.ui.Select()
    select.placeholder = "New placeholder"
    assert select.placeholder == "New placeholder"

    select.placeholder = None
    assert select.placeholder is None

    with pytest.raises(TypeError):
        select.placeholder = 12345  # type: ignore


def test_select_min_values_setter():
    select = discord.ui.Select()
    select.min_values = 3
    assert select.min_values == 3


def test_select_max_values_setter():
    select = discord.ui.Select()
    select.max_values = 10
    assert select.max_values == 10


def test_select_disabled_setter():
    select = discord.ui.Select()
    select.disabled = True
    assert select.disabled is True


@pytest.mark.asyncio
async def test_add_option():
    select = discord.ui.Select()

    for i in range(1, 25 + 1):
        select.add_option(label=str(i), value=str(i))

    with pytest.raises(ValueError):
        select.add_option(label="26", value="26")


def test_add_option_with_emoji():
    select = discord.ui.Select()
    select.add_option(label="Happy", value="happy", emoji="😀")
    assert len(select.options) == 1
    assert select.options[0].emoji is not None


def test_add_option_with_description():
    select = discord.ui.Select()
    select.add_option(label="Option", value="opt", description="A description")
    assert select.options[0].description == "A description"


def test_add_option_default():
    select = discord.ui.Select()
    select.add_option(label="Default", value="default", default=True)
    assert select.options[0].default is True


def test_append_option():
    select = discord.ui.Select()
    option = discord.SelectOption(label="Appended", value="appended")
    select.append_option(option)
    assert len(select.options) == 1
    assert select.options[0].label == "Appended"


def test_append_option_max_limit():
    select = discord.ui.Select()
    for i in range(25):
        select.append_option(discord.SelectOption(label=str(i), value=str(i)))

    with pytest.raises(ValueError):
        select.append_option(discord.SelectOption(label="26", value="26"))


def test_select_option_init():
    option = discord.SelectOption(label="Test", value="test")
    assert option.label == "Test"
    assert option.value == "test"
    assert option.description is None
    assert option.emoji is None
    assert option.default is False


def test_select_option_with_emoji():
    option = discord.SelectOption(label="Test", value="test", emoji="🎉")
    assert option.emoji is not None
    assert option.emoji.name == "🎉"


def test_select_option_with_partial_emoji():
    emoji = discord.PartialEmoji(name="custom", id=123456789)
    option = discord.SelectOption(label="Test", value="test", emoji=emoji)
    assert option.emoji == emoji


def test_select_option_default():
    option = discord.SelectOption(label="Default", value="default", default=True)
    assert option.default is True


def test_user_select_init():
    select = discord.ui.UserSelect(placeholder="Select a user")
    assert select.placeholder == "Select a user"


def test_user_select_default_values():
    user = discord.Object(id=123456789)
    select = discord.ui.UserSelect(default_values=[user])
    assert len(select.default_values) == 1


def test_role_select_init():
    select = discord.ui.RoleSelect(placeholder="Select a role")
    assert select.placeholder == "Select a role"


def test_channel_select_init():
    select = discord.ui.ChannelSelect(placeholder="Select a channel")
    assert select.placeholder == "Select a channel"


def test_channel_select_with_channel_types():
    select = discord.ui.ChannelSelect(
        channel_types=[discord.ChannelType.text, discord.ChannelType.voice]
    )
    assert len(select.channel_types) == 2
    assert discord.ChannelType.text in select.channel_types
    assert discord.ChannelType.voice in select.channel_types


def test_channel_select_channel_types_setter():
    select = discord.ui.ChannelSelect()
    select.channel_types = [discord.ChannelType.forum]
    assert select.channel_types == [discord.ChannelType.forum]


def test_mentionable_select_init():
    select = discord.ui.MentionableSelect(placeholder="Select users or roles")
    assert select.placeholder == "Select users or roles"
