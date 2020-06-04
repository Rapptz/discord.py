import discord
from discord.ext import tasks


# A task that sends a message to the channel once per minute.
@tasks.loop(minutes=1)
async def my_task(client):
    # https://discordpy.readthedocs.io/en/latest/api.html?highlight=wait%20until%20re#discord.Client.wait_until_ready
    await client.wait_until_ready()
    
    channel = client.get_channel(12345)
    await channel.send('message per minute!')


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tasks must be started by calling 'start' on them.
        my_task.start(self)  # We pass 'self' since 'self' is our client.

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')


MyClient = MyClient()
MyClient.run('token')
