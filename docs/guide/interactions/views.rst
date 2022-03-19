.. currentmodule:: discord

.. _guide_interactions_views:

Views
=======

Views are the primary way to design message component based UIs.

This section details how to create and use views in various situations.


Creating a View
-----------------

Let's start off with a simple example, a confirmation prompt.

By the end of this section we'll have a generic confirmation prompt we can use in a variety of situations.

For example, a ban command:

.. image:: /images/guide/interactions/views1.png

The first step is to create a :class:`~discord.ui.View` subclass. Let's call it ``Confirm``

.. code-block:: python

    class Confirm(discord.ui.View):
        
        def __init__(self, user: discord.User, *, timeout: Optional[int] = None) -> None:
            super().__init__(timeout=timeout)
            self.user: discord.User = user
            self.result: Optional[bool] = None

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user == self.user 

In the constructor, or the ``__init__`` method, we initialise some context-specific attributes; ``user``, which
we can use later to know who we are prompting for confirmation, and ``result`` which we'll use to store the result of 
the prompt.

The :class:`~discord.ui.View` class also supports a :meth:`~discord.ui.View.interaction_check` method, which we'll
use to check if the user who clicked on buttons in the view is the same as the user we're prompting for confirmation.
It should return a boolean value, which when ``False`` will ignore the interaction.

Creating components
~~~~~~~~~~~~~~~~~~~~

We also need to create components for our UI, two buttons, a `Yes` and `No` button.

There are two main ways to create components, we'll cover both in this section.

Class-Based Components
^^^^^^^^^^^^^^^^^^^^^^^^

Firstly we can create a component by subclassing the related component class, for a button this is the :class:`~discord.ui.Button` class.

Our code might look like this:

.. code-block:: python

    class YesButton(discord.ui.Button[Confirm]):
        def __init__(self) -> None:
            super().__init__(
                label="Yes",
                style=discord.ButtonStyle.danger,
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            self.view.result = True
            self.view.stop()

There's a bit to unpack here already, the ``__init__`` is setting the ``style`` and ``label`` parameters, which 
set the colour and text of the button respectively.

And then there's the :meth:`Button.callback() <discord.ui.Button.callback>` method, this is the method that will be called when the button is clicked.
In this case it's being used to set the ``result`` attribute of the :class:`~discord.ui.View` subclass we created earlier.

Now we've made our first component, we should add it to the view.

The :class:`~discord.ui.View` class has a :meth:`~discord.ui.View.add_item` method, which takes a component as a parameter.
so in our ``__init__`` method we can add:

.. code-block:: python
    :emphasize-lines: 7

    class Confirm(discord.ui.View):

        def __init__(self, user: discord.User, *, timeout: Optional[int] = None) -> None:
            super().__init__(timeout=timeout)
            self.user: discord.User = user
            self.result: Optional[bool] = None
            self.add_item(YesButton())

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user == self.user 

After the call to the parent constructor.

Decorator-based Components
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In reality, our components are relatively simple, so we can use a helper function decorator instead.

In this case, we're creating a button we can use the :func:`~discord.ui.button` decorator inside our ``View`` like so:

.. code-block:: python
    :emphasize-lines: 12-19

    class Confirm(discord.ui.View):

        def __init__(self, user: discord.User, *, timeout: Optional[int] = None) -> None:
            super().__init__(timeout=timeout)
            self.user: discord.User = user
            self.result: Optional[bool] = None
            self.add_item(YesButton())

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user == self.user 

        @discord.ui.button(label="No", style=discord.ButtonStyle.primary)
        async def no_button(
            self,
            button: discord.ui.Button[Confirm],
            interaction: discord.Interaction,
        ) -> None:
            self.result = False
            self.stop()

Using the decorator approach greatly simplifies the code, but it's not as flexible as using a custom class.
We set parameters prior to the creation of the view-instance, so context-specific variables are not available.
If modifications are needed, we would instead have to override component instance attributes in the ``__init__`` method.

The function we're decorating acts similarly to the :meth:`~discord.ui.Button.callback` method, it's called when the button is clicked.
However the arguments passed to the function are different. Rather than ``self`` referring to the component, it refers to the view, with
the component being passed as the next argument.

When using component decorators, we no longer need to explicitly add the component to the view, this is done automatically.

Sending views
--------------

We send views using the ``view`` parameter in methods which send messages. for example :meth:`TextChannel.send`.

In our case we're creating a confirmation prompt for our ban command, so we'll want to use the :meth:`InteractionResponse.send_message`.

Our command might look like this:

.. code-block:: python

    @discord.app_commands.command()
    @discord.app_commands.describe(member="The member to ban.")
    async def ban(interaction: discord.Interaction, member: discord.Member) -> None:
        """Ban a member from the server."""
        confirmation = Confirm(interaction.user)
        await interaction.send_message(f'Are you sure you want to ban {member.name}?', view=confirmation)
        await confirmation.wait()
        if confirmation.result:
            await member.ban()

We first assign the ``View`` instance to the variable ``confirmation``, because we'll need it later.
In our interaction response we send the instance via the ``view`` parameter.
Finally, using :meth:`confirmation.wait() <discord.ui.View.wait>`, we wait for the view to stop listening for interactions,
which occurs either when the user clicks on a button (as we had called :meth:`View.stop() <discord.ui.View.stop>`)
or the view had timed-out.

Since our component callbacks assign the ``result`` attribute of the view, we can use it to determine if the user clicked on the
`Yes` or `No` button, and in the `Yes` case we can ban the member.


Persistent Views
-----------------

There are instances where we might want to create a view that will persist for a long time.
For example, a view which allows members of a Guild to select a role to assign to themselves.

.. image:: /images/guide/interactions/views2.png

Let's make one such view.


Designing a Persistent View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We'll start by creating a class to represent the view, again like above we'll create a 
subclass of :class:`~discord.ui.View`. We'll also create a :class:`~discord.ui.Select` component,
which is a dropdown menu using the :func:`@select <discord.ui.select>` decorator. We'll set some 
placeholder text for the dropdown menu and set both the minimum and maximum number of elements 
a user can select to `1`.

To start out our code might look like this:

.. code-block:: python

    class RoleSelector(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)

        @discord.ui.select(
            placeholder='Select a role',
            min_values=1,
            max_values=1,
        )
        async def selector(
            self,
            component: discord.ui.Select['RoleSelector'],
            interaction: discord.Interaction,
        ) -> None:
            raise NotImplementedError

This is missing a few important things however, for example the select component 
needs to know what roles to display in the dropdown, so we'll need to pass in the roles to the component, 
using the :meth:`~discord.ui.Select.add_option` method, we can iterate over the roles and add the
role name as the ``label`` and the role ID as the ``value``.

Additionally, since this view is persistent we'll need to specify a :attr:`~discord.ui.Select.custom_id` for our 
:class:`~discord.ui.Select` component, which is used to identify the component when a user interacts with it.
Since we could have multiple role selectors, we'll use the ID of the message the view is attached to as part of the ``custom_id``.

After adding these details our code will look something like this:

.. code-block:: python
    :emphasize-lines: 2,5-9

    class RoleSelector(discord.ui.View):
        def __init__(self, message_id: int, roles: List[discord.Role]) -> None:
            super().__init__(timeout=None)

            self.selector.custom_id = f'role_selector_{message_id}'

            self.roles: List[discord.Role] = roles
            for role in roles:
                self.selector.add_option(label=role.name, value=str(role.id))

        @discord.ui.select(
            placeholder='Select a role',
            min_values=1,
            max_values=1,
        )
        async def selector(
            self,
            component: discord.ui.Select['RoleSelector'],
            interaction: discord.Interaction,
        ) -> None:
            raise NotImplementedError

We'll also need to add a body to our ``selector`` callback function which will assign the selected role to the user:
This is fairly simple to do, when the callback is invoked we can access the options the user selected via the
:attr:`~discord.ui.Select.options` attribute. This holds a list of values, but since we limited the number of values to `1`
we can just access the first element directly. We can then use sets to determine what roles the user already has, and then with :meth:`Member.edit <discord.Member.edit>` 
override the members roles.

Our function body might look like this:

.. code-block:: python
    :emphasize-lines: 21-24

    class RoleSelector(discord.ui.View):
        def __init__(self, message_id: int, roles: List[discord.Role]) -> None:
            super().__init__(timeout=None)

            self.selector.custom_id = f'role_selector_{message_id}'

            self.roles: List[discord.Role] = roles
            for role in roles:
                self.selector.add_option(label=role.name, value=str(role.id))

        @discord.ui.select(
            placeholder='Select a role',
            min_values=1,
            max_values=1,
        )
        async def selector(
            self,
            component: discord.ui.Select['RoleSelector'],
            interaction: discord.Interaction,
        ) -> None:
            role_id = int(component.values[0])
            role = discord.Object(id=role_id)
            await interaction.user.remove_roles(*self.roles)
            await interaction.user.add_roles(role)


Making a View Persist
~~~~~~~~~~~~~~~~~~~~~~

Now our view class is complete we can manually attach an instance to a message to retrieve the ID.
When we're doing this the ``custom_id`` can be set to anything since the view handling will be done 
when we mark the view as persistent.

.. code-block:: python

    ROLE_IDS = [490320652230852629, 714516281293799438, 859169678966784031, 673195396834656257]
    roles = [guild.get_role(id) for id in ROLE_IDS]
    await channel.send('Choose your house', view=RoleSelector(0, roles)) # we don't know the message ID yet.

Once we have a message ID we just need to create an instance of our view and attach it to the :class:`~discord.Client`
with the :meth:`~discord.Client.add_view` method.

.. code-block:: python

    GUILD_ID = 336642139381301249
    SELECTOR_MESSAGE_ID = 881049369850306610
    ROLE_IDS = [490320652230852629, 714516281293799438, 859169678966784031, 673195396834656257]

    class MyClient(discord.Client):

        async def setup_role_selector(self) -> None:
            await self.wait_until_ready()
            guild = self.get_guild(GUILD_ID)
            roles = [guild.get_role() for id in ROLE_IDS]
            client.add_view(RoleSelector(SELECTOR_MESSAGE_ID, roles), message_id=SELECTOR_MESSAGE_ID)

        async def setup_hook(self) -> None:
            asyncio.create_task(self.setup_role_selector())

    client = MyClient()
    client.run(...)

If we did everything correctly, the user should be able to select a role and the role should be assigned to the user.


Further Reading
-----------------

You can find more information on `Views` and `Components` in the :ref:`Bot UI Kit <discord_ui_kit>` section of the API reference.

There are also a number of examples in the :repo:`examples/views` directory on GitHub.
