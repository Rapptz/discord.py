import discord
from discord.ext import commands

bot = commands.Bot("!")

@bot.command()
async def hello(ctx):
    await f"Hello {ctx.author}!".send(f"#{ctx.channel.name}")
    # or
    await f"#{ctx.channel.name}".say(f"Hello {ctx.author}!")

bot.run("token")
