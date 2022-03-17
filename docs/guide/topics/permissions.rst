.. currentmodule:: discord

.. _guide_topic_permissions:


Permissions
============

Permissions are the bread and butter of how control over a Discord server (which will from now on be referenced as a "guild" to align with Discord's official API terminology).

Controlling permissions is necessary for securing and controlling how your guild functions and operates.


Permission hierarchy explanation
---------------------------------

Discord permissions work on a hierarchy system. This means that roles placed logically above each other (in the Roles UI) have descending order of precedence.

If you have a role list, like so:

- ``Administrator (#1)``
- ``Manager (#2)``
- ``Moderator (#3)``
- ``@everyone (#4)``

This means that Administrator role (someone who has it) can kick, ban and timeout Manager.
Manager **cannot** kick, ban or timeout Administrator.

discord.py is aware of this and has implemented the :meth:`~Role.__gt__` and similar methods on :class:`~Role` that allows you to perform the following:

.. code-block:: python3

    if administrator_role > manager_role:
        # The administrator role is greater in the hierarchy than manager.

One small caveat to note with the discord permissions system, is that in the case of overwrites, explicit allow will always overwrite explicit deny.

In clearer terms, imagine this:

Take a scenario where you have a text channel, that gives the ``@everyone`` role the ``send_messages`` overwrite set to ``True`` (or a green check-mark in the UI).
If you then have a Muted role, that is supposed to disallow members from sending messages, but that role has the ``send_messages`` overwrite set to ``False`` (or a red cross in the UI)
then members with that Muted role **can** still send  messages within this channel.

A small example to show this:

.. image:: /images/guide/topics/permissions/hierarchy_explanation.png

The solution to this issue is to set the ``@everyone`` role overwrites for ``send_messages`` to ``None`` (or a grey strike in the UI).
This allows for permissions to be cascaded to it.

.. image:: /images/guide/topics/permissions/green_check.png
    :scale: 80%

.. image:: /images/guide/topics/permissions/red_cross.png
    :scale: 80%

.. image:: /images/guide/topics/permissions/grey_strike.png
    :scale: 80%


Using permissions within discord.py
------------------------------------

discord.py has two primary ways of interaction with the permissions of a guild or channels:

- :class:`~Permissions` for interacting with general permissions for roles and channels.
- :class:`~PermissionOverwrite` for interacting with the overwrites on a guild channel.

Let's use both of these now in actual examples.

Permission values
------------------

A small preface to this, is that Discord themselves represent the permissions system as a bit field.
They have a great in-depth `explanation to this <https://discord.com/developers/docs/topics/permissions>`_ on their API documentation page.

If you desire to use permission integers within discord.py, you can do it similar to the below:

.. code-block:: python3

    # If you wanted to create a new admin role, that has the `Administrator` permission, you can do it like so:
    permissions = discord.Permissions(administrator=True)

    # However, the underlying value for this permission (or `bit` as the API docs explain it) can be viewed by:
    permissions.value
    >>> 8

    # You can also instantiate a Permissions class with an integer that represents the bit(s) you want to provide, like so:
    permissions = discord.Permissions(268435634)
    # This Permissions instance has the `view_audit_log`, `manage_server`, `manage_roles`, `manage_channels` and `kick_members` permissions.


Using Permissions to create a new role
---------------------------------------

Let's imagine we have a server where we talk about the latest games.

.. code-block:: python3

    async def create_new_role(name: str, mentionable: bool, guild: discord.Guild) -> discord.Role:
        await guild.create_role(name=name, mentionable=mentionable, reason="New game!")

This rather short example just creates a new role within the :class:`~Guild` passed to this method.

Let's flesh it out more, and use the :meth:`~Guild.create_role` method to its full capability with a set of :class:`Permissions`.

.. code-block:: python3

    # So we want to create a new role, and to give that role some permissions.
    # We will define a set of `Permissions` that do what we need:
    permissions = discord.Permissions()
    permissions.send_messages = True
    permissions.add_reactions = True
    permissions.create_public_threads = True

    # Above is now a working Permissions instance with the name `permissions`, we could also define it like so:
    permissions = discord.Permissions(send_messages=True, add_reactions=True, create_public_threads=True)

    # and we pass this to the role creation method!
    await guild.create_role(name="My cool game", mentionable=True, permissions=permissions, reason="New game!")

Now we have a brand new role, named ``"My cool game"`` and it now also has the permissions we outlined above.

Setting permissions on an existing channel
-------------------------------------------

Let's say you wanted to edit the permissions of an existing channel, perhaps to give a role more access.
An example here is that my new moderator role needs the Manage Messages permission in the #general channel.
We will be using the :meth:`~TextChannel.set_permissions` method:

.. code-block:: python3

    # Let's create a PermissionOverwrite instance that has some explicit permissions set:
    overwrite = discord.PermissionOverwrite()
    overwrite.update(send_messages=True, send_messages_in_threads=True)

    # and now we update that with `manage_messages`:
    overwrite.manage_messages = True

    # we can now set those permissions on the channel:
    await channel.set_permissions(moderator_role, overwrite=overwrites)

This short example briefly goes over PermissionOverwrite objects, let's look more into those now:

Using ``PermissionOverwrite`` objects during channel creation
--------------------------------------------------------------

We can also create channels with permissions set from the start.
Let's create a text channel where only the moderator role, and someone trying to make a report, can see the channel.

We need to construct a mapping of ``Role | Member: PermissionOverwrite``:

.. code-block:: python3

    # We can now create the overwrites mapping necessary for this, you can do it in one dictionary instantiation, or spead it across multiple lines.

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False, read_messages=False, read_message_history=False),
        moderator_role: discord.PermissionOverwrite(manage_messages=True),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, read_message_history=True)
    }

    # or alternatively:
    overwrites = {}
    overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False, send_messages=False, read_messages=False, read_message_history=False)
    overwrites[moderator_role] = discord.PermissionOverwrite(manage_messages=True)
    overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, read_message_history=True)

    # We can now pass these to channel creation:

    await guild.create_text_channel(name="Ticket", overwrites=overwrites)

The channel created whose permissions look something like this:

.. image:: /images/guide/topics/permissions/ticket_channel.png

Using ``PermissionOverwrite`` objects for finer control over channels
----------------------------------------------------------------------

:class:`~PermissionOverwrite` makes controlling access to channels a much easier task.
Let's create a scenario where you want to "lock down" a channel, denying the ``@everyone`` role the permission to send messages.

.. code-block:: python3

    # One of the easiest ways to do this, is to get the current overwrites for the Role or Member we're editing:
    overwrite = channel.overwrites_for(guild.default_role)
    # We now have the PermissionOverwrite instance for the `@everyone` role, in the channel.

    # All we do now, is update it. There are two ways to do this:
    overwrite.send_messages = False
    # or, if you have bulk permissions to update:
    overwrite.update(send_messages=False)

    # Since we have a singular PermissionOverwrite, we want to use the `set_permissions` method of the channel:
    await channel.set_permissions(guild.default_role, overwrite=overwrite)

Now, that channel has explicitly denied the ``send_messages`` permission to the defalt role of the guild.

In an alternate scenario, let's say we want to add multiple overwrites to a channel at the same time, to deny ``add_reactions`` permissions to roles and members:

.. code-block:: python3

    # Let's make a shortcut variable to the existing overwrites.
    overwrites = channel.overwrites

    # we'll now grab the specific overwrites relating to that role and member:
    role_overwrite = channel.overwrites_for(role)
    member_overwrite = channel.overwrites_for(member)

    # edit the attribute for each specific permission
    role_overwrite.add_reactions = False
    member_overwrite.add_reactions = False
    # alternatively, if you have a bulk of permissions to update, you can use the `.update` method of them:
    role_overwrite.update(add_reaction=False)
    member_overwrite.update(add_reaction=False)

    # We now place these overwrites into the existing and working copy of the overwrites we took:
    overwrites[role] = role_overwrite
    overwrites[member] = member_overwrite

    # and edit the channel with them:
    await channel.edit(overwrites=overwrites)
