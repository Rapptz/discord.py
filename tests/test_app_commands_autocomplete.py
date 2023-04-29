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
from typing import List

import discord
import pytest
from discord import app_commands
from discord.utils import MISSING


async def free_function_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return []


async def invalid_free_function(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return []


class X(app_commands.Transformer):
    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return []


class ClassBased:
    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return []

    async def invalid(self, interaction: discord.Interaction, current: str, bad: int) -> List[app_commands.Choice[str]]:
        return []


lookup = ClassBased()
bound_autocomplete = lookup.autocomplete
invalid_bound_autocomplete = lookup.invalid


def test_free_function_autocomplete():
    @app_commands.command()
    @app_commands.autocomplete(name=free_function_autocomplete)
    async def cmd(interaction: discord.Interaction, name: str):
        ...

    param = cmd._params['name']
    assert param.autocomplete is not MISSING
    assert not param.autocomplete.pass_command_binding  # type: ignore


def test_invalid_free_function_autocomplete():
    with pytest.raises(TypeError):

        @app_commands.command()
        @app_commands.autocomplete(name=invalid_free_function)
        async def cmd(interaction: discord.Interaction, name: str):
            ...


def test_transformer_autocomplete():
    @app_commands.command()
    async def cmd(interaction: discord.Interaction, param: app_commands.Transform[str, X]):
        ...

    param = cmd._params['param']
    assert param.autocomplete is not MISSING
    assert getattr(param.autocomplete, '__self__', None) is not None
    assert not getattr(param.autocomplete, 'pass_command_binding', False)


first_instance = X()
second_instance = X()


def test_multiple_transformer_autocomplete():
    @app_commands.command()
    async def cmd(
        interaction: discord.Interaction,
        param: app_commands.Transform[str, first_instance],
        second: app_commands.Transform[str, second_instance],
    ):
        ...

    param = cmd._params['param']
    assert param.autocomplete is not MISSING
    assert getattr(param.autocomplete, '__self__', None) is first_instance
    assert not getattr(param.autocomplete, 'pass_command_binding', False)

    param = cmd._params['second']
    assert param.autocomplete is not MISSING
    assert getattr(param.autocomplete, '__self__', None) is second_instance
    assert not getattr(param.autocomplete, 'pass_command_binding', False)


def test_bound_function_autocomplete():
    @app_commands.command()
    @app_commands.autocomplete(name=bound_autocomplete)
    async def cmd(interaction: discord.Interaction, name: str):
        ...

    param = cmd._params['name']
    assert param.autocomplete is not MISSING
    assert getattr(param.autocomplete, '__self__', None) is lookup
    assert not getattr(param.autocomplete, 'pass_command_binding', False)


def test_invalid_bound_function_autocomplete():
    with pytest.raises(TypeError):

        @app_commands.command()
        @app_commands.autocomplete(name=invalid_bound_autocomplete)  # type: ignore
        async def cmd(interaction: discord.Interaction, name: str):
            ...


def test_group_function_autocomplete():
    class MyGroup(app_commands.Group):
        @app_commands.command()
        async def foo(self, interaction: discord.Interaction, name: str):
            ...

        @foo.autocomplete('name')
        async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
            return []

    g = MyGroup()
    param = g.foo._params['name']

    assert param.autocomplete is not MISSING
    assert getattr(param.autocomplete, '__self__', None) is None
    assert getattr(param.autocomplete, 'pass_command_binding', False)
