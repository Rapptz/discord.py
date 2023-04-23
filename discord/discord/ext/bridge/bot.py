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
from abc import ABC

from discord.interactions import Interaction
from discord.message import Message

from ..commands import AutoShardedBot as ExtAutoShardedBot
from ..commands import Bot as ExtBot
from .context import BridgeApplicationContext, BridgeExtContext
from .core import BridgeCommand, bridge_command

__all__ = ("Bot", "AutoShardedBot")


class BotBase(ABC):
    async def get_application_context(
        self, interaction: Interaction, cls=None
    ) -> BridgeApplicationContext:
        cls = cls if cls is not None else BridgeApplicationContext
        # Ignore the type hinting error here. BridgeApplicationContext is a subclass of ApplicationContext, and since
        # we gave it cls, it will be used instead.
        return await super().get_application_context(interaction, cls=cls)  # type: ignore

    async def get_context(self, message: Message, cls=None) -> BridgeExtContext:
        cls = cls if cls is not None else BridgeExtContext
        # Ignore the type hinting error here. BridgeExtContext is a subclass of Context, and since we gave it cls, it
        # will be used instead.
        return await super().get_context(message, cls=cls)  # type: ignore

    def add_bridge_command(self, command: BridgeCommand):
        """Takes a :class:`.BridgeCommand` and adds both a slash and traditional (prefix-based) version of the command
        to the bot.
        """
        # Ignore the type hinting error here. All subclasses of BotBase pass the type checks.
        command.add_to(self)  # type: ignore

    def bridge_command(self, **kwargs):
        """A shortcut decorator that invokes :func:`bridge_command` and adds it to
        the internal command list via :meth:`~.Bot.add_bridge_command`.

        Returns
        --------
        Callable[..., :class:`BridgeCommand`]
            A decorator that converts the provided method into an :class:`.BridgeCommand`, adds both a slash and
            traditional (prefix-based) version of the command to the bot, and returns the :class:`.BridgeCommand`.
        """

        def decorator(func) -> BridgeCommand:
            result = bridge_command(**kwargs)(func)
            self.add_bridge_command(result)
            return result

        return decorator


class Bot(BotBase, ExtBot):
    """Represents a discord bot, with support for cross-compatibility between command types.

    This class is a subclass of :class:`.ext.commands.Bot` and as a result
    anything that you can do with a :class:`.ext.commands.Bot` you can do with
    this bot.

    .. versionadded:: 2.0
    """

    pass


class AutoShardedBot(BotBase, ExtAutoShardedBot):
    """This is similar to :class:`.Bot` except that it is inherited from
    :class:`.ext.commands.AutoShardedBot` instead.

    .. versionadded:: 2.0
    """

    pass
