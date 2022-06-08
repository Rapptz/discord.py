.. currentmodule:: discord

.. _guide_interactions_checks:

Checks
=======

Checks are a feature that allows you to set requirements in order for a command to be executed. This can include things like requiring administrator permissions, requiring a user to have a role, making sure that the bot has necessary permissions to execute a task, adding a cooldown to a command, creating a custom check function, or any combination of these.

These checks will be used as decorators in conjunction with any :func:`@app_commands.command <.app_commands.command>` or :func:`@app_commands.context_menu <.app_commands.context_menu>` decorators.

Before getting started, the examples shown below are made using both :class:`.app_commands.Command` and :class:`.app_commands.ContextMenu` methods. All of the checks present here can apply to either one. Let's take a look at each of the possible checks.

Role Checks
------------

These checks allow a simple way to ensure that the user triggering a command has a role, or any role from a set of roles.

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
        await interaction.response.send_message('You have all the roles!', ephemeral=True)

Let's take a quick look through the code here:

- First, a simple :class:`.app_commands.Command` is registered using the :func:`@app_commands.command() <.app_commands.command>` decorator.
- Then, a :func:`@has_role <.app_commands.checks.has_role>` check is added to ensure that a user has a given role. This role can either be a :class:`str` representing the name of the role, or an :class:`int` representing the id of the role.
- Then, the actual function callback for the command is created.

A very similar process happens for checking multiple roles:

- First, a :class:`.app_commands.ContextMenu` is registered using the :func:`@app_commands.context_menu() <.app_commands.context_menu>` decorator.
- Then, a :func:`@has_role <.app_commands.checks.has_any_role>` is added for multiple roles. Again, these roles are either :class:`str` or :class:`int` values.
- Then, the callback for the context menu is created.

Permission Checks
------------------

These checks handle validating whether the user activating a command has certain permissions in a server, or whether the bot user has a specific permission.

.. code-block:: python3
    :emphasize-lines: 3,9

    # User permissions check.
    @app_commands.command()
    @app_commands.has_permissions(administrator=True)
    async def user_permission_check(interaction: discord.Interaction):
        await interaction.response.send_message('Hello administrator!', ephemeral=True)

    # Bot permissions check.
    @app_commands.command()
    @app_commands.bot_has_permissions(delete_messages=True, manage_guild=True)
    async def bot_permission_check(interaction: discord.Interaction):
        await interaction.response.send_message('I can do that!', ephemeral=True)

These two checks are identical in usage. The only difference is that one checks the permissions of the user who calls the command, and one checks the permissions of the bot user the command is issued to.

The permissions given to the checks can be any number of permissions, which can be found in :class:`.Permissions`, and must have a boolean value.

Cooldown Checks
----------------

It is also possible to use a check decorator that will directly attach a cooldown to your command.

There are two cooldown methods, static and dynamic.

Static Cooldown
~~~~~~~~~~~~~~~~

Static cooldowns are methods which limit a command to a certain number of uses per time frame.

.. code-block:: python3
    :emphasize-lines: 2

    @app_commands.command()
    @app_commands.checks.cooldown(1, 5.0, key=lambda interaction: (i.guild_id, i.user.id))
    async def cooldown_check(interaction: discord.Interaction):
        await interaction.response.send_message('Not on cooldown yet!', ephemeral=True)

The :func:`@cooldown <.app_commands.checks.cooldown>` decorator takes 3 possible arguments:

- The ``rate`` parameter first takes an integer value. This value is the number of usages that can be used within a time frame before the cooldown is activated.
- The ``per`` parameter then takes a float value. This is the number of seconds to wait for a cooldown once it has been activated.
- The third and final parameter, ``key``, can be used to specify what criteria are used for applying the cooldown. This is given as a function that takes a :class:`.Interaction` as an argument, and can be a coroutine.

Now that we know what the parameters for a static cooldown are, let's take a closer look at the shown example:

- The ``rate`` is set to ``1``, so the cooldown will trigger every time the command is used.
- The ``per`` param is set to ``5.0``, so the cooldown will lock the command for 5 seconds when it is used.
- The ``key`` parameter has a ``lambda`` function which accepts the :class:`.Interaction`, and then returns a tuple for the :attr:`~.Interaction.guild_id` and :attr:`user.id <.Interaction.user>` values. This means that the cooldown will be put in effect for each user individually, in each server.

Putting it all together: an individual user can use the command once every five seconds in any one guild. This means that if they were to then proceed to use the command in another guild, the cooldown from the first guild would not be applied.

.. note::

    By default, the "key" parameter will operate on the :class:`.User` level. So if no "key" parameter is specified, the cooldown will be applied per user, globally. Similarly, if the "key" parameter is set to "None", then the cooldown is considered a "global" cooldown for all users and guilds.

Dynamic Cooldown
~~~~~~~~~~~~~~~~~

Dynamic cooldowns allow you to register a custom handler for cooldown checks.

.. code-block:: python3
    :emphasize-lines: 10

    def cooldown_skip_owner(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
        if interactions.user.id == 1234567890:
            app_commands.Cooldown(1, 5.0)
        if interactions.guild is not None and interactions.guild.owner_id == interactions.user.id:
            return None

        return app_commands.Cooldown(1, 10.0)

    @app_commands.command()
    @app_commands.checks.dynamic_cooldown(cooldown_skip_owner)
    async def dynamic_cooldown_check(interaction: discord.Interaction):
        await interaction.response.send_message('Not on cooldown!', ephemeral=True)

The :func:`@dynamic_cooldown <.app_commands.checks.dynamic_cooldown>` is passed a reference to a function, which can be used to control when to apply a different cooldown to specific use-cases, or ignore it all together.

In this specific use case, the function is used to apply a ``10.0`` second per usage cooldown to each individual user. However, if the user is the owner of the guild the command is used in, the command cooldown is bypassed. Similarly, if the user is a specific user mentioned by id, a lesser cooldown is applied, of just ``5.0`` seconds per usage.

Custom Check
-------------

Custom check commands can also be implemented if further functionality is needed outside of the checks listed above. These will generally come in two forms: a standard check decorator that is passe a custom function, or a custom decorator for common checks.

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

In this example, the first check is implemented to only allow the command usage if the user who runs the command is the owner of the guild the command is used in. This is simply a function which takes a :class:`.Interaction` as an argument, which is passed to a :func:`@check <.app_commands.check>` decorator. The second check implemented creates a custom decorator which checks if the user who activates a command has a specific id. This limits a command to only one user.

Combining Checks
-----------------

You can combine multiple checks on a command to end up with a vary particular functionality for your needs, in a very concise manner.

As an example, here is a command which only runs if a user has a certain role, ``send_messages`` permissions, the bot has ``manage_messages`` permissions, and with a ``15`` second global cooldown:

.. code-block:: python3

    @app_commands.command()
    @app_commands.checks.has_role('Necessary Role')
    @app_commands.checks.has_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.checks.cooldown(1, 15.0, key=None)
    async def check_example(interaction: discord.Interaction):
        await interaction.send_message('Checks passed!', ephemeral=True)

.. note::

    When checks are failed, they will throw an error. By implementing custom error handling for these errors, you can create a system that will do something different when a check is failed. See the :ref:`error handling guide <guide_interactions_error-handling>` for further information on this.