#imports
import os
import discord

# token and client info
TOKEN = '<TOKEN>'
client = discord.Client()

# client event on ready
@client.event
async def on_ready():
    # log that the bot has connected
    print(f'{client.user} has connected to Discord!')

# client event on message
@client.event
async def on_message(msg):
    # get the content of the message all as lowercase
    content = msg.content.lower()
	
	# if the message contains hello
	if 'hello' in content:
		# send a new reply of Hello!
		await msg.reply('Hello!')
