:orphan:

.. currentmodule:: discord

.. _guide_interaction_checks:

Interaction Checks Guide
=========================

Checks allow you to set requirements for a command to be executable. They can enforce a user being an administrator, any number of roles, the bot's permissions, cooldowns, custom checks, or any combination of these.

These checks will be used as decorators in conjunction with any :func:`@app_commands.command <.app_commands.command>` or :func:`@app_commands.context_menu <.app_commands.context_menu>` decorators.

Before getting started, the examples shown below demonstrate both :class:`.app_commands.Command` and :class:`.app_commands.ContextMenu` checks. All of the checks present here can apply to either one. Let's take a look at each of the possible checks.

.. note::

    For information on slash commands, see the :ref:`Slash Commands Guide <discord_slash_commands>`. For more information on context menus, see the :ref:`Context Menus Guide <guide_interactions_context-menus>`.

.. _guide_interaction_checks_role-check:

Role Checks
------------

These checks ensure that the user triggering a command has a role, or any role from a set of roles.

.. code-block:: python3
    :emphasize-lines: 2,7

    # Single role check.
    @app_commands.command()
    @app_commands.checks.has_role('Role Name')
    async def single_role_check(interaction: discord.Interaction):
        await interaction.response.send_message('You have the role!', ephemeral=True)

    # Any role from set of roles check.
    @app_commands.context_menu()
    @app_commands.checks.has_any_role('Role Name', 1234567890, 'AnotherOne')
    async def multiple_role_check(interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message('You have one of the roles!', ephemeral=True)

Let's take a quick look through the code here:

- First, a simple :class:`.app_commands.Command` is registered using the :func:`@app_commands.command() <.app_commands.command>` decorator.
- Then, a :func:`@has_role <.app_commands.checks.has_role>` check is added to ensure that a user has a given role. This role can either be a :class:`str` representing the name of the role, or an :class:`int` representing the id of the role.
- Then, the actual function callback for the command is created.

A very similar process happens for checking multiple roles:

- First, a :class:`.app_commands.ContextMenu` is registered using the :func:`@app_commands.context_menu() <.app_commands.context_menu>` decorator.
- Then, a :func:`@has_role <.app_commands.checks.has_any_role>` is added for multiple roles. Again, these roles are either :class:`str` or :class:`int` values with the types having the same meanings.
- Then, the callback for the context menu is created.

.. _guide_interaction_checks_permission-check:

Permission Checks
------------------

These checks handle validating whether the user activating a command has certain permissions in a guild, or whether the bot user has specific permissions.

.. code-block:: python3
    :emphasize-lines: 3,9

    # User permissions check.
    @app_commands.command()
    @app_commands.has_permissions(administrator=True)
    async def user_permission_check(interaction: discord.Interaction):
        await interaction.response.send_message('Hello administrator!', ephemeral=True)

    # Bot permissions check.
    @app_commands.command()
    @app_commands.bot_has_permissions(manage_messages=True, manage_guild=True)
    async def bot_permission_check(interaction: discord.Interaction):
        await interaction.response.send_message('I can do that!', ephemeral=True)

These two checks are identical in usage. The only difference is that the first checks the permissions of the user who calls the command, and the other checks the permissions of the bot user the command is issued to.

The permissions given to the check can be any number of permissions, which can be found in :class:`.Permissions`, and must have a boolean value.

.. _guide_interaction_checks_cooldown-check:

Cooldown Checks
----------------

It is also possible to use a check decorator that will directly attach a cooldown to your command.

There are two cooldown types, static and dynamic.

Static Cooldown
~~~~~~~~~~~~~~~~

Static cooldowns limit a command to a fixed number of uses, per time frame.

.. code-block:: python3
    :emphasize-lines: 2

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda interaction: (interaction.guild_id, interaction.user.id))
    async def cooldown_check(interaction: discord.Interaction):
        await interaction.response.send_message('Not on cooldown yet!', ephemeral=True)

The :func:`@cooldown <.app_commands.checks.cooldown>` decorator takes 3 possible arguments:

- The ``rate`` parameter first takes an :class:`int`, which determines the number of times a command can be used within a time frame before the cooldown is activated.
- The ``per`` parameter then takes a :class:`float` which determines the number of seconds to wait for a cooldown once it has been activated.
- The third and final parameter, ``key``, can be used to specify what criteria are used for applying the cooldown. This is given as a function that takes a :class:`.Interaction` as an argument, and can return a coroutine.

Now that we know what the parameters for a static cooldown are, let's take a closer look at the shown example:

- The ``rate`` parameter is set to ``1``, so the cooldown will trigger every time the command is used.
- The ``per`` parameter is set to ``5.0``, so the cooldown will lock the command for 5 seconds when it is used.
- The ``key`` parameter has a ``lambda`` function which accepts the :class:`.Interaction`, and then returns a :class:`tuple` for the :attr:`~.Interaction.guild_id` and :attr:`user.id <.Interaction.user>` values. This means that the cooldown will be put in effect for each user individually, in each guild.

Putting it all together: an individual user can use the command once every 5 seconds per guild. This means that if they were to then proceed to use the command in another guild, the cooldown from the first guild would not be applied.

.. note::

    By default, the "key" parameter will operate on the :class:`.User` level. So if no "key" parameter is specified, the cooldown will be applied per user, globally. Similarly, if the "key" parameter is set to ``None``, then the cooldown is considered a "global" cooldown for all users and guilds.

Dynamic Cooldown
~~~~~~~~~~~~~~~~~

Dynamic cooldowns allow you to register a custom handler for cooldown checks.

.. code-block:: python3
    :emphasize-lines: 10

    def cooldown_skip_owner(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
        if interactions.user.id == 1234567890:
            return app_commands.Cooldown(1, 5.0)
        if interactions.guild is not None and interactions.guild.owner_id == interactions.user.id:
            return None

        return app_commands.Cooldown(1, 10.0)

    @app_commands.command()
    @app_commands.checks.dynamic_cooldown(cooldown_skip_owner)
    async def dynamic_cooldown_check(interaction: discord.Interaction):
        await interaction.response.send_message('Not on cooldown!', ephemeral=True)

The :func:`@dynamic_cooldown <.app_commands.checks.dynamic_cooldown>` is passed a reference to a function, which can be used to control when to apply a different cooldown to specific use-cases, or ignore it all together.

In this specific use case, the function is used to apply a 10 second per usage cooldown to each individual user. However, if the user is the owner of the guild the command is used in, the command cooldown is bypassed. Similarly, if the user is a specific user mentioned by id, a lesser cooldown is applied, of just 5 seconds per usage.

.. _guide_interaction_checks_custom-check:

Custom Check
-------------

Custom checks can also be implemented if further functionality is needed outside of the checks listed above or in the :ref:`API reference <interactions#checks>`. These generally come in two forms: a standard check decorator that is passed a custom function, or a custom decorator for common checks.

.. code-block:: python3
    :emphasize-lines: 6,17

    # Custom check function.
    def check_if_owner(interaction: discord.Interaction) -> bool:
        return interaction.guild is not None and interaction.user.id == interaction.guild.owner_id

    @app_commands.command()
    @app_commands.check(check_if_owner)
    async def owners_only(interaction: discord.Interaction):
        await interaction.response.send_message('Hello boss!')

    # Custom check decorator.
    def is_me():
        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.id == 1234567890
        return app_commands.check(predicate)

    @app_commands.command()
    @is_me()
    async def me_only(interaction: discord.Interaction):
        await interaction.response.send_message('I know you!', ephemeral=True)

In this example, the first check is implemented to only allow the command usage if the user who runs the command is the owner of the guild the command is used in. This is a function which takes a :class:`.Interaction` as an argument, which is passed to the :func:`@check <.app_commands.check>` decorator. The second check implemented creates a custom decorator which checks if the user who activates a command has a specific id. This limits a command to only one user.

.. _guide_interaction_checks_combining-checks:

Combining Checks
-----------------

You can combine multiple checks on a command which requires all to pass for invocation to succeed.

As an example, here is a command which only runs if a user has a certain role, ``send_messages`` permissions, the bot has ``manage_messages`` permissions, and with a 15 second global cooldown:

.. code-block:: python3

    @app_commands.command()
    @app_commands.checks.has_role('Necessary Role')
    @app_commands.checks.has_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 15.0, key=None)
    async def check_example(interaction: discord.Interaction):
        await interaction.send_message('Checks passed!', ephemeral=True)

.. _guide_interaction_checks_global-checks:

Global Interaction Checks
--------------------------

In addition to adding individual or combined checks onto specific app commands or context menus, it is also possible to create global interaction checks. For these, any interaction
passed through the bot for either app commands or context menus will first run this check.

In order to implement a global check, we will need to create our own subclass of the :class:`.app_commands.CommandTree` class, and implement the :meth:`.app_commands.CommandTree.interaction_check` method.

.. code-block:: python3

    import discord
    from discord import app_commands
    from discord.ext import commands

    class MyCommandTree(app_commands.CommandTree):
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id == 1234567890:
                return False

            if interaction.guild is None:
                return False

            return True

    # Using with a discord.Client implementation
    client = discord.Client(...)
    tree = MyCommandTree(client)

    # Using with a commands.Bot implementation
    bot = commands.Bot(..., tree_cls=MyCommandTree)


Alright, let's deconstruct this now:

- First of all, we create a subclass of :class:`.app_commands.CommandTree` which implements a :meth:`.app_commands.CommandTree.interaction_check` method, which takes our interaction as its sole parameter.
- Next, we can perform any number of logical checks based on the interaction. In this example, the check verifies that the user of the interaction is *not* a specific user ID, and that the interaction is being used in a guild.
- The return value of the interaction determines whether the check is passed. A ``False`` value will fail the check, while a ``True`` value will pass.
- Lastly, we need to tell our bot to use this command tree.
    - For a :class:`.Client` implementation that does not use the commands extension, we create the client instance and then instantiate the custom command tree by passing that client in.
    - For a :class:`.ext.commands.Bot` implementation, we can pass in our customer command tree class directly when we instantiate the bot.
- After this, any interactions across the entire bot will first have this check run before continuing.

.. note::

    When checks do not pass, they will throw an error. By implementing custom error handling for these errors,
    you can create a system that will do something different when a check is failed.
    See the :ref:`Error Handling Guide <guide_error_handling>` for further information on this.

.. _guide_integration_permissions:

Integration Permissions
------------------------

In addition to the previously mentioned checks, there are a few other "check-like" functionalities provided.

These include:

- The :func:`@app_commands.default_permissions() <.app_commands.default_permissions>` decorator.
- The :func:`@app_commands.guild_only() <.app_commands.guild_only>` decorator.
- The ``nsfw`` parameter for :func:`commands <.app_commands.command>` and :func:`context menus <.app_commands.context_menu>`.

The main difference is that these features are handled by Discord itself, client-side, before the interaction is ever handed off
to the bot to work with. However, the drawback to this is that it is not possible to perform any sort of custom error
handling when these situations arise.

.. note::

    If you wish to perform error handling of these kinds of features yourself,
    you can implement a :ref:`custom check <guide_interaction_checks_custom-check>`.

.. warning::

    Due to a limitation of Discord, these features cannot be applied directly to a subcommand.
    It must be used on the parent command of a command group.

.. _guide_integration_permissions_default-perms:

Default Permissions
~~~~~~~~~~~~~~~~~~~~

The :func:`default_permissions <.app_commands.default_permissions>` decorator will set the default permissions necessary
for a user to execute a slash command or interact with a context menu.

Using this means that a slash command or context menu will by default require the provided permissions.
However, an administrator in the server will be able to override these permissions directly in the Discord client,
without the bot's knowledge.

.. code-block:: python3

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def default_permissions_slash_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Greetings administrator & whoever else was given permission!')

    @app_commands.context_menu(name='User Context')
    @app_commands.default_permissions(manage_messages=True, manage_guild=True)
    async def default_permissions_slash_command(interaction: discord.Interaction, user: discord.User) -> None:
        await interaction.response.send_message('You may or may not have those permissions!'


In the first example above, we limit the permissions to use the slash command to administrators only by default.

.. note::

    Not passing any parameters to the :func:`default_permissions <.app_commands.default_permissions>` will result
    in the default permissions being set to administrator only.

In the second example, the context menu will be limited to only users with the ``delete_messages`` and ``manage_guild``
permissions. The provided values can be any number of :class:`.Permissions`,
and must have a boolean value.

Here is what the context menu above looks like in the Discord client, found inside of the ``Integrations`` section of
the ``Server Settings``.

.. image:: /images/guide/interactions/default_permissions_1.png

When you click on the ``View`` button:

.. image:: /images/guide/interactions/default_permissions_2.png

As you can see from the first image, there is the option to add specific members, roles, and channels as overrides
to the default permission list.

.. _guide_integration_permissions_guild-only:

Guild Only
~~~~~~~~~~~

The :func:`guild_only <.app_commands.guild_only>` decorator will mark a slash command or context menu as only being executable within a guild.


.. code-block:: python3

    # Slash Command
    @app_commands.command()
    @app_commands.guild_only()
    async def guild_only_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Hello fellow guildmate!')

    # Context Menu
    @app_commands.context_menu(name='Greet')
    @app_commands.guild_only()
    async def guild_only_context(interaction: discord.Interaction, user: discord.Member) -> None:
        await interaction.response.send_message(f'{interaction.user.mention} greets {user.mention}!')


In this example, both the slash command and the context menu will be unavailable outside of a guild.


.. _guide_integration_permissions_nsfw:

NSFW Only
~~~~~~~~~~

The ``nsfw`` parameter is passed directly to the decorator for a slash command or a context menu, and it indicates
whether to limit the availability of the interaction to only NSFW channels. By default this value is ``False``,
allowing the command to be used in all locations.

.. code-block:: python3

    # Slash Command
    @app_commands.command(nsfw=True)
    async def guild_only_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message('This is an NSFW channel!')

    # Context Menu
    @app_commands.context_menu(nsfw=True)
    async def guild_only_context(interaction: discord.Interaction, user: discord.Member) -> None:
        await interaction.response.send_message(f'{user.mention} is in the NSFW channel!')

Both the slash command and the context menu shown above will only be available in NSFW channels.