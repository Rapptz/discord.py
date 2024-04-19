import discord
import random

from discord.ext import commands
from discord import app_commands

class Cog_basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def roll(self, ctx: discord.Interaction, dice: str):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.response.send_message('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.response.send_message(result)

async def setup(bot):
    await bot.add_cog(Cog_basic(bot))