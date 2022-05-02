# TODO:
# discord.User, etc
# Channel Example
# Attachment Example
# Autocomplete example
# Custom Transformer (Using the example from docs)

# This example requires the 'members' privileged intent to use the Member transformer.
from typing import Optional

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
        await self.tree.sync(guild=MY_GUILD)


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