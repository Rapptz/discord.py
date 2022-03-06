import discord
from discord import app_commands, Object, ui

# Just default intents and a `discord.Client` instance
# We don't need a `commands.Bot` instance because we are not
# creating text-based commands.
intents = discord.Intents().default()
client = discord.Client(intents=intents)

# We need an `discord.app_commands.CommandTree` instance to register slash commands
tree = app_commands.CommandTree(client)

# The guild in which this slash command will be registered.
# As global commands can take up to an hour to propagate, it is ideal
# to test it in a guild.
test_guild = Object(ID_HERE)

@client.event
async def on_ready():
    print(f"Connected as {client.user}")
    # Sync the slash commands with Discord.
    await tree.sync(guild=test_guild)

class Feedback(ui.Modal, title='Feedback'):
    # This will be a short input, where the user can enter their name
    # It will also be required, denoted by the `required=True` kwarg
    name = ui.TextInput(
        label='Name', 
        style=discord.TextStyle.short, 
        placeholder='Your name here...',
        required=True,
        custom_id='modal_name'
    )

    # This is a longer, paragraph style input, where user can submit feedback
    # Unlike the name, it is not required. If filled out, however, it will
    # only accept a maximum of 300 characters, denoted by the
    # `max_length=300` kwarg.
    feedback = ui.TextInput(
        label='What do you think of this new feature?',
        style=discord.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        custom_id='modal_feedback',
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Self explanatory, this will be called when the modal is submitted
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        # Also self explanatory, this will be called when an error happens.
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True) 


@tree.command(guild=test_guild, description="Submit feedback")
async def feedback(interaction: discord.Interaction):
    """Slash command that initiates the modal.
    
    Usage: /feedback
    """

    # Send the modal with an instance of our `Feedback` class
    await interaction.response.send_modal(Feedback())

client.run("TOKEN")