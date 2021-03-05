"""Uses a messages to add and remove roles through reactions."""

import discord

class RoleReactClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.role_message_id = 0  # ID of message that can be reacted to to add role
        self.emoji_to_role = {
            '🔴': 0,  # ID of the role associated with unicode emoji '🔴'
            '🟡': 0,  # ID of the role associated with unicode emoji '🟡'
            0: 0, # ID of the role associated with a partial emoji's id.
        }

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gives a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
            return

        try:
            # If it is a unicode emoji, it should use .name, otherwise it should use .id.
            emoji = payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji.id
            role_id = self.emoji_to_role[emoji]
        except KeyError:
            # If the emoji isn't the one we care about then exit as well.
            return

        role = guild.get_role(role_id)
        if role is None:
            # Make sure the role still exists and is valid.
            return

        try:
            # Finally add the role
            await payload.member.add_roles(role)
        except discord.HTTPException:
            # If we want to do something in case of errors we'd do it here.
            pass

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Removes a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
            return

        try:
            # If it is a unicode emoji, it should use the name, otherwise it should use the ID.
            emoji = payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji.id
            role_id = self.emoji_to_role[emoji]
        except KeyError:
            # If the emoji isn't the one we care about then exit as well.
            return

        role = guild.get_role(role_id)
        if role is None:
            # Make sure the role still exists and is valid.
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            # Makes sure the member still exists and is valid
            return

        try:
            # Finally, remove the role
            await member.remove_roles(role)
        except discord.HTTPException:
            # If we want to do something in case of errors we'd do it here.
            pass

# This bot requires the members and reactions intents.
intents = discord.Intents.default()
intents.members = True

client = RoleReactClient(intents=intents)
client.run('token')
