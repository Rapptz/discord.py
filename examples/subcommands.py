import discord
from discord.ext import commands

description = """An example bot to showcase the subcommands feature."""
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='?', description=description, intents=intents)


# first command-subcommand group
@bot.group()
async def spam(ctx):
    """Main command of the spam group.
    This will be executed every time it is called with a subcommand.
    """
    await ctx.send('Spam!')


# we can set the name of the command in the decorator
# the coroutine and command name can be different
@spam.command(name='egg')
async def spam_egg(ctx):
    """Subcommand of the spam group.
    Can only be called with the spam command.
    Ie. `?spam egg`
    """
    # this subcommand will result in two messages being sent;
    # "Spam!", from the parent command, and "and Eggs!".
    await ctx.send('and Eggs!')


# the following parent command will not be executed when
# invoking it with a subcommand because of the keyword argument
# invoke_without_command bring set to True
@bot.group(invoke_without_command=True)
async def foo(ctx):
    """Main command of the foo group.
    This will only be executed when it is called without a subcommand.
    """
    await ctx.send('Foo!')


# subcommand of the group "foo"
@foo.command()
async def bar(ctx):
    """Subcommand of the foo group.
    Can only be called with the foo command,
    Ie. `?foo bar`
    """
    await ctx.send('Bar!')


# the following showcases that subcommands can be nested;
# Group objects can contain other Groups, and so on.
@bot.group()
async def eeny(ctx):
    """Big group parent command."""

    await ctx.send('Eeny, meeny, miny, moe,')


@eeny.group()
async def meeny(ctx):
    """First subcommand.
    Invoked with `?eeny meeny`
    """
    await ctx.send('Catch a tiger by the toe.')


@meeny.group()
async def miny(ctx):
    """Second subcommand.
    Invoked with `?eeny meeny miny`
    """
    await ctx.send('If he hollers, let him go,')


@miny.command()
async def moe(ctx):
    """Third subcommand.
    Invoked with `?eeny meeny miny moe`
    """
    await ctx.send('Eeny, meeny, miny, moe,')


token = 'TOKEN'
bot.run(token)
