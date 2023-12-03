.. currentmodule:: discord

.. _guide_sharding:

Sharding
==========

When bots start to get considerably large, the amount of events they have to deal with can start to become problematic. At high user and guild counts, the number of incoming messages, typing events, and status updates can start to become as high as hundreds per second.

To help deal with this large amount of traffic, Discord supports **sharding**, a feature where your bot can split its guilds amongst separate connections, reducing the amount of data each connection has to handle.

This not only helps Discord by reducing how much data they need to direct to one place, but also helps us, as we can split our bot's work across different connections, environments, or even entirely different machines. 

Discord recommends sharding when your application reaches 1,000 guilds. Once your application reach 2,500 guilds, sharding is required.

Let's discuss our options for setting up sharding with discord.py.

Client vs AutoShardedClient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both :class:`~Client` and :class:`~ext.commands.Bot` have auto sharded variants, :class:`~AutoShardedClient` and :class:`~ext.commands.AutoShardedBot` respectively.

The key difference between the two is that the former can only support one connection (one shard), while the auto sharded variants can handle multiple gateway connections.

There's 2 ways you can do sharding:

Using auto sharding
~~~~~~~~~~~~~~~~~~~~~

If you want to use a single process and the recommended number of shards by Discord, you can simply use :class:`~AutoShardedClient` or :class:`~ext.commands.AutoShardedBot` instead of :class:`~Client` or :class:`~ext.commands.Bot` respectively.

Specifying shard count and IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may want to specify a total shard count instead of relying on Discord's recommendation if you find you need more or less shards, or if you want to keep it consistent across restarts of your bot.

.. note::

    When nearing 150,000 guilds, Discord will migrate your bot to [large bot sharding](https://discord.com/developers/docs/topics/gateway#sharding-for-large-bots). More details are available on their documentation page.

.. warning::

    When specifying a shard count, note that each shard must have less than 2,500 guilds.

Specifying shard IDs is useful for bots running as multiple processes. For example, if a bot has 16 shards, you may have one process run shards 0-7 and another process run shards 8-15. These values can be specified with, for example, an environment variable, to allow passing different values to each process.

.. note::

    If you specify shard IDs, you must also specify a shard count. This does not do the same effect vice versa.

.. warning::

    Don't forget that indexing in Python starts at 0, and that shard_id 0 is a valid thing.

Examples
~~~~~~~~~~

Let's make a bot using :class:`~ext.commands.AutoShardedBot`:

.. code-block:: python3

    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.AutoShardedBot(command_prefix='!', intents=intents)

    @bot.command()
    async def shards(ctx):
        await ctx.send(f"I am running on {bot.shard_count} shards!")
    
    bot.run("token")

If you don't want to use discord's recommended shard count, you can specify your own:

.. code-block:: python3

    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.AutoShardedBot(command_prefix='!', shard_count=10, intents=intents)

    @bot.command()
    async def shards(ctx):
        await ctx.send(f"I am running on {bot.shard_count} shards!")
    
    bot.run("token")

.. note::
    
    You can specify the shard_count in AutoShardedBot, but it makes more sense to use :class:`~ext.commands.Bot` for this.
