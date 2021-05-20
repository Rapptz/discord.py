import asyncio
import discord

async def async_webhook():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        # webhook url anatomy:
        # https://discord.com/api/webhooks/<id>/<token>

        webhook = discord.Webhook.from_url(
            # To create and get the webhook url:
            # Server Settings > Integration > Webhooks > New Webhook > Copy Webhook Url
            url = "your webhook url here",
            # adapters are what define how your request should be handled
            # here discord.AsyncWebhookAdapter is used since we're using aiohttp
            adapter=discord.AsyncWebhookAdapter(session),
        )
        # Or, webhook can also be created using it's ID and Token:
        webhook = discord.Webhook.partial(
            123, "your webhook token",
            adapter=discord.AsyncWebhookAdapter(session),
        )

        message = await webhook.send(
            # webhook messages can hyperlink even without embeds
            "[Check out the webhook documentation!](https://discordpy.readthedocs.io/en/latest/api.html#webhook-support)",
            embed=discord.Embed(title="Hello", description="World!", colour=discord.Color.blurple()),

            # webhook's username and avatar_url can also be set per message, they use the default one if None
            username="Cool Webhook (async)",
            avatar_url="avatar url of your choice",

            # this waits for the server to confirm the message send before spending a response
            # So, it returns a WebhookMessage object if wait=True otherwise returns None.
            wait=True,
        )

        await asyncio.sleep(2)
        # Edit the WebhookMessage content. Note that this is not possible when wait=False, since it will return NoneType
        await message.edit(
            content="[Checkout WebhookMessage docs!](https://discordpy.readthedocs.io/en/latest/api.html#webhookmessage)",
        )

def sync_webhook():
    import time
    # getting webhook object is same as the async version just pass a sync adapter
    webhook = discord.Webhook.from_url("your webhook url", adapter=discord.RequestsWebhookAdapter())
    # Or, using webhook ID and Token
    webhook = discord.Webhook.partial(123, "your webhook token", adapter=discord.RequestsWebhookAdapter())

    # Same as async version but not a coroutine, so don't await them.
    message = webhook.send(
        "[Check out the webhook documentation!](https://discordpy.readthedocs.io/en/latest/api.html#webhook-support)",
        embed=discord.Embed(title="Hello", description="World!", colour=discord.Color.blurple()),
        username="Cool Webhook (sync)",
        avatar_url="avatar url of your choice",
        wait=True,
    )

    time.sleep(2)
    message.edit(
        content="[Checkout WebhookMessage docs!](https://discordpy.readthedocs.io/en/latest/api.html#webhookmessage)",
    )

# webhook example from a discord client

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._webhook = None

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        if message.content.startswith('!webhook'):
            if self._webhook is None:
                # this is another way to get webhooks. It returns a list of adapter bound webhooks from
                # the guild but we can still create Webhook objects from url or id and token, like shown before
                try:
                    webhooks = await message.guild.webhooks()
                except discord.Forbidden:
                    # we need Manage Webhooks permission to fetch guild webhooks
                    return await message.channel.send("I don't have `Manage Webhooks` permission.")
                if webhooks:
                    self._webhook = webhooks[0]
                else:
                    return await message.channel.send("This server has no webhooks.")

            await self._webhook.send("Hi, I'm a webhook sent from a discord client!")

client = MyClient()
loop = asyncio.get_event_loop()

sync_webhook()
loop.run_until_complete(async_webhook())
client.run('your client token')
