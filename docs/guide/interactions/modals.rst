.. currentmodule:: discord

.. _guide_interactions_modals:

Modals
========

Modals are a form of interaction response which prompt the user for additional information.


This section will detail how to create and use these modals in your code.


Defining a Modal
------------------

Modals share some similarities with :ref:`Views <guide_interactions_views>`, and are created by subclassing the :class:`~discord.ui.Modal` class.

For example, the following code:

.. code-block:: python3

    class FeedbackForm(discord.ui.Modal, title="Feedback"):
        name = discord.ui.TextInput(label="Name")
        feedback = discord.ui.TextInput(label="Feedback", style=discord.TextStyle.long)
        additional_information = discord.ui.TextInput(
            label="Additional Information", style=discord.TextStyle.long, required=False
        )

        async def on_submit(self, interaction):
            ... # do something with the data

            await interaction.response.send_message(f'Thank you {self.name}, your submission was recorded.')

produces a modal which appears as:

.. image:: /images/guide/interactions/modals1.png

Let's break down the code:


Title
~~~~~~

When defining the class an additional ``title`` argument can be provided to set the title of the modal.

If not set, then a title must always be set when creating an instance of the modal class for use in an interaction response.
This is done by the same-named ``title`` parameter in the constructor.


Fields
~~~~~~~

Inside the class body, modal fields are defined by assigning them to attributes of the class. In our example above we have
three fields: ``name``, ``feedback``, and ``additional_information``.

All of which are instances of the :class:`~discord.ui.TextInput` class.

.. note:: 

    The order in which fields are defined is the order in which they will be displayed in the modal.
    So for instance, as `name` is defined first, it will be displayed first.

At least one field is required, and a maximum of 5 fields can be defined. Fields can also be added or removed from a modal instance using the :meth:`~discord.ui.View.add_item` and :meth:`~discord.ui.View.remove_item` methods.

.. warning:: 

    Ensure that class-attribute defined fields do not conflict with attributes or methods defined in the class, as this
    will cause unexpected behavior.


Modal fields can be modified at an instance level by attribute access. For example, to change the label of the ``name`` field to ``"Your Name"``:

.. code-block:: python3

    form = FeedbackForm()
    form.name.label = "Your Name"


Handling a User Responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once A user has clicked `Submit` the user-defined :meth:`~discord.ui.Modal.on_submit` method will be called.

The values of the fields are accessible through the relevant attributes on the fields.
For instance, in the example above the value of the ``name`` field is accessible through ``self.name.value``.

the ``on_submit`` is passed a new :class:`~discord.Interaction` instance, which requires a response.


Handling an error
~~~~~~~~~~~~~~~~~~

In the event an exception is raised within the :meth:`~discord.ui.Modal.on_submit` callback, similarly to :class:`~discord.ui.View`
the :meth:`~discord.ui.Modal.on_error` method will be called.

This method is passed the exception raised, and the :class:`~discord.Interaction` instance, allowing you to handle the error and if necessary
send a response to the user.


Sending a Modal
-----------------

A modal can be sent by calling the :meth:`~discord.InteractionResponse.send_modal` method on a :class:`~discord.InteractionResponse`.

For example, a slash command invocation may respond with a modal:


.. code-block:: python3

    @discord.app_commands.command()
    async def feedback(interaction):
        """Send important feedback."""
        await interaction.response.send_modal(FeedbackForm())


Once a modal is sent it will be displayed to the user, who will be able to submit the modal.

.. note::

    It is currently not possible to tell if a user has closed the modal prompt without submitting.
