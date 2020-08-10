import discord
from discord.ext import commands

description = "A simple example showcasing how to make a secret text channel."

bot = commands.Bot(command_prefix="?", description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Bot Online!')

@bot.command()
@commands.has_permissions(manage_channels=True)
async def create(ctx, *, channel_name: str):
    """Command to create a private text channel."""

    # find needed roles and store them in variables for later use
    admin = discord.utils.get(ctx.guild.roles, name="YOUR_ADMIN_ROLE")
    mods = discord.utils.get(ctx.guild.roles, name="YOUR_MOD_ROLE")

    # using a dictionary, permissions can be chosen for the new channel
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        admin: discord.PermissionOverwrite(read_messages=True),
        mods: discord.PermissionOverwrite(read_messages=True)
    }
    
    # the overwrites dict is assigned to the overwrites parameter 
    channel = await ctx.guild.create_text_channel(channel_name, overwrites=overwrites)
    await channel.send("Private text channel {} was created!".format(channel_name))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def delete(ctx, *, channel_name: str):
    """Command to delete a given channel."""

    # search through channels on a guild for the given channel name
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    await channel.delete()
    await ctx.send("Channel {} was deleted!".format(channel_name))

bot.run('token')
