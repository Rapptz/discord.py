# In this example you will learn how to make cogs (not extensions)

from asyncio import sleep as async_sleep

import discord
from discord.ext import commands
from discord import app_commands


class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

    @app_commands.command(description='Test app command in cogs')
    @app_commands.describe(first='First number', second='Second number', msg='Message')
    async def test_app_command(self, interaction: discord.Interaction, first: int, second: int, msg: str):
        await interaction.response.send_message('Hello, world!')
        await async_sleep(1.0)  # Sleep by 1 second
        await interaction.response.edit_message(content=f'{first} + {second} = {first + second}. {msg}')

    @app_commands.context_menu()
    @app_commands.default_permissions(administrator=True)  # Only admins can use this command
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        await member.ban(reason='Admin wants to ban you')
        await interaction.response.send_message(f'Banned {str(member)}')


# Create bot with cogs
class MyBot(commands.Bot):
    def __init__(self) -> None:
        command_prefix = '!'
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix, intents=intents)

    async def setup_hook(self):
        print('The start of cogs installation')
        await self.add_cog(MyCog(self))
        print('The end of cogs installation')


bot = MyBot()

bot.run('token')  # Replace with your token
