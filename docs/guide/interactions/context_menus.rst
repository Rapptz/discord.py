:orphan:

.. currentmodule:: discord

.. _guide_interactions_context-menus:

Context Menus
==============

Context menus allow for commands to be triggered through a context menu upon right clicking a related object, then selecting the name of the command to run from the ``Apps`` menu.

- Context menus can be categorized into two separate types, one for :class:`.User` and :class:`.Member` objects, and one for :class:`.Message` objects.
- The command does not have any arguments, and will simply return the target object.


Basic Usage
~~~~~~~~~~~~

.. code-block:: python3

    @app_commands.context_menu(name="User Context")
    async def example(interaction: discord.Interaction, user: Union[discord.User, discord.Member]):
        await interaction.response.send_message(f"Interacting with user {user}.", ephemeral=True)

    @app_commands.context_menu(name="Message Context")
    async def example(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_message(f"Interacting with message {message.content}.", ephemeral=True)

- The ``name`` argument of the :func:`@context_menu <.app_commands.context_menu>` decorator defines the command name that appears in the context menu.
- The second argument can be of type :class:`.User`, :class:`.Member`, or :class:`.User` | :class:`.Member` for user context menus.
- Likewise, for message context menus, the second argument would be of type :class:`.Message`.
- Any messages sent to the :attr:`~.Interaction.response` attribute of the :class:`.Interaction` will appear in the channel that the user of the context menu currently has open.
- The profile image of the bot which owns a particular command will appear next to the command in the context menu.

The User Context Menu produces an option that looks like the following:

.. image:: /images/guide/interactions/user_context_menu.png

The Message Context Menu produces an option that looks like the following:

.. image:: /images/guide/interactions/message_context_menu.png

Checks
~~~~~~~

One of the most common current uses of context menus is to implement a variety of extended moderation features. Some ideas might include a ``Toggle Mute``, ``Warn``, ``Report``, or ``Info`` commands. For implementing moderation commands like these, it will likely be useful to add checks in order to ensure that only those who are allowed to can use the moderation commands.

For examples of checks, view the :ref:`interaction checks guide <guide_interactions_checks>`.