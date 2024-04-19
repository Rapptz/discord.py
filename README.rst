import discord
from discord.ext import commands

# تهيئة البوت
bot = commands.Bot(command_prefix='!')

# الأمر للرد على الرسالة "مرحبًا"
@bot.command()
async def hello(ctx):
    await ctx.send('مرحبًا!')

# ربط البوت بـ Token الخاص بك
bot.run('MTIzMDUzNDEyMzE1NjgwMzc3NQ.GI_Lcm.B9ZxIKdta7HDcL47qRrCr2dylNa8fFgM9ys3-k')

