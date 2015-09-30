import discord
import logging

# Set up the logging module to output diagnostic to the console.
logging.basicConfig()

client = discord.Client()
client.login('email', 'password')

if not client.is_logged_in:
    print('Logging in to Discord failed')
    exit(1)

@client.event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
def on_message(message):
    if message.author.id != client.user.id:
        client.send_message(message.channel, message.content)

client.run()
