"""
DISCLAIMER:
Please understand Music bots are complex, and that even this basic example can be daunting to a beginner.
For this reason it's highly advised you familiarize yourself with discord.py, python and asyncio, BEFORE
you attempt to write a music bot.

This example makes use of Python 3.6

For a more basic voice example please read:
    https://github.com/Rapptz/discord.py/blob/rewrite/examples/basic_voice.py
"""
import discord
from discord.ext import commands

import asyncio
import async_timeout
import youtube_dl


if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')


opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s-%(autonumber)s.%(ext)s',  # Autonumber to avoid conflicts
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
    }
ytdl = youtube_dl.YoutubeDL(opts)


ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
    }


class YTDLSource(discord.PCMVolumeTransformer):
    """A class which uses YTDL to retrieve a song and returns it as a source for Discord."""
    def __init__(self, source, *, data, entry, volume):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.requester = entry.requester
        self.channel = entry.channel

    @classmethod
    async def from_url(cls, entry, *, loop=None, player):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, ytdl.extract_info, entry.query)

        if 'entries' in data:
            data = data['entries'][0]

        await entry.channel.send(f'```ini\n[Added: {data["title"]} to the queue.]\n```', delete_after=15)

        filename = ytdl.prepare_filename(data)
        await player.queue.put(cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, entry=entry,
                                   volume=player.volume))


class MusicPlayer:
    """Music Player instance.

    Each guild using music will have a separate instance."""

    def __init__(self, bot, ctx):
        self.bot = bot

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.die = asyncio.Event()

        self.guild = ctx.guild
        self.default_chan = ctx.channel
        self.current = None
        self.volume = .4

        self.now_playing = None

        self.player_task = self.bot.loop.create_task(self.player_loop())
        self.inactive_task = self.bot.loop.create_task(self.inactive_check(ctx))

    async def inactive_check(self, ctx):
        await self.die.wait()
        await ctx.invoke(self.bot.get_command('stop'))

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                with async_timeout.timeout(300):  # Auto leave after 5 minutes of inactivity.
                    entry = await self.queue.get()
            except asyncio.TimeoutError:
                await self.default_chan.send('I have been inactive for 5 minutes. Goodbye!')
                return self.die.set()

            channel = entry.channel
            requester = entry.requester
            self.guild.voice_client.play(entry, after=lambda s: self.bot.loop.call_soon_threadsafe(self.next.set))

            self.now_playing = await channel.send(f'**Now Playing:** `{entry.title}` requested by `{requester}`')

            # Wait until the players after function is called. Then do some cleanup on the old source.
            await self.next.wait()
            entry.cleanup()

            try:
                await self.now_playing.delete()
            except discord.HTTPException:
                pass

            # Avoid smashing together songs.
            await asyncio.sleep(1)


class MusicEntry:
    def __init__(self, ctx, query):
        self.requester = ctx.author
        self.channel = ctx.channel
        self.query = query


class Music:
    """Music Cog containing various commands for playing music.

    This cog supports cross guild music playing and implements a queue for playlists."""

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def __local_check(self, ctx):
        """A check which applies to all commands in Music."""
        if ctx.invoked_with == 'help':
            return True
        if not ctx.guild:
            await ctx.send('Music commands can not be used in DMs.')
            return False
        return True

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(self.bot, ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connect', aliases=['summon', 'join', 'move'])
    async def voice_connect(self, ctx, *, channel: discord.VoiceChannel=None):
        """Summon the bot to a voice channel.

        This command handles both summoning and moving the bot."""
        channel = getattr(ctx.author.voice, 'channel', channel)
        vc = ctx.guild.voice_client

        if not channel:
            return await ctx.send('No channel to join. Please either specify a valid channel or join one.')

        if not vc:
            try:
                await channel.connect(timeout=15)
            except asyncio.TimeoutError:
                return await ctx.send('Unable to connect to the voice channel at this time. Please try again.')
            await ctx.send(f'Connected to: **{channel}**', delete_after=15)
        else:
            if channel == vc.channel:
                return
            try:
                await vc.move_to(channel)
            except Exception:
                return await ctx.send('Unable to move this channel. Perhaps missing permissions?')
            await ctx.send(f'Moved to: **{channel}**', delete_after=15)

    @commands.command(name='play')
    async def play_song(self, ctx, *, query: str):
        """Add a song to the queue.

        Uses YTDL to auto search for a song. A URL may also be provided."""
        vc = ctx.guild.voice_client

        if vc is None:
            await ctx.invoke(self.voice_connect)
            if not ctx.guild.voice_client:
                return
        else:
            if ctx.author not in vc.channel.members:
                return await ctx.send(f'You must be in **{vc.channel}** to request songs.', delete_after=30)

        player = self.get_player(ctx)

        entry = MusicEntry(ctx, query)
        async with ctx.typing():
            try:
                await YTDLSource.from_url(entry, loop=self.bot.loop, player=player)
            except Exception as e:
                await ctx.send(f'There was an error with retrieving your song:\n```css\n[{e}]\n```')

    @commands.command(name='stop')
    async def stop_player(self, ctx):
        """Stops the player and clears the queue."""
        vc = ctx.guild.voice_client

        if vc is None:
            return

        player = self.get_player(ctx)
        inact = player.inactive_task

        vc.stop()
        try:
            player.player_task.cancel()
            del self.players[ctx.guild.id]
        except Exception as e:
            return print(e)

        await vc.disconnect()
        await ctx.send('Disconnected from voice and cleared your queue. Goodbye!', delete_after=15)

        try:
            inact.cancel()
        except Exception as e:
            print(e)

    @commands.command(name='pause')
    async def pause_song(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.guild.voice_client

        if vc is None or not vc.is_playing():
            return await ctx.send('I am not currently playing anything.', delete_after=20)

        if vc.is_paused():
            return await ctx.send('I am already paused.', delete_after=20)

        vc.pause()
        await ctx.send(f'{ctx.author.mention} has paused the song.')

    @commands.command(name='resume')
    async def resume_song(self, ctx):
        """Resume a song if it is currently paused."""
        vc = ctx.guild.voice_client

        if vc is None or not vc.is_connected():
            return await ctx.send('I am not currently playing anything.', delete_after=20)

        if vc.is_paused():
            vc.resume()
            await ctx.send(f'{ctx.author.mention} has resumed the song.')

    @commands.command(name='skip')
    async def skip_song(self, ctx):
        """Skip the current song."""
        vc = ctx.guild.voice_client

        if vc is None or not vc.is_connected():
            return await ctx.send('I am not currently playing anything.', delete_after=20)

        vc.stop()
        await ctx.send(f'{ctx.author.mention} has skipped the song.')

    @commands.command(name='current', aliases=['currentsong', 'nowplaying', 'np'])
    async def current_song(self, ctx):
        """Return some information about the current song."""
        vc = ctx.guild.voice_client

        if not vc.is_playing():
            return await ctx.send('Not currently playing anything.')

        player = self.get_player(ctx)
        msg = player.now_playing.content

        try:
            await player.now_playing.delete()
        except discord.HTTPException:
            pass

        player.now_playing = await ctx.send(msg)

    @commands.command(name='volume', aliases=['vol'])
    async def adjust_volume(self, ctx, *, vol: int):
        """Adjust the player volume."""

        if not 0 < vol < 101:
            return await ctx.send('Please enter a value between 1 and 100.')

        vc = ctx.guild.voice_client

        if vc is None:
            return await ctx.send('I am not currently connected to voice.')

        player = self.get_player(ctx)
        adj = float(vol) / 100

        try:
            vc.source.volume = adj
        except Exception:
            pass

        player.volume = adj
        await ctx.send(f'Changed player volume to: **{vol}%**')


bot = commands.Bot(command_prefix=commands.when_mentioned_or("?"),
                   description='Playlist example for discord.py@rewrite.')


@bot.event
async def on_ready():
    print(f'\nLogged in as {bot.user.name} | {bot.user.id}\nDiscord Version: {discord.__version__}\n\n{"~"*15}')

bot.add_cog(Music(bot))
bot.run('TOKEN')
