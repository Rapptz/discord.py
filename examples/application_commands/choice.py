import discord
from discord import app_commands
from typing import Literal

intents = discord.Intents.default()

MY_GUILD_ID = 1234567890

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@app_commands.command()
@app_commands.describe(fruits='choose your favorite animal')
async def fruit(interaction: discord.Interaction, animal: Literal['dog', 'cat', 'monkey', 'lion', 'wolf']):
    await interaction.response.send_message(f'Your favourite animal is {animal}.')
    
client.run("TOKEN")
