import discord

import asyncio
import discord

from discord.ext import commands
from discord import app_commands
from typing import Optional, List


TOKEN = "your bot token here"

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs) -> commands.Bot:
        super().__init__(command_prefix = "!", *args, **kwargs, intents = discord.Intents.all())

bot = MyBot()

# A simple hybrid command.
@bot.hybrid_command(
    name = "hi",
    with_app_command = True)
async def hi(ctx: commands.Context):
    """Hybrid command outside of a cog"""

    # When @hybrid_command() decorator is used, context can be passed in and interaction related kwargs can be used.
    if ctx.interaction: # Checking if interaction is true
        return await ctx.send(f"Hi **{ctx.author}**", ephemeral = True) # If we don't use the `ephemeral` kwarg, the value will be set to `False` by default
    return await ctx.send(f"Hi **{ctx.author}**")

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# ---------- #

# Below shows how one can make hybrid commands and groups in hybrid commands inside a cog.
class Hybrid_In_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name = "ping",
        brief = "ping members")
    async def ping(self, ctx: commands.Context, *, member: discord.Member):
        """Ping People"""
        if not member:
            return await ctx.send("Please pass in a member to ping")
        return await ctx.send(f"Hi {member.mention}")

    async def number_autocomplete(self, interaction: discord.Interaction, current: int) -> List[app_commands.Choice[int]]:
        nums = [1, 2, 3, 4, 5]
        return [app_commands.Choice(name = nums, value = nums) for nums in nums]

    async def letters_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        letts = ["a", "b", "c", "d", "e"]
        return [app_commands.Choice(name = letts, value = letts) for letts in letts if current.lower() in letts]

    @commands.hybrid_command(
        name = "people",
        brief = "ping people")
    async def people(self, ctx: commands.Context, *, member: discord.Member):
        """Ping People"""
        if not member:
            return await ctx.send("Please pass in a member to ping")
        return await ctx.send(f"Hi {member.mention}")

    # Subcommands can be made by using the `@commands.hybrid_group()` decorator.
    @commands.hybrid_group(name = "say")
    async def say(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # As we see from the above, we are able to utilize the `app_commands` decorators present in hybrid commands.
    @say.command(name = "number")
    @app_commands.rename(arg = "number")
    @app_commands.describe(arg = "Tell a number to repeat")
    @app_commands.autocomplete(arg = number_autocomplete)
    async def say_num(self, ctx: commands.Context, *, arg: int):
        """Say a number"""
        if ctx.interaction:
            return await ctx.send(arg)
        return await ctx.send(arg)

    @say.command(name = "letters")
    @app_commands.rename(arg = "letters")
    @app_commands.autocomplete(arg = letters_autocomplete)
    @app_commands.describe(arg = "Tell a letter(s) to repeat")
    async def say_letters(self, ctx: commands.Context, *, arg: str):
        """Say a letter"""
        if ctx.interaction:
            return await ctx.send(arg)
        return await ctx.send(arg)

async def setup(bot):
    await bot.add_cog(Hybrid_In_Cog(bot))