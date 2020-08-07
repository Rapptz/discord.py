# import discord and any other libraries
import discord
from discord.ext import commands
from discord.utils import get

# bot description
description = "A simple example showcasing how to make text and voice channels (as well as private ones)."

# create a bot instance with prefix "?" and description
bot = commands.Bot(command_prefix="?", description=description)

@bot.event
async def on_ready():
    """Prints information to the console once the bot is ready."""

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Bot Online!')

def can_create():
    """A check to see if the user has the required manage_channels permission."""
    
    async def predicate(ctx):
        member = ctx.author
        return member.guild_permissions.manage_channels
    return commands.check(predicate)

@bot.group(invoke_without_command=True)
@can_create()
async def create(ctx, *, new_channel: str):
    """Command to create an open text channel."""

    # the passed argument new_channel is used to name the created channel
    channel = await ctx.guild.create_text_channel(new_channel, overwrites=None, category=None, reason=None)
    await channel.send(f"Text channel {new_channel} was created!") # sends a message into that channel

@create.command()
@can_create()
async def voice(ctx, *, new_channel: str):
    """Subcommand to create an open voice channel."""

    # note: ctx.guild.categories will return a list of possible categories that the server has
    # you can then select where the channel will be created in the category list
    channel = await ctx.guild.create_voice_channel(new_channel, category=ctx.guild.categories[1])
    await ctx.send(f"Voice channel {new_channel} was created!") # will send into channel that command was invoked from

@create.command()
@can_create()
async def priv(ctx, *, new_channel: str):
    """Subcommand to create a private text channel."""

    # use discord.utils.get() for retrieving and storing a role into variables
    # guild.roles is an iterable, and name is an attribute to search for
    admin = get(ctx.guild.roles, name="YOUR_ADMIN_ROLE")
    mods = get(ctx.guild.roles, name="YOUR_MOD_ROLE")

    # using a dictionary, permissions can be chosen for the new channel
    # guild.default_role is @everyone, guild.me is the bot itself
    # using admin and mods allows to include them into the new channel
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        admin: discord.PermissionOverwrite(read_messages=True),
        mods: discord.PermissionOverwrite(read_messages=True)
    }
    
    # the overwrites dict is assigned to the overwrites parameter 
    channel = await ctx.guild.create_text_channel(new_channel, overwrites=overwrites)
    await channel.send(f"Private text channel {new_channel} was created!")

@create.command()
@can_create()
async def priv_voice(ctx, *, new_channel: str):
    """Subcommand to create a private voice channel."""
    
    admin = get(ctx.guild.roles, name="YOUR_ADMIN_ROLE")
    mods = get(ctx.guild.roles, name="YOUR_MOD_ROLE")

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        admin: discord.PermissionOverwrite(read_messages=True),
        mods: discord.PermissionOverwrite(read_messages=True)
    }

    # using create_voice_channel to create a new voice channel
    # the parameters are used in the same manner as the create_text_channel command
    channel = await ctx.guild.create_voice_channel(new_channel, overwrites=overwrites)
    await ctx.send(f"Private voice channel {new_channel} was created!")

@bot.command()
@can_create()
async def delete(ctx, *, channel_name: str):
    """Command to delete a given channel."""

    # using discord.utils.get() and bot.get_all_channels(), you can specify an attribute
    # to search through an iterable, in this case all the channels on a guild
    channel = get(bot.get_all_channels(), name=channel_name)
    await channel.delete()
    await ctx.send(f"Channel {channel_name} was deleted!")

# note: you can use environment variables when pushing up to Github.
# this could be handy for the token, channels you'd like to include,
# or other important info 
bot.run("YOUR_TOKEN") # this command will run the bot
