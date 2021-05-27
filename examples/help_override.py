import discord
from discord.ext import commands
description="A simple bot to show how to override the default help command"

bot=commands.Bot(command_prefix='!',description=description)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

bot.remove_command("help")


# Embed Help ->
@bot.command()
async def help(ctx):
    embed=discord.Embed(title="Bot Help", description="Below is the list of commands that you can use with the bot")
    embed.add_field(name="!ping",value="Returns pong",inline=False)
    embed.add_field(name="!cmd1", value="Gives reply 1",inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    ctx.send("Pong!")

@bot.command()
async def cmd1(ctx):
    ctx.send("reply 1)

bot.run("Token")
    
