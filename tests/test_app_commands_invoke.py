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


from functools import wraps
import pytest
from typing import Awaitable, TYPE_CHECKING, Callable, Coroutine, Optional, TypeVar, Any, Type, List, Union

import discord

if TYPE_CHECKING:

    from typing_extensions import ParamSpec
    from discord.types.interactions import (
        ApplicationCommandInteraction as ApplicationCommandInteractionPayload,
        ChatInputApplicationCommandInteractionData as ChatInputApplicationCommandInteractionDataPayload,
        ApplicationCommandInteractionDataOption as ApplicationCommandInteractionDataOptionPayload,
    )

    P = ParamSpec('P')


T = TypeVar('T')


class MockCommandInteraction(discord.Interaction):
    @classmethod
    def _get_command_options(cls, **options: str) -> List[ApplicationCommandInteractionDataOptionPayload]:
        return [
            {
                'type': discord.AppCommandOptionType.string.value,
                'name': name,
                'value': value,
            }
            for name, value in options.items()
        ]

    @classmethod
    def _get_command_data(
        cls,
        command: Union[discord.app_commands.Command[Any, ..., Any], discord.app_commands.Group],
        options: List[ApplicationCommandInteractionDataOptionPayload],
    ) -> ChatInputApplicationCommandInteractionDataPayload:

        data: Union[ChatInputApplicationCommandInteractionDataPayload, ApplicationCommandInteractionDataOptionPayload] = {
            'type': discord.AppCommandType.chat_input.value,
            'name': command.name,
            'options': options,
        }

        if command.parent is None:
            data['id'] = hash(command)  # type: ignore # narrowing isn't possible
            return data  # type: ignore # see above
        else:
            return cls._get_command_data(command.parent, [data])

    def __init__(
        self,
        client: discord.Client,
        command: discord.app_commands.Command[Any, ..., Any],
        **options: str,
    ) -> None:

        data: ApplicationCommandInteractionPayload = {
            "id": 0,
            "application_id": 0,
            "token": "",
            "version": 1,
            "type": 2,
            "data": self._get_command_data(command, self._get_command_options(**options)),
        }
        super().__init__(data=data, state=client._connection)


client = discord.Client(intents=discord.Intents.default())


class MockTree(discord.app_commands.CommandTree):
    last_exception: Optional[discord.app_commands.AppCommandError]

    async def _call(self, interaction: discord.Interaction) -> None:
        self.last_exception = None
        return await super()._call(interaction)

    async def on_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        self.last_exception = error


tree = MockTree(client)


@tree.command()
async def test_command(interaction: discord.Interaction, foo: str) -> None:
    pass


def wrapper(func: Callable[P, Awaitable[T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    @wraps(func)
    async def deco(*args: P.args, **kwargs: P.kwargs) -> T:
        return await func(*args, **kwargs)

    return deco


@tree.command()
@wrapper
async def test_wrapped_command(interaction: discord.Interaction, foo: str) -> None:
    pass


@tree.command()
async def test_command_raises(interaction: discord.Interaction, foo: str) -> None:
    raise TypeError


@tree.command()
@wrapper
async def test_wrapped_command_raises(interaction: discord.Interaction, foo: str) -> None:
    raise TypeError


group = discord.app_commands.Group(name='group', description='...')
test_subcommand = group.command()(test_command.callback)
test_wrapped_subcommand = group.command()(test_wrapped_command.callback)
test_subcommand_raises = group.command()(test_command_raises.callback)
test_wrapped_subcommand_raises = group.command()(test_wrapped_command_raises.callback)
tree.add_command(group)


@pytest.mark.parametrize(
    ('command', 'raises'),
    [
        (test_command, None),
        (test_wrapped_command, None),
        (test_command_raises, TypeError),
        (test_wrapped_command_raises, TypeError),
        (test_subcommand, None),
        (test_wrapped_subcommand, None),
        (test_subcommand_raises, TypeError),
        (test_wrapped_subcommand_raises, TypeError),
    ],
)
@pytest.mark.asyncio
async def test_valid_command_invoke(
    command: discord.app_commands.Command[Any, ..., Any], raises: Optional[Type[BaseException]]
):
    interaction = MockCommandInteraction(client, command, foo='foo')
    await tree._call(interaction)

    if raises is None:
        assert tree.last_exception is None
    else:
        assert isinstance(tree.last_exception, discord.app_commands.CommandInvokeError)
        assert isinstance(tree.last_exception.original, raises)


@pytest.mark.parametrize(
    ('command',),
    [
        (test_command,),
        (test_wrapped_command,),
        (test_command_raises,),
        (test_wrapped_command_raises,),
        (test_subcommand,),
        (test_subcommand_raises,),
        (test_wrapped_subcommand,),
        (test_wrapped_subcommand_raises,),
    ],
)
@pytest.mark.asyncio
async def test_invalid_command_invoke(command: discord.app_commands.Command[Any, ..., Any]):
    interaction = MockCommandInteraction(client, command, bar='bar')
    await tree._call(interaction)

    assert isinstance(tree.last_exception, discord.app_commands.CommandSignatureMismatch)
