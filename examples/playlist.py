import discord
from discord.ext import commands
import youtube_dl
import asyncio


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(self, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, ytdl.extract_info, url)
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = ytdl.prepare_filename(data)
        return self(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music:
    # guilds = { guild_id, guild_list[] }
    # guild_list = [ voice_client, requests[] ]
    # requests = [ request_info[] ]
    # request_info = [ctx, query]
    guilds = {}

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.next_song())

    async def get_guild_voice_client(self, ctx):
        voice_client = None
        try:
            voice_client = self.guilds[ctx.guild.id][0]
        except KeyError:
            if ctx.author.voice:
                self.guilds[ctx.guild.id] = [await ctx.author.voice.channel.
                                             connect(), []]
                voice_client = self.guilds[ctx.guild.id][0]
        return voice_client

    async def get_current_queue(self, requests):
        queue_string = ""
        i = 1
        for ctx, query in requests:
            queue_string += "{}. {} | Requested by {}\n".format(
                            i, query, ctx.author.name)
        return queue_string

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""
        guild_voice_client = await self.get_guild_voice_client(ctx)
        if ctx.author.voice is None:
            return await ctx.send("You must be in a voice channel to make "
                                  "requests.")
        elif ctx.me.voice.channel is not ctx.author.voice.channel and \
                guild_voice_client.is_playing():
            return await ctx.send("I am already playing music in {}.".format(
                guild_voice_client.channel))
        else:
            request_info = [ctx, query]
            try:
                voice_client = self.guilds[ctx.guild.id][0]
                self.guilds[ctx.guild.id][1].append(request_info)
            except:
                self.guilds[ctx.guild.id] = [ctx.voice_client,
                                             [].append(request_info)]
            await ctx.send("**{}** has been added to the queue for **{}**.\n"
                           "```{}```".format(query, ctx.guild.name,
                                             await self.get_current_queue(
                                                 self.guilds[ctx.guild.id][1])))

    async def next_song(self):
        # have a loop that continously loops through each guild and checks to
        # see if the voice client is playing. if not, grab the next item from
        # the queue, if it exists, and play it.
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild_list in self.guilds.values():
                # guild_list = [voice_client, request_info]
                # request_info = [ctx, query]
                if guild_list[0].is_playing() or len(guild_list[1]) == 0:
                    pass
                else:
                    try:
                        next_request = guild_list[1].pop(0)
                        ctx = next_request[0]
                        song = next_request[1]
                        player = await YTDLSource.from_url(song,
                                                           loop=self.bot.loop)
                        guild_list[0].play(player, after=lambda e: print(
                            'Player error: %s' % e) if e else None)
                        await ctx.send('Now playing: {}'.format(player.title))
                    except IndexError:
                        pass
            await asyncio.sleep(2)
        return

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        ctx.voice_client.source.volume = volume
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()


def setup(bot):
    bot.add_cog(Music(bot))
