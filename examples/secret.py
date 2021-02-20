import typing

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned, description="Nothing to see here!")

@bot.event
async def on_command(ctx):
    try:
        await ctx.message.delete(delay=5)
    except discord.HTTPException:
        # Oh well, looks like we don't have the ability
        # to hide the secret.
        pass

# the `hidden` keyword argument hides it from the help command. 
@bot.group(invoke_without_command=True, hidden=True)
async def secret(ctx: commands.Context):
    """What is this "secret" you speak of?"""
    if ctx.invoked_subcommand is None:
        await ctx.send('Shh!', delete_after=5)

def create_overwrites(ctx, *objects):
    """This is just a helper function that creates the overwrites for the 
    voice/text channels.

    A `discord.PermissionOverwrite` allows you to determine the permissions
    of an object, whether it be a `discord.Role` or a `discord.Member`.

    In this case, the `read_messages` permission is being used to hide the channel
    from being viewed by whoever does not meet the criteria, thus creating a
    secret channel.
    """

    overwrites = {
        obj: discord.PermissionOverwrite(read_messages=True) for obj in objects
    }
 
    overwrites.setdefault(ctx.guild.default_role, discord.PermissionOverwrite(read_messages=False))
    # prevents the default role (@everyone) from viewing the channel
    # if it isn't already allowed to view the channel.
    
    overwrites[ctx.guild.me] = discord.PermissionOverwrite(read_messages=True)
    # makes sure the client is always allowed to view the channel.

    return overwrites

@commands.guild_only()
@secret.command()
async def text(ctx: commands.Context, name: str, *objects: typing.Union[discord.Role, discord.Member]):
    """This may or may not make a text channel with a specified name 
    that is only visible to roles or members that are specified.
    """
    
    overwrites = create_overwrites(ctx, *objects)

    await ctx.guild.create_text_channel(
        name,
        overwrites=overwrites,
        topic='Top secret text channel. Any leakage of this channel may result in serious trouble.',
        reason='Very secret business.',
    )

@commands.guild_only()
@secret.command()
async def voice(ctx: commands.Context, name: str, *objects: typing.Union[discord.Role, discord.Member]):
    """This may or may not do the same thing as the `text` subcommand
    but instead creates a voice channel.
    """

    overwrites = create_overwrites(ctx, *objects)

    await ctx.guild.create_voice_channel(
        name,
        overwrites=overwrites,
        reason='Very secret business.'
    )

@commands.guild_only()
@secret.command()
async def emoji(ctx: commands.Context, emoji: discord.PartialEmoji, *roles: discord.Role):
    """There is a slight chance this could very well clone an emoji
    that only specified roles are allowed to use.
    """

    emoji_bytes = await emoji.url.read()
    # fetch the emoji asset and read it as bytes

    await ctx.guild.create_custom_emoji(
        name=emoji.name,
        image=emoji_bytes,
        roles=roles,
        reason='Very secret business.'
    )


bot.run('token')
