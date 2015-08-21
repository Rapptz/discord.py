import discord

client = discord.Client()
client.login('email', 'password')

@client.event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
def on_message_delete(message):
    client.send_message(message.channel, '{} has deleted the message:\n{}'.format(message.author.name, message.content))

client.run()
