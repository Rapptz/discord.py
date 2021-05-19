import discord




def vc_required(func):
    async def get_vc(self, msg):
        vc = await self.get_vc(msg)
        if not vc:
            return
        await func(self, msg, vc)
    return get_vc


def args_to_filters(args):
    filters = {}
    if '--time' in args:
        index = args.index('--time')
        try:
            seconds = args[index+1]
        except IndexError:
            return "You must provide an amount of seconds for the time."
        try:
            seconds = int(seconds)
        except ValueError:
            return "You must provide a value integer value"
        filters.update({'time': seconds})
    if '--users' in args:
        users = []
        index = args.index('--users')+1
        while True:
            try:
                users.append(int(args[index]))
            except IndexError:
                break
            except ValueError:
                break
            index += 1
        if not users:
            return "You must provide at least one user, or multiple separated by spaces"
        filters.update({'users': users})
    return filters


def get_encoding(args):
    if '--output' in args:
        index = args.index('--output')
        try:
            encoding = args[index+1].lower()
            if encoding not in discord.Sink.valid_encodings:
                return
            return encoding
        except IndexError:
            return
    else:
        return 'wav'


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
        connection = self.connections.get(message.guild.id)
        if connection:
            if connection.channel.id == message.author.voice.channel.id:
                return connection

            await connection.move_to(vc.channel)
            return connection
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
        args = msg.content.split()[1:]
        filters = args_to_filters(args)
        if type(filters) == str:
            return await msg.channel.send(filters)
        encoding = get_encoding(args)
        if encoding is None:
            return await msg.channel.send("You must provide a valid output encoding.")

        vc.start_recording(discord.Sink(encoding=encoding, filters=filters), self.on_stopped, msg.channel)

        await msg.channel.send("The recording has started!")

    @vc_required
    async def pause_recording(self, msg, vc):
        vc.pause_recording()
        await msg.channel.send(f"The recording has been {'paused' if vc.paused else 'unpaused}")

    @vc_required
    async def stop_recording(self, msg, vc):
        vc.stop_recording()

    async def on_stopped(self, sink, *args):
        channel = args[0]
        # Note: sink.audio_data = {user_id: AudioData}
        recorded_users = [f" <@{str(user_id)}> ({os.path.split(audio.file)[1]}) " for user_id, audio in sink.audio_data.items()]
        await channel.send(f"Finished! Recorded audio for {','.join(recorded_users)}")

    async def on_voice_state_update(self, member, before, after):
        if member.id == self.user.id:
            if before.channel and not after.channel and member.guild.id in self.connections:
                print("Disconnected")
                del self.connections[member.guild.id]


intents = discord.Intents.all()
client = Client(intents=intents)
client.run('token')
