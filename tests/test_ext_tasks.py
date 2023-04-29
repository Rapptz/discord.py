# -*- coding: utf-8 -*-

"""

Tests for discord.ext.tasks

"""

import asyncio
import datetime

import pytest
import sys

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


def test_task_regression_issue7659():
    jst = datetime.timezone(datetime.timedelta(hours=9))

    # 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
    times = [datetime.time(hour=h, tzinfo=jst) for h in range(0, 24, 3)]

    @tasks.loop(time=times)
    async def loop():
        pass

    before_midnight = datetime.datetime(2022, 3, 12, 23, 50, 59, tzinfo=jst)
    after_midnight = before_midnight + datetime.timedelta(minutes=9, seconds=2)

    expected_before_midnight = datetime.datetime(2022, 3, 13, 0, 0, 0, tzinfo=jst)
    expected_after_midnight = datetime.datetime(2022, 3, 13, 3, 0, 0, tzinfo=jst)

    assert loop._get_next_sleep_time(before_midnight) == expected_before_midnight
    assert loop._get_next_sleep_time(after_midnight) == expected_after_midnight

    today = datetime.date.today()
    minute_before = [datetime.datetime.combine(today, time, tzinfo=jst) - datetime.timedelta(minutes=1) for time in times]

    for before, expected_time in zip(minute_before, times):
        expected = datetime.datetime.combine(today, expected_time, tzinfo=jst)
        actual = loop._get_next_sleep_time(before)
        assert actual == expected


def test_task_regression_issue7676():
    jst = datetime.timezone(datetime.timedelta(hours=9))

    # 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
    times = [datetime.time(hour=h, tzinfo=jst) for h in range(0, 24, 3)]

    @tasks.loop(time=times)
    async def loop():
        pass

    # Create pseudo UTC times
    now = utils.utcnow()
    today = now.date()
    times_before_in_utc = [
        datetime.datetime.combine(today, time, tzinfo=jst).astimezone(datetime.timezone.utc) - datetime.timedelta(minutes=1)
        for time in times
    ]

    for before, expected_time in zip(times_before_in_utc, times):
        actual = loop._get_next_sleep_time(before)
        actual_time = actual.timetz()
        assert actual_time == expected_time


@pytest.mark.skipif(sys.version_info < (3, 9), reason="zoneinfo requires 3.9")
def test_task_is_imaginary():
    import zoneinfo

    tz = zoneinfo.ZoneInfo('America/New_York')

    # 2:30 AM was skipped
    dt = datetime.datetime(2022, 3, 13, 2, 30, tzinfo=tz)
    assert tasks.is_imaginary(dt)

    now = utils.utcnow()
    # UTC time is never imaginary or ambiguous
    assert not tasks.is_imaginary(now)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="zoneinfo requires 3.9")
def test_task_is_ambiguous():
    import zoneinfo

    tz = zoneinfo.ZoneInfo('America/New_York')

    # 1:30 AM happened twice
    dt = datetime.datetime(2022, 11, 6, 1, 30, tzinfo=tz)
    assert tasks.is_ambiguous(dt)

    now = utils.utcnow()
    # UTC time is never imaginary or ambiguous
    assert not tasks.is_imaginary(now)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="zoneinfo requires 3.9")
@pytest.mark.parametrize(
    ('dt', 'key', 'expected'),
    [
        (datetime.datetime(2022, 11, 6, 1, 30), 'America/New_York', datetime.datetime(2022, 11, 6, 1, 30, fold=1)),
        (datetime.datetime(2022, 3, 13, 2, 30), 'America/New_York', datetime.datetime(2022, 3, 13, 3, 30)),
        (datetime.datetime(2022, 4, 8, 2, 30), 'America/New_York', datetime.datetime(2022, 4, 8, 2, 30)),
        (datetime.datetime(2023, 1, 7, 12, 30), 'UTC', datetime.datetime(2023, 1, 7, 12, 30)),
    ],
)
def test_task_date_resolve(dt, key, expected):
    import zoneinfo

    tz = zoneinfo.ZoneInfo(key)

    actual = tasks.resolve_datetime(dt.replace(tzinfo=tz))
    expected = expected.replace(tzinfo=tz)
    assert actual == expected
