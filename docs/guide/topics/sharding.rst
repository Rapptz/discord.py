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

There are 2 ways you can shard your bot:

Using auto sharding
~~~~~~~~~~~~~~~~~~~~~

If you want to use a single process to run multiple shards under, you can simply use :class:`~AutoShardedClient` or :class:`~ext.commands.AutoShardedBot` instead of :class:`~Client` or :class:`~ext.commands.Bot` respectively. By default, if ``shard_ids`` and ``shard_count`` are not provided, they will use Discord's recommended number of shards.

Specifying shard count and IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may want to specify a total shard count instead of relying on Discord's recommendation to regulate load balancing, if for example, your clusters do not have the computational requirements to handle the recommended number.

.. note::

    The shard count does not restrict the number of potential shards you have as it is only used for routing traffic. In other words, you can have multiple sessions running as shard ``3`` for example, allowing you to orchestrate a "zero-downtime" solution.

.. note::

    When nearing 150,000 guilds, Discord will migrate your bot to `large bot sharding <https://discord.com/developers/docs/topics/gateway#sharding-for-large-bots>`_. More details are available on their documentation page.

.. warning::

    When specifying a shard count, note that each shard must have less than 2,500 guilds.

Specifying shard IDs is useful for bots running as multiple processes. For example, if a bot has 16 shards, you may have one process run shards 0-7 and another process run shards 8-15. These values can be specified with, for example, an environment variable, to allow passing different values to each process. This behaviour can be achieved with ``commands.AutoShardedBot`` and its ``shard_ids`` parameter which accepts a list of values, such as ``list(range(8))``

To calculate which shard receives which events, we can use the following formula ``shard_id = (guild_id >> 22) % num_shards``. For example, this may be used to calculate which cluster to send a payload to along an IPC which connects shards and a web dashboard.

.. note::

    If you specify shard IDs, you must also specify a shard count, however if you choose to run all your bot's shards under one process, you can simply provide a ``shard_count`` and omit the ``shard_ids`` parameter altogether.

.. warning::

    Discord will only dispatch DMs to the first shard, that is the shard with ID ``0``.

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
    
