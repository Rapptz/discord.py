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

from io import BytesIO

import discord
import pytest


FILE = BytesIO()


def test_file_with_no_name():
    f = discord.File('.gitignore')
    assert f.filename == '.gitignore'


def test_io_with_no_name():
    f = discord.File(FILE)
    assert f.filename == 'untitled'


def test_file_with_name():
    f = discord.File('.gitignore', 'test')
    assert f.filename == 'test'


def test_io_with_name():
    f = discord.File(FILE, 'test')
    assert f.filename == 'test'


def test_file_with_no_name_and_spoiler():
    f = discord.File('.gitignore', spoiler=True)
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_with_spoiler_name_and_implicit_spoiler():
    f = discord.File('.gitignore', 'SPOILER_.gitignore')
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_with_spoiler_name_and_spoiler():
    f = discord.File('.gitignore', 'SPOILER_.gitignore', spoiler=True)
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_with_spoiler_name_and_not_spoiler():
    f = discord.File('.gitignore', 'SPOILER_.gitignore', spoiler=False)
    assert f.filename == '.gitignore'
    assert f.spoiler == False


def test_file_with_name_and_double_spoiler_and_implicit_spoiler():
    f = discord.File('.gitignore', 'SPOILER_SPOILER_.gitignore')
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_with_name_and_double_spoiler_and_spoiler():
    f = discord.File('.gitignore', 'SPOILER_SPOILER_.gitignore', spoiler=True)
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_with_name_and_double_spoiler_and_not_spoiler():
    f = discord.File('.gitignore', 'SPOILER_SPOILER_.gitignore', spoiler=False)
    assert f.filename == '.gitignore'
    assert f.spoiler == False


def test_file_with_spoiler_with_overriding_name_not_spoiler():
    f = discord.File('.gitignore', spoiler=True)
    f.filename = '.gitignore'
    assert f.filename == '.gitignore'
    assert f.spoiler == False


def test_file_with_spoiler_with_overriding_name_spoiler():
    f = discord.File('.gitignore', spoiler=True)
    f.filename = 'SPOILER_.gitignore'
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_not_spoiler_with_overriding_name_not_spoiler():
    f = discord.File('.gitignore')
    f.filename = '.gitignore'
    assert f.filename == '.gitignore'
    assert f.spoiler == False


def test_file_not_spoiler_with_overriding_name_spoiler():
    f = discord.File('.gitignore')
    f.filename = 'SPOILER_.gitignore'
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_not_spoiler_with_overriding_name_double_spoiler():
    f = discord.File('.gitignore')
    f.filename = 'SPOILER_SPOILER_.gitignore'
    assert f.filename == 'SPOILER_.gitignore'
    assert f.spoiler == True


def test_file_reset():
    f = discord.File('.gitignore')

    f.reset(seek=True)
    assert f.fp.tell() == 0

    f.reset(seek=False)
    assert f.fp.tell() == 0


def test_io_reset():
    f = discord.File(FILE)

    f.reset(seek=True)
    assert f.fp.tell() == 0

    f.reset(seek=False)
    assert f.fp.tell() == 0


def test_io_failure():
    class NonSeekableReadable(BytesIO):
        def seekable(self):
            return False

        def readable(self):
            return False

    f = NonSeekableReadable()

    with pytest.raises(ValueError) as excinfo:
        discord.File(f)

    assert str(excinfo.value) == f"File buffer {f!r} must be seekable and readable"


def test_io_to_dict():
    buffer = BytesIO(b"test content")
    file = discord.File(buffer, filename="test.txt", description="test description")

    data = file.to_dict(0)
    assert data["id"] == 0
    assert data["filename"] == "test.txt"
    assert data["description"] == "test description"


def test_file_to_dict():
    f = discord.File('.gitignore', description="test description")

    data = f.to_dict(0)
    assert data["id"] == 0
    assert data["filename"] == ".gitignore"
    assert data["description"] == "test description"
