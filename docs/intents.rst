.. currentmodule:: discord
.. versionadded:: 1.5
.. _intents_primer:

A Primer to Gateway Intents
=============================

In version 1.5 comes with the introduction of :class:`Intents`. This is a radical change in how bots are written. An intent basically allows a bot to subscribe into specific buckets of events. The events that correspond to each intent is documented in the individual attribute of the :class:`Intents` documentation.

These intents are passed to the constructor of :class:`Client` or its subclasses (:class:`AutoShardedClient`, :class:`~.AutoShardedBot`, :class:`~.Bot`) with the ``intents`` argument.

If intents are not passed, then the library defaults to every intent being enabled except the privileged intents, currently :attr:`Intents.members` and :attr:`Intents.presences`.

What intents are needed?
--------------------------

The intents that are necessary for your bot can only be dictated by yourself. Each attribute in the :class:`Intents` class documents what :ref:`events <discord-api-events>` it corresponds to and what kind of cache it enables.

For example, if you want a bot that functions without spammy events like presences or typing then we could do the following:

.. code-block:: python3

    import discord
    intents = Intents(typing=False, presences=False)

Note that this doesn't enable :attr:`Intents.members` since it's a privileged intent.

Another example showing a bot that only deals with messages and guild information:

.. code-block:: python3

    import discord
    intents = discord.Intents(messages=True, guilds=True)
    # If you also want reaction events enable the following:
    # intents.reactions = True

.. _privileged_intents:

Privileged Intents
---------------------

With the API change requiring bot authors to specify intents, some intents were restricted further and require more manual steps. These intents are called **privileged intents**.

A privileged intent is one that requires you to go to the developer portal and manually enable it. To enable privileged intents do the following:

1. Make sure you're logged on to the `Discord website <https://discord.com>`_.
2. Navigate to the `application page <https://discord.com/developers/applications>`_
3. Click on the bot you want to enable privileged intents for.
4. Navigate to the bot tab on the left side of the screen.

    .. image:: /images/discord_bot_tab.png
        :alt: The bot tab in the application page.

5. Scroll down to the "Privileged Gateway Intents" section and enable the ones you want.

    .. image:: /images/discord_privileged_intents.png
        :alt: The privileged gateway intents selector.

.. warning::

    Enabling privileged intents when your bot is in over 100 guilds requires going through `bot verification <https://support.discord.com/hc/en-us/articles/360040720412>`_. If your bot is already verified and you would like to enable a privileged intent you must go through `discord support <https://dis.gd/contact>`_ and talk to them about it.

Do I need privileged intents?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a quick checklist to see if you need specific privileged intents.

Presence Intent
+++++++++++++++++

- Whether you use :attr:`Member.status` at all to track member statuses.
- Whether you use :attr:`Member.activity` or :attr:`Member.activities` to check member's activities.

Member Intent
+++++++++++++++

- Whether you track member joins or member leaves, corresponds to :func:`on_member_join` and :func:`on_member_remove` events.
- Whether you want to track member updates such as nickname or role changes.
- Whether you want to track user updates such as usernames, avatars, discriminators, etc.
- Whether you want to request the guild member list through :meth:`Guild.chunk` or :meth:`Guild.fetch_members`.
- Whether you want high accuracy member cache under :attr:`Guild.members`.

Member Cache
-------------

Along with intents, Discord now further restricts the ability to cache members and expects bot authors to cache as little as is necessary. However, to properly maintain a cache the :attr:`Intents.members` intent is required in order to track the members who left and properly evict them.

To aid with member cache where we don't need members to be cached, the library now has a :class:`MemberCacheFlags` flag to control the member cache. The documentation page for the class goes over the specific policies that are possible.

It should be noted that certain things do not need a member cache since Discord will provide full member information if possible. For example:

- :func:`on_message` will have :attr:`Message.author` be a member even if cache is disabled.
- :func:`on_voice_state_update` will have the ``member`` parameter be a member even if cache is disabled.
- :func:`on_reaction_add` will have the ``user`` parameter be a member even if cache is disabled.
- :func:`on_raw_reaction_add` will have :attr:`RawReactionActionEvent.member` be a member even if cache is disabled.
- The reaction removal events do not have the member information. This is a Discord limitation.

Other events that take a :class:`Member` will require the use of the member cache. If absolute accuracy over the member cache is desirable, then it is advisable to have the :attr:`Intents.members` intent enabled.
