import asyncio
import logging
import os

import aiohttp
import discord
from discord.ext import commands

from .custom_context import MyContext

__all__ = ('MyBot',)

# Logging is the important part for all projects.
# set the logger up for your own purposes.
logger = logging.getLogger('bot')


def _get_prefix(bot: 'MyBot', message: discord.Message) -> str:
    """A method used to get the right prefix for the bot.

    Parameters
    ----------
    bot : MyBot
        Our custom bot, gets passed automatically.
    message : discord.Message
        A message to get a prefix from, gets passed automatically.

    Returns
    -------
    str
        The final prefix (specific for (DM,Text)channels).
    """
    if message.guild is None:
        # Since DMChannels are not located in guilds, i.e servers
        # we have to check whether a guild does not exist.
        # If so, we are declaring the prefix as 'dm '.
        prefix = 'dm '
    else:
        # In any else case we are declaring the prefix as 'ex '.
        prefix = 'ex '

    # Trigger a bot whenever it gets mentioned or the message starts
    # with the given prefix (with following commands).
    # Also, the inner function requires 2 parameters to get passed: bot, msg.
    # We are consequently passing them to get the results.
    # Learn more at: https://discordpy.rtfd.io/en/stable/ext/commands/api.html#discord.ext.commands.when_mentioned_or
    return commands.when_mentioned_or(prefix)(bot, message)


class MyBot(commands.Bot):
    """Custom `commands.Bot` implementation with some additional features."""

    def __init__(self, **kwargs):
        # Get more kwargs here: https://discordpy.rtfd.io/en/stable/api.html#discord.Client
        super().__init__(
            command_prefix=_get_prefix,
            activity=discord.Game(name='with commands.'),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, replied_user=False
            ),
            **kwargs
        )
        # LOOP-RELATED
        self.loop = asyncio.get_event_loop()
        # Creating a new session everytime you need to request
        # is considered as a bad practice. Here, we are declaring a
        # single session which can be called from everywhere in the project.
        # Learn more at: https://docs.aiohttp.org/en/stable/http_request_lifecycle.html#how-to-use-the-clientsession
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def on_ready(self) -> None:
        """Event that gets triggered everytime you successfully run the bot.

        Called when the bot is done preparing the data received from Discord.
        """
        logger.info('Logged in as: {0} | ID: {0.id}'.format(self.user))

    async def get_context(
        self, message: discord.Message, *, cls=MyContext
    ) -> MyContext:
        """The same get_context but with the custom context class.

        Parameters
        ----------
        message : discord.Message
            A message object to get the context from.
        cls : optional
            The classmethod parameter, by default MyContext

        Returns
        -------
        MyContext
            The context brought from the message.
        """
        return await super().get_context(message, cls=cls)

    async def close(self) -> None:
        """Overridden `Bot.close` method.

        This also closes the `aiohttp.ClientSession` instance.
        """
        await super().close()
        await self.session.close()

    @staticmethod
    def list_modules(cogs_path: str = 'cogs') -> list:
        return [md for md in os.listdir(cogs_path) if not md.startswith('_')]


# The preparing part.
bot = MyBot(description='A testing bot.')


@bot.command(name='modules')
async def command_modules(ctx: MyContext) -> None:
    """List all the available modules the bot has."""
    # With a new `bot.list_modules` function, we can list
    # all of the cogs located in the `./cogs` directory.
    await ctx.send('The list of my modules: ' + ', '.join(ctx.bot.list_modules))


# This is probably the most important part before running.
# You shouldn't keep your token that way shown below.
# It's more recommended to store it in a secret file that
# is only available to you, do not forget to .gitignore!
token = 'Paste your token here.'
bot.run(token)
