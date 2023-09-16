.. currentmodule:: discord

.. _guide_interactions_views:

Views
=======

Views are the primary way to design message component based UIs.

This section details how to create and use views in various situations.


Creating a View
-----------------

Let's start with a simple example, a confirmation prompt.

By the end of this section, we'll have a generic confirmation prompt that we can use in a variety of situations.

For example, a ban command:

.. image:: /images/guide/interactions/view_prompt_example.png

The first step is to create a :class:`~discord.ui.View` subclass. Let's call it ``Confirm``.

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
It should return a boolean value which, when ``False``, will cause the interaction to be ignored.


Creating components
~~~~~~~~~~~~~~~~~~~~

We also need to create components for our UI. Two buttons; a `Yes` and a `No` button.

There are two main ways to create components, which we'll cover in this section.


Class-Based Components
^^^^^^^^^^^^^^^^^^^^^^^^

Firstly we can create a component by subclassing the related component class. For a button this is the :class:`~discord.ui.Button` class.

Our code might look like this:

.. code-block:: python

    class YesButton(discord.ui.Button[Confirm]):
        def __init__(self) -> None:
            super().__init__(
                label='Yes',
                style=discord.ButtonStyle.danger,
            )

        async def callback(self, interaction: discord.Interaction) -> None:
            self.view.result = True
            self.view.stop()
            await interaction.response.defer()

There's a bit to unpack here already, the ``__init__`` is setting the ``style`` and ``label`` parameters, which 
set the colour and text of the button respectively.

And then there's the :meth:`Button.callback() <discord.ui.Button.callback>` method, which is the method that will be called when the button is clicked.
In this case it's being used to set the ``result`` attribute of the :class:`~discord.ui.View` subclass we created earlier.

Now we've made our first component, we should add it to the view.

The :class:`~discord.ui.View` class has a :meth:`~discord.ui.View.add_item` method, which takes a component as a parameter.
so in our ``__init__`` method we can add the following after the call to the parent constructor.

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


Decorator-based Components
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In reality, our components are relatively simple, so we can use a helper function decorator instead.

In this case, we're creating a button, so we can use the :func:`~discord.ui.button` decorator inside our ``View`` like so:

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

        @discord.ui.button(label='No', style=discord.ButtonStyle.primary)
        async def no_button(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button[Confirm],
        ) -> None:
            self.result = False
            self.stop()
            await interaction.response.defer()

Using the decorator approach greatly simplifies the code, but it's not as flexible as using a custom class.
We set parameters prior to the creation of the view instance, so context-specific variables are not available.
If modifications are needed, we would instead have to override component instance attributes in the ``__init__`` method.

The function we're decorating acts similarly to the :meth:`~discord.ui.Button.callback` method, it's called when the button is clicked.
However, the arguments passed to the function are different. Rather than ``self`` referring to the component, it refers to the view, with
the component being passed as the last argument.

When using component decorators, we no longer need to explicitly add the component to the view, this is done automatically.


Sending views
--------------

We send views using the ``view`` parameter in methods which send messages, for example :meth:`TextChannel.send`.

In our case we're creating a confirmation prompt for our ban command, so we'll want to use the :meth:`InteractionResponse.send_message` method.

Our command might look like this:

.. code-block:: python

    @discord.app_commands.command()
    @discord.app_commands.describe(member='The member to ban.')
    async def ban(interaction: discord.Interaction, member: discord.Member) -> None:
        """Ban a member from the server."""
        confirmation = Confirm(interaction.user)
        await interaction.response.send_message(f'Are you sure you want to ban {member.name}?', view=confirmation)
        await confirmation.wait()
        if confirmation.result:
            await member.ban()

We first assign the ``View`` instance to the variable ``confirmation``, because we'll need it later.
In our interaction response we send the instance via the ``view`` parameter.
Finally, using :meth:`confirmation.wait() <discord.ui.View.wait>`, we wait for the view to stop listening for interactions,
which occurs either when the user clicks on a button (as we had called :meth:`View.stop() <discord.ui.View.stop>`)
or the view had timed-out.

Since our component callbacks assign the ``result`` attribute of the view, we can use it to determine if the user clicked on the
`Yes` or `No` button, and ban them if they clicked `Yes`.


Persistent Views
-----------------

There are instances where we might want to create a view that will persist for a long time.
For example, a view which allows members of a Guild to select a role to assign to themselves.

.. image:: /images/guide/interactions/view_select_example.png

Let's make one such view.


Designing a Persistent View
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To start off, we need to create a class to represent the view, which we'll achieve by creating a 
subclass of :class:`~discord.ui.View`. In that class we need a :class:`~discord.ui.Select` component,
which is a dropdown menu using the :func:`@select <discord.ui.select>` decorator. We can set some 
placeholder text for the dropdown menu and set both the minimum and maximum number of elements 
a user can select to `1`.

To start out, our code might look like this:

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
            interaction: discord.Interaction,
            component: discord.ui.Select['RoleSelector'],
        ) -> None:
            raise NotImplementedError

However, there are a few important things missing. For instance, the select component must be aware of which roles to display in the dropdown.
To achieve this, we will pass the roles to the component. By utilizing the :meth:`~discord.ui.Select.add_option` method, 
we can iterate through the roles and assign the role name to the ``label`` and the role ID to the ``value``.

Additionally, since this view is persistent we need to specify a :attr:`~discord.ui.Select.custom_id` for our 
:class:`~discord.ui.Select` component, which is used to identify the component when a user interacts with it.
As we could have multiple role selectors, it seems fitting to use the ID of the message the view is attached
to as part of the ``custom_id``.

After adding these details, our code will look something like this:

.. code-block:: python
    :emphasize-lines: 2,5-9

    class RoleSelector(discord.ui.View):
        def __init__(self, message_id: int, roles: List[discord.Role]) -> None:
            super().__init__(timeout=None)

            self.selector.custom_id = f'role_selector:{message_id}'

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
            interaction: discord.Interaction,
            component: discord.ui.Select['RoleSelector'],
        ) -> None:
            raise NotImplementedError

We also need to add a body to our ``selector`` callback function, which will assign the selected role to the user.
This is fairly simple to do, when the callback is invoked we can access the options the user selected via the
:attr:`~discord.ui.Select.options` attribute. This holds a list of values, but since we limited the number of values to `1`,
we can just access the first element directly. We can then use sets to determine what roles the user already has, 
and then override the member's roles with :meth:`Member.edit <discord.Member.edit>`.

Our function body might look like this:

.. code-block:: python
    :emphasize-lines: 21-25

    class RoleSelector(discord.ui.View):
        def __init__(self, message_id: int, roles: List[discord.Role]) -> None:
            super().__init__(timeout=None)

            self.selector.custom_id = f'role_selector:{message_id}'

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
            interaction: discord.Interaction,
            component: discord.ui.Select['RoleSelector'],
        ) -> None:
            role_id = int(component.values[0])
            role = discord.Object(id=role_id, type=discord.Role)
            roles = set(interaction.user.roles) - set(self.roles) | {role}
            await interaction.user.edit(roles=roles)
            await interaction.response.defer()


Making a View Persist
~~~~~~~~~~~~~~~~~~~~~~

Now our view class is complete, we can manually attach an instance to a message to retrieve the ID.
When we're doing this, the ``custom_id`` can be set to anything since the view handling will be done 
when we mark the view as persistent.

.. code-block:: python

    ROLE_IDS = [490320652230852629, 714516281293799438, 859169678966784031, 673195396834656257]
    roles = [guild.get_role(id) for id in ROLE_IDS]
    await channel.send('Choose your house', view=RoleSelector(0, roles)) # we don't know the message ID yet.

Once we have a message ID, we just need to create an instance of our view and attach it to the :class:`~discord.Client`
with the :meth:`~discord.Client.add_view` method.

.. code-block:: python

    GUILD_ID = 336642139381301249
    SELECTOR_MESSAGE_ID = 881049369850306610
    ROLE_IDS = [490320652230852629, 714516281293799438, 859169678966784031, 673195396834656257]

    class MyClient(discord.Client):

        async def setup_role_selector(self) -> None:
            await self.wait_until_ready()
            guild = self.get_guild(GUILD_ID)
            roles = [guild.get_role(id) for id in ROLE_IDS]
            client.add_view(RoleSelector(SELECTOR_MESSAGE_ID, roles), message_id=SELECTOR_MESSAGE_ID)

        async def setup_hook(self) -> None:
            asyncio.create_task(self.setup_role_selector())

    client = MyClient(intents=discord.Intents.default())
    client.run(...)

If we did everything correctly, the user should be able to select a role and the role should be assigned to the user.


Dynamic Components
-------------------

In some instances, there may be some additional data we'll need when handling a component interaction.
For example, we could create a counter which increments every time the button is clicked.

The :class:`~discord.ui.DynamicItem` class allows us to define components with custom data contained in the ``custom_id``.


Designing a Dynamic Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Firstly, we'll need to create a subclass of :class:`~discord.ui.DynamicItem` which will represent out dynamic component.

Our code might start out looking like this:

.. code-block:: python

    class DynamicCounter(discord.ui.DynamicItem[discord.ui.Button], template=r'counter:(?P<count>\d+)'):
        def __init__(self, count: int = 0) -> None:
            self.count: int = count
            super().__init__(
                discord.ui.Button(
                    label=f'Total: {count}',
                    style=discord.ButtonStyle.primary,
                    custom_id=f'counter:{count}',
                )
            )

There are a few things to note here;

#. Dynamic components are defined by subclassing the :class:`~discord.ui.DynamicItem` class. They don't have an associated :class:`~discord.ui.View`.
#. We need to specify the type of component we're creating, in this case a :class:`~discord.ui.Button`.
#. We need to specify a regular expression pattern to match the ``custom_id`` against. This is done using the ``template`` parameter.
#. We need to define a constructor which takes the data we need to construct the component and passes a component instance to the parent constructor.

Subclasses of :class:`~discord.ui.DynamicItem` also require a :func:`classmethod` called :meth:`~discord.ui.DynamicItem.from_custom_id`,
which is used to construct the component from the ``custom_id`` when an interaction is received.

This method is passed both the :class:`~discord.Interaction` and a :class:`~re.Match` object, which contains the regular expression
match details using the ``template`` attribute of the class as the pattern.

In our case, we can cast the ``count`` group to an integer and pass it to the constructor.

.. code-block:: python
    :emphasize-lines: 12-15

    class DynamicCounter(discord.ui.DynamicItem[discord.ui.Button], template=r'counter:(?P<count>\d+)'):
        def __init__(self, count: int = 0) -> None:
            self.count: int = count
            super().__init__(
                discord.ui.Button(
                    label=f'Total: {count}',
                    style=discord.ButtonStyle.primary,
                    custom_id=f'counter:{count}',
                )
            )

        @classmethod
        async def from_custom_id(cls, interaction: discord.Interaction, match: re.Match[str], /):
            count = int(match['count'])
            return cls(count)


And like all other interactions we'll need to define some kind of callback to handle the interaction.
In this case we'll want to increment the counter and update the button label.

Our callback might look like this:

.. code-block:: python
    :emphasize-lines: 17-21

    class DynamicCounter(discord.ui.DynamicItem[discord.ui.Button], template=r'counter:(?P<count>\d+)'):
        def __init__(self, count: int = 0) -> None:
            self.count: int = count
            super().__init__(
                discord.ui.Button(
                    label=f'Total: {count}',
                    style=discord.ButtonStyle.primary,
                    custom_id=f'counter:{count}',
                )
            )

        @classmethod
        async def from_custom_id(cls, interaction: discord.Interaction, match: re.Match[str], /):
            count = int(match['count'])
            return cls(count)

        async def callback(self, interaction: discord.Interaction) -> None:
            self.count += 1
            self.item.label = f'Total: {self.count}'
            self.custom_id = f'counter:{self.count}'
            await interaction.response.edit_message(view=self.view)


Sending and Registering Dynamic Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that we've defined out dynamic component, we'll need to attach send a message which contains the component in a :class:`~discord.ui.View`.

Let's quickly define a view which contains our dynamic component.

.. code-block:: python

    class CounterView(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)
            self.add_item(DynamicCounter())

We'll also need some way to send a message with the view, so let's create a command to do that.

.. code-block:: python
    
    @discord.app_commands.command()
    async def counter(interaction: discord.Interaction) -> None:
        """Send a counter view."""
        await interaction.response.send_message(view=CounterView())

Lastly, to get our bot to handle interactions we'll need to register the dynamic component
with the :class:`~discord.Client` with the :meth:`~discord.Client.add_dynamic_items` method.

.. code-block:: python

    class MyClient(discord.Client):

        async def setup_hook(self) -> None:
            self.add_dynamic_items(DynamicCounter)

    client = MyClient(intents=discord.Intents.default())
    client.run(...)

Assuming we did everything right the bot should now increment the counter every time the button is clicked.


Further Reading
-----------------

You can find more information on `Views` and `Components` in the :ref:`Bot UI Kit <discord_ui_kit>` section of the API reference.

There are also a number of examples in the :repo:`examples/views` directory on GitHub.
