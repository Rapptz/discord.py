.. currentmodule:: discord

.. _guide_topic_reactions

Reactions
==========

Reactions are a feature within Discord where you can add emojis next to messages.
They have many uses, but a common one for bots is for polls or giving feedback to a command without sending a new message.
Anyone can react to a message.



Adding a reaction
~~~~~~~~~~~~~~~~~~

Adding reactions is quite simple.

To add a custom emoji reaction you can do the following:

.. code-block:: python3

    await message.add_reaction("<:amogus:819046807370989599>")

Which would add a reaction to the message like so:

.. image:: /images/guide/topics/reactions/add_custom_emoji.png
    :scale: 50%


.. note::

    You must have the permission :attr:`~Permissions.read_message_history` to add reactions.
    Additionally, if no one else has reacted to the message using this emoji, you will also need the
    :attr:`~Permissions.add_reactions` permission.

In addition to :class:`str`, you can also pass :class:`~Emoji`, :class:`~PartialEmoji`, or :class:`~Reaction` to :meth:`~Message.add_reaction`.
For example, the following shows an alternative way to add a custom emoji reaction:

.. code-block:: python3

    emoji = client.get_emoji(819046807370989599)
    await message.add_reaction(emoji)

You may notice that if you try to add a standard Discord emoji like ``:smile:``, you'll receive an error.
This is because to add standard Discord emojis to a message, you must pass their unicode values.
Because of this, to add 😄 / ``:smile:`` you would do either of the following:

.. code-block:: python3

    # Pass the emoji codepoint via 32-bit hexadecimal escape.
    # For more information, see: https://docs.python.org/3/howto/unicode.html#the-string-type
    await message.add_reaction("\U0001f604")
    
    # Alternatively, use the codepoint's name.
    # See: https://docs.python.org/3/library/unicodedata.html
    await message.add_reaction("\N{SMILING FACE WITH OPEN MOUTH AND SMILING EYES}")

This would then result in:

.. image:: /images/guide/topics/reactions/add_standard_emoji.png
    :scale: 50%

You can find the documentation for adding reactions to a message object at :meth:`~Message.add_reaction`.

Removing a reaction
~~~~~~~~~~~~~~~~~~~~~

Removing reactions is similar to adding a reaction, but you must also specify a member to remove the reaction from.
This can be anything that meets the abc :class:`~abc.Snowflake`, like :class:`~discord.Member` or :class:`~discord.Object`.
This means that you cannot pass simply only an id, and you must instead pass something with an ``id`` attribute.

.. code-block:: python3

    await message.remove_reaction(
        "<:amogus:819046807370989599>",
        guild.me
    )

This removes a custom emoji reaction with the id ``819046807370989599`` added by us (see :attr:`~Guild.me`) from the message:

.. image:: /images/guide/topics/reactions/remove_reaction_before.png
    :scale: 50%

.. image:: /images/guide/topics/reactions/remove_reaction_after.png
    :scale: 50%

Removing all reactions of a given emoji from a message is also possible: 

.. code-block:: python3

    await message.clear_reaction("<:amogus:819046807370989599>")

And we can also remove all reactions entirely:

.. code-block:: python3

    await message.clear_reactions()

If you have a :class:`~Reaction`, you can also call :meth:`.clear() <Reaction.clear>` on that to clear reactions of that given emoji.

.. note:: 
    
    To remove a reaction that is not your own, you will need the :attr:`~Permissions.manage_messages` permission.

Getting reactions
~~~~~~~~~~~~~~~~~~

The :attr:`~Message.reactions` attribute allows you to get a list of the reactions on the message. This returns a :class:`~Reaction`
per unique emoji on the message.

For example, to get all the users that reacted with a given emoji:

.. code-block:: python3

    # This fetches the first 5 users that reacted with that emoji.
    async for user in reaction.users(limit = 5):
        await channel.send(f"{user} reacted with `{reaction.emoji}")

You can also flatten the users into a list.

.. code-block:: python3

    users = [u async for u in reaction.users()]
    # users is now a list of User...
    winner = random.choice(users)
    await channel.send(f'{winner} has won the raffle.')

Next Steps
~~~~~~~~~~~

You can find further information about :class:`~Reaction` in its documentation.
Additionally, :meth:`~Client.wait_for` can pair well with reactions.