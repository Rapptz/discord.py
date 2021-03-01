import discord
from discord.ext import commands

# https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html is the documentation page for cogs.
description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.
The example uses cogs to organize the code
'''

intents = discord.Intents.default()
intents.members = True

# We define the basic bot, setting the prefix, description and intents
bot = commands.Bot(command_prefix='?', description=description, intents=intents)

# we define the class that will house the Utility commands
# the class inherits from the commands.Cog class
# The main advantage is we can take advantage of Object Oriented Programming
# This also groups all commands in the help command under the `Utility` cog
class Miscellaneous(commands.Cog, name="Misc"):
    """
    A simple utility cog
    """

    def __init__(self, bot):

        # We pass in the bot parameter when initializing the class, and make it a property. This lets us access the bot paramater throughput
        self.bot = bot
        # You can also add other properties to the class
        self.other_vale = "this is a property of the class"

    # Cog checks are nice feature in cogs.
    # They allow you to define a check that works for every single command in the cog
    # You return a boolean value. if the check passes the command runs, otherwise a CheckFailure is raised. 
    async def cog_check(self, ctx):
        # Check if there is a guild the command was invoked in
        if ctx.guild:
            return True
        return False

    # A simple basic command inside a cog
    # Instead of using bot.command decorator, the commands.command decorator is used

    @commands.command()
    async def add(self, ctx, left: int, right: int):
        """Adds two numbers together"""
        await ctx.send(left + right)

    # A command group inside a cog
    @commands.group()
    async def cool(ctx):
        """Says if a user is cool.
        In reality this just checks if a subcommand is being invoked.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('No, {0.subcommand_passed} is not cool'.format(ctx))

    @cool.command(name='bot')
    async def _bot(ctx):
        """Is the bot cool?"""
        await ctx.send('Yes, the bot is cool.')

    # Listening for events using a cog
    # This works similar to the bot.event decorator
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.system_channel is not None:
            to_send = 'Welcome {0.mention} to {1.name}!'.format(member, guild)
            await guild.system_channel.send(to_send)


# This method allows us to add our Cog to the main bot. Without this you cog won't show up.
# You can use bot.remove_cog to remove cogs from a bot
bot.add_cog(Utility(bot))
bot.run('token')
