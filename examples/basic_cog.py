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
        self.afk = {}

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
    async def hello(self, ctx):
        """Adds two numbers together"""
        await ctx.send("Hello am I an example bot!")

    # A command group within a Cog.
    # The `invoke_without_command` flag for the group allows us to use the parent of the group as a command.
    @commands.group(invoke_without_command=True)
    async def afk(self, ctx, *, reason: str):
        """
        Set your afk status
        """
        u_id = ctx.author.id
        # Simply check if they exist in our afk dictionary aldready.
        # If they exist then tell them they are afk, or let them set a new afk status.
        rating = self.afk.get(u_id)
        if not rating:
            self.afk[u_id] = reason
            await ctx.send(f"{ctx.author.mention} I have set your afk status as `{reason}`.")
        else:
            await ctx.send(f"{ctx.author.mdention} you are aldready afk.")

    # Subcommand for the group
    @afk.command(name='user')
    async def _user(self, ctx, *, user: discord.User = None):
        """Check a user's afk status"""
        if not user:
            return await ctx.send("I need a user to check the afk status")
        afk = self.afk.get(user.id)
        if afk:
            return await ctx.send(f"{user.name} is afk with reason `{afk}`")
        return await ctx.send(f'{user.name} is currently not afk')

    # Listening to events within a cog requires the `commands.Cog.listener` decorator.
    # Note that `self` has to be passed for these as well.
    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't want to reply to bots
        if message.author.bot:
            return
        # Ensure that the message wasn't the afk command
        ctx = await self.bot.get_context(message)
        if ctx.invoked_with == "afk":
            return

        # If an afk user has sent a message, remove their afk
        m_id = message.author.id
        afk_status = self.afk.get(m_id)
        if afk_status:
            await message.channel.send(f"Welcome back {message.author.mention}! I have removed your afk status.")
            self.afk.pop(m_id)
            return

        # If an afk user is mentioned in a message, let the author of the message know they are afk
        mentions = [user.id for user in message.mentions]
        common = [afk_user for afk_user in self.afk.keys()
                  if afk_user in mentions]
        if len(common) != 0:
            akf_users = ",".join(str(self.bot.get_user(c)) for c in common)
            await message.channel.send(f"{akf_users} {'is' if len(common) == 1 else 'are'} afk.")


# Cogs have to be explicitly added.
bot.add_cog(Miscellaneous(bot))
bot.run('token')
