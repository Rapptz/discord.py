"""Uses two messages to add and remove roles through reactions."""

import discord
from discord.ext import commands

# This bot requires the members and reactions intensions.
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

role_message_id = 0  # ID of message that can be reacted to to add role
emoji_to_role = {
    "👍": 0,  # ID of role associated with thumbs up emoji
    "test": 0  # ID of role associated with custom emoji 'test'
}

@bot.event
async def on_raw_reaction_add(payload):
    """Gives a role based on a reaction emoji."""
    if payload.guild_id:
        if payload.emoji.name in emoji_to_role:
            if payload.message_id == role_message_id:
                guild = bot.get_guild(payload.guild_id)
                role = guild.get_role(emoji_to_role[payload.emoji.name])
                await payload.member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    """Removes a role based on a reaction emoji."""
    if payload.guild_id:
        if payload.emoji.name in emoji_to_role:
            if payload.message_id == role_message_id:
                guild = bot.get_guild(payload.guild_id)
                role = guild.get_role(emoji_to_role[payload.emoji.name])
                member = guild.get_member(payload.user_id)
                await member.remove_roles(role)

bot.run("token")
