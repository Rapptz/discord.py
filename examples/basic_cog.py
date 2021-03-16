import discord
from discord.ext import commands
import random

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

bot = commands.Bot(command_prefix='?',
                   description=description, intents=intents)


# This defines a class that contains commands in a "Miscellaneous" category
# The library calls this concept a Cog and they must inherit from `commands.Cog`
# Cogs are useful for grouping commands and having them share state
# This class will group commands in a "Misc" category in the default help command
# The `name` keyword argument passed allows us to set the name of the Cog
# If a name is not given then it will default to the name of the class
# Read more here: https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html


class Miscellaneous(commands.Cog, name='Misc'):
    """
    A simple Miscellaneous cog.
    """

    def __init__(self, bot):

        # We pass in the bot parameter when initializing the class, and make it an instance attribute.
        # This lets us access the bot parameter throughout our methods.
        self.bot = bot
        # You can also add other attributes to the class.
        self.ratings = {}

    # Cogs also have the capability to define checks that apply to every command in the Cog
    # They work similarly to regular checks elsewhere in the framework.
    # ref: https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#checks
    async def cog_check(self, ctx):
        # Check if the command was invoked within a Guild channel.
        return ctx.guild is not None

    # Commands within a Cog are defined using the commands.command decorator
    # instead of the bot.command decorator.
    # They must also pass a `self` parameter since it's within a class.
    @commands.command()
    async def add(self, ctx, left: int, right: int):
        """Adds two numbers together"""
        await ctx.send(left + right)

    # A  method for getting the rating of a username.
    def get_rating(self, name):
        # We check the `self.ratings` dict to see if the member has a rating.
        rating = self.ratings.get(name)
        # We can now check if a rating exists, if not we generate a new one.
        if not rating:
            rating = random.randint(1, 100)
            self.ratings[name] = rating
        return rating

    # A command group within a Cog.
    # The `invoke_without_command` flag for the group allows us to use the parent of the group as a command.
    @commands.group(invoke_without_command=True)
    async def rate(self, ctx):
        """Let the bot rate you.
        Generate a random rating between 1 and 100.
        """
        # Thie command uses the random stdlib to generate a number
        # We use teh class method `get_rating`
        rating = self.get_rating(ctx.author.name)
        await ctx.send(f"{ctx.author.mention} is `{rating}%` cool.")

    # Subcommand for the group
    @rate.command(name='user')
    async def _user(self, ctx, *, user: discord.User = None):
        """Rate another user"""
        if not user:
            return await ctx.send("I need a user to rate.")
        rating = self.get_rating(user.name)
        await ctx.send(f'I have given {user.mention} a rating of `{rating}%`.')

    # Listening to events within a cog requires the `commands.Cog.listener` decorator.
    # Note that `self` has to be passed for these as well.
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        if guild.system_channel is not None:
            to_send = 'Welcome {0.mention} to {1.name}!'.format(member, guild)
            await guild.system_channel.send(to_send)


# Cogs have to be explicitly added.
bot.add_cog(Miscellaneous(bot))
bot.run('token')
