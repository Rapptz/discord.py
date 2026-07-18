# This example requires the 'message_content' privileged intent to function.

from discord.ext import commands

import discord


class Bot(commands.Bot):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


# Define a LayoutView, which will allow us to add v2 components to it.
class Layout(discord.ui.LayoutView):
    # you can add any top-level component (ui.ActionRow, ui.Section, ui.Container, ui.File, etc.) here

    action_row = discord.ui.ActionRow()

    @action_row.button(label='Click Me!')
    async def action_row_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Hi!', ephemeral=True)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            'Click the above button to receive a **very special** message!',
        ),
        accent_colour=discord.Colour.blurple(),
    )


bot = Bot()


@bot.command()
async def layout(ctx: commands.Context):
    """Sends a very special message!"""
    await ctx.send(view=Layout())  # sending LayoutView's does not allow for sending any content, embed(s), stickers, or poll


bot.run('token')
