import asyncio

import discord

client = discord.Client() # Can also be an instance of commands.Bot


async def my_background_task():
    await client.wait_until_ready() # Pauses the function until on_ready has been called
    counter = 0
    channel = client.get_channel(123456)  # channel ID goes here
    while not client.is_closed():
        counter += 1
        await channel.send(counter)
        await asyncio.sleep(60)  # task runs every 60 seconds


client.loop.create_task(my_background_task())
client.run("token")
