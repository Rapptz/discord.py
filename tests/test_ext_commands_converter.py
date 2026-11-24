
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from discord.ext import commands


@pytest.fixture
def users():
    main_user = SimpleNamespace(
        id=123456789012345678,
        name="zaku956",
        global_name="Zaku",
        discriminator="0",
    )

    alt_user = SimpleNamespace(
        id=987654321098765432,
        name="tomoro0",
        global_name="zaku956",
        discriminator="0",
    )

    return main_user, alt_user


def make_context(users):
    cache = {user.id: user for user in users}

    bot = SimpleNamespace(
        get_user=Mock(side_effect=cache.get),
        fetch_user=AsyncMock(),
    )

    return SimpleNamespace(
        _state=SimpleNamespace(_users=cache),
        bot=bot,
        message=SimpleNamespace(mentions=list(users)),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("reverse_order", [False, True])
async def test_username_priority(users, reverse_order):
    main_user, alt_user = users

    if reverse_order:
        cached_users = [main_user, alt_user]
    else:
        cached_users = [alt_user, main_user]

    ctx = make_context(cached_users)
    result = await commands.UserConverter().convert(ctx, "zaku956")

    assert result is main_user


@pytest.mark.asyncio
async def test_global_name_fallback(users):
    _, alt_user = users

    ctx = make_context([alt_user])
    result = await commands.UserConverter().convert(ctx, "zaku956")

    assert result is alt_user


@pytest.mark.asyncio
async def test_unknown_user(users):
    ctx = make_context(users)

    with pytest.raises(commands.UserNotFound):
        await commands.UserConverter().convert(ctx, "unknown_user")


@pytest.mark.asyncio
async def test_discriminator_lookup(users):
    main_user, alt_user = users

    ctx = make_context([alt_user, main_user])
    result = await commands.UserConverter().convert(
        ctx, "zaku956#0"
    )

    assert result is main_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "argument",
    ["123456789012345678", "<@123456789012345678>"],
)
async def test_id_and_mention_lookup(users, argument):
    main_user, alt_user = users

    ctx = make_context([alt_user, main_user])
    result = await commands.UserConverter().convert(ctx, argument)

    assert result is main_user
    ctx.bot.fetch_user.assert_not_awaited()
