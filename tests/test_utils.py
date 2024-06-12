# -*- coding: utf-8 -*-

"""

Tests for discord.utils

"""

import datetime
import random
import collections
import secrets
import sys
import time
import typing

import pytest

from discord import utils


# Async generator for async support
async def async_iterate(array):
    for item in array:
        yield item


def test_cached_properties():
    # cached_property
    class Test:
        @utils.cached_property
        def time(self) -> float:
            return time.perf_counter()

    instance = Test()

    assert instance.time == instance.time

    # cached_slot_property
    class TestSlotted:
        __slots__ = '_cs_time'

        @utils.cached_slot_property('_cs_time')
        def time(self) -> float:
            return time.perf_counter()

    instance = TestSlotted()

    assert instance.time == instance.time
    assert not hasattr(instance, '__dict__')


@pytest.mark.parametrize(
    ('snowflake', 'time_tuple'),
    [
        (10000000000000000, (2015, 1, 28, 14, 16, 25)),
        (12345678901234567, (2015, 2, 4, 1, 37, 19)),
        (100000000000000000, (2015, 10, 3, 22, 44, 17)),
        (123456789012345678, (2015, 12, 7, 16, 13, 12)),
        (661720302316814366, (2020, 1, 1, 0, 0, 14)),
        (1000000000000000000, (2022, 7, 22, 11, 22, 59)),
    ],
)
def test_snowflake_time(snowflake: int, time_tuple: typing.Tuple[int, int, int, int, int, int]):
    dt = utils.snowflake_time(snowflake)

    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) == time_tuple

    assert utils.time_snowflake(dt, high=False) <= snowflake <= utils.time_snowflake(dt, high=True)


@pytest.mark.asyncio
async def test_get_find():
    # Generate a dictionary of random keys to values
    mapping = {secrets.token_bytes(32): secrets.token_bytes(32) for _ in range(100)}

    # Turn it into a shuffled iterable of pairs
    pair = collections.namedtuple('pair', 'key value')
    array = [pair(key=k, value=v) for k, v in mapping.items()]
    random.shuffle(array)

    # Confirm all values can be found
    for key, value in mapping.items():
        # Sync get
        item = utils.get(array, key=key)
        assert item is not None
        assert item.value == value

        # Async get
        item = await utils.get(async_iterate(array), key=key)
        assert item is not None
        assert item.value == value

        # Sync find
        item = utils.find(lambda i: i.key == key, array)
        assert item is not None
        assert item.value == value

        # Async find
        item = await utils.find(lambda i: i.key == key, async_iterate(array))
        assert item is not None
        assert item.value == value


def test_get_slots():
    class A:
        __slots__ = ('one', 'two')

    class B(A):
        __slots__ = ('three', 'four')

    class C(B):
        __slots__ = ('five', 'six')

    assert set(utils.get_slots(C)) == {'one', 'two', 'three', 'four', 'five', 'six'}


def test_valid_icon_size():
    # Valid icon sizes
    for size in [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
        assert utils.valid_icon_size(size)

    # Some not valid icon sizes
    for size in [-1, 0, 20, 103, 500, 8192]:
        assert not utils.valid_icon_size(size)


@pytest.mark.parametrize(
    ('url', 'code'),
    [
        ('https://discordapp.com/invite/dpy', 'dpy'),
        ('https://discord.com/invite/dpy', 'dpy'),
        ('https://discord.gg/dpy', 'dpy'),
    ],
)
def test_resolve_invite(url, code):
    assert utils.resolve_invite(url).code == code


@pytest.mark.parametrize(
    ('url', 'event_id'),
    [
        ('https://discordapp.com/invite/dpy', None),
        ('https://discord.com/invite/dpy', None),
        ('https://discord.gg/dpy', None),
        ('https://discordapp.com/invite/dpy?event=22222222', 22222222),
        ('https://discord.com/invite/dpy?event=4098', 4098),
        ('https://discord.gg/dpy?event=727', 727),
    ],
)
def test_resolve_invite_event(url, event_id: typing.Optional[int]):
    assert utils.resolve_invite(url).event == event_id


@pytest.mark.parametrize(
    ('url', 'code'),
    [
        ('https://discordapp.com/template/foobar', 'foobar'),
        ('https://discord.com/template/foobar', 'foobar'),
        ('https://discord.new/foobar', 'foobar'),
    ],
)
def test_resolve_template(url, code):
    assert utils.resolve_template(url) == code


@pytest.mark.parametrize(
    'mention', ['@everyone', '@here', '<@80088516616269824>', '<@!80088516616269824>', '<@&381978264698224660>']
)
def test_escape_mentions(mention):
    assert mention not in utils.escape_mentions(mention)
    assert mention not in utils.escape_mentions(f"one {mention} two")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('source', 'chunk_size', 'chunked'),
    [
        ([1, 2, 3, 4, 5, 6], 2, [[1, 2], [3, 4], [5, 6]]),
        ([1, 2, 3, 4, 5, 6], 3, [[1, 2, 3], [4, 5, 6]]),
        ([1, 2, 3, 4, 5, 6], 4, [[1, 2, 3, 4], [5, 6]]),
        ([1, 2, 3, 4, 5, 6], 5, [[1, 2, 3, 4, 5], [6]]),
    ],
)
async def test_as_chunks(source, chunk_size, chunked):
    assert [x for x in utils.as_chunks(source, chunk_size)] == chunked
    assert [x async for x in utils.as_chunks(async_iterate(source), chunk_size)] == chunked


@pytest.mark.parametrize(
    ('annotation', 'resolved'),
    [
        (datetime.datetime, datetime.datetime),
        ('datetime.datetime', datetime.datetime),
        ('typing.Union[typing.Literal["a"], typing.Literal["b"]]', typing.Union[typing.Literal["a"], typing.Literal["b"]]),
        ('typing.Union[typing.Union[int, str], typing.Union[bool, dict]]', typing.Union[int, str, bool, dict]),
    ],
)
def test_resolve_annotation(annotation, resolved):
    assert resolved == utils.resolve_annotation(annotation, globals(), locals(), None)


@pytest.mark.parametrize(
    ('annotation', 'resolved', 'check_cache'),
    [
        (datetime.datetime, datetime.datetime, False),
        ('datetime.datetime', datetime.datetime, True),
        (
            'typing.Union[typing.Literal["a"], typing.Literal["b"]]',
            typing.Union[typing.Literal["a"], typing.Literal["b"]],
            True,
        ),
        ('typing.Union[typing.Union[int, str], typing.Union[bool, dict]]', typing.Union[int, str, bool, dict], True),
    ],
)
def test_resolve_annotation_with_cache(annotation, resolved, check_cache):
    cache = {}

    assert resolved == utils.resolve_annotation(annotation, globals(), locals(), cache)

    if check_cache:
        assert len(cache) == 1

        cached_item = cache[annotation]

        latest = utils.resolve_annotation(annotation, globals(), locals(), cache)

        assert latest is cached_item
        assert typing.get_origin(latest) is typing.get_origin(resolved)
    else:
        assert len(cache) == 0


def test_resolve_annotation_optional_normalisation():
    value = utils.resolve_annotation('typing.Union[None, int]', globals(), locals(), None)
    assert value.__args__ == (int, type(None))


@pytest.mark.skipif(sys.version_info < (3, 10), reason="3.10 union syntax")
@pytest.mark.parametrize(
    ('annotation', 'resolved'),
    [
        ('int | None', typing.Optional[int]),
        ('str | int', typing.Union[str, int]),
        ('str | int | None', typing.Optional[typing.Union[str, int]]),
    ],
)
def test_resolve_annotation_310(annotation, resolved):
    assert resolved == utils.resolve_annotation(annotation, globals(), locals(), None)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="3.10 union syntax")
@pytest.mark.parametrize(
    ('annotation', 'resolved'),
    [
        ('int | None', typing.Optional[int]),
        ('str | int', typing.Union[str, int]),
        ('str | int | None', typing.Optional[typing.Union[str, int]]),
    ],
)
def test_resolve_annotation_with_cache_310(annotation, resolved):
    cache = {}

    assert resolved == utils.resolve_annotation(annotation, globals(), locals(), cache)
    assert typing.get_origin(resolved) is typing.Union

    assert len(cache) == 1

    cached_item = cache[annotation]

    latest = utils.resolve_annotation(annotation, globals(), locals(), cache)
    assert latest is cached_item
    assert typing.get_origin(latest) is typing.get_origin(resolved)


# is_inside_class tests


def not_a_class():
    def not_a_class_either():
        pass

    return not_a_class_either


class ThisIsAClass:
    def in_a_class(self):
        def not_directly_in_a_class():
            pass

        return not_directly_in_a_class

    @classmethod
    def a_class_method(cls):
        def not_directly_in_a_class():
            pass

        return not_directly_in_a_class

    @staticmethod
    def a_static_method():
        def not_directly_in_a_class():
            pass

        return not_directly_in_a_class

    class SubClass:
        pass


def test_is_inside_class():
    assert not utils.is_inside_class(not_a_class)
    assert not utils.is_inside_class(not_a_class())
    assert not utils.is_inside_class(ThisIsAClass)
    assert utils.is_inside_class(ThisIsAClass.in_a_class)
    assert utils.is_inside_class(ThisIsAClass.a_class_method)
    assert utils.is_inside_class(ThisIsAClass.a_static_method)
    assert not utils.is_inside_class(ThisIsAClass().in_a_class())
    assert not utils.is_inside_class(ThisIsAClass.a_class_method())
    assert not utils.is_inside_class(ThisIsAClass().a_static_method())
    assert not utils.is_inside_class(ThisIsAClass.a_static_method())
    # Only really designed for callables, although I guess it is callable due to the constructor
    assert utils.is_inside_class(ThisIsAClass.SubClass)


@pytest.mark.parametrize(
    ('dt', 'style', 'formatted'),
    [
        (datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), None, '<t:0>'),
        (datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), None, '<t:1577836800>'),
        (datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), 'F', '<t:1577836800:F>'),
        (datetime.datetime(2033, 5, 18, 3, 33, 20, 0, tzinfo=datetime.timezone.utc), 'D', '<t:2000000000:D>'),
    ],
)
def test_format_dt(dt: datetime.datetime, style: typing.Optional[utils.TimestampStyle], formatted: str):
    assert utils.format_dt(dt, style=style) == formatted


@pytest.mark.parametrize(
    ("parameters", "flattened"),
    [
        # Python 3.8: Literal[Literal[0]].__args__ == (Literal[0],)
        # Python 3.x: Literal[Literal[0]].__args__ == (0,)
        ([], ()),
        ([0, 1, 2], (0, 1, 2)),
        ([0, typing.Literal["a", 1], "b"], (0, "a", 1, "b")),
        ([0, "a", typing.Literal[1, "b", 2], typing.Literal["c"]], (0, "a", 1, "b", 2, "c")),
    ],
)
def test_flatten_literal_params(parameters: typing.Iterable[typing.Any], flattened: typing.Tuple[typing.Any, ...]) -> None:
    assert utils.flatten_literal_params(parameters) == flattened


def test__human_join() -> None:
    assert utils._human_join([]) == ""
    assert utils._human_join(["cat"]) == "cat"
    assert utils._human_join(["cat", "dog"]) == "cat or dog"
    assert utils._human_join(["cat", "dog", "fish"]) == "cat, dog or fish"
    assert utils._human_join(["cat", "dog", "fish", "bird"], delimiter="; ", final="and") == "cat; dog; fish and bird"
