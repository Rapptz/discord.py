# This example covers advanced startup options and uses some real world examples for why you may need them.

import asyncio
import logging
import os

from typing import Optional

import asyncpg  # asyncpg is not a dependency of the discord.py, and is only included here for illustrative purposes.
import discord
from discord.ext import commands
from aiohttp import ClientSession


class CustomBot(commands.Bot):
    def __init__(
        self,
        *args,
        initial_extensions: list,
        db_pool: asyncpg.Pool,
        web_client: ClientSession,
        testing_guild_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.db_pool = db_pool
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions

    async def setup_hook(self) -> None:

        # here, we are loading extensions prior to sync to ensure we are syncing interactions defined in those extensions.

        for extension in self.initial_extensions:
            await self.load_extension(extension)

        # In overriding setup hook,
        # we can do things that require a bot prior to starting to process events from the websocket.
        # In this case, we are using this to ensure that once we are connected, we sync for the testing guild.
        # You should not do this for every guild or for global sync, those should only be synced when changes happen.
        if self.testing_guild_id:
            await self.tree.sync(guild=discord.Object(self.testing_guild_id))

        # This would also be a good place to connect to our database and
        # load anything that should be in memory prior to handling events.


async def main():

    # When taking over how the bot process is run, you become responsible for a few additional things.

    # 1. logging

    # for this example, we're just going to use some basic defaults provided by python
    # for more info on setting up logging, see https://docs.python.org/3/howto/logging.html
    logging.basicConfig(level=logging.INFO)

    # One of the reasons to take over more of the process though
    # is to ensure use with other libraries or tools which also require their own cleanup.

    # Here we have a web client and a database pool, both of which do cleanup at exit.
    # We also have our bot, which depends on both of these.

    async with ClientSession() as our_client, asyncpg.create_pool(user='postgres', command_timeout=30) as pool:
        # 2. We become responsible for starting the bot.

        exts = ["general", "mod", "dice"]
        async with CustomBot(commands.when_mentioned, db_pool=pool, web_client=our_client, initial_extensions=exts) as bot:
            await bot.start(os.getenv('TOKEN', ''))


# For most use cases, after defining what needs to run, we can just tell asyncio to run it:
asyncio.run(main())
