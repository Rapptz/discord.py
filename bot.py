import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='zz',
                   owner_id=162074751341297664,
                   intents=intents,
                   help_command=None)

bot.load_extension('jishaku')

@bot.event
async def on_ready():
    print(f'\tReady {bot.user}')

bot.run('NTI3NjUxNzA2MzQzOTE1NTQy.XCQj8g.4SEQyoS-wrd9In2Ng_n-dPVJZso')
