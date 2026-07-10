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

from discord.http import handle_message_parameters
from discord.webhook.async_ import interaction_message_response_params


def make_file(index: int) -> discord.File:
    return discord.File(BytesIO(b'test'), filename=f'test-{index}.txt')


def test_handle_message_parameters_rejects_too_many_files():
    files = [make_file(index) for index in range(11)]

    with pytest.raises(ValueError, match='files has a maximum of 10 elements'):
        handle_message_parameters(content='test', files=files)


def test_interaction_message_response_params_rejects_too_many_files():
    files = [make_file(index) for index in range(11)]

    with pytest.raises(ValueError, match='files has a maximum of 10 elements'):
        interaction_message_response_params(type=4, content='test', files=files)


