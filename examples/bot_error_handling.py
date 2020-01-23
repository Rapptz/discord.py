import traceback

from discord.ext import commands

bot = commands.Bot(command_prefix="?")

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def repeat(ctx, times: int, *, message: commands.clean_content):
    """Repeat a message a total number of times.

    The message can be at most 200 characters and can be repeated up to 5 times."""
    if len(message) > 200:
        raise commands.BadArgument("I can't repeat a message longer than 200 characters.")

    if times > 5:
        raise commands.BadArgument("I can't repeat a message more than 5 times.")

    for _ in range(times):
        await ctx.send(message)

@bot.command()
async def divide(ctx, left: int, right: int):
    """Divide two numbers."""
    await ctx.send(left / right)

@divide.error
async def on_divide_error(ctx, error): # the name of the function doesn't matter in this case
    # this event is called every time an exception occurs during the "divide" command's processing.
    # this can be caused by parsing errors (e.g. invalid quotes or a converter raising the exception),
    # the command being on cooldown, disabled or a general invoke error.
    # Note: the global command error handler (see below) will be called after.
    #
    # ctx   = the command's context
    # error = the exception raised

    # all exceptions that do not derive from CommandError are wrapped
    # into CommandInvokeError and stored in its 'original' attribute,
    # so we unwrap it.
    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    # respond with an error message if the user tries do divide by zero
    if isinstance(error, ZeroDivisionError):
        await ctx.send("You can't divide a number by zero.")

@bot.event
async def on_command_error(ctx, error):
    # this event is called every time an exception occurs during a command's processing.
    # this can be caused by parsing errors (e.g. invalid quotes or a converter raising the exception),
    # a command being on cooldown, disabled, not found or a general invoke error.
    #
    # ctx   = the command's context
    # error = the exception raised

    # this checks if the command has a local error handler (see above),
    # if so skip all the below handling.
    if hasattr(ctx.command, "on_error"):
        return

    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    # do nothing since we don't really care in this case
    if isinstance(error, commands.CommandNotFound):
        return

    # as the name says, this catches all errors derived from user input.
    elif isinstance(error, commands.UserInputError):
        # this is fine for most use cases since it replies with a friendly error message.
        await ctx.send(error)

    # the command is on cooldown
    elif isinstance(error, commands.CommandOnCooldown):
        # we can easily access the exception and context's attributes to give a more helpful error message.
        msg = "The \"{0}\" command is on cooldown, wait {1:.2f} seconds.".format(ctx.command.name, error.retry_after)
        await ctx.send(msg)

    # here you can handle all other types of exceptions.

    else:
        await ctx.send("An unexpected error has occurred and my developer has been notified, sorry.")
        # make sure to always print the exception's traceback at the end of the event, else it will be "eaten".

        # Note: it's impossible to use traceback.print_exc() or traceback.format_exc() due to
        # how event dispatching messes with the exception context.

        traceback.print_exception(type(error), error, error.__traceback__)

# Treat your bot's token like your account's password,
# never share it with anyone or upload it anywhere.
bot.run("TOKEN")
