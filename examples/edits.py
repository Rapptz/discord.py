import discord
import asyncio

client = discord.Client()

@client.async_event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.async_event
def on_message(message):
    if message.content.startswith('!editme'):
        msg = yield from client.send_message(message.author, '10')
        yield from asyncio.sleep(3)
        yield from client.edit_message(msg, '40')

@client.async_event
def on_message_edit(before, after):
    fmt = '**{0.author}** edited their message:\n{1.content}'
    yield from client.send_message(after.channel, fmt.format(after, before))

client.run('email', 'password')
