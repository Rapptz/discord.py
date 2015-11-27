import discord

client = discord.Client()
client.login('email', 'password')

@client.event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
def on_message(message):
    if message.content.startswith('!deleteme'):
        msg = client.send_message(message.channel, 'I will delete myself now...')
        client.delete_message(msg)

@client.event
def on_message_delete(message):
    client.send_message(message.channel, '{} has deleted the message:\n{}'.format(message.author.name, message.content))

client.run()
