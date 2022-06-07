# TODO:
# Attachment Example
# Autocomplete example
# Custom Transformer (Using the example from docs)

# This example requires the 'members' privileged intent to use the Member transformer.
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands


MY_GUILD = discord.Object(id=0)  # replace with your guild id


class MyBot(commands.Bot):
    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        cmds = await self.tree.sync(guild=MY_GUILD)
        print([c.name for c in cmds])


intents = discord.Intents.default()
intents.members = True

# In order to use a basic synchronization of the app commands in the setup_hook,
# you have to replace the 0 with your bot's application_id that you find in the developer portal.
bot = MyBot('?', intents=intents, application_id=0)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.tree.command()
# app_commands.Range is a type annotation that can be applied to a parameter to require
# a numeric type to fit within the range provided. You can provide int or float as a type.
async def age(interaction: discord.Interaction, age: app_commands.Range[int, 0, 99]):
    """Tell the bot how old you are."""
    await interaction.response.send_message(f'{interaction.user} is {age} years old.')


@bot.tree.command()
async def userinfo(interaction: discord.Interaction, user: Optional[discord.User]):
    """Get some information about a User"""
    # In the command signature above, you can see that the `user`
    # parameter is typehinted to `Optinal[discord.User]`. This means that
    # the end-user will be able to pick a user that has access
    # to the channel or to provide an user id.
    # After command was invoked this will resolve the user to a `discord.User` instance.

    # If no user is explicitly provided then we use the command user here
    user = user or interaction.user

    await interaction.response.send_message(f'User found - {user}\nAvatar: {user.display_avatar.url}')


@bot.tree.command()
async def channelinfo(
    interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.Thread]
):
    # Using an Union we can provide the different channel types that are allowed.
    # Here the user can select between the text channels, the voice channels and the threads on the guild.
    if isinstance(channel, discord.TextChannel):
        channel_type = "text channel"
    elif isinstance(channel, discord.VoiceChannel):
        channel_type = "voice channel"
    elif isinstance(channel, discord.Thread):
        channel_type = "thread"

    await interaction.response.send_message(
        f"{channel.mention} is a {channel_type} and was created {discord.utils.format_dt(channel.created_at)}"
    )


bot.run("token")
