import discord
import argparse


def vc_required(func):
    async def get_vc(self, msg):
        vc = await self.get_vc(msg)
        if not vc:
            return
        await func(self, msg, vc)
    return get_vc


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_msg = None

    def convert_arg_line_to_args(self, arg_line: str):
        return arg_line.split()  # this is good enough for our arguments

    def parse_args(self, args=None):
        self.error_msg = None
        return super().parse_args(args)

    def error(self, message: str):
        self.error_msg = message


start_arg_parser = ArgumentParser()
start_arg_parser.add_argument('-o', '--out', choices=['wav', 'mp3'], default='mp3')


class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections = {voice.guild.id: voice for voice in self.voice_clients}
        self.out = None

        self.commands = {
            'start': self.start_listening,
            'stop': self.stop_listening,
            'pause': self.pause_listening,
            'resume': self.resume_listening,
        }

    # Commands
    @vc_required
    async def start_listening(self, msg, vc):
        if vc.is_listening():
            return await msg.channel.send("Already listening")
        args = " ".join(msg.content.split()[1:])
        args = start_arg_parser.parse_args(start_arg_parser.convert_arg_line_to_args(args))
        if start_arg_parser.error_msg is not None:
            return await msg.channel.send(start_arg_parser.error_msg)
        vc.listen(self.get_sink(args.out), after=self.on_listening_stopped)
        await msg.channel.send("Started listening")

    @vc_required
    async def stop_listening(self, msg, vc):
        if not vc.is_listening():
            return await msg.channel.send("Not currently listening")
        vc.stop_listening()
        await vc.disconnect()
        await msg.channel.send("No longer listening.")

    @vc_required
    async def pause_listening(self, msg, vc):
        if vc.is_listening_paused():
            return await msg.channel.send("Listening already paused")
        vc.pause_listening()
        await self.change_deafen_state(vc, True)
        await msg.channel.send("Listening has been paused")

    @vc_required
    async def resume_listening(self, msg, vc):
        if not vc.is_listening_paused():
            return await msg.channel.send("Already resumed")
        vc.resume_listening()
        await self.change_deafen_state(vc, False)
        await msg.channel.send("Listening has been resumed")

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

    async def change_deafen_state(self, vc, deafen):
        state = vc.guild.me.voice
        await vc.guild.change_voice_state(channel=vc.channel, self_mute=state.self_mute,
                                          self_deaf=deafen)

    def get_sink(self, out_type):
        return {
            "mp3": discord.MP3AudioFileSink,
            "wav": discord.WaveAudioFileSink
        }[out_type]('audio-output')

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
            del self.connections[member.guild.id]

    def on_listening_stopped(self, sink, exc=None):
        sink.convert_files()  # convert whatever audio we have before throwing error
        if exc:
            raise exc


with open(".env", "r") as f:
    env = dict(map(lambda line: line.split("="), f.read().split("\n")))


intents = discord.Intents.all()
client = Client(intents=intents)
client.run(env["TOKEN"])
