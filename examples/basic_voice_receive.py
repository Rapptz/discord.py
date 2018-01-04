import asyncio

import discord

from discord.ext import commands

# The user to record audio from
TARGET_USER_ID = 161508165672763392

class Recorder:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def die(self, ctx):
        await self.bot.logout()

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        voice_client = await channel.connect()
        
        target = bot.get_user(TARGET_USER_ID)
        file_ = open('audio.pcm', 'wb')
        await voice_client.pipe_voice_into_file(target, file_)

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='Record audio from a voice channel.')

@bot.event
async def on_ready():
    print('Logged in as {0.id}/{0}'.format(bot.user))
    print('------')

bot.add_cog(Recorder(bot))
bot.run('token')
