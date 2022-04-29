import discord
from discord import app_commands
from discord.ext import commands

class MyBot(commands.Bot):

    # In this basic example, we just synchronize the app commands to one guild,
    # without requiring to set the guild to every command individually by just copying them over.
    # By doing so we don't have to wait up to 1hr until they are shown for the end-user.

    # If you want to synchronize your app commands to every guild your bot is in, 
    # remove the following setup_hook and uncomment the one below.
    async def setup_hook(self):
        # Replace ... with the guild id you want your commands to be synced with.
        guild = discord.Object(...)
        self.tree.copy_global_to(guild=guild)
        synced_app_commands = await self.tree.sync(guild=guild)
        print(f'Synced the following commands to {guild.id}: {[c.name for c in synced_app_commands]}')

    # async def setup_hook(self):
    #     synced_app_commands = await self.tree.sync()
    #     print(f'Synced the following commands to every guild: {[c.name for c in synced_app_commands]}')

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
@app_commands.describe(first_value='The first value you want to add something to', second_value='The value you want to add to the first value')
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')

# To make an argument optional, you can make it a default argument
@bot.tree.command()
@app_commands.describe(member='The member you want to get the joined date from, defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: discord.Member = None):
    """Says when a member joined."""
    # By doing this we use the member that was provided, 
    # tho if this is None we use the user that has invoked the command
    member = member or interaction.user

    await interaction.response.send_message(f'{member} joined in {member.joined_at}')

bot.run('token')
