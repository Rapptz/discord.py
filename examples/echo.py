import discord

client = discord.Client()

@client.async_event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.async_event
def on_message(message):
    if message.author.id != client.user.id:
        yield from client.send_message(message.channel, message.content)

client.run('email', 'password')
