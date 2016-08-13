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
	s = p.itemReader(('item',) + params)
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
async def weakauras(*params : str):
	"""Links for WeakAuras"""
	p = DictionaryReader()
	s = p.commandReader(('wa',) + params)
	if s != 'None':
		await bot.say(s)
		
@bot.command()
async def wa(*params : str):
	"""Links for WeakAuras"""
	p = DictionaryReader()
	s = p.commandReader(('wa',) + params)
	if s != 'None':
		await bot.say(s)
        
@bot.command()
async def bis(*params : str):
	"""Links for Best in Slot lists"""
	p = DictionaryReader()
	s = p.commandReader(('bis',) + params)
	if s != 'None':
		await bot.say(s)
		
@bot.command()
async def discord(*params : str):
	"""Links for all class Discords"""
	p = DictionaryReader()
	s = p.commandReader(('discord',) + params)
	if s != 'None':
		await bot.say(s)
		
@bot.command()
async def shame(*params : str):
	"""Shame on you!"""
	await bot.say('http://i.imgur.com/FidZknJ.gif')
	
@bot.command()
async def power(*params : str):
	"""Don't underestimate it!"""
	await bot.say('http://i.imgur.com/8Igah2t.png')
		
@bot.command()
async def boss(*params : str):
	"""Links for Boss Discussions"""
	p = DictionaryReader()
	s = p.commandReader(('boss',) + params)
	if s != 'None':
		await bot.say(s)

@bot.command()
async def artifact(*params : str):
	"""Useful info on Artifacts"""
	p = DictionaryReader()
	s = p.commandReader(('artifact',) + params)
	if s != 'None':
		await bot.say(s)		
		
@bot.command()
async def decent(*params : str):
	"""Best Voidform NA"""
	await bot.say('Here is Twintop\'s best StM to date:\nhttps://puu.sh/qgWCQ/f565207eb0.jpg')		
	
@bot.command()
async def fantasy(*params : str):
	"""Can you feel it?"""
	await bot.say('http://i.imgur.com/EMSiUF3.jpg')	
	
@bot.command()
async def racial(*params : str):
	"""Best racial for Legion"""
	await bot.say('"Follow your :heart:"\n~Hygeiah 2016')		
	
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

