.. currentmodule:: discord

.. _guide_sharding

Sharding
==========

For bots in a large number of guilds, sharding may be required. Sharding is where a subset of the bot's total guilds are processed in each gateway connection. This allows a bot to handle more events, by splitting them by connection and possibly process. Sharding is generally not recommended for bots in less than 1,000 guilds and is required by Discord when a bot is in over 2,500 guilds.

Client vs AutoShardedClient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both :class:`~Client` and :class:`~ext.commands.AutoShardedClient` have auto sharded variants, :class:`~AutoShardedClient` and :class:`~ext.commands.AutoShardedBot` respectively.

The key difference between the two is that the former can only support one connection (one shard), while the auto sharded variants can handle multiple gateway connections. If you are running multiple shards, it is recommended to use the auto sharded variants and have multiple connections in each process.

Using auto sharding
~~~~~~~~~~~~~~~~~~~~~

If you want to use a single process and the recommended number of shards by Discord, you can simply use :class:`~AutoShardedClient` or :class:`~ext.commands.AutoShardedBot` instead of :class:`~Client` or :class:`~ext.commands.Bot` respectively.

Specifying shard count and IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may want to specify a total shard count instead of relying on Discord's recommendation if you find you need more or less shards, or if you want to keep it consistent across restarts of your bot.

.. warning::

    When specifying a shard count, note that each shard must have less than 2,500 guilds.

Specifying shard IDs is useful for bots running as multiple processes. For example, if a bot has 16 shards, you may have one process run shards 0-7 and another process run shards 8-15. These values can be specified with for example an environment variable to keep allow passing different values to each process. If you specify shard IDs, you must also specify a shard count.
