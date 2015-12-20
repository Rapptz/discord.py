import discord
import asyncio

client = discord.Client()

@asyncio.coroutine
def my_background_task():
    yield from client.wait_until_ready()
    counter = 0
    channel = discord.Object(id='channel_id_here')
    while not client.is_closed:
        counter += 1
        yield from client.send_message(channel, counter)
        yield from asyncio.sleep(60) # task runs every 60 seconds

@client.async_event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

loop = asyncio.get_event_loop()

try:
    loop.create_task(my_background_task())
    loop.run_until_complete(client.login('email', 'password'))
    loop.run_until_complete(client.connect())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
