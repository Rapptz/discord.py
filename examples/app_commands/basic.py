from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

MY_GUILD = discord.Object(id=0)  # replace with your guild id


class MyBot(commands.Bot):

    # In this basic example, we just synchronize the app commands to one guild,
    # without requiring to set the guild to every command individually by just copying them over.
    # By doing so we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()

# In order to use a basic synchronization of the app commands in the setup_hook,
# you have replace ... with your bots application_id you find in the developer portal.
bot = MyBot(command_prefix='?', intents=intents, application_id=...)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@bot.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to', second_value='The value you want to add to the first value'
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')

# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing library. This example does both.
@bot.tree.command()
@app_commands.describe(member='The member you want to get the joined date from, defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    await interaction.response.send_message(f'{member} joined in {member.joined_at}')


bot.run('token')
