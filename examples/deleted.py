import discord

client = discord.Client()

@client.async_event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.async_event
def on_message(message):
    if message.content.startswith('!deleteme'):
        msg = yield from client.send_message(message.channel, 'I will delete myself now...')
        yield from client.delete_message(msg)

@client.async_event
def on_message_delete(message):
    fmt = '{0.author.name} has deleted the message:\n{0.content}'
    yield from client.send_message(message.channel, fmt.format(message))

client.run('email', 'password')
