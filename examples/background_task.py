import discord
from discord.ext import tasks
import asyncio

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Start the task
        self.my_background_task.start()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    @tasks.loop(minutes=1.0)
    async def my_background_task(self):
        channel = self.get_channel(1234567) # channel ID goes here
        await channel.send(my_background_task.current_loop)
    
    @my_background_task.before_loop
    async def before_loop(self):
        await self.wait_until_ready()

client = MyClient()
client.run('token')
