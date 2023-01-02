# In this example you will learn how to make cogs (not extensions)

import discord
from discord.ext import commands
from discord.ext.commands import HelpCommand
from discord import app_commands

from typing import Optional, Type, Any
from asyncio import sleep as async_sleep


class MyCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot  # Assign bot who is setuping cog

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.content.startswith('!ping'):
            await message.reply('Pong!')

    @commands.bot_has_permissions(administrator=True)
    @commands.command()
    async def admin_check(self, ctx: commands.Context):
        await ctx.send('You are admin!')

    @app_commands.command()
    @app_commands.describe(first='First number', second='Second number', msg='Message')
    async def test_app_command(self, interaction: discord.Interaction, first: int, second: int, msg: str):
        await interaction.response.send_message('Hello, world!')
        await async_sleep(1.0)  # Sleep by 1 second
        await interaction.response.edit_message(content=f'{first} + {second} = {first + second}. {msg}')


# Create bot with cogs
class Bot(commands.Bot):
    def __init__(
        self,
        command_prefix,
        *,
        help_command: Optional[HelpCommand] = ...,
        tree_cls: Type[app_commands.CommandTree[Any]] = app_commands.CommandTree,
        description: Optional[str] = None,
        intents: discord.Intents,
        **options: Any,
    ) -> None:
        super().__init__(
            command_prefix=command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            description=description,
            intents=intents,
            **options,
        )

    async def setup_hook(self):
        print('The start of cogs installation')
        await self.add_cog(MyCog(self))
        print('The end of cogs installation')


intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix='!', intents=intents)

bot.run('YOUR_TOKEN')  # Replace with your token
