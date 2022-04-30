from typing import Optional

import discord
from discord import app_commands

MY_GUILD = discord.Object(id=0)  # replace with your guild id


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, application_id: int):
        super().__init__(intents=intents, application_id=application_id)

        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild,
    # without requiring to set the guild to every command individually by just copying them over.
    # By doing so we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()

# In order to use a basic synchronization of the app commands in the setup_hook,
# you have replace ... with your bots application_id you find in the developer portal.
client = MyClient(intents=intents, application_id=0)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')





client.run('token')
