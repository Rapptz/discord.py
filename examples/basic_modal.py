from discord import app_commands

import discord

my_guild_id = 1234567 # id used for registering slash commands in a specific guild 
suggestion_channel_id = 1234567 # where to send the suggestion

class SuggestionsBot(discord.Client):
    def __init__(self):
        super().__init__()
        # Create the CommandTree used for creating slash commands.
        self.tree = app_commands.CommandTree(self)
        self.loop.create_task(self.sync_commands())
        
    # Task used for syncing slash commands only for a specific guild
    async def sync_commands(self):
        await self.wait_until_ready()
        await self.tree.sync(guild=discord.Object(id=my_guild_id)) 

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


# Create the modal interface for users to interact and answer
class Suggestions(discord.ui.Modal, title='Server Suggestions'):
    # Define the ClassVar TextInput objects which represents each field in the modal
    summary = discord.ui.TextInput(
        label='Summarize your suggestion.', min_length=10, max_length=100
    )

    reasoning = discord.ui.TextInput(
        label='Provide a reasoning for this suggestion.',
        min_length=10,
        max_length=100,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):

        suggestion = discord.Embed(
            title='New Suggestion',
            description=f'Suggestion from {interaction.user.mention}',
            color=discord.Colour.light_grey(),
            timestamp=discord.utils.utcnow(),
        )
        suggestion.set_author(
            name=interaction.user, icon_url=interaction.user.display_avatar.url
        )

        # Setting the value of the embed field to the value given in the modal.
        # str(self.summary) also works
        suggestion.add_field(name='Suggestion Summary', value=self.summary.value)
        suggestion.add_field(name='Reasoning', value=self.reasoning.value)

        suggestion_channel = interaction.guild.get_channel(suggestion_channel_id) 

        if suggestion_channel is None:
            return await interaction.response.send_message(
                'The suggestion channel could not be found (invalid ID)', ephemeral=True
            )

        await suggestion_channel.send(embed=suggestion)
        await interaction.response.send_message(
            'Your suggestion has been sent successfully!', ephemeral=True
        )


client = SuggestionsBot()

# We create a slash command that opens the modal
@client.tree.command(guild=discord.Object(id=my_guild_id))
async def suggest(interaction: discord.Interaction):
    """Suggest something for the server!"""
    await interaction.response.send_modal(Suggestions())


client.run('token')
