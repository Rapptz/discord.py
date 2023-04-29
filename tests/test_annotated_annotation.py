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
from typing import Optional
from typing_extensions import Annotated

import discord
from discord import app_commands
from discord.ext import commands

import pytest

def test_annotated_annotation():
    # can't exactly test if the parameter is the same, so just test if it raises something
    @app_commands.command()
    async def foo(interaction: discord.Interaction, param: Annotated[float, Optional[int]]):
        pass


    def to_hex(arg: str) -> int:
        return int(arg, 16)

    class Flag(commands.FlagConverter):
        thing: Annotated[int, to_hex]

    assert Flag.get_flags()['thing'].annotation == to_hex

    @commands.command()
    async def bar(ctx: commands.Context, param: Annotated[float, Optional[int]]):
        pass

    assert bar.clean_params['param'].annotation == Optional[int]

    @commands.command()
    async def nested(ctx: commands.Context, param: Optional[Annotated[str, int]]):
        pass

    assert nested.clean_params['param'].annotation == Optional[int]

