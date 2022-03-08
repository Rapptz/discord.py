# -*- coding: utf-8 -*-

"""

Tests for discord.ext.tasks

"""

import asyncio
import datetime

import pytest

from discord import utils
from discord.ext import tasks


@pytest.mark.asyncio
async def test_explicit_initial_runs_tomorrow_single():
    now = utils.utcnow()

    if not ((0, 4) < (now.hour, now.minute) < (23, 59)):
        await asyncio.sleep(5 * 60)  # sleep for 5 minutes

    now = utils.utcnow()

    has_run = False

    async def inner():
        nonlocal has_run
        has_run = True

    time = utils.utcnow() - datetime.timedelta(minutes=1)

    # a loop that should have an initial run tomorrow
    loop = tasks.loop(time=datetime.time(hour=time.hour, minute=time.minute))(inner)

    loop.start()
    await asyncio.sleep(1)

    try:
        assert not has_run
    finally:
        loop.cancel()


@pytest.mark.asyncio
async def test_explicit_initial_runs_tomorrow_multi():
    now = utils.utcnow()

    if not ((0, 4) < (now.hour, now.minute) < (23, 59)):
        await asyncio.sleep(5 * 60)  # sleep for 5 minutes

    now = utils.utcnow()

    # multiple times that are in the past for today
    times = []
    for _ in range(3):
        now -= datetime.timedelta(minutes=1)
        times.append(datetime.time(hour=now.hour, minute=now.minute))

    has_run = False

    async def inner():
        nonlocal has_run
        has_run = True

    # a loop that should have an initial run tomorrow
    loop = tasks.loop(time=times)(inner)

    loop.start()
    await asyncio.sleep(1)

    try:
        assert not has_run
    finally:
        loop.cancel()
