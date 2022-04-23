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


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        ('0xFF1294', 0xFF1294),
        ('0xff1294', 0xFF1294),
        ('0xFFF', 0xFFFFFF),
        ('0xfff', 0xFFFFFF),
        ('#abcdef', 0xABCDEF),
        ('#ABCDEF', 0xABCDEF),
        ('#ABC', 0xAABBCC),
        ('#abc', 0xAABBCC),
        ('rgb(68,36,59)', 0x44243B),
        ('rgb(26.7%, 14.1%, 23.1%)', 0x44243B),
        ('rgb(20%, 24%, 56%)', 0x333D8F),
        ('rgb(20%, 23.9%, 56.1%)', 0x333D8F),
        ('rgb(51, 61, 143)', 0x333D8F),
    ],
)
def test_from_str(value, expected):
    assert discord.Colour.from_str(value) == discord.Colour(expected)


@pytest.mark.parametrize(
    ('value'),
    [
        'not valid',
        '0xYEAH',
        '#YEAH',
        '#yeah',
        'yellow',
        'rgb(-10, -20, -30)',
        'rgb(30, -1, 60)',
        'invalid(a, b, c)',
        'rgb(',
    ],
)
def test_from_str_failures(value):
    with pytest.raises(ValueError):
        discord.Colour.from_str(value)
