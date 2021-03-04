import discord
from discord.ext import commands
import traceback

description = '''
A basic bot featuring error handling for command errors
'''

# Constructing the bot with a prefix and the description
bot = commands.Bot(command_prefix='!', description=description)

# Example command to showcase a potential error raised.
# The important ones to see are `MissingRequiredArgument` and `BadArgument`.
# `MissingRequiredArgument` will be raised when a required argument is not passed.
# Bad Argument will be raised in this case when the arg cannot be converted to an `int`.
@bot.command()
async def divide(ctx, dividend: float, divisor: float):
    quotient = dividend / divisor
    await ctx.send('{} / {} = {}'.format(dividend, divisor, quotient))

# This command showcases the `is_owner` check, which will raise `commands.NotOwner` if the user doesn't own the bot.
@commands.is_owner()
@bot.command()
async def owner_check(ctx):
    await ctx.send('{}, you own this bot!'.format(ctx.author))

# Here is a command with a cooldown.
# The syntax for cooldown is rate / per / type.
# Here we are doing 1 per 5 seconds per member.
@commands.cooldown(1, 5, commands.BucketType.member)
@bot.command()
async def cooldown_example(ctx):
    await ctx.send('{}, you are not on cooldown!'.format(ctx.author))

# Here we are **overriding** on_command_error.
# You can also use `bot.listen()` if you prefer not to override it, though there isn't a difference here.
# The event takes 2 args, `ctx` and `error`.
@bot.event
async def on_command_error(ctx, error):
    # Check if the command has a local handler.
    if ctx.command and ctx.command.has_error_handler():
        return

    # Check for ctx.cog and return if it has a local handler.
    elif ctx.cog and ctx.cog.has_error_handler():
        return

    # The errors below are in a format that is readable, so we can just call `str` on them.
    readable_errors = (
        commands.BadArgument,
        commands.MissingRequiredArgument,
        commands.NotOwner
    )

    # Exceptions that do not derive from `commands.CommandError` are wrapped in a `commands.CommandInvokeError` exception. Unwrap this using the following: 
    # to fix this, we unwrap the error.
    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    # We use isinstance to check the type of error. 
    if isinstance(error, commands.CommandNotFound):
        # We can suppress the `commands.CommandNotFound` exception to suppress extra noise.
        return
    
    # Checking for our readable error types and then sending their string format to the invoking channel.
    elif isinstance(error, readable_errors):
        await ctx.send(str(error))

    # Here we send a custom error message if the user is on cooldown.
    # We also format the cooldown seconds to 2 digits.
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send('You are on cooldown! Please wait `{}` seconds'.format(round(error.retry_after, 2)))

    # If the error isn't picked up by any of our other checks, then we should just print it.
    # **NOTE**: This error is *not* being raised. It is being printed.
    else:
        traceback.print_exc()

# Run the bot. You should really read the token from a configuration file.
bot.run('TOKEN HERE')
