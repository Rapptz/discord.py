import discord
from discord.ext import commands

description = """An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.
The example uses cogs to organize the code
"""

# The intents chosen are the default intents which allow us to get all but presence and member intents.
# We use the member intent for the `on_member_join` event.
# For more information on intents read https://discordpy.readthedocs.io/en/latest/intents.html#intents-primer.
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)


# This defines a class that contains commands in a 'Miscellaneous' category.
# The library calls this concept a Cog and they must inherit from `commands.Cog`.
# Cogs are useful for grouping commands and having them share state.
# This class will group commands in a 'Misc' category in the default help command.
# The `name` keyword argument passed allows us to set the name of the Cog.
# If a name is not given then it will default to the name of the class.
# Read more here: https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html.


class Miscellaneous(commands.Cog, name='Misc'):
    """
    A simple Miscellaneous cog.
    """

    def __init__(self, bot):

        # We pass in the bot parameter when initializing the class, and make it an instance attribute.
        # This lets us access the bot parameter throughout our methods.
        self.bot = bot
        # You can also add other attributes to the class.
        self.afk_reasons = {}

    # Cogs also have the capability to define checks that apply to every command in the Cog.
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
        """Have the bot greet you."""
        await ctx.send('Hello I am an example bot!')

    # A command group within a Cog.
    @commands.group(invoke_without_command=True)
    async def afk(self, ctx, *, reason: str):
        """Set your afk status"""
        user_id = ctx.author.id
        if user_id not in self.afk_reasons:
            self.afk_reasons[user_id] = reason
            mentions = discord.AllowedMentions.none()
            await ctx.send(f'I\'ve set your afk status to `{reason}`', allowed_mentions=mentions)
        else:
            await ctx.send('You are already afk.')

    # Subcommand for the group:
    @afk.command(name='user')
    async def _user(self, ctx, *, user: discord.User):
        """Check a user's afk status"""
        # If a user isn't found an error will be thrown Handle that in an error handler.
        # If the user input isn't present `MissingRequiredArgument` will be thrown
        # If a value that cannot be parsed to a member is present, `UserNotFound` will be thrown.
        # See the error handling example for how it will be handled.
        mentions = discord.AllowedMentions.none()
        try:
            reason = self.afk_reasons[user.id]
            return await ctx.send(f'{user.name} is afk with reason `{reason}`', allowed_mentions=mentions)
        except KeyError:
            return await ctx.send(f'{user.name} is currently not afk', allowed_mentions=mentions)

    # Listening to events within a cog requires the `commands.Cog.listener` decorator.
    # Note that `self` has to be passed for these as well.
    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't want to reply to bots
        if message.author.bot:
            return
        # Ensure that the message wasn't the afk command:
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        # If an afk user has sent a message, remove their afk:
        user_id = message.author.id
        if user_id in self.afk_reasons:
            await message.channel.send(f'Welcome back {message.author.mention}! I have removed your afk status.')
            del self.afk_reasons[user_id]
        # If an afk user is mentioned in a message, let the author of the message know they are afk
        mentions = {user.id: user for user in message.mentions}
        mentioned_afk_users = [user_id for user_id in self.afk_reasons if user_id in mentions]
        if mentioned_afk_users:
            plural_or_singular = 'is' if len(mentioned_afk_users) == 1 else 'are'
            # formats each user as Username#0000
            formatted_users = [str(bot.get_user(user)) for user in mentioned_afk_users]
            afk_users = ', '.join(formatted_users)
            await message.channel.send(f'{afk_users} {plural_or_singular} afk.')

# Cogs have to be explicitly added.
bot.add_cog(Miscellaneous(bot))
bot.run('discord_bot_token')
