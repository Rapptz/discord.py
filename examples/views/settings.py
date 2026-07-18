from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union
from discord.ext import commands
from discord import ui
import discord
import enum


class FruitType(enum.Enum):
    apple = 'Apple'
    banana = 'Banana'
    orange = 'Orange'
    grape = 'Grape'
    mango = 'Mango'
    watermelon = 'Watermelon'
    coconut = 'Coconut'

    @property
    def emoji(self) -> str:
        emojis = {
            'Apple': '🍎',
            'Banana': '🍌',
            'Orange': '🍊',
            'Grape': '🍇',
            'Mango': '🥭',
            'Watermelon': '🍉',
            'Coconut': '🥥',
        }
        return emojis[self.value]

    def as_option(self) -> discord.SelectOption:
        return discord.SelectOption(label=self.value, emoji=self.emoji, value=self.name)


# This is where we'll store our settings for the purpose of this example.
# In a real application you would want to store this in a database or file.
@dataclass
class Settings:
    fruit_type: FruitType = FruitType.apple
    channel: Optional[discord.PartialMessageable] = None
    members: List[Union[discord.Member, discord.User]] = field(default_factory=list)
    count: int = 1
    silent: bool = False


class Bot(commands.Bot):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.settings: Settings = Settings()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


class FruitsSetting(ui.ActionRow['SettingsView']):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.update_options()

    def update_options(self):
        for option in self.select_fruit.options:
            option.default = option.value == self.settings.fruit_type.name

    @ui.select(placeholder='Select a fruit', options=[fruit.as_option() for fruit in FruitType])
    async def select_fruit(self, interaction: discord.Interaction[Bot], select: discord.ui.Select) -> None:
        self.settings.fruit_type = FruitType[select.values[0]]
        self.update_options()
        await interaction.response.edit_message(view=self.view)


class ChannelSetting(ui.ActionRow['SettingsView']):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        if settings.channel is not None:
            self.select_channel.default_values = [
                discord.SelectDefaultValue(id=settings.channel.id, type=discord.SelectDefaultValueType.channel)
            ]

    @ui.select(
        placeholder='Select a channel',
        channel_types=[discord.ChannelType.text, discord.ChannelType.public_thread],
        max_values=1,
        min_values=0,
        cls=ui.ChannelSelect,
    )
    async def select_channel(self, interaction: discord.Interaction[Bot], select: ui.ChannelSelect) -> None:
        if select.values:
            channel = select.values[0]
            self.settings.channel = interaction.client.get_partial_messageable(
                channel.id, guild_id=channel.guild_id, type=channel.type
            )
            select.default_values = [discord.SelectDefaultValue(id=channel.id, type=discord.SelectDefaultValueType.channel)]
        else:
            self.settings.channel = None
            select.default_values = []
        await interaction.response.edit_message(view=self.view)


class MembersSetting(ui.ActionRow['SettingsView']):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.update_options()

    def update_options(self):
        self.select_members.default_values = [
            discord.SelectDefaultValue(id=member.id, type=discord.SelectDefaultValueType.user)
            for member in self.settings.members
        ]

    @ui.select(placeholder='Select members', max_values=5, min_values=0, cls=ui.UserSelect)
    async def select_members(self, interaction: discord.Interaction[Bot], select: ui.UserSelect) -> None:
        self.settings.members = select.values
        self.update_options()
        await interaction.response.edit_message(view=self.view)


class CountModal(ui.Modal, title='Set emoji count'):
    count = ui.TextInput(label='Count', style=discord.TextStyle.short, default='1', required=True)

    def __init__(self, view: 'SettingsView', button: SetCountButton):
        super().__init__()
        self.view = view
        self.settings = view.settings
        self.button = button

    async def on_submit(self, interaction: discord.Interaction[Bot]) -> None:
        try:
            self.settings.count = int(self.count.value)
            self.button.label = str(self.settings.count)
            await interaction.response.edit_message(view=self.view)
        except ValueError:
            await interaction.response.send_message('Invalid count. Please enter a number.', ephemeral=True)


class SetCountButton(ui.Button['SettingsView']):
    def __init__(self, settings: Settings):
        super().__init__(label=str(settings.count), style=discord.ButtonStyle.secondary)
        self.settings = settings

    async def callback(self, interaction: discord.Interaction[Bot]) -> None:
        # Tell the type checker that a view is attached already
        assert self.view is not None
        await interaction.response.send_modal(CountModal(self.view, self))


class NotificationToggleButton(ui.Button['SettingsView']):
    def __init__(self, settings: Settings):
        super().__init__(label='\N{BELL}', style=discord.ButtonStyle.green)
        self.settings = settings
        self.update_button()

    def update_button(self):
        if self.settings.silent:
            self.label = '\N{BELL WITH CANCELLATION STROKE} Disabled'
            self.style = discord.ButtonStyle.red
        else:
            self.label = '\N{BELL} Enabled'
            self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction[Bot]) -> None:
        self.settings.silent = not self.settings.silent
        self.update_button()
        await interaction.response.edit_message(view=self.view)


class SettingsView(ui.LayoutView):
    row = ui.ActionRow()

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

        # For this example, we'll use multiple sections to organize the settings.
        container = ui.Container()
        header = ui.TextDisplay('# Settings\n-# This is an example to showcase how to do settings.')
        container.add_item(header)
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        self.count_button = SetCountButton(self.settings)
        container.add_item(
            ui.Section(
                ui.TextDisplay('## Emoji Count\n-# This is the number of times the emoji will be repeated in the message.'),
                accessory=self.count_button,
            )
        )
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(
            ui.Section(
                ui.TextDisplay(
                    '## Notification Settings\n-# This controls whether the bot will use silent messages or not.'
                ),
                accessory=NotificationToggleButton(self.settings),
            )
        )
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
        container.add_item(ui.TextDisplay('## Fruit Selection\n-# This is the fruit that is shown in the message.'))
        container.add_item(FruitsSetting(self.settings))
        container.add_item(ui.TextDisplay('## Channel Selection\n-# This is the channel where the message will be sent.'))
        container.add_item(ChannelSetting(self.settings))
        container.add_item(
            ui.TextDisplay('## Member Selection\n-# These are the members that will be mentioned in the message.')
        )
        container.add_item(MembersSetting(self.settings))
        self.add_item(container)

        # Swap the row so it's at the end
        self.remove_item(self.row)
        self.add_item(self.row)

    @row.button(label='Finish', style=discord.ButtonStyle.green)
    async def finish_button(self, interaction: discord.Interaction[Bot], button: ui.Button) -> None:
        # Edit the message to make it the interaction response...
        await interaction.response.edit_message(view=self)
        # ...and then send a confirmation message.
        await interaction.followup.send(f'Settings saved.', ephemeral=True)
        # Then delete the settings panel
        self.stop()
        await interaction.delete_original_response()


bot = Bot()


@bot.command()
async def settings(ctx: commands.Context[Bot]):
    """Shows the settings view."""
    view = SettingsView(ctx.bot.settings)
    await ctx.send(view=view)


@bot.command()
async def send(ctx: commands.Context[Bot]):
    """Sends the message with the current settings."""
    settings = ctx.bot.settings

    if settings.channel is None:
        await ctx.send('No channel is configured. Please use the settings command to set one.')
        return

    # This example is super silly, so don't do this for real. It's annoying.
    content = ' '.join(settings.fruit_type.emoji for _ in range(settings.count))
    mentions = ' '.join(member.mention for member in settings.members)

    await settings.channel.send(content=f'{mentions} {content}', silent=settings.silent)


bot.run('token')
