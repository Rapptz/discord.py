:orphan:

.. currentmodule:: discord

.. _guide_help_command:

Help Command
============

A help command is a command which gives the user help on
how the bot works, what commands are featured, the
usage of the command, etc...

The optimal way to create a help command is to subclass one
of the 3 help command classes discord.py offers: :class:`~ext.commands.HelpCommand`, 
:class:`~ext.commands.DefaultHelpCommand`, and :class:`~ext.commands.MinimalHelpCommand`.

DefaultHelpCommand
------------------

:class:`~ext.commands.DefaultHelpCommand` is the help command class that is given by default.
When you instantiate a :class:`~ext.commands.Bot` instance, discord.py automatically creates 
a help command using this class. Here is what it looks like:

.. image of help command.

The layout of the default help command is essentially the following:


::

    This is my cool bot made in discord.py!                          ]--- Description

    Help:                                                            ]--- Cog Name
      sos     Send Help!                                             ]--- Cog Command
    No Category:                                                     ]--- No Cog
      add     Adds two numbers together.                             \
      choose  Chooses between multiple choices. This will get cut...  |
      cool    Says if a user is cool.                                 |
      help    Shows this message.                                     |--- No Cog Commands
      joined  Says when a member joined.                              |
      repeat  Repeats a message multiple times.                       |
      roll    Rolls a dice in NdN format.                            /

    Type ?help command for more info on a command.                   \___ Ending Note
    You can also type ?help category for more info on a category.    /


This implementation is available for use, however, if we want a more custom and advanced help command,
we will need to subclass as aforementioned. 

MinimalHelpCommand
--------------------

:class:`~ext.commands.MinimalHelpCommand` is another class we can use to create a help command.
It is a subclass of :class:`~ext.commands.HelpCommand` intended to result in minimal output.
To switch to this help command, use the ``help_command`` keyword argument when instantating your :class:`~ext.commands.Bot`
instance. 

.. code-block:: python3

  import discord
  from discord.ext import commands

  bot = commands.Bot(command_prefix='!', help_command=commands.MinimalHelpCommand())
    
  # an alternate way to do this is
  bot.help_command = commands.MinimalHelpCommand()

Creating a Custom Help Command
------------------------------

As previously mentioned, the optimal way of creating a help command is subclassing one of these classes.
In this example, we will subclass :class:`~ext.commands.HelpCommand`, however, it is feasible to subclass
the other two classes as well.

.. code-block:: python3

  import discord
  from discord.ext import commands

  class MyHelp(commands.HelpCommand):

    async def send_bot_help(self, mapping):
      destination = self.get_destination()
      await destination.send('send_bot_help got called')

    async def send_cog_help(self, cog):
      destination = self.get_destination()
      await destination.send('send_cog_help got called')

    async def send_group_help(self, group):
      destination = self.get_destination()
      await destination.send('send_group_help got called')

    async def send_command_help(self, command):
      destination = self.get_destination()
      await destination.send('send_command_help got called')

    async def send_error_message(self, error):
      destination = self.get_destination()
      await destination.send('Oh no! An error has occurred!')

  bot = commands.Bot(command_prefix='!', help_command=MyHelp())

First, we created a class called "MyHelp" which subclasses 
:class:`~ext.commands.HelpCommand`. Next, we added a method which is called 
"send_bot_help". This method overrides the existing method:
:meth:`~discord.ext.commands.HelpCommand.send_bot_help`, it is called whenever 
someone uses the help command with no other arguments(e.g. ``!help``). 

This method takes in one positional only parameter, ``mapping``, 
which is a dictionary of :class:`~ext.commands.Cog` objects as 
the key and a list of :class:`~ext.commands.Command` objects as the value. 

.. note:: 

  A key in the ``mapping`` parameter can possibly be ``None``. This means that the command was not in any cog.

Using :meth:`~discord.ext.commands.HelpCommand.get_destination`, we are able to send the help command message
in the channel that the command was invoked under. This method returns a :class:`~discord.abc.Messageable` object
which is the context's channel by default. We can use the :meth:`~discord.abc.Messageable.send` method 
to send the message to the appropriate channel.

The other methods: ``send_cog_help``, ``send_group_help``, ``send_command_help``, ``send_error_message``
override :meth:`~discord.ext.commands.HelpCommand.send_cog_help`, :meth:`~discord.ext.commands.HelpCommand.send_group_help`,
:meth:`~discord.ext.commands.HelpCommand.send_command_help`, and :meth:`~discord.ext.commands.HelpCommand.send_error_message`
respectively. 

- The ``send_cog_help`` method gets called when the help command is used with a valid cog in the command usage (i.e. ``!help [cog]``).

- The ``send_group_help`` method gets called when the help command is used with a valid group in the command usage(i.e. ``!help [group]``).

- The ``send_command_help`` method gets called when the help command is used with a valid command in the command usage(i.e. ``!help [command]``).

- The ``send_error_message`` method gets called when an error occurrs during executing the code in help command. 

.. image of this

Overriding these methods combined with utilizing
the provided attributes of :class:`~ext.commands.Command`
objects, we can create a superb help command!

Listing Commands
~~~~~~~~~~~~~~~~

We can use :meth:`~discord.ext.commands.HelpCommand.send_bot_help` 
to help list out the commands our bot has via overriding as we previously did. 

.. code-block:: python3

  import discord
  from discord.ext import commands

  class MyHelp(commands.HelpCommand):

    async def send_bot_help(self, mapping):
      embed = discord.Embed(title='My commands', description='')
      for cog, commands in mapping.items():
        cog_name = getattr(cog, 'qualified_name', 'No Category')
        command_names = [command.name for command in commands]
        embed.description += '**{0}**\n{1}\n'.format(cog_name, '\n'.join(command_names))
      destination = self.get_destination()
      await destination.send(embed=embed)

We have instantiated an instance of :class:`~discord.Embed` and then
we iterate over :meth:`~collections.abc.Mapping.items`. Since ``cog`` might be ``None`` in the event that the command is
not in a cog, we use ``getattr`` to get the name of the cog or make it "No Category" if it is not in a cog. 
We then use a list comprehension and access the :attr:`~ext.commands.Command.name` attribute
of all of the commands in the cog. We then use :meth:`~discord.Embed.add_field` to add the cog to the ``name``
portion of the field and the command names to the ``value`` portion of the field.

With this code, the output should look like this:

.. image of this

Help with Command attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To define the behavior when a user searches a specific command, 
we can override :meth:`~discord.ext.commands.HelpCommand.send_command_help`.
From there, we can use different command attributes to reveal information for the command.

.. code-block:: python3

  import discord
  from discord.ext import commands

  class MyHelp(commands.HelpCommand):

    async def send_command_help(self, command):
      embed = discord.Embed(title=command.name)
      command_signature = self.get_command_signature(command)
      embed.add_field(name='Command Signature', value=command_signature, inline=False)
      embed.add_field(name='Description', value=command.description)
      if command.aliases:
        embed.add_field(name='Aliases', value=', '.join(command.aliases))
      destination = self.get_destination()
      await destination.send(embed=embed)
      
In this code, we do the following: 

1. Override :meth:`~ext.commands.HelpCommand.send_command_help`.

2. Instantiate an :class:`~discord.Embed` instance. 

3. Get the command signature using :meth:`~ext.commands.HelpCommand.get_command_signature`. 

4. Add this to a field of the embed using :meth:`~discord.Embed.add_field`. 

5. Do the same for the description of the command using the :attr:`~ext.commands.Command.description` attribute to get the description of the command. 

6. To add a field with the aliases of the command, we use the :attr:`~ext.commands.Command.aliases` attribute in an if statement to check if the command has any aliases. 

7. If it does, we add them as a field and use :meth:`str.join` in the ``value`` keyword argument. 

8. Lastly, we get the destination using :meth:`~ext.commands.HelpCommand.get_destination` and send the message.

All in all, the result of our code should look like this:

.. image of the result of code

.. TODO: Add a section that explains cog and patching around the original and new help commands

Conclusion
----------

.. working on