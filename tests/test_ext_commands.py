# -*- coding: utf-8 -*-

"""

Tests for discord.ext.commands.converter

"""

from typing import Optional, Union

import pytest

from discord.ext import commands


# converter tests


@pytest.mark.xfail
@pytest.mark.parametrize(('arg'), [str, None, Optional[str], Optional[int], Union[None, int], Union[int, None]])
def test_greedy_rejected_params(arg):
    _ = commands.Greedy[arg]
