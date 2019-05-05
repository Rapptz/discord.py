import discord
import youtube_dl
from discord.ext import commands
from discord.voice_client import VoiceClient


bot = commands.Bot(command_prefix='+')

@bot.event
async def on_ready():
    print('Bot is ready.')

@bot.event
async def on_group_join(channel, user):
    print(f'{user} has entered the boardroom.')
    await ctx.send(f'{user} has entered the boardroom.', tts=True)

@bot.event
async def on_group_remove(channel, user):
    print(f'{user} has left the boardroom.', tts=True)

@bot.command()
async def join(ctx):
    await ctx.message.author.voice.channel.connect()

@bot.command()
async def play(ctx, url):
    player = await VoiceClient.create_ytdl_player(url)
    player.start()

bot.run('NTczNDM4OTU4OTUyNzc1Njgw.XMvd4g.NW3f4pZZEt6lRPFviOtKK3uCnVw')
