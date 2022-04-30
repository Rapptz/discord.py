import discord
from discord import app_commands
from discord.ext import commands

class FirstCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Create the cog and define our bot
    
    @app_commands.command(name="cog", description="This command comes from a cog!")
    async def fromcog(self, interaction: discord.Interaction):
        # Our command inside the cog
        await interaction.response.send_message("Hello, I'm sending from the cog!")

async def setup(bot):
    await bot.add_cog(FirstCog(bot))
    # When this extension is loaded, add the cog to the bot