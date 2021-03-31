.. _quickstart:

.. currentmodule:: discord

Quickstart
============

This page gives a brief introduction to the library. It assumes you have the library installed,
if you don't check the :ref:`installing` portion.

A Minimal Bot
---------------

Let's make a bot that responds to a specific message and walk you through it.

It looks something like this:

.. code-block:: python3

    import discord

    client = discord.Client()

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

    client.run('your token here')

Let's name this file ``example_bot.py``. Make sure not to name it ``discord.py`` as that'll conflict
with the library.

There's a lot going on here, so let's walk you through it step by step.

1. The first line just imports the library, if this raises a `ModuleNotFoundError` or `ImportError`
   then head on over to :ref:`installing` section to properly install.
2. Next, we create an instance of a :class:`Client`. This client is our connection to Discord.
3. We then use the :meth:`Client.event` decorator to register an event. This library has many events.
   Since this library is asynchronous, we do things in a "callback" style manner.

   A callback is essentially a function that is called when something happens. In our case,
   the :func:`on_ready` event is called when the bot has finished logging in and setting things
   up and the :func:`on_message` event is called when the bot has received a message.
4. Since the :func:`on_message` event triggers for *every* message received, we have to make
   sure that we ignore messages from ourselves. We do this by checking if the :attr:`Message.author`
   is the same as the :attr:`Client.user`.
5. Afterwards, we check if the :class:`Message.content` starts with ``'$hello'``. If it is,
   then we send a message in the channel it was used in with ``'Hello!'``.
6. Finally, we run the bot with our login token. If you need help getting your token or creating a bot,
   look in the :ref:`discord-intro` section.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 example_bot.py

On other systems:

.. code-block:: shell

    $ python3 example_bot.py

Now you can try playing around with your basic bot.

A Command Bot
---------------

Let's make a bot that supports command-driven functions and walk you through it.


Pros
 * Easier to configure command-driven commands.
 * Self-documenting.
Cons
 * Bulky for light bot applications.

command_bot.py
"""""""""""""""
.. code-block:: python3

    import discord
    from discord.ext.commands import Bot, Context

    # This is the symbol that tells the bot a message is a command.
    PREFIX = '$'

    bot = Bot(
        command_prefix=PREFIX,
        # For info about intents: https://discordpy.readthedocs.io/en/stable/intents.html
        intents=discord.Intents.default(),
        # This makes the commands `$hello` and `$Hello` act as the same command.
        case_insensitive=True
        )

    @bot.event
    async def on_ready():
        print('Bot logged in as: {0.user}'.format(bot))

    @bot.command(name='hello', aliases=['hi'])
    async def hello(ctx: Context):
        '''Replies Hello.'''
        await ctx.reply('Hello {0.user}!'.format(ctx))

    if __name__ == '__main__':
        # Run the bot.
        bot.run('your token here')

Let's name this file ``command_bot.py``. Make sure not to name it ``discord.py`` as that'll conflict
with the library.

There's a lot going on here, so let's walk you through it step by step.


1. The first lines just import the library, if this raises a `ModuleNotFoundError` or `ImportError`
   then head on over to :ref:`installing` section to properly install.

2. Next, we give the program the prefix we want our commands to begin with.

3. Then, we create an instance of a :class:`Bot`. This bot is our connection to Discord.

4. This bot structure uses the bot extension of discord.py.

5. We use the :meth:`bot.event` decorator to register an event and :meth:`bot.command` for commands.
   Since this library is asynchronous, we do things in a "callback" style manner.

6. A callback is essentially a function that is called when something happens. In our case,
   the :func:`on_ready` event is called when the bot has finished logging in and setting things
   up and the `hello` command is called when the bot has received a command.

7. The docstrings of each command function give descriptions in the help command. This is extremely
   helpful in making your bot more user-friendly.

8. Finally, we run the bot with our login token. If you need help getting your token or creating a bot,
   look in the :ref:`discord-intro` section.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 example_bot.py

On other systems:

.. code-block:: shell

    $ python3 example_bot.py

Now you can try playing around with your basic bot.

Go ahead and type ``$hello`` in a channel you and your bot are in.
