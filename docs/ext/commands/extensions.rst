.. currentmodule:: discord

.. _ext_commands_extensions:

Extensions
=============

There may come a time in bot development when you want to extend the bot functionality at run-time and quickly load and unload code (also called hot-reloading). The command framework comes with this functionality built-in, through a concept called **extensions**.

Primer
--------

An extension at its core is a Python file with an entry point called ``setup``. This setup must be a plain Python function (*not* a coroutine). It takes a single parameter -- the :class:`~.commands.Bot` that loads the extension.

An example extension:

.. code-block:: python3
    :caption: hello.py
    :emphasize-lines: 7,8

    from discord.ext import commands

    @commands.command()
    async def hello(ctx):
        await ctx.send('Hello {0.display_name}.'.format(ctx.author))

    def setup(bot):
        bot.add_command(hello)

In this example, a simple command is defined, and when the extension is loaded, this command is added to the bot. Now the final step is loading the extension, by calling 
:meth:`.commands.Bot.load_extension`. To load this extension, call ``bot.load_extension('hello')``.

.. admonition:: Cogs
    :class: helpful

    Extensions are usually used in conjunction with cogs. To read more about them, check out the documentation, :ref:`ext_commands_cogs`.

.. note::

    Extension paths are ultimately similar to the import mechanism. This means dot-qualifying files in folders. For example, to load an extension in ``plugins/hello.py``, use 
the string ``plugins.hello``.

Reloading
-----------

The act of reloading an extension is quite simple -- it is as simple as unloading and reloading:

.. code-block:: python3

    >>> bot.unload_extension('hello')
    >>> bot.load_extension('hello')

Once you remove and load the extension, any changes made to the extension's code will be applied. This is useful if you want to add or remove functionality without restarting your 
bot.

Cleaning Up
-------------

Although rare, sometimes an extension needs to run some clean-up code before unloading. For cases like these, there is another entry point named ``teardown`` which is similar to ``setup``, but called when the extension is *un*loaded.

.. code-block:: python3
    :caption: basic_ext.py

    def setup(bot):
        print('I am being loaded!')

    def teardown(bot):
        print('I am being unloaded!')
