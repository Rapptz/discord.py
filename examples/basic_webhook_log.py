import re
import datetime
import traceback

import aiohttp
import discord

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_webhook = None
        self.session = aiohttp.ClientSession(loop=self.loop)
        # we are using a partial webhook for banned word log,
        # partial webhooks can be used only with their id and token
        self._webhook = discord.Webhook.from_url("https://discord.com/api/webhooks/<id>/<token>", session=self.session)
        self._banned_pattern = re.compile(r'\b(list|of|banned|words)\b', re.IGNORECASE)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself or webhook
        if (message.author.id == self.user.id) or (message.webhook_id is not None):
            return

        # look for bad words in messages of a certain guild
        if message.guild and message.guild.id == 12345 and self._banned_pattern.search(message.content):
            embeds = []
            content_embed = discord.Embed(
                description=message.content,
                timestamp=message.created_at,
                colour=message.author.colour,
            )
            content_embed.set_author(name=message.author, icon_url=message.author.avatar.url)
            embeds.append(content_embed)

            # delete message if client has permission, otherwise just log the message
            log_message = ""
            try:
                await message.delete()
            except discord.Forbidden as error:
                # webhook contents support hyperlink
                log_message += (
                    f"[Message]({message.jump_url}) (ID: {message.id}) from"
                    f" {message.channel.mention} contains a banned word."
                )
                error_embed = discord.Embed(
                    title="Couldn't Delete Message",
                    description=error, colour=discord.Colour.red(),
                )
                embeds.append(error_embed)
            else:
                log_message += (
                    f"Deleted message (ID: {message.id}) from" 
                    f" {message.channel.mention} for using a banned word."
                )

            await self._webhook.send(
                log_message,
                # webhooks support sending multiple embeds 
                embeds=embeds,
                # webhooks can set username and avatar per message
                # we want the username and avatar to be of our client's instead of default webhook one
                username=self.user.name,
                avatar_url=self.user.avatar.url,
            )

    async def on_error(self, event_method, *args, **kwargs):
        """Logs unhandled event exceptions to a webhook dedicated to errors."""
        if self._error_webhook is None:
            # we are fetching a "full" webhook this time
            # assuming our client has the permission to access it
            self._error_webhook = await self.fetch_webhook(12345) # your webhook id
        
        embed = discord.Embed(
            title=f"Ignoring Exception in `{event_method}`...",
            description=f"```py\n{traceback.format_exc()}```",
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.utcnow(),
        )
        await self._error_webhook.send(
            # this time we're sending one embed, embed and embeds are mutually exclusive
            embed=embed,
            username=f"{self.user.name} [Error]",
            avatar_url=self.user.avatar.url,
        )

    async def close(self):
        await super().close()
        # override close to also close our session
        await self.session.close()

client = MyClient()
client.run('your client token')