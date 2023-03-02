import discord
import os


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

        self.commands = {
            'start': self.start_listening,
            'stop': self.stop_listening,
        }

    # Commands
    @vc_required
    async def start_listening(self, msg, vc):
        if vc.listening:
            return await msg.channel.send("Already listening")
        vc.listen(discord.AudioFileSink("audio-output"))
        await msg.channel.send("Started listening")

    @vc_required
    async def stop_listening(self, msg, vc):
        vc.stop_listening()
        await vc.disconnect()

    # Util

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
            self.connections[message.guild.id] = vc
            return vc

    # Events

    async def on_message(self, msg):
        if not msg.content or not msg.content.startswith("!"):
            return
        cmd = msg.content.split()[0].strip()[1:].lower()
        if cmd in self.commands:
            await self.commands[cmd](msg)

    async def on_voice_state_update(self, member, before, after):
        if member.id != self.user.id:
            return

        if before.channel is not None and after.channel is None:
            sink = self.connections[member.guild.id].sink
            if sink is not None:
                sink.cleanup()
                sink.convert_files()
            del self.connections[member.guild.id]


with open(".env", "r") as f:
    env = dict(map(lambda line: line.split("="), f.read().split("\n")))


intents = discord.Intents.all()
client = Client(intents=intents)
client.run(env["TOKEN"])
