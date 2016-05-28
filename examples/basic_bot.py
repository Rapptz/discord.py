import discord
from discord.ext import commands
import random
from dict import DictionaryReader
from botkey import Key
from subprocess import call
import sys

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='!', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def joined(member : discord.Member):
    """Says when a member joined."""
    await bot.say('{0.name} joined in {0.joined_at}'.format(member))
	
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
async def statweights(*params : str):
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
	call(["cmdhere.bat"])
	sys.exit();
	await bot.say('http://i.imgur.com/EMSiUF3.jpg')		

bot.run(Key().value())

