import discord
from discord import app_commands


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apples_picked = []
        # initiate our command tree, with the client
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')  # type: ignore
        print('------')

        # Sync our local tree with Discord
        await self.tree.sync(guild=guild)


intents = discord.Intents.default()
# the guild to register the command to, remove to make global
# (global commands can take up to an hour to register)
# you could also pass a `discord.Guild` and it would work.
guild = discord.Object(id=GUILD_ID_HERE)
client = MyClient(intents=intents)

# initiate the command on top of our coroutine
@client.tree.command(guild=guild)
@app_commands.describe(apple='The Apple to Pick')  # describe what the option is
async def pick(interaction: discord.Interaction, apple: str):
    """Pick an Apple from a tree"""  # the docstring representing the commands description

    # make sure the apple isn't already picked
    if apple in client.apples_picked:
        await interaction.response.send_message('This Apple is already picked!')
        return

    # add the apple to the list
    client.apples_picked.append(apple)
    await interaction.response.send_message(f'You picked {apple}!')


# initiate the command on top of our coroutine
@client.tree.command(guild=guild)
@app_commands.describe(apple='The Apple to Plant')  # describe what the option is
async def plant(interaction: discord.Interaction, apple: str):
    # the docstring representing the commands description
    # this can have spaces, and have capital letters.
    # context menu commands cannot have a description
    """Plant a Apple"""

    # make sure the apple is picked
    if apple not in client.apples_picked:
        await interaction.response.send_message('This Apple hasn\'t been picked yet!')
        return

    # remove the apple from the list
    client.apples_picked.remove(apple)
    await interaction.response.send_message(f'You planted {apple}!')


client.run('token')
