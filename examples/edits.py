import discord
import time
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
    if message.content.startswith('!editme'):
        msg = client.send_message(message.author, '10')
        time.sleep(3)
        client.edit_message(msg, '40')

@client.event
def on_message_edit(before, after):
    client.send_message(after.channel, '**{}** edited their message:\n{}'.format(after.author.name, before.content))

client.run()
