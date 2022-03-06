import discord
from discord import app_commands, Object, ui

intents = discord.Intents().default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
test_guild = Object(ID_HERE)

@client.event
async def on_ready():
    print(f"Connected as {client.user}")
    await tree.sync(guild=test_guild)

class Feedback(ui.Modal, title='Feedback'):
    name = ui.TextInput(
        label='Name', 
        style=discord.TextStyle.short, 
        placeholder='Your name here...',
        required=True,
        custom_id='modal_name'
    )

    feedback = ui.TextInput(
        label='What do you think of this new feature?',
        style=discord.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        custom_id='modal_feedback',
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True) 


@tree.command(guild=test_guild, description="Submit feedback")
async def feedback(interaction: discord.Interaction):
    await interaction.response.send_modal(Feedback())

client.run("TOKEN")