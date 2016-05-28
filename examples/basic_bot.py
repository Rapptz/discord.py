import discord
from discord.ext import commands
import random
from dict import DictionaryReader
from botkey import Key
from subprocess import call
import sys

description = '''I'm PriestBot, your robot friend for links and quick info!

Below you'll find my basic commands.

You can find my full list of commands at https://github.com/lgkern/discord.py/blob/async/examples/dictEntries.txt'''
bot = commands.Bot(command_prefix='!', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
	
@bot.command()
async def list(*params : str):
	"""Lists of items"""
	p = DictionaryReader()
	s = p.commandReader(('list',) + params)
	if s != 'None':
		await bot.say(s)
		
@bot.command()
async def item(*params : str):
	"""Direct link to different items"""
	p = DictionaryReader()
	s = p.commandReader(('item',) + params)
	if s != 'None':
		await bot.say(s)
		
@bot.command()
async def link(*params : str):
	"""Useful website/forum links"""
	p = DictionaryReader()
	s = p.commandReader(('link',) + params)
	if s != 'None':
		await bot.say(s)
		
@bot.command()
async def stats(*params : str):
	"""Stat weights"""
	p = DictionaryReader()
	s = p.commandReader(('stat',) + params)
	if s != 'None':
		await bot.say(s)
	
@bot.command()
async def classfantasy(*params : str):
	"""Insightful"""
	await bot.say('http://i.imgur.com/EMSiUF3.jpg')	
	
@bot.command()
async def update():
	"""Update the bot link database to the most recent one"""
	call(["git","pull"])

@bot.command()
async def fullUpdate():
	"""Fully updates the bot's code"""
	call(["git","pull"])
	call(["cmdhere.bat"])
	sys.exit();
	

bot.run(Key().value())

