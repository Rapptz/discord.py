import discord

client = discord.Client()
client.login('email', 'password')

if not client.is_logged_in:
    print('Logging in to Discord failed')
    exit(1)

@client.event
def on_message(message):
    if message.content.startswith('!hello'):
        client.send_message(message.channel, 'Hello {}!'.format(message.author.mention()))

@client.event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run()
