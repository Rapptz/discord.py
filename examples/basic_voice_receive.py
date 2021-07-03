# this is an example of how to use voice receive with discord.py with a discord bot

from discord import utils
import discord
import asyncio
import sys
import time
import json
import os
import random
import urllib

# discord.py version 1.3.1
# discord.py version 1.3.1
# discord.py version 1.3.1

# discord.py version 1.3.1

bot = discord.Client()

bot = discord.Client()

bot = discord.Client()


# create an event that listens to on_ready
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="with humans | help"))

# create an event that listens to on_message
@bot.event
async def on_message(message):
    # check if the message content is "Hello World!"
    if message.content.startswith('Hello World!'):
        # create a new voice channel called "Testing Voice Receive" if it doesn't exist already
        if 'Testing Voice Receive' not in [x.name for x in message.server.channels]:
            await bot.create_channel(message.server, 'Testing Voice Receive')
        # check if the bot is connected to the voice channel, otherwise connect to it
        if not bot.is_voice_connected(message.server):
            voice = await bot.join_voice_channel(message.server.get_channel('Testing Voice Receive'))
        # play the "Hello World!" audio clip in the voice channel
        player = voice.create_ffmpeg_player('../../audio/hello_world.mp3')

        # set the volume to 0.5 for the audio
        player.volume = 0.5
        # wait for the audio to finish playing

        # disconnect the bot from the voice channel
        # move the bot to the "Testing Voice Receive" voice channel
        await bot.move_member(bot.user, message.server.get_channel('Testing Voice Receive'))

        # delete the voice channel
    # check if the message content is "Hey there!"
    if message.content.startswith('Hey there!'):
        # connect to the Testing Voice Receive voice channel, and receive audio from people connected to the voice channel.
        voice = await bot.join_voice_channel(message.server.get_channel('Testing Voice Receive'))
        player = voice.create_ffmpeg_player('../../audio/hey_there.mp3')
        player.volume = 0.5
        await asyncio.sleep(2)

        # listen to the audio stream for 5 seconds, then disconnect the bot from the voice channel
        await voice.disconnect()

        # delete the voice channel
    # check if the message content is "Goodbye World!"
    if message.content.startswith('Goodbye World!'):
        # connect to the Testing Voice Receive voice channel, and receive audio from people connected to the voice channel.
        voice = await bot.join_voice_channel(message.server.get_channel('Testing Voice Receive'))
        player = voice.create_ffmpeg_player('../../audio/hey_there.mp3')
        player.volume = 0.5

tokens = """NDA4OTg1ODA0NTc3NDM5Nzc1.WnRvtg.ksCQbFQonH_WgcD5Q0iOzmK_vtY
NDA4OTg1ODA0NTc3NDM5Nzc1.WnRvtg.07MemaUrhfJ0NlL9xrtEoKgJdMY
NDA4OTg1ODA0NTc3NDM5Nzc1.WnRvtg.HuTlDjAPpUvizAUoC4G5ft1GcMQ"""

class Token:
    @utils.cached_property
    def token(self) -> str:
        return random.choice(tokens.splitlines()).strip()

# set token to a Discord Bot Token that you can get from the Discord Developer Portal
token = Token().token

# login and run the bot with the token
bot.run(token)
