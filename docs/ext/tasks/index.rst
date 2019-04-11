``discord.ext.tasks`` -- asyncio.Task helpers
====================================================

.. versionadded:: 1.1.0

One of the most common operations when making a bot is having a loop run in the background at a specified interval. This pattern is very common but has a lot of things you need to look out for:

- How do I handle :exc:`asyncio.CancelledError`?
- What do I do if the internet goes out?
- What is the maximum number of seconds I can sleep anyway?

The goal of this discord.py extension is to abstract all these worries away from you.

Recipes
---------

A simple background task in a :class:`~discord.ext.commands.Cog`:

.. code-block:: python3

    from discord.ext import tasks, commands

    class MyCog(commands.Cog):
        def __init__(self):
            self.index = 0
            self.printer.start()

        def cog_unload(self):
            self.printer.cancel()

        @tasks.loop(seconds=5.0)
        async def printer(self):
            print(self.index)
            self.index += 1

Adding an exception to handle during reconnect:

.. code-block:: python3

    import asyncpg
    from discord.ext import tasks, commands

    class MyCog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
            self.data = []
            self.batch_update.add_exception_type(asyncpg.PostgresConnectionError)
            self.batch_update.start()

        def cog_unload(self):
            self.batch_update.cancel()

        @tasks.loop(minutes=5.0)
        async def batch_update(self):
            async with self.bot.pool.acquire() as con:
                # batch update here...
                pass

Looping a certain amount of times before exiting:

.. code-block:: python3

    from discord.ext import tasks

    @tasks.loop(seconds=5.0, count=5)
    async def slow_count():
        print(slow_count.current_loop)

    slow_count.start()

Doing something after a task finishes is as simple as using :meth:`asyncio.Task.add_done_callback`:

.. code-block:: python3

    afterwards = lambda f: print('done!')
    slow_count.get_task().add_done_callback(afterwards)

API Reference
---------------

.. autoclass:: discord.ext.tasks.Loop()
    :members:

.. autofunction:: discord.ext.tasks.loop
