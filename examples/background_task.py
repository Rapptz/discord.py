import discord
import asyncio

client = discord.Client()

async def my_background_task():
    await client.wait_until_ready()
    counter = 0
    channel = discord.Object(id='channel_id_here')
    while not client.is_closed:
        counter += 1
        await client.send_message(channel, counter)
        await asyncio.sleep(60) # task runs every 60 seconds

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

loop = asyncio.get_event_loop()

try:
    loop.create_task(my_background_task())
    loop.run_until_complete(client.login('token'))
    loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
