import discord
from discord import app_commands
from discord.ext import commands

@app_commands.context_menu(name="Click")
async def click(interaction: discord.Interaction, user: discord.User):
    # Our context menu
    await interaction.response.send_message(f"You clicked on {user.mention}")

class ContextMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tree.add_command(click)
        # Add the context menu to the tree
    
    def cog_unload(self):
        self.bot.tree.remove_command("Click", type=discord.AppCommandType.user)
        # Remove the context menu from the tree

async def setup(bot):
    await bot.add_cog(ContextMenuCog(bot))
    # When this extension is loaded, add the cog to the bot