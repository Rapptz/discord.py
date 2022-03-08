import discord
from discord import app_commands

import traceback

# Just default intents and a `discord.Client` instance
# We don't need a `commands.Bot` instance because we are not
# creating text-based commands.
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# We need an `discord.app_commands.CommandTree` instance 
# to register application commands (slash commands in this case)
tree = app_commands.CommandTree(client)

# The guild in which this slash command will be registered.
# As global commands can take up to an hour to propagate, it is ideal
# to test it in a guild.
TEST_GUILD = discord.Object(ID)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

    # Sync the application command with Discord.
    await tree.sync(guild=TEST_GUILD)

class Feedback(discord.ui.Modal, title='Feedback'):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.
    name = discord.ui.TextInput(
        label='Name', 
        placeholder='Your name here...',
    )

    # This is a longer, paragraph style input, where user can submit feedback
    # Unlike the name, it is not required. If filled out, however, it will
    # only accept a maximum of 300 characters, as denoted by the
    # `max_length=300` kwarg.
    feedback = discord.ui.TextInput(
        label='What do you think of this new feature?',
        style=discord.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True) 

        # Make sure we know what the error actually is
        traceback.print_tb(error.__traceback__)


@tree.command(guild=TEST_GUILD, description="Submit feedback")
async def feedback(interaction: discord.Interaction):
    # Send the modal with an instance of our `Feedback` class
    await interaction.response.send_modal(Feedback())

client.run('token')