# In this example you will learn how to make cogs (not extension)

import discord
from discord.ext import commands
from discord.ext.commands import HelpCommand
from discord import app_commands

from typing import Optional, Type, Any


class MyCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot # Assign bot that is setuping cog
    
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

# Create bot with cogs
class Bot(commands.Bot):
    def __init__(
        self,
        command_prefix,
        *, help_command: Optional[HelpCommand] = ...,
        tree_cls: Type[app_commands.CommandTree[Any]] = app_commands.CommandTree,
        description: Optional[str] = None,
        intents: discord.Intents,
        **options: Any
    ) -> None:
        super().__init__(
            command_prefix=command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            description=description,
            intents=intents,
            **options
        )
    async def on_ready(self):
        print('Start installing cogs!')
        await self.add_cog(MyCog(self))
        print('Finish installing cogs!')
        
        print("I'm ready")

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix='!', intents=intents)

bot.run('YOUR_TOKEN')
