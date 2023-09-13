:orphan:

.. currentmodule:: discord

.. _guide_interactions_context-menus:

Context Menus Guide
====================

Context menus allow for commands to be triggered through a context menu upon right clicking a related object in the Discord UI,
then selecting the name of the command to run from the ``Apps`` menu.

.. note::

    Context menus are not designed to be put inside of cogs. If you would like to use a context menu within a cog,
    you will need to handle creating the :class:`.app_commands.ContextMenu` yourself.


Basic Usage
~~~~~~~~~~~~

.. code-block:: python3

    @app_commands.context_menu(name="User Context")
    async def example(interaction: discord.Interaction, user: discord.User | discord.Member):
        await interaction.response.send_message(f"Interacting with user {user}.", ephemeral=True)

    @app_commands.context_menu(name="Message Context")
    async def example(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_message(f"Interacting with message {message.content}.", ephemeral=True)

- Context menus can be triggered from two possible sources: by right clicking on a user or server member, or by right clicking on a message.
- The ``name`` argument of the :func:`@context_menu <.app_commands.context_menu>` decorator defines the command name that appears in the context menu.
- The second argument can be of type :class:`.User`, :class:`.Member`, or :class:`.User` | :class:`.Member` for user context menus.
- Likewise, for message context menus, the second argument would be of type :class:`.Message`.
- Any messages sent to the :attr:`~.Interaction.response` attribute of the :class:`.Interaction` will appear in the channel that the user who activated the context menu currently has open.
- The profile image of the bot which owns a particular command will appear next to the command in the context menu.

The User Context Menu produces an option that looks like the following:

.. image:: /images/guide/interactions/user_context_menu.png

The Message Context Menu produces an option that looks like the following:

.. image:: /images/guide/interactions/message_context_menu.png

Checks
~~~~~~~

One of the most common current uses of context menus is to implement a variety of extended moderation features. Some ideas might include a ``Toggle Mute``, ``Warn``, ``Report``, or ``Info`` commands. For implementing moderation commands like these, it will be useful to add checks in order to ensure that only those who are allowed to can use said commands.

For examples of checks, view the :ref:`Interaction Checks Guide <guide_interaction_checks>`.