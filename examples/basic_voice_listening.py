# This example uses slash commands. You can learn more about them by looking at examples/app_commands/basic.py

from typing import Literal, Optional

import discord
from discord import app_commands


class Client(discord.Client):
    GUILD = discord.Object(id=592956400875864085)

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.GUILD)
        await self.tree.sync(guild=self.GUILD)


intents = discord.Intents.default()
client = Client(intents=intents)

# Maps a file format to a sink object
FILE_FORMATS = {"mp3": discord.MP3AudioFile, "wav": discord.WaveAudioFile}


async def is_in_guild(interaction: discord.Interaction):
    # If this interaction was invoked outside a guild
    if interaction.guild is None:
        await interaction.response.send_message("This command can only be used within a server.")
        return False
    return True


async def get_vc(interaction: discord.Interaction) -> Optional[discord.VoiceClient]:
    # If the bot is currently in a vc
    if interaction.guild.voice_client is not None:
        # If the bot is in a vc other than the one of the user invoking the command
        if interaction.guild.voice_client.channel != interaction.user.voice.channel:
            # Move to the vc of the user invoking the command.
            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
        return interaction.guild.voice_client
    # If the user invoking the command is in a vc, connect to it
    if interaction.user.voice is not None:
        return await interaction.user.voice.channel.connect()


async def change_deafen_state(vc: discord.VoiceClient, deafen: bool) -> None:
    state = vc.guild.me.voice
    await vc.guild.change_voice_state(channel=vc.channel, self_mute=state.self_mute, self_deaf=deafen)


async def send_audio_file(channel: discord.TextChannel, file: discord.AudioFile):
    # Get the user id of this audio file's user if possible
    # If it's not None, then it's either a `Member` or `Object` object, both of which have an `id` attribute.
    user = file.user if file.user is None else file.user.id

    # Send the file and if the file is too big (ValueError is raised) then send a message
    # saying the audio file was too big to send.
    try:
        await channel.send(
            f"Audio file for <@{user}>" if user is not None else "Could not resolve this file to a user...",
            file=discord.File(file.path),
        )
    except ValueError:
        await channel.send(
            f"Audio file for <@{user}> is too big to send"
            if user is not None
            else "Audio file for unknown user is too big to send"
        )


# The key word arguments passed in the listen function MUST have the same name.
# You could alternatively do on_listen_finish(sink, exc, channel, ...) because exc is always passed
# regardless of if it's None or not.
async def on_listen_finish(sink: discord.AudioSink, exc=None, channel=None):
    # Convert the raw recorded audio to its chosen file type
    sink.convert_files()
    if channel is not None:
        for file in sink.output_files.values():
            await send_audio_file(channel, file)

    # Raise any exceptions that may have occurred
    if exc is not None:
        raise exc


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command(description="Join the vc you're in and begin recording.")
@app_commands.describe(
    file_format=f"The file format to write the audio data to. Valid types: {', '.join(FILE_FORMATS.keys())}"
)
async def start(interaction: discord.Interaction, file_format: Literal["mp3", "wav"] = "mp3"):
    if not await is_in_guild(interaction):
        return
    # Check that a valid file format was provided.
    file_format = file_format.lower()
    if file_format not in FILE_FORMATS:
        return await interaction.response.send_message(
            "That's not a valid file format. " f"Valid file formats: {', '.join(FILE_FORMATS.keys())}"
        )
    vc = await get_vc(interaction)
    # Make sure the person invoking the command is in a vc.
    if vc is None:
        return await interaction.response.send_message("You're not currently in a vc.")
    # Make sure we're not already recording.
    if vc.is_listen_receiving():
        return await interaction.response.send_message("Already recording.")
    # Good practice to check this before calling listen, especially if it were being called within a loop.
    if vc.is_listen_cleaning():
        return await interaction.response.send_message("Currently busy cleaning... try again in a second.")
    # Initialize the process pool which will be used for processing audio.
    # The number passed signifies the maximum number of processes to spawn.
    if not vc.is_audio_process_pool_initialized():
        vc.init_audio_processing_pool(1)
    # Start listening for audio and pass it to one of the AudioFileSink objects which will
    # record the audio to file for us. We're also passing the on_listen_finish function
    # which will be called when listening has finished.
    vc.listen(
        discord.AudioFileSink(FILE_FORMATS[file_format], "audio-output"), after=on_listen_finish, channel=interaction.channel
    )
    await interaction.response.send_message("Started recording.")


@client.tree.command(description="Stop the current recording.")
async def stop(interaction: discord.Interaction):
    if not await is_in_guild(interaction):
        return
    # Make sure we're currently in vc and recording.
    if interaction.guild.voice_client is None or not (await get_vc(interaction)).is_listen_receiving():
        return await interaction.response.send_message("Not currently recording.")
    vc = interaction.guild.voice_client
    # Stop listening and disconnect from vc. The after function passed to vc.listen in the start command
    # will be called after listening stops.
    vc.stop_listening()
    await vc.disconnect()
    await interaction.response.send_message("Recording stopped.")


@client.tree.command(description="Pause the current recording.")
async def pause(interaction: discord.Interaction):
    if not await is_in_guild(interaction):
        return
    # Make sure we're currently in vc and recording.
    if interaction.guild.voice_client is None or not (await get_vc(interaction)).is_listen_receiving():
        return await interaction.response.send_message("Not currently recording.")
    vc = interaction.guild.voice_client
    # Make sure we're not already paused
    if vc.is_listening_paused():
        return await interaction.response.send_message("Recording is already paused.")
    # Pause the recording and then change deafen state to indicate so. Note the
    # deafen state does not actually prevent the bot from receiving audio.
    vc.pause_listening()
    await change_deafen_state(vc, True)
    await interaction.response.send_message("Recording paused.")


@client.tree.command(description="Resume the current recording.")
async def resume(interaction: discord.Interaction):
    if not await is_in_guild(interaction):
        return
    # Make sure we're currently in vc and recording.
    if interaction.guild.voice_client is None or not (await get_vc(interaction)).is_listen_receiving():
        return await interaction.response.send_message("Not currently recording.")
    vc = interaction.guild.voice_client
    # Make sure we're paused
    if not vc.is_listening_paused():
        return await interaction.response.send_message("Recording is already resumed.")
    # Resume the recording and then change the deafen state to indicate so.
    vc.resume_listening()
    await change_deafen_state(vc, False)
    await interaction.response.send_message("Recording resumed.")


# THIS IF STATEMENT IS IMPORTANT FOR USING THE LISTEN FUNCTIONALITY OF THIS LIBRARY
if __name__ == "__main__":
    client.run("token")
