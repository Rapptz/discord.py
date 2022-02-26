:orphan:

.. currentmodule:: discord

.. _guide_quickstart:

Quickstart
===========

This page will contain a simple explanation of how to make a basic bot using the commands extension "ext.commands".
Before you begin, make sure to install discord.py - see :ref:`guide_intro_installation` for more information.

Obtaining a Bot Token
----------------------

You will need a bot application before being able to run a bot. A step-by-step tutorial with screenshots follows:

1. Go to the `Discord Developer Portal <https://discord.com/developers/applications/>`_.
2. Create a new application if you have not made one already:
    .. image:: /images/discord_create_app_button.png
        :scale: 90 %
    
    Be sure to give it a good name!
3. Navigate over to the ``bot`` tab:
    .. image:: /images/discord_bot_tab.png
        :scale: 80 %
4. Create a new Bot user if you have not done so already:
    .. image:: /images/discord_create_bot_user.png
        :scale: 80 %
5. If you need these intents, scroll down and click on these check boxes:
    .. image:: /images/discord_privileged_intents.png
        :scale: 80%
6. Copy your bot token here:
    .. image:: /images/discord_bot_token.png
        :scale: 100%
    
.. warning::

    This token is **VERY IMPORTANT** and you should treat it like the password to your bot. Keep it as secure as possible and never give this to anyone.
    If you ever leak it, you can click the ``Regenerate`` button to forcibly invalidate all copies of the token. This will also terminate all running instances of this bot.

.. warning::

    You may be thinking to use the ``Client Secret`` for your bot token. This is **NOT** what you are looking for, you need the bot **Token**, which is a completely different format.

    .. image:: /images/discord_client_secret_big_nono.png
        :scale: 90 %

A Simple Bot
-------------

This step-by-step walkthrough will show you how to make a bot using the commands framework.

1. Create a new Python file in the folder you want to work in.

    .. warning::

        Do not name the file ``discord.py``, this will cause conflicts with the discord.py library.
    
2. Open the new Python file in your preferred editor.

    If you do not have an editor installed, you can use a community recommended one, such as `Visual Studio Code <https://code.visualstudio.com/>`_,
    `PyCharm <https://www.jetbrains.com/pycharm/>`_ or `Sublime Text 4 <https://www.sublimetext.com/>`_.

    .. note::

        Due to the lack of features with Python's built in IDLE, it is not recommended to be used as your bot's editor.

3. Now you can start creating your bot. The following steps will go over a simple bot line-by-line to help you understand what's happening.

First, you need to import the discord.py library:

.. code-block:: python

    import discord
    from discord.ext import commands

We import ``discord.ext.commands`` here as we will need it for our bot.

.. code-block:: python

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", description="This is my awesome bot!", intents=intents)

This is your bot instance. You can name it whatever you like but for simplicity's sake we will keep it as is.
You will need to specify a ``command_prefix`` here, we use ``!``, but you can use any string, or a list of strings for multiple prefixes.

.. note::

    ``Intents`` are a way to specify which gateway events you wish to receive. ``Intents.default()`` means you will receive all events that are not locked behind bot verification.
    For more information, see :ref:`intents_primer`.

.. code-block:: python

    @bot.listen()
    async def on_ready():
        print("Ready! I am", bot.user, "and my ID is", bot.user.id)

This is the ``ready`` event. It is called when the bot has finished loading and everything is cached.
We use the :meth:`@bot.listen() <ext.commands.Bot.listen>` decorator as to not override the main event.
For a list of available events, see :ref:`discord-api-events`.

.. warning::

    Using :meth:`@bot.event <ext.commands.Bot.event>` is also valid, but keep in mind that using :meth:`@bot.event <ext.commands.Bot.event>` with the ``on_message`` event can cause your commands to stop responding.
    To remedy this, either switch to :meth:`@bot.listen() <ext.commands.Bot.listen>`, or add :meth:`~ext.commands.Bot.process_commands` to your ``on_message`` event.

.. warning::

    ``on_ready`` can and will be called multiple times throughout your bots uptime. Avoid running expensive API calls such as changing your bot's presence, sending messages etc. in this event.

.. code-block:: python

    @bot.command()
    async def echo(ctx: commands.Context, *, sentence: commands.clean_content):
        await ctx.send(sentence)

Here's where our commands will be defined. We use the :meth:`@bot.command() <ext.commands.Bot.command>` decorator to flag this function as a command.
This creates a command ``!echo`` that we can type into a channel, and the bot will respond with the given sentence. A few key features:

- :class:`~ext.commands.Context` refers to the command invocation context - this includes the :attr:`~ext.commands.Context.channel`, command :attr:`~ext.commands.Context.author`, :attr:`~ext.commands.Context.message` and more.
- The ``*`` is a sign to tell discord.py that the following parameter should **consume all text afterward** and condense it into that parameter.
    .. note::
    
        As this consumes all text, parameters defined **after the next** will never be filled, so you should never have more than one parameter after the ``*``.

- :meth:`~ext.commands.clean_content` is a :ref:`Converter <ext_commands_api_converters>` used to clean user pings and ``@everyone`` mentions. This way people will not be able to ping everyone by using your bot. For more information, see :ref:`ext_commands_commands_converters`.

.. code-block:: python

    TOKEN = "your bot token here"
    bot.run(TOKEN)

This is the final step, you put your bot token here and run the script. Your bot should now be live!

.. note::

    :meth:`~ext.commands.Bot.run` is blocking, so any code after it will **not be run**. 

.. warning::

    As this is an example, token security is not applied here. However, you should be very careful with your bot token. Keep it in a secure place and only access it when you are starting the bot.