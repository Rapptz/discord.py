.. _discord-intro:

Creating a Bot Account
========================

In order to work with the library and the Discord API in general, we must first create a Discord Bot account.

Creating a Bot account is a pretty straightforward process.

1. Make sure you're logged on to the `Discord website <https://discordapp.com>`_.
2. Navigate to the `application page <https://discordapp.com/developers/applications/me>`_
3. Click on the "New App" button.

    .. image:: /images/discord_create_app_button.png
        :alt: The new app button.

4. Give the application a name and a description if wanted and click "Create App".

    - You can also put an avatar you want your bot to use, don't worry you can change this later.
    - **Leave the Redirect URI(s) blank** unless are creating a service.

    .. image:: /images/discord_create_app_form.png
        :alt: The new application form filled in.
5. Create a Bot User by clicking on the accompanying button and confirming it.

    .. image:: /images/discord_create_bot_user.png
        :alt: The Create a Bot User button.
6. Make sure that **Public Bot** is ticked if you want others to invite your bot.

    - You should also make sure that **Require OAuth2 Code Grant** is unchecked unless you
      are developing a service that needs it. If you're unsure, then **leave it unchecked**.

    .. image:: /images/discord_bot_user_options.png
        :alt: How the Bot User options should look like for most people.

7. Click to reveal the token.

    - **This is not the Client Secret**
    - Look at the image above to see where the **Token** is.

    .. warning::

        It should be worth noting that this token is essentially your bot's
        password. You should **never** share this to someone else. In doing so,
        someone can log in to your bot and do malicious things, such as leaving
        servers, ban all members inside a server, or pinging everyone maliciously.

        The possibilities are endless, so **do not share this token.**

And that's it. You now have a bot account and you can login with that token.

.. _discord_invite_bot:

Inviting Your Bot
-------------------

So you've made a Bot User but it's not actually in any server.

If you want to invite your bot you must create an invite URL for your bot.

First, you must fetch the Client ID of the Bot. You can find this in the Bot's application page.

.. image:: /images/discord_client_id.png
    :alt: The Bot's Client ID.

Copy paste that into the pre-formatted URL:

.. code-block:: none

    https://discordapp.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=0

Replace ``YOUR_CLIENT_ID`` with the Client ID we got in the previous step. For example,
in the image above our client ID is 312777964700041216 so the resulting URL would be
https://discordapp.com/oauth2/authorize?client_id=312777964700041216&scope=bot&permissions=0
(note that this bot has been deleted).

Now you can click the link and invite your bot to any server you have "Manage Server" permissions on.

Adding Permissions
~~~~~~~~~~~~~~~~~~~~

In the above URL, you might have noticed an interesting bit, the ``permissions=0`` fragment.

Bot accounts can request specific permissions to be granted upon joining. When the bot joins
the guild, they will be granted a managed role that contains the permissions you requested.
If the permissions is 0, then no special role is created.

This ``permissions`` value is calculated based on bit-wise arithmetic. Thankfully, people have
created a calculator that makes it easy to calculate the permissions necessary visually.

- https://discordapi.com/permissions.html
- https://finitereality.github.io/permissions/

Feel free to use whichever is easier for you to grasp.

If you want to generate this URL dynamically at run-time inside your bot and using the
:class:`discord.Permissions` interface, you can use :func:`discord.utils.oauth_url`.
