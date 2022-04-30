import discord
from discord import app_commands
from discord.ext import commands

class CommandGroup(app_commands.Group):
    def __init__(self, bot):
        super().__init__(
            name="group"
        )
        # Create the group with name "group"
        
        self.bot = bot

    @app_commands.command(name="one", description="The first command of the group")
    async def one(self, interaction: discord.Interaction):
        # Command named "one", this will appear as `/group one` in chat
        await interaction.response.send_message("One!") 

    @app_commands.command(name="two", description="The second command of the group")
    async def two(self, interaction: discord.Interaction):
        # Command named "two", this will appear as `/group two` in chat
        await interaction.response.send_message("Two!")
    
    @app_commands.command(name="three", description="The third command of the group")
    async def three(self, interaction: discord.Interaction):
        # Command named "three", this will appear as `/group three` in chat
        await interaction.response.send_message("Three!")

class CommandGroupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.group = CommandGroup(bot=self.bot)
        # Make the group instance

        self.bot.tree.add_command(self.group)
        # Add the group to the tree

    def cog_unload(self):
        self.bot.tree.remove_command(self.group.name, type=discord.AppCommandType.message)
        # Remove the group from the tree when unloading


async def setup(bot):
    await bot.add_cog(CommandGroupCog(bot))
    # When this extension is loaded, add the cog to the bot