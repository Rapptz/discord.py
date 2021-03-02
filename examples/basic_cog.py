import discord
from discord.ext import commands

# https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html is the documentation page for cogs.
description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.
The example uses cogs to organize the code
'''

# The intents chosen are the default intents which allow us to get all but presence and member intents.
# We use the member intent for the `on_member_join` event.
# For more information on intents read https://discordpy.readthedocs.io/en/latest/intents.html#intents-primer.
intents = discord.Intents.default()
intents.members = True

# We define the basic bot, setting the prefix, description and intents.
bot = commands.Bot(command_prefix='?', description=description, intents=intents)

# We define the class that will house the Miscellaneous commands.
# The class *must* inherit from the `commands.Cog` class.
# The main advantage is we can take advantage of Object Oriented Programming.
# This also groups all commands in the help command under the `Misc` category.
# The name kwarg passed allows us to set the name of the Cog. If not set it will default to the name of the class.
class Miscellaneous(commands.Cog, name="Misc"):
    """
    A simple Miscellaneous cog.
    """

    def __init__(self, bot):

        # We pass in the bot parameter when initializing the class, and make it a class attribute. 
        # This lets us access the bot parameter throughout our methods.
        self.bot = bot
        # You can also add other attributes to the class.
        self.other_value = 'This is a class attribute.'

    # Cog checks are nice feature in Cogs.
    # They allow you to define a check that applies to every single command in the Cog.
    # You return a boolean value. If the check passes the command runs, otherwise a `commands.CheckFailure` is raised. 
    async def cog_check(self, ctx):
        # Check if the command was invoked within a Guild channel.
        if ctx.guild:
            return True
        return False

    # A simple basic command within a Cog.
    # Instead of using bot.command decorator, the commands.command decorator is used.
    # This is as the bot.command decorator will add the command to the bot's command list. 
    # commands.commands.command is used so the command is registered under the Cog's command list.
    @commands.command()
    async def add(self, ctx, left: int, right: int):
        """Adds two numbers together"""
        await ctx.send(left + right)

    # A command group within a Cog.
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

    # Listening for events within a cog.
    # This is how you create an event listener for a cog.
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.system_channel is not None:
            to_send = 'Welcome {0.mention} to {1.name}!'.format(member, guild)
            await guild.system_channel.send(to_send)


# This method allows us to add our Cog to the main bot. 
# Without this your  Cog will not be added to `Bot.cogs` and therefore its listeners and commands will not be registered.
# You can use bot.remove_cog to remove a Cog from a bot.
bot.add_cog(Miscellaneous(bot))
bot.run('token')
