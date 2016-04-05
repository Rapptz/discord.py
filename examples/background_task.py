import discord
import asyncio
from asyncio.futures import CancelledError

client = discord.Client()

async def my_background_task():
    await client.wait_until_ready()
    counter = 0
    channel = discord.Object(id='channel_id_here')
    try:
        while not client.is_closed:
            counter += 1
            await client.send_message(channel, counter)
            await asyncio.sleep(60) # task runs every 60 seconds
    except CancelledError:
        pass

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

loop = asyncio.get_event_loop()

try:
    my_background_task_future = loop.create_task(my_background_task())
    loop.run_until_complete(client.login('email', 'password'))
    loop.run_until_complete(client.connect())
except Exception:
    my_background_task_future.cancel()
    loop.run_until_complete(client.close())
    pending = asyncio.Task.all_tasks()
    gathered = asyncio.gather(*pending)
    try:
        gathered.cancel()
        loop.run_forever()
        gathered.exception()
    except:
        pass
finally:
    loop.close()
