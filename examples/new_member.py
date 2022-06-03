# This example requires the 'members' privileged intent to function.

import discord


class MyClient(discord.Client):
    async def on_ready(self) -> None:
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild.system_channel is not None:
            to_send = f'Welcome {member.mention} to {guild.name}!'
            await guild.system_channel.send(to_send)


intents = discord.Intents.default()
intents.members = True

client = MyClient(intents=intents)
client.run('token')
