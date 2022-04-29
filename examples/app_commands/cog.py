import discord
from discord.ext import commands
from discord import app_commands

from typing import Optional

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def hello(self, interaction: discord.Interaction):
        """Says hello to you."""
        await interaction.response.send_message(f"Hello, {interaction.user.mention}.")

    @app_commands.command()
    @app_commands.describe(user="From which user do you wanna get the avatar?") # This adds a description to the user argument 
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        """Sends the avatar from the user."""
        user = user or interaction.user

        avatar = await user.display_avatar.to_file()
        await interaction.response.send_message(file=avatar)