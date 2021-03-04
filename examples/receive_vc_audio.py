import discord


TOKEN = '*****'


def vc_required(func):
    async def get_vc(self, msg):
        vc = await self.get_vc(msg)
        if not vc:
            return
        await func(self, msg, vc)
    return get_vc


class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections = {voice.guild.id: voice for voice in self.voice_clients}
        self.playlists = {}

        self.commands = {
            '!start': self.start_recording,
            '!stop': self.stop_recording,
            '!pause': self.pause_recording,
        }

    async def get_vc(self, message):
        vc = message.author.voice
        if not vc:
            await message.channel.send("You're not in a vc right now")
            return
        if message.guild.id in self.connections:
            if self.connections[message.guild.id].channel.id == message.author.voice.channel.id:
                return self.connections[message.guild.id]
            await self.connections[message.guild.id].move_to(vc.channel)
            return self.connections[message.guild.id]
        else:
            vc = await vc.channel.connect()
            self.connections.update({message.guild.id: vc})
            return vc

    async def on_message(self, msg):
        if not msg.content:
            return
        cmd = msg.content.split()[0]
        if cmd in self.commands:
            await self.commands[cmd](msg)

    @vc_required
    async def start_recording(self, msg, vc):
        vc.start_recording(self.on_stopped, msg.channel)
        await msg.channel.send("The recording has started!")

    @vc_required
    async def pause_recording(self, msg, vc):
        vc.pause_recording()
        await msg.channel.send("The recording has been " + {True: "paused!", False: 'unpaused!'}[vc.paused])

    @vc_required
    async def stop_recording(self, msg, vc):
        vc.stop_recording()
        await msg.channel.send("Recording has stopped! The pcm files will begin to be converted to wave files.")

    async def on_stopped(self, vc, pcm, *args):
        channel = args[0]
        if not pcm:
            await channel.send("No audio was recorded")
            return
        vc.pcm_to_wave_file(pcm)
        await channel.send("The files are finished being converted!")

    async def on_voice_state_update(self, member, before, after):
        if member.id == self.user.id:
            if before.channel and not after.channel and member.guild.id in self.connections:
                print("Disconnected")
                del self.connections[member.guild.id]


intents = discord.Intents.all()
client = Client(intents=intents)
client.run(TOKEN)
