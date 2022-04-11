.. currentmodule:: discord

.. _guide_webhooks:

Webhooks
========

Webhooks are used for posting messages in Discord text channels without relying on a bot user.

The focus of this section is to provide a basic understanding of webhooks and
working with them using discord.py.

For detailed information about webhooks, See the documentation for :ref:`webhooks <discord-api-webhooks>`.

Introduction to webhooks
~~~~~~~~~~~~~~~~~~~~~~~~

The difference between sending messages with webhooks and bots is that bots require proper authentication and a bot user
whereas webhooks don't need either.

There are currently three types of webhooks:

1. Incoming webhooks
2. Channel follower webhooks
3. Application webhooks

**Incoming webhooks** are associated to a channel and can post messages in that channel
using a webhook token.

**Channel follower webhooks** are used for crossposting of messages in news channels
by Discord. This type does not have any token associated to it and bots cannot post
messages through these webhooks.

**Application webhooks** are used for creating interaction responses. The management of
this type of webhooks are handled internally by the library and is not in scope of this guide.

This guide will primarily focus on the first type, incoming webhooks.

Creating a webhook
~~~~~~~~~~~~~~~~~~

In order to create incoming webhooks in a channel, the member needs the
:attr:`~Permissions.manage_webhooks` permission in the given guild or text channel.

To create a webhook in a server, Navigate to "Server Settings > Integrations" page. Alternatively, webhooks
can also be created from the "Integrations" page in a channel's settings.

.. image:: /images/guide/webhooks/guild_settings_integrations.png
    :alt: Integrations Settings

Click "Create Webhook" to create a webhook.

.. image:: /images/guide/webhooks/webhook_created.png
    :alt: Webhook

From here, you can edit the webhook's name and the associated channel the webhook
will send messages in. We'll be using the URL of webhook later in this guide so make
sure to copy it too.

The URL of webhook is used for executing the webhook and includes the webhook token
so don't store it in a public place.

You can also create webhooks through API using the :meth:`TextChannel.create_webhook` method.

Initializing webhooks
~~~~~~~~~~~~~~~~~~~~~

We'll now be initializing a webhook instance in our code.

There are two variants of webhooks provided by the library.

- :class:`Webhook`
- :class:`SyncWebhook`

The :class:`Webhook` is suitable for most cases as it is asynchronous while
:class:`SyncWebhook` is synchronous and is suitable for blocking environments. Both have the same
functionality with the difference of being sync and async. The HTTP methods usually return
the :class:`Webhook` class instance.

Webhooks are retrieved in two ways. They can be obtained through the :meth:`Guild.webhooks`
or :meth:`TextChannel.webhooks` methods. These methods requires authentication via a bot user.

The other method is to initialize "partial" webhooks using only webhook ID and token. This
method does not require authentication via bot user.

To create a partial webhook we would be using the URL that we copied earlier, passing it
in the :meth:`~Webhook.from_url` method.

.. code-block:: py

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url("webhook-url-here", session=session)

The webhooks retrieved through HTTP methods are automatically bound to library's
internal HTTP session. However in order to initialize partial webhooks, We must
create our own HTTP session and pass it through the ``session`` parameter.

It is worth noting that for asynchronous :class:`Webhook`, The ``session`` parameter
takes in a :class:`aiohttp.ClientSession` instance. However for synchronous variant, The
``session`` parameter takes the :class:`requests.Session` instance.

:meth:`~Webhook.from_url` is a helper that automatically extracts webhook ID and token
from the given URL. We also have :meth:`Webhook.partial` method to initialize partial
webhooks directly using the ID and token.

.. code-block:: py

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.partial(webhook_id, webhook_token, session=session)

Fetching webhooks
~~~~~~~~~~~~~~~~~

Partial webhooks only contain the webhook ID and token as these are the only required
components to perform basic requests. However if you want to retrieve complete webhook
information, you can fetch them. Use the :meth:`Webhook.fetch` method to do so.

.. code-block:: py

    partial_webhook = discord.Webhook.from_url("url-here", session=session)
    print(partial_webhook.is_partial()) # True
    webhook = await partial_webhook.fetch()
    print(webhook.is_partial()) # False

When you have a :meth:`Client` instance available, you can use it's :meth:`~Client.fetch_webhook` method to
fetch the webhook using the ID. It is worth noting that this method does not require you to create a separate 
HTTP session. The library's internal session is automatically bound to the webhook and is managed by the library.

Fetched webhook will include the complete webhook information like username, avatar etc. Fetching the webhook isn't
necessary when you just want to perform simple HTTP operations such as sending messages, editing or deleting them.
Only fetch the webhook when you need this information, avoid making unnecessary API calls.

Sending messages
~~~~~~~~~~~~~~~~

This is where the fun begins, Let's start posting messages through our webhook.
We use the :meth:`Webhook.send` method to send the messages.

.. code-block:: py

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url("webhook-url", session=session)
        await webhook.send("Hello World")

This will produce the following output in Discord:

.. image:: /images/guide/webhooks/webhook_message.png
    :alt: Webhook message

Like normal messages, Webhooks support embeds, file attachments, allowed mentions and
other message features. An example of sending embeds is given below.

.. code-block:: py

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url("webhook-url", session=session)
        embed = discord.Embed(title="Hello World", description="I'm a nice embed!")
        await webhook.send(embed=embed)

.. image:: /images/guide/webhooks/webhook_message_with_embed.png
    :alt: Webhook message with embed.

There are some features that are exclusive to webhook messages like hyperlinks in
raw message's content.

Webhooks also allow you to set different avatar and username on each message. This
is done using by passing in ``avatar_url`` and ``username`` parameters in the
:meth:`~Webhook.send` method.

.. code-block:: py

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url("webhook-url", session=session)
        await webhook.send(
            "Hello world",
            username="A different username",
            avatar_url="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f914.png"
        )

The message created will have it's author with specified username and avatar set.

.. image:: /images/guide/webhooks/webhook_message_with_username_avatar.png
    :alt: Webhook message with specified avatar and username

Managing messages
~~~~~~~~~~~~~~~~~

Incoming webhooks can also fetch, edit and delete the messages sent by that webhook.

It is worth noting that a webhook can only fetch messages that are sent by it and
cannot fetch messages from other users or webhooks.

To fetch the message, we use the :meth:`Webhook.fetch_message` method.

Webhook messages are represented by the :class:`WebhookMessage` class. This class inherits
:class:`Message` and has similar functionality with changes to :meth:`~WebhookMessage.delete`
and :meth:`~WebhookMessage.edit` methods.

Example of fetching, editing and deleting webhook messages is given below.

.. code-block:: py

    message = await webhook.fetch_message(12345679) # Replace the message ID here.
    await message.edit(content="Deleting in 5 seconds...")
    await asyncio.sleep(5)
    await message.delete()

.. image:: /images/guide/webhooks/webhook_message_management.gif

Sometimes you don't want to make an extra API call for fetching the messages. If
you have the message ID you can directly edit or delete them using :meth:`Webhook.edit_message`
and :meth:`Webhook.delete_message` methods. This way, you can avoid unnecessary API calls.

.. code-block:: py

    await webhook.edit_message(12345679, content="Deleting in 5 seconds...")
    await asyncio.sleep(5)
    await webhook.delete_message(12345679)

Next Steps
~~~~~~~~~~

Webhooks can come in handy in various use cases. Every aspect of webhooks cannot be covered 
in this short guide. To discover more features, Read the API reference for :ref:`webhooks <discord-api-webhooks>`.
