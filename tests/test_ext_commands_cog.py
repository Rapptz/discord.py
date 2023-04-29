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

from collections.abc import Coroutine
from typing import Any, Type
from unittest.mock import AsyncMock

import discord
from discord import app_commands
from discord.ext import commands
import pytest


@pytest.fixture
def mock_bot() -> object:
    return object()


@pytest.fixture
def mock_interaction() -> object:
    return object()


@pytest.fixture
def mock_on_group_error_handler() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_on_sub_group_error_handler() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sub_group_class() -> Type[app_commands.Group]:
    class MySubGroup(app_commands.Group):
        @app_commands.command()
        async def my_sub_group_command(self, interaction: discord.Interaction) -> None:
            ...

    return MySubGroup


@pytest.fixture
def sub_group_with_handler_class(mock_on_sub_group_error_handler: AsyncMock) -> Type[app_commands.Group]:
    class MySubGroup(app_commands.Group):
        @app_commands.command()
        async def my_sub_group_command(self, interaction: discord.Interaction) -> None:
            ...

        def on_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
        ) -> Coroutine[Any, Any, None]:
            return mock_on_sub_group_error_handler(self, interaction, error)

    return MySubGroup


@pytest.fixture
def group_class(sub_group_class: Type[app_commands.Group]) -> Type[app_commands.Group]:
    class MyGroup(app_commands.Group):
        my_sub_group = sub_group_class()

        @app_commands.command()
        async def my_group_command(self, interaction: discord.Interaction) -> None:
            ...

    return MyGroup


@pytest.fixture
def group_with_handler_class(
    sub_group_class: Type[app_commands.Group], mock_on_group_error_handler: AsyncMock
) -> Type[app_commands.Group]:
    class MyGroupWithHandler(app_commands.Group):
        my_sub_group = sub_group_class()

        @app_commands.command()
        async def my_group_command(self, interaction: discord.Interaction) -> None:
            ...

        def on_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
        ) -> Coroutine[Any, Any, None]:
            return mock_on_group_error_handler(self, interaction, error)

    return MyGroupWithHandler


@pytest.fixture
def group_with_handler_and_sub_group_handler_class(
    sub_group_with_handler_class: Type[app_commands.Group], mock_on_group_error_handler: AsyncMock
) -> Type[app_commands.Group]:
    class MyGroupWithHandler(app_commands.Group):
        my_sub_group = sub_group_with_handler_class()

        @app_commands.command()
        async def my_group_command(self, interaction: discord.Interaction) -> None:
            ...

        def on_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
        ) -> Coroutine[Any, Any, None]:
            return mock_on_group_error_handler(self, interaction, error)

    return MyGroupWithHandler


class TestCog:
    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_command(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            @app_commands.command()
            async def my_command(self, interaction: discord.Interaction) -> None:
                ...

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_command._invoke_error_handlers(mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_command_with_error_handler(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
    ) -> None:
        on_error = AsyncMock()
        on_command_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            @app_commands.command()
            async def my_command(self, interaction: discord.Interaction) -> None:
                ...

            @my_command.error
            async def on_my_command_with_handler_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> None:
                await on_command_error(self, interaction, error)

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_command._invoke_error_handlers(mock_interaction, error)
        on_command_error.assert_awaited_once_with(cog, mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_group(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        group_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            my_group = group_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_group.my_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_sub_group(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        group_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            my_group = group_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_group.my_sub_group.my_sub_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_group_with_handler(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        mock_on_group_error_handler: AsyncMock,
        group_with_handler_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            my_group = group_with_handler_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_group.my_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        mock_on_group_error_handler.assert_awaited_once_with(cog.my_group, mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_sub_group_with_parent_handler(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        mock_on_group_error_handler: AsyncMock,
        group_with_handler_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            my_group = group_with_handler_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_group.my_sub_group.my_sub_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        mock_on_group_error_handler.assert_awaited_once_with(cog.my_group, mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_sub_group_with_handler_and_parent_handler(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        mock_on_group_error_handler: AsyncMock,
        mock_on_sub_group_error_handler: AsyncMock,
        group_with_handler_and_sub_group_handler_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.Cog):
            my_group = group_with_handler_and_sub_group_handler_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_group.my_sub_group.my_sub_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        mock_on_sub_group_error_handler.assert_awaited_once_with(cog.my_group.my_sub_group, mock_interaction, error)  # type: ignore
        mock_on_group_error_handler.assert_awaited_once_with(cog.my_group, mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)


class TestGroupCog:
    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_command(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.GroupCog):
            @app_commands.command()
            async def my_command(self, interaction: discord.Interaction) -> None:
                ...

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_command._invoke_error_handlers(mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_command_with_error_handler(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
    ) -> None:
        on_error = AsyncMock()
        on_command_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.GroupCog):
            @app_commands.command()
            async def my_command(self, interaction: discord.Interaction) -> None:
                ...

            @my_command.error
            async def on_my_command_with_handler_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> None:
                await on_command_error(self, interaction, error)

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_command._invoke_error_handlers(mock_interaction, error)
        on_command_error.assert_awaited_once_with(cog, mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_sub_group(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        sub_group_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.GroupCog):
            my_sub_group = sub_group_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_sub_group.my_sub_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        on_error.assert_awaited_once_with(cog, mock_interaction, error)

    @pytest.mark.asyncio
    async def test_cog_app_command_error_from_sub_group_with_handler(
        self,
        mock_bot: commands.Bot,
        mock_interaction: discord.Interaction,
        mock_on_sub_group_error_handler: AsyncMock,
        sub_group_with_handler_class: Type[app_commands.Group],
    ) -> None:
        on_error = AsyncMock()
        error = app_commands.CheckFailure()

        class MyCog(commands.GroupCog):
            my_sub_group = sub_group_with_handler_class()

            def cog_app_command_error(
                self,
                interaction: discord.Interaction,
                error: app_commands.AppCommandError,
            ) -> Coroutine[Any, Any, None]:
                return on_error(self, interaction, error)

        cog = MyCog(mock_bot)

        await cog.my_sub_group.my_sub_group_command._invoke_error_handlers(mock_interaction, error)  # type: ignore
        mock_on_sub_group_error_handler.assert_awaited_once_with(cog.my_sub_group, mock_interaction, error)
        on_error.assert_awaited_once_with(cog, mock_interaction, error)
