import asyncio
import discord

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    discord.opus.load_opus('opus')

class VoiceEntry:
    def __init__(self, message, song):
        self.requester = message.author
        self.channel = message.channel
        self.song = song

class Bot(discord.Client):
    def __init__(self):
        super().__init__()
        self.songs = asyncio.Queue()
        self.play_next_song = asyncio.Event()
        self.starter = None
        self.player = None
        self.current = None

    def toggle_next_song(self):
        self.loop.call_soon_threadsafe(self.play_next_song.set)

    def can_control_song(self, author):
        return author == self.starter or (self.current is not None and author == self.current.requester)

    def is_playing(self):
        return self.player is not None and self.player.is_playing()

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.channel.is_private:
            await self.send_message(message.channel, 'You cannot use this bot in private messages.')

        elif message.content.startswith('$join'):
            if self.is_voice_connected():
                await self.send_message(message.channel, 'Already connected to a voice channel')
            channel_name = message.content[5:].strip()
            check = lambda c: c.name == channel_name and c.type == discord.ChannelType.voice
            channel = discord.utils.find(check, message.server.channels)
            if channel is None:
                await self.send_message(message.channel, 'Cannot find a voice channel by that name.')
            else:
                await self.join_voice_channel(channel)
                self.starter = message.author

        elif message.content.startswith('$leave'):
            if not self.can_control_song(message.author):
                return
            self.starter = None
            await self.voice.disconnect()

        elif message.content.startswith('$pause'):
            if not self.can_control_song(message.author):
                fmt = 'Only the requester ({0.current.requester}) can control this song'
                await self.send_message(message.channel, fmt.format(self))
            elif self.player.is_playing():
                self.player.pause()

        elif message.content.startswith('$resume'):
            if not self.can_control_song(message.author):
                fmt = 'Only the requester ({0.current.requester}) can control this song'
                await self.send_message(message.channel, fmt.format(self))
            elif self.player is not None and not self.is_playing():
                self.player.resume()

        elif message.content.startswith('$next'):
            filename = message.content[5:].strip()
            await self.songs.put(VoiceEntry(message, filename))
            await self.send_message(message.channel, 'Successfully registered {}'.format(filename))

        elif message.content.startswith('$play'):
            if self.player is not None and self.player.is_playing():
                await self.send_message(message.channel, 'Already playing a song')
                return
            while True:
                if not self.is_voice_connected():
                    await self.send_message(message.channel, 'Not connected to a voice channel')
                    return
                self.play_next_song.clear()
                self.current = await self.songs.get()
                self.player = self.voice.create_ffmpeg_player(self.current.song, after=self.toggle_next_song)
                self.player.start()
                fmt = 'Playing song "{0.song}" from {0.requester}'
                await self.send_message(self.current.channel, fmt.format(self.current))
                await self.play_next_song.wait()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')


bot = Bot()
bot.run('email', 'password')
