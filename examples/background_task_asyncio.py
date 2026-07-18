import discord
import asyncio


class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        channel = self.get_channel(1234567)  # channel ID goes here

        # Tell the type checker that this is a messageable channel
        assert isinstance(channel, discord.abc.Messageable)

        while not self.is_closed():
            counter += 1
            await channel.send(str(counter))
            await asyncio.sleep(60)  # task runs every 60 seconds


client = MyClient(intents=discord.Intents.default())
client.run('token')
