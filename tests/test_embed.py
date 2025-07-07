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

import datetime

import discord
import pytest


@pytest.mark.parametrize(
    ('title', 'description', 'colour', 'url'),
    [
        ('title', 'description', 0xABCDEF, 'https://example.com'),
        ('title', 'description', 0xFF1294, None),
        ('title', 'description', discord.Colour(0x333D8F), 'https://example.com'),
        ('title', 'description', discord.Colour(0x44243B), None),
    ],
)
def test_embed_initialization(title, description, colour, url):
    embed = discord.Embed(title=title, description=description, colour=colour, url=url)
    assert embed.title == title
    assert embed.description == description
    assert embed.colour == colour or embed.colour == discord.Colour(colour)
    assert embed.url == url


@pytest.mark.parametrize(
    ('text', 'icon_url'),
    [
        ('Hello discord.py', 'https://example.com'),
        ('text', None),
        (None, 'https://example.com'),
        (None, None),
    ],
)
def test_embed_set_footer(text, icon_url):
    embed = discord.Embed()
    embed.set_footer(text=text, icon_url=icon_url)
    assert embed.footer.text == text
    assert embed.footer.icon_url == icon_url


def test_embed_remove_footer():
    embed = discord.Embed()
    embed.set_footer(text='Hello discord.py', icon_url='https://example.com')
    embed.remove_footer()
    assert embed.footer.text is None
    assert embed.footer.icon_url is None


@pytest.mark.parametrize(
    ('name', 'url', 'icon_url'),
    [
        ('Rapptz', 'http://example.com', 'http://example.com/icon.png'),
        ('NCPlayz', None, 'http://example.com/icon.png'),
        ('Jackenmen', 'http://example.com', None),
    ],
)
def test_embed_set_author(name, url, icon_url):
    embed = discord.Embed()
    embed.set_author(name=name, url=url, icon_url=icon_url)
    assert embed.author.name == name
    assert embed.author.url == url
    assert embed.author.icon_url == icon_url


def test_embed_remove_author():
    embed = discord.Embed()
    embed.set_author(name='Rapptz', url='http://example.com', icon_url='http://example.com/icon.png')
    embed.remove_author()
    assert embed.author.name is None
    assert embed.author.url is None
    assert embed.author.icon_url is None


@pytest.mark.parametrize(
    ('thumbnail'),
    [
        ('http://example.com'),
        (None),
    ],
)
def test_embed_set_thumbnail(thumbnail):
    embed = discord.Embed()
    embed.set_thumbnail(url=thumbnail)
    assert embed.thumbnail.url == thumbnail


@pytest.mark.parametrize(
    ('image'),
    [
        ('http://example.com'),
        (None),
    ],
)
def test_embed_set_image(image):
    embed = discord.Embed()
    embed.set_image(url=image)
    assert embed.image.url == image


@pytest.mark.parametrize(
    ('name', 'value', 'inline'),
    [
        ('music', 'music value', True),
        ('sport', 'sport value', False),
    ],
)
def test_embed_add_field(name, value, inline):
    embed = discord.Embed()
    embed.add_field(name=name, value=value, inline=inline)
    assert len(embed.fields) == 1
    assert embed.fields[0].name == name
    assert embed.fields[0].value == value
    assert embed.fields[0].inline == inline


def test_embed_insert_field():
    embed = discord.Embed()
    embed.add_field(name='name', value='value', inline=True)
    embed.insert_field_at(0, name='name 2', value='value 2', inline=False)
    assert embed.fields[0].name == 'name 2'
    assert embed.fields[0].value == 'value 2'
    assert embed.fields[0].inline is False


def test_embed_set_field_at():
    embed = discord.Embed()
    embed.add_field(name='name', value='value', inline=True)
    embed.set_field_at(0, name='name 2', value='value 2', inline=False)
    assert embed.fields[0].name == 'name 2'
    assert embed.fields[0].value == 'value 2'
    assert embed.fields[0].inline is False


def test_embed_set_field_at_failure():
    embed = discord.Embed()
    with pytest.raises(IndexError):
        embed.set_field_at(0, name='name', value='value', inline=True)


def test_embed_clear_fields():
    embed = discord.Embed()
    embed.add_field(name="field 1", value="value 1", inline=False)
    embed.add_field(name="field 2", value="value 2", inline=False)
    embed.add_field(name="field 3", value="value 3", inline=False)
    embed.clear_fields()
    assert len(embed.fields) == 0


def test_embed_remove_field():
    embed = discord.Embed()
    embed.add_field(name='name', value='value', inline=True)
    embed.remove_field(0)
    assert len(embed.fields) == 0


@pytest.mark.parametrize(
    ('title', 'description', 'url'),
    [
        ('title 1', 'description 1', 'https://example.com'),
        ('title 2', 'description 2', None),
    ],
)
def test_embed_copy(title, description, url):
    embed = discord.Embed(title=title, description=description, url=url)
    embed_copy = embed.copy()

    assert embed == embed_copy
    assert embed.title == embed_copy.title
    assert embed.description == embed_copy.description
    assert embed.url == embed_copy.url


@pytest.mark.parametrize(
    ('title', 'description'),
    [
        ('title 1', 'description 1'),
        ('title 2', 'description 2'),
    ],
)
def test_embed_len(title, description):
    embed = discord.Embed(title=title, description=description)
    assert len(embed) == len(title) + len(description)


@pytest.mark.parametrize(
    ('title', 'description', 'fields', 'footer', 'author'),
    [
        (
            'title 1',
            'description 1',
            [('field name 1', 'field value 1'), ('field name 2', 'field value 2')],
            'footer 1',
            'author 1',
        ),
        ('title 2', 'description 2', [('field name 3', 'field value 3')], 'footer 2', 'author 2'),
    ],
)
def test_embed_len_with_options(title, description, fields, footer, author):
    embed = discord.Embed(title=title, description=description)
    for name, value in fields:
        embed.add_field(name=name, value=value)
    embed.set_footer(text=footer)
    embed.set_author(name=author)
    assert len(embed) == len(title) + len(description) + len("".join([name + value for name, value in fields])) + len(
        footer
    ) + len(author)


def test_embed_to_dict():
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    embed = discord.Embed(title="Test Title", description="Test Description", timestamp=timestamp)
    data = embed.to_dict()
    assert data['title'] == "Test Title"
    assert data['description'] == "Test Description"
    assert data['timestamp'] == timestamp.isoformat()


def test_embed_from_dict():
    data = {
        'title': 'Test Title',
        'description': 'Test Description',
        'url': 'http://example.com',
        'color': 0x00FF00,
        'timestamp': '2024-07-03T12:34:56+00:00',
    }
    embed = discord.Embed.from_dict(data)
    assert embed.title == 'Test Title'
    assert embed.description == 'Test Description'
    assert embed.url == 'http://example.com'
    assert embed.colour is not None and embed.colour.value == 0x00FF00
    assert embed.timestamp is not None and embed.timestamp.isoformat() == '2024-07-03T12:34:56+00:00'


@pytest.mark.parametrize(
    ('value'),
    [
        -0.5,
        '#FFFFFF',
    ],
)
def test_embed_colour_setter_failure(value):
    embed = discord.Embed()
    with pytest.raises(TypeError):
        embed.colour = value

@pytest.mark.parametrize(
    ('title', 'return_val'),
    [
        ('test', True),
        (None, False)
    ]
)
def test_embed_truthiness(title: str, return_val: bool) -> None:
    embed = discord.Embed(title=title)
    assert bool(embed) is return_val
