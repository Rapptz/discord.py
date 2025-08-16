from discord.ext import tasks

import discord


class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # an attribute we can access from our task
        self.counter = 0

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=60)  # task runs every 60 seconds
    async def my_background_task(self):
        channel = self.get_channel(1234567)  # channel ID goes here
        # Tell the type checker that this is a messageable channel
        assert isinstance(channel, discord.abc.Messageable)

        self.counter += 1
        await channel.send(str(self.counter))

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient(intents=discord.Intents.default())
client.run('token')
