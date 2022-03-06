import discord
from discord import app_commands

intents = discord.Intents.default()

MY_GUILD_ID = 1234567890

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(guild=discord.Object(id=MY_GUILD_ID))
async def slash(interaction: discord.Interaction):
    await interaction.response.send_message("Hello World!")
    
client.run("TOKEN")
