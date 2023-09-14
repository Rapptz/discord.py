.. currentmodule:: discord

.. _guide_sharding:

Sharding
==========

When bots start to get considerably large, the amount of events they have to deal with can start to become problematic.

At high user and guild counts the incoming messages, typing events, and status updates can start to climb to being as frequent as hundreds per second.

To help deal with this large amount of traffic, Discord supports **sharding**, a feature where your bot can split its guilds amongst separate connections, reducing the amount of data each individual connection has to handle.

This not only helps Discord by reducing how much data they need to direct to one place, but also helps us, as we can split our bot's overall work across different connections, environments, or even entirely different machines. 

Discord recommends using sharding once you get over 1,000 guilds, and once you reach beyond 2,500 guilds, it becomes a requirement.

Now, let's discuss what options we have for setting up sharding within discord.py.

Client vs AutoShardedClient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both :class:`~Client` and :class:`~ext.commands.Bot` have auto sharded variants, :class:`~AutoShardedClient` and :class:`~ext.commands.AutoShardedBot` respectively.

The key difference between the two is that the former can only support one connection (one shard), while the auto sharded variants can handle multiple gateway connections. If you are running multiple shards, it is recommended to use the auto sharded variants and have multiple connections in each process.

There's 2 ways you can do sharding:

Using auto sharding
~~~~~~~~~~~~~~~~~~~~~

If you want to use a single process and the recommended number of shards by Discord, you can simply use :class:`~AutoShardedClient` or :class:`~ext.commands.AutoShardedBot` instead of :class:`~Client` or :class:`~ext.commands.Bot` respectively.

Specifying shard count and IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may want to specify a total shard count instead of relying on Discord's recommendation if you find you need more or less shards, or if you want to keep it consistent across restarts of your bot.

.. warning::

    When specifying a shard count, note that each shard must have less than 2,500 guilds.

Specifying shard IDs is useful for bots running as multiple processes. For example, if a bot has 16 shards, you may have one process run shards 0-7 and another process run shards 8-15. These values can be specified with, for example, an environment variable, to allow passing different values to each process. If you specify shard IDs, you must also specify a shard count.

.. note::

    This does not have the same effect vice versa.

Examples
~~~~~~~~~~

Let's make a bot using :class:`~ext.commands.AutoShardedBot`:

.. code-block:: python3

    import discord
    from discord.ext import commands

    bot = commands.AutoShardedBot(command_prefix='!')

    @bot.command()
    async def shards(ctx):
        await ctx.send(f"I am running on {bot.shard_count} shards!")
    
    bot.run("token")

.. note::
    
    You can specify the shard_count in AutoShardedBot, but that defeats the whole purpose of :class:`~AutoShardedBot` and you should just use :class:`~Bot` instead.

If you don't wanna use discord's recommended shard count, you can specify your own:

.. code-block:: python3

    import discord
    from discord.ext import commands

    bot = commands.Bot(command_prefix='!', shard_count=10)

    @bot.command()
    async def shards(ctx):
        await ctx.send(f"I am running on {bot.shard_count} shards!")
    
    bot.run("token")