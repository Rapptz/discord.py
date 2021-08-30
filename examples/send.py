import discord
from discord.ext import commands

bot = commands.Bot("!")

@bot.command()
async def hello(ctx):
    await f"Hello {ctx.author}!".send(f"#{ctx.channel.name}")

bot.run("token")
