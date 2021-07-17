import typing

import discord
from discord import emoji
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('$'))

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# Gives us a view containing a dropdown menu
class Dropdown(discord.ui.View):
    def __init__(self, *, timeout: typing.Optional[float] = 180):
        super().__init__(timeout=timeout)

    # Send a message pinging the user with their selected choice
    @discord.ui.select(options=[
        discord.SelectOption(label='Red', description = 'Your favourite color is red', emoji='🟥'), 
        discord.SelectOption(label='Green', description = 'Your favourite color is green', emoji='🟩'), 
        discord.SelectOption(label='Blue', description = 'Your favourite color is blue', emoji = '🟦')
    ], placeholder="Choose your favourite color...")
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.send_message(f"{interaction.user.mention}'s favourite color is {select.values[0]}!")

bot = Bot()

@bot.command()
async def select(ctx: commands.Context):
    """Sends a message with a dropdown."""

    # Creating the view
    view = Dropdown()

    # Sending the message with the view
    await ctx.send('Pick your favourite color:', view = view)

bot.run('token')
