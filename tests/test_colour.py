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
        ('0x#333D8F', 0x333D8F),
    ],
)
def test_from_str(value, expected):
    assert discord.Colour.from_str(value) == discord.Colour(expected)


@pytest.mark.parametrize(
    ('value'),
    [
        None,
        'not valid',
        '0xYEAH',
        '#YEAH',
        '#yeah',
        'yellow',
        'rgb(-10, -20, -30)',
        'rgb(30, -1, 60)',
        'invalid(a, b, c)',
        'rgb(',
        '#1000000',
        '#FFFFFFF',
        "rgb(101%, 50%, 50%)",
        "rgb(50%, -10%, 50%)",
        "rgb(50%, 50%, 150%)",
        "rgb(256, 100, 100)",
    ],
)
def test_from_str_failures(value):
    with pytest.raises(ValueError):
        discord.Colour.from_str(value)


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (discord.Colour.default(), 0x000000),
        (discord.Colour.teal(), 0x1ABC9C),
        (discord.Colour.dark_teal(), 0x11806A),
        (discord.Colour.brand_green(), 0x57F287),
        (discord.Colour.green(), 0x2ECC71),
        (discord.Colour.dark_green(), 0x1F8B4C),
        (discord.Colour.blue(), 0x3498DB),
        (discord.Colour.dark_blue(), 0x206694),
        (discord.Colour.purple(), 0x9B59B6),
        (discord.Colour.dark_purple(), 0x71368A),
        (discord.Colour.magenta(), 0xE91E63),
        (discord.Colour.dark_magenta(), 0xAD1457),
        (discord.Colour.gold(), 0xF1C40F),
        (discord.Colour.dark_gold(), 0xC27C0E),
        (discord.Colour.orange(), 0xE67E22),
        (discord.Colour.dark_orange(), 0xA84300),
        (discord.Colour.brand_red(), 0xED4245),
        (discord.Colour.red(), 0xE74C3C),
        (discord.Colour.dark_red(), 0x992D22),
        (discord.Colour.lighter_grey(), 0x95A5A6),
        (discord.Colour.dark_grey(), 0x607D8B),
        (discord.Colour.light_grey(), 0x979C9F),
        (discord.Colour.darker_grey(), 0x546E7A),
        (discord.Colour.og_blurple(), 0x7289DA),
        (discord.Colour.blurple(), 0x5865F2),
        (discord.Colour.greyple(), 0x99AAB5),
        (discord.Colour.ash_theme(), 0x2E2E34),
        (discord.Colour.dark_theme(), 0x1A1A1E),
        (discord.Colour.onyx_theme(), 0x070709),
        (discord.Colour.light_theme(), 0xFBFBFB),
        (discord.Colour.fuchsia(), 0xEB459E),
        (discord.Colour.yellow(), 0xFEE75C),
        (discord.Colour.ash_embed(), 0x37373E),
        (discord.Colour.dark_embed(), 0x242429),
        (discord.Colour.onyx_embed(), 0x131416),
        (discord.Colour.light_embed(), 0xFFFFFF),
        (discord.Colour.pink(), 0xEB459F),
    ],
)
def test_static_colours(value, expected):
    assert value.value == expected


@pytest.mark.parametrize(
    ('value', 'property', 'expected'),
    [
        (discord.Colour(0x000000), 'r', 0),
        (discord.Colour(0xFFFFFF), 'g', 255),
        (discord.Colour(0xABCDEF), 'b', 239),
        (discord.Colour(0x44243B), 'r', 68),
        (discord.Colour(0x333D8F), 'g', 61),
        (discord.Colour(0xDBFF00), 'b', 0),
    ],
)
def test_colour_properties(value, property, expected):
    assert getattr(value, property) == expected
