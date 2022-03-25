.. currentmodule:: discord


==========================
Errors and Error Handling
==========================

Handling Errors
===============

When an error ocurrs in a command or an event, it will, by default, show an error in the console to denote that the error 
ocurred and has been silently ignored. In order to avoid this, an error handler is needed.

In :ref:`Commands <discord_ext_commands>`
-----------------------------------------

All errors that are raised by a command derive from :exc:`~.ext.commands.CommandError`. If an error that occurs during a command does
not inherit from :exc:`~.ext.commands.CommandError`, it will automatically get wrapped in a :exc:`~.ext.commands.CommandInvokeError`, 
to retrieve/unwrap this error we need to access it's ``.original`` attribute.

**Example**

.. code-block:: python3

    if isinstance(error, commands.CommandInvokeError):
         error = error.original

Global Error handlers
~~~~~~~~~~~~~~~~~~~~~

You can create global error handlers by creating :func:`.on_command_error` events, which work like any other event in 
the :ref:`discord-api-events`, these are called for every exception that occurs in a command, before invoke hooks, command
converters, etc.

**Example**

.. code-block:: python3
    :emphasize-lines: 1, 2

    @bot.listen()
    async def on_command_error(ctx, error):
        """ This is an example global error handler. """

        # First we unwrap any error that gets wrapped in a CommandInvokeError
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        # Then we continue with our actual logic:

        # We use isinstance() to check which error ocurred:
        if isinstance(error, commansd.CommandNotFound):
            await ctx.send("I couldn't find that command, sorry!")

        elif isinstance(error, commands.NotOwner):
            await ctx.send("This command can only be used by my owner!")

        else:  # Important!
            print(f"Ignoring unhandled exception in command {ctx.command!r}")
            traceback.print_exception(type(error), error, error.__traceback__)
            

.. note::
    We don't want our global error handler to 'eat' our unhandled errors without displaying anything in the console, so we add
    an :ref:`else <py:else>` statement at the end of our logic and handle all the remaining 'unhandled' errors.

Local Error Handlers
~~~~~~~~~~~~~~~~~~~~

In :class:`Cogs <~ext.commands.Cog>`

***************************************

To handle errors in only a single :class:`~ext.commands.Cog` you override it's :meth:`~ext.commands.Cog.cog_command_error` method,
which gets called when an error occurs inside of this Cog.

**Example**

.. code-block:: python3
    :emphasize-lines: 8

    class ExampleCog(commands.Cog):

        async def cog_check(ctx):
            """ Custom check for this cog only. """
            if ctx.guild and ctx.guild.id != GUILD_ID:
                raise commands.DisabledCommand

        async def cog_command_error(self, ctx, error):
            """ This error handler is only for this specific Cog. """

            if isinstance(error, commands.DisabledCommand):
                await ctx.send(f"The command {ctx.command!r} cannot be used in this server!")
      
In a :class:`~.ext.commands.Command`

************************************


To handle errors for a specific command, we decorate the function with :meth:`~ext.commands.Command.error`, which will 
only get called for that specific command.

You can use the same function for multiple commands too, simply by adding multiple decorators on top of it.

**Example**

.. code-block:: python3
    :emphasize-lines: 17, 18

    @bot.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(ctx, member: discord.Member):
        """ Kicks a member from this server. """
        await member.kick()
        await ctx.send(f"Kicked {member}! Bye bye.")

    @bot.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(ctx, member: discord.User):
        """ Bans a member from this server. """
        await ctx.guild.ban(user)
        await ctx.send(f"Banned {member}! Begone.")

    @kick.error
    @ban.error
    async def kick_error(ctx, error):
        """ This error handler is only for the `kick` and `ban` commands """

        if isinstance(error, commands.MissingPermissions):
            formatted_perms = ', '.join(error.missing_perms)
            await ctx.send(f'You are missing the following permissions: {perms}')

        elif isinstance(error, commands.BotMissingPermissions):
            formatted_perms = ', '.join(error.missing_perms)
            await ctx.send(f'I am missing the following permissions: {perms}')


.. warning::
    After the local error handlers get called, the global error handler gets called too. If you're handling unhandled errors 
    in it, do not handle them in local error handlers, as this may cause them to be handled twice or more.

Using Global and Local Error Handlers Together
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some times, you may want or need to use local and global error handlers, in these cases, there are multiple ways of checking if 
the error has already been handled before. There are many approaches on how to do this:

- Using the :meth:`Cog.has_error_handler <discord.ext.commands.Cog.has_error_handler>`
  and :meth:`Command.has_error_handler <discord.ext.commands.Command.has_error_handler>`
  methods in your global error handler.

**Example**

.. code-block:: python3

    @bot.listen()
    async def on_command_error(ctx, error):
        """ Global error handler that ignores local error handlers. """

        if ctx.cog and ctx.cog.has_error_handler():
            # If the cog has an error handler, we return,
            # ignoring the error.
            return
        
        if ctx.command and ctx.command.has_error_handler():
            # We do the same for the command.
            return
        
        # Simpler way to handle CommandInvokeError using getattr
        error = getattr(error, 'original', error)

        # Then we continue with our error handling as normal...
        print(f"Ignoring unhandled exception in command {ctx.command!r}")
        traceback.print_exception(type(error), error, error.__traceback__)

- Attaching flags to the :class:`Context <~.ext.commands.Context>` to denote the error has been handled.

**Example**

*1. In the local error handler, we attach an attribute to our Context:*

.. code-block:: python3

    @ban.error
    async def ban_error(ctx, error):
        """ Handles only the MissingRequiredArgument error. """

        if isinstance(error, commands.MissingRequiredArgument):
            # We set an attribute to the context that will then
            # be detected in the global error handler.
            ctx.ignore_error = True

            # Then we do the rest
            await ctx.send(f'Please mention the person to ban using `{ctx.clean_prefix}ban @member`')

*2. Then, in our error handler, we use ``getattr()`` to check for the custom attribute we just set:*

..
    Note, I couldn't get to reference getattr() to the python docs... >_<

.. code-block:: python3

    @bot.listen('on_command_error')
    async def global_error_handler(ctx, error):
        """ Global error handler that handles errors that aren't maked as ignored"""

        # Check if `ctx.ignore_error` is True
        if getattr(ctx, 'ignore_error', False) is True:
            return  # we ignore the error

        # Simpler way to handle CommandInvokeError using getattr
        error = getattr(error, 'original', error)

        # Then we continue with our error handling as normal...
        print(f"Ignoring unhandled exception in command {ctx.command!r}")
        traceback.print_exception(type(error), error, error.__traceback__)

In :ref:`Events <discord-api-events>`
-------------------------------------

If an error ocurrs in an event, it does not go to any command error handler, as it is not a command. These errors are instead
propagated to :meth:`~Client.on_error`, and can be retrieved with a standard call to :func:`sys.exc_info`. 

**Example**

.. code-block:: python3

    import sys
    import traceback

    @client.event
    async def on_error(event, *args, **kwargs):
        """ Handles errors in events. """

        # Firs we get the information of the error:
        err_type, err_value, err_traceback = sys.exc_info()

        # Then we can use it to generate a traceback text:
        err_lines = traceback.format_exception(err_type, err_value, err_traceback)
        err_text = ''.join(err_lines)

        # Then we can do whatever with these, for example, printing them to console,
        # or even sending them to some log channel to keep track of them!
        print(f"Ignoring unhandled exception in event {event!r}\n{err_text}")

.. note::

    ``on_error`` will only be dispatched to :meth:`Client.event`.

    It will not be received by :meth:`Client.wait_for`, or, if used, :ref:`ext_commands_api_bot` listeners such as
    :meth:`~ext.commands.Bot.listen` or :meth:`~ext.commands.Cog.listener`.

In :ref:`Interactions <interactions_api>`
-----------------------------------------

In :ref:`Views <discord_ui_kit>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handling errors in a :class:`~.ui.View` is as simple as overriding it's :meth:`~.ui.View.on_error`.

**Example**

.. code-block:: python3

    class ErrorHandledView(discord.ui.View):

        async def on_error(self, error, item, interaction):
            """ Handles errors for this view. """
            ...

In :ref:`Application Commands <discord_app_commands>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To handle errors in a :class:`~.app_commands.CommandTree` there's two ways of doing so:
  - Subclassing :class:`~.app_commands.CommandTree` and overriding :meth:`~.app_commands.CommandTree.on_error`.
  - Decorating a function with :meth:`~.app_commands.CommandTree.error`, which is the recommended way.

All errors that are raised by an application command derive from :exc:`~.app_commands.CommandError`. If an error that occurs during a 
command does not inherit from :exc:`~.ext.commands.CommandError`, it will get wrapped in a :exc:`~.app_commands.CommandInvokeError`, 
to retrieve/unwrap this error we need to access it's ``.original`` attribute.

**Example**

.. code-block:: python3

    from discord import app_commands

    client = discord.Client()
    tree = app_commands.CommandTree(client)

    @tree.error
    async def tree_error_handler(interaction, command, error):
        """ Handles errors for all application commands
            associated with this CommandTree.
        """

        # We unpack all CommandInvokeErrors first.
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        # Then we continue with our actual logic:

        needs_syncing = (
            app_commands.CommandSignatureMismatch, 
            app_commands.CommandNotFound,
        )

        if isinstance(error, needs_syncing):
            await interaction.response.send_message(
                "Sorry, but this command seems to be unavailable! "
                "Please try again later...", ephemeral=True)
            await tree.sync()
        
        else:  # important!
            print(f"Ignoring unhandled exception in application command {command!r}")
            traceback.print_exception(type(error), error, error.__traceback__)

.. note::
    We don't want our error handler to 'eat' our unhandled application command errors without displaying anything in the console, 
    so we add an :ref:`else <py:else>` statement at the end of our logic and handle all the remaining 'unhandled' errors.

.. warning::
    :ref:`ext_commands_api_bot` already have a :attr:`Bot.tre <~ext.commands.Bot.tree>` associated with it, attempting to create a 
    new one will cause a :class:`~.ClientException` to be raised denoting that there is already a tree associated with that client.

In :ref:`Tasks <discord_ext_tasks>`
----------------------------------------------------

If an error occurs in a :meth:`~ext.tasks.loop` it will, by default, print the error to console and stop the task from running. 
If you'd like to overwrite this behaviour, you can add an error handler that calls :meth:`~ext.tasks.Loop.restart` on the loop on 
top of printing the error, or sending it to a channel or whatever you may want.

**Example**

.. code-block:: python3
    :emphasize-lines: 9
    
    import traceback
    from discord.ext import tasks

    @tasks.loop(hours=1)
    async def hourly_message():
        """ Sends a message to a channel every hour """

        channel = bot.get_channel(336642776609456130)
        await channel.send('Hello from discord.py!')

    @hourly_message.error
    async def hourly_message_error(error):
        """ Handles errors for my hourly task """

        # We print the error, and then restart the task
        print(f"An error ocurred in hourly_task during run number {hourly_message.current_loop}")
        traceback.print_exc()
        hourly_messages.restart()

Creating Custom Errors
======================

Working on it.