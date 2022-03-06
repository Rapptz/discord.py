import discord
from discord import app_commands

client = discord.Client()

# intitiate our command tree, with the client
apple_group = app_commands.CommandTree(client)
apples_picked = []

@client.event
async def on_ready():

    # add the commands to our guild
    await apple_group.sync(guild=discord.Object(id=12345))

@apple_group.command(guild=discord.Object(id=12345))
@app_commands.describe(apple='The Apple to Pick') # describe what the command is
async def pick(inter: discord.Interaction, apple: str):
    """Pick an Apple from a tree"""
 
    # make sure the apple isn't already picked
    if apple in apples_picked:
        await inter.response.send_message('This Apple is already picked!')

    # pick the apple
    apples_picked.append(apple)
    await inter.response.send_message(f'You picked {apple}!')

@apple_group.command(guild=discord.Object(id=12345))
@app_commands.describe(apple='The Apple to Plant')
async def plant(inter: discord.Interaction, apple: str):
    """Plant a Apple"""

    # make sure the apple is picked
    if apple not in apples_picked:
        await inter.response.send_message('This Apple hasn\'t been picked yet!')

    # plant the apple
    apples_picked.remove(apple)
    await inter.response.send_message(f'Your planted {apple}!')

client.run('token')
