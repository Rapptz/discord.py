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
    client.send_message(message.channel, message.content)

client.run()
