"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

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
from typing import Any, List, Union
import asyncio

import discord.commands.options
from discord.commands import Option, SlashCommand
from discord.enums import SlashCommandOptionType

from ..commands import AutoShardedBot as ExtAutoShardedBot
from ..commands import BadArgument
from ..commands import Bot as ExtBot
from ..commands import (
    Command,
    Converter,
    GuildChannelConverter,
    RoleConverter,
    UserConverter,
)

__all__ = ("BridgeCommand", "bridge_command", "BridgeExtCommand", "BridgeSlashCommand")

from ...utils import get
from ..commands.converter import _convert_to_bool


class BridgeSlashCommand(SlashCommand):
    """
    A subclass of :class:`.SlashCommand` that is used to implement bridge commands.
    """

    ...


class BridgeExtCommand(Command):
    """
    A subclass of :class:`.ext.commands.Command` that is used to implement bridge commands.
    """

    ...


class BridgeCommand:
    """
    This is the base class for commands that are compatible with both traditional (prefix-based) commands and slash
    commands.

    Parameters
    ----------
    callback: Callable[[:class:`.BridgeContext`, ...], Awaitable[Any]]
        The callback to invoke when the command is executed. The first argument will be a :class:`BridgeContext`,
        and any additional arguments will be passed to the callback. This callback must be a coroutine.
    kwargs: Optional[Dict[:class:`str`, Any]]
        Keyword arguments that are directly passed to the respective command constructors.
    """

    def __init__(self, callback, **kwargs):
        self.callback = callback
        self.kwargs = kwargs

        self.ext_command = BridgeExtCommand(self.callback, **self.kwargs)
        self.application_command = BridgeSlashCommand(self.callback, **self.kwargs)

    def get_ext_command(self):
        """A method to get the ext.commands version of this command.

        Returns
        -------
        :class:`BridgeExtCommand`
            The respective traditional (prefix-based) version of the command.
        """
        return self.ext_command

    def get_application_command(self):
        """A method to get the discord.commands version of this command.

        Returns
        -------
        :class:`BridgeSlashCommand`
            The respective slash command version of the command.
        """
        return self.application_command

    def add_to(self, bot: Union[ExtBot, ExtAutoShardedBot]) -> None:
        """Adds the command to a bot.

        Parameters
        ----------
        bot: Union[:class:`.Bot`, :class:`.AutoShardedBot`]
            The bot to add the command to.
        """

        bot.add_command(self.ext_command)
        bot.add_application_command(self.application_command)

    def error(self, coro):
        """A decorator that registers a coroutine as a local error handler.

        This error handler is limited to the command it is defined to.
        However, higher scope handlers (per-cog and global) are still
        invoked afterwards as a catch-all. This handler also functions as
        the handler for both the prefixed and slash versions of the command.

        This error handler takes two parameters, a :class:`.BridgeContext` and
        a :class:`~discord.DiscordException`.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the local error handler.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The error handler must be a coroutine.")

        self.ext_command.on_error = coro
        self.application_command.on_error = coro

        return coro

    def before_invoke(self, coro):
        """A decorator that registers a coroutine as a pre-invoke hook.

        This hook is called directly before the command is called, making
        it useful for any sort of set up required. This hook is called
        for both the prefixed and slash versions of the command.

        This pre-invoke hook takes a sole parameter, a :class:`.BridgeContext`.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The pre-invoke hook must be a coroutine.")

        self.ext_command.before_invoke = coro
        self.application_command.before_invoke = coro

        return coro

    def after_invoke(self, coro):
        """A decorator that registers a coroutine as a post-invoke hook.

        This hook is called directly after the command is called, making it
        useful for any sort of clean up required. This hook is called for
        both the prefixed and slash versions of the command.

        This post-invoke hook takes a sole parameter, a :class:`.BridgeContext`.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The post-invoke hook must be a coroutine.")

        self.ext_command.after_invoke = coro
        self.application_command.after_invoke = coro

        return coro


def bridge_command(**kwargs):
    """A decorator that is used to wrap a function as a command.

    Parameters
    ----------
    kwargs: Optional[Dict[:class:`str`, Any]]
        Keyword arguments that are directly passed to the respective command constructors.
    """

    def decorator(callback):
        return BridgeCommand(callback, **kwargs)

    return decorator


class MentionableConverter(Converter):
    """A converter that can convert a mention to a user or a role."""

    async def convert(self, ctx, argument):
        try:
            return await RoleConverter().convert(ctx, argument)
        except BadArgument:
            return await UserConverter().convert(ctx, argument)


def attachment_callback(*args):  # pylint: disable=unused-argument
    raise ValueError("Attachments are not supported for bridge commands.")


BRIDGE_CONVERTER_MAPPING = {
    SlashCommandOptionType.string: str,
    SlashCommandOptionType.integer: int,
    SlashCommandOptionType.boolean: lambda val: _convert_to_bool(str(val)),
    SlashCommandOptionType.user: UserConverter,
    SlashCommandOptionType.channel: GuildChannelConverter,
    SlashCommandOptionType.role: RoleConverter,
    SlashCommandOptionType.mentionable: MentionableConverter,
    SlashCommandOptionType.number: float,
    SlashCommandOptionType.attachment: attachment_callback,
}


class BridgeOption(Option, Converter):
    async def convert(self, ctx, argument: str) -> Any:
        try:
            if self.converter is not None:
                converted = await self.converter.convert(ctx, argument)
            else:
                converter = BRIDGE_CONVERTER_MAPPING[self.input_type]
                if issubclass(converter, Converter):
                    converted = await converter().convert(ctx, argument)  # type: ignore # protocol class
                else:
                    converted = converter(argument)

            if self.choices:
                choices_names: List[Union[str, int, float]] = [
                    choice.name for choice in self.choices
                ]
                if converted in choices_names and (
                    choice := get(self.choices, name=converted)
                ):
                    converted = choice.value
                else:
                    choices = [choice.value for choice in self.choices]
                    if converted not in choices:
                        raise ValueError(
                            f"{argument} is not a valid choice. Valid choices: {list(set(choices_names + choices))}"
                        )

            return converted
        except ValueError as exc:
            raise BadArgument() from exc


discord.commands.options.Option = BridgeOption
