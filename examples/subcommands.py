import discord
from discord.ext import commands

description = '''An example bot to showcase subcommands in the discord.ext.commands extension
module.
'''

bot = commands.Bot(command_prefix='?', description=description)

# Our `commands.Group` object, which will be our parent command
# Any checks specified on our group will carry over to subcommands
# Note that case insensitivity will not carry over from our bot to our subcommands
@bot.group()
@commands.guild_only()
async def greet(ctx):
    """The group command for our greet commands"""
    # The parent command is always called even if subcommands are invoked
    # So we are checking the invoked subcommand with `ctx.invoked_subcommand`
    if ctx.invoked_subcommand is None:
        # If none are found we send our help command
        await ctx.send_help(ctx.command)

# Defining our subcommand as a command of our group
# We will invoke this command with `?greet hello`
# We can define additional checks specific to this subcommand
@greet.command()
@commands.is_owner()
async def hello(ctx):
    """Say hello!"""
    await ctx.send(f'Hello {ctx.author}!')

# This would be invoked with `?greet goodbye <member>`
@greet.command()
async def goodbye(ctx, member: discord.Member):
    """Say goodbye to someone"""
    await ctx.send(f'Goodbye {member.author}')

# We can also nest groups!
@greet.group()
async def everyone(ctx):
    """Say hi to everyone"""
    # Same logic as above
    if ctx.invoked_subcommand is None:
        await ctx.send_help(ctx.command)

# Define our nested subcommand
# As we defined hello above already, we can not make another one without overriding
# To fix this, we can use the name keyword argument
# Also notice because these are separate subcommands, we can have multiple commands with the same name
# Invoked with `?greet everyone hello`
@everyone.command(name="hello")
async def everyone_hello(ctx):
    """Say hi to everyone!"""
    await ctx.send('Hello everyone!')

# Sometimes you may want a subcommand to function independently from the rest
# To do this, we can use the `invoke_without_command` keyword argument
# When set to `True`, the parent command will only be invoked when no subcommand is found
# Invoked with `?role <member> <role>`
@bot.group(invoke_without_command=True)
@commands.has_guild_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    """Add a role to a target member"""
    await member.add_roles(role)
    await ctx.send('Done!')

# Because we made our group separate, checks will not carry over from the parent command
# Invoked with `?role info <member>`
@role.command()
async def info(ctx, member: discord.Member):
    """View the roles a member has"""
    roles = '\n'.join(r.mention for r in member.roles)
    await ctx.send(
        f'{member} Currently has:\n {roles}',
        # Don't want to ping anyone :^)
        allowed_mentions = discord.AllowedMentions.none()
    )

bot.run('token')

