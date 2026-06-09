import discord
from discord import app_commands

import traceback

# The guild in which this slash command will be registered.
# It is recommended to have a test guild to separate from your "production" bot
TEST_GUILD = discord.Object(0)
# The ID of the channel where reports will be sent to
REPORTS_CHANNEL_ID = 0


class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self) -> None:
        # Just default intents and a `discord.Client` instance
        # We don't need a `commands.Bot` instance because we are not
        # creating text-based commands.
        intents = discord.Intents.default()
        super().__init__(intents=intents)

        # We need an `discord.app_commands.CommandTree` instance
        # to register application commands (slash commands in this case)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def setup_hook(self) -> None:
        await self.tree.sync(guild=TEST_GUILD)


# Define a modal dialog for reporting issues or feedback
class ReportModal(discord.ui.Modal, title='Your Report'):
    topic = discord.ui.Label(
        text='Topic',
        description='Select the topic of the report.',
        component=discord.ui.Select(
            placeholder='Choose a topic...',
            options=[
                discord.SelectOption(label='Bug', description='Report a bug in the bot'),
                discord.SelectOption(label='Feedback', description='Provide feedback or suggestions'),
                discord.SelectOption(label='Feature Request', description='Request a new feature'),
                discord.SelectOption(label='Performance', description='Report performance issues'),
                discord.SelectOption(label='UI/UX', description='Report user interface or experience issues'),
                discord.SelectOption(label='Security', description='Report security vulnerabilities'),
                discord.SelectOption(label='Other', description='Other types of reports'),
            ],
        ),
    )
    report_title = discord.ui.Label(
        text='Title',
        description='A short title for the report.',
        component=discord.ui.TextInput(
            style=discord.TextStyle.short,
            placeholder='The bot does not respond to commands',
            max_length=120,
        ),
    )
    description = discord.ui.Label(
        text='Description',
        description='A detailed description of the report.',
        component=discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            placeholder='When I use /ping, the bot does not respond at all. There are no error messages.',
            max_length=2000,
        ),
    )
    images = discord.ui.Label(
        text='Images',
        description='Upload any relevant images for your report (optional).',
        component=discord.ui.FileUpload(
            max_values=10,
            custom_id='report_images',
            required=False,
        ),
    )
    footer = discord.ui.TextDisplay(
        'Please ensure your report follows the server rules. Any kind of abuse will result in a ban.'
    )

    def to_view(self, interaction: discord.Interaction) -> discord.ui.LayoutView:
        # Tell the type checker what our components are...
        assert isinstance(self.topic.component, discord.ui.Select)
        assert isinstance(self.description.component, discord.ui.TextInput)
        assert isinstance(self.report_title.component, discord.ui.TextInput)
        assert isinstance(self.images.component, discord.ui.FileUpload)

        topic = self.topic.component.values[0]
        title = self.report_title.component.value
        description = self.description.component.value
        files = self.images.component.values

        view = discord.ui.LayoutView()
        container = discord.ui.Container()
        view.add_item(container)

        container.add_item(discord.ui.TextDisplay(f'-# User Report\n## {topic}'))

        timestamp = discord.utils.format_dt(interaction.created_at, 'F')
        footer = discord.ui.TextDisplay(f'-# Reported by {interaction.user} (ID: {interaction.user.id}) | {timestamp}')

        container.add_item(discord.ui.TextDisplay(f'### {title}'))
        container.add_item(discord.ui.TextDisplay(f'>>> {description}'))

        if files:
            gallery = discord.ui.MediaGallery()
            gallery.items = [discord.MediaGalleryItem(media=attachment.url) for attachment in files]
            container.add_item(gallery)

        container.add_item(footer)
        return view

    async def on_submit(self, interaction: discord.Interaction[MyClient]):
        view = self.to_view(interaction)

        # Send the report to the designated channel
        reports_channel = interaction.client.get_partial_messageable(REPORTS_CHANNEL_ID)
        await reports_channel.send(view=view)
        await interaction.response.send_message('Thank you for your report! We will look into it shortly.', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


client = MyClient()


@client.tree.command(guild=TEST_GUILD, description='Report an issue or provide feedback.')
async def report(interaction: discord.Interaction):
    # Send the modal with an instance of our `ReportModal` class
    # Since modals require an interaction, they cannot be done as a response to a text command.
    # They can only be done as a response to either an application command or a button press.
    await interaction.response.send_modal(ReportModal())


client.run('token')
