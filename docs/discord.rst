.. _discord-intro:

Creating a Bot Account
========================

In order to work with the library and the Discord API in general, we must first create a Discord Bot account.

Creating a Bot account is a pretty straightforward process.

1. Make sure you're logged on to the `Discord website <https://discord.com>`_.
2. Navigate to the `application page <https://discord.com/developers/applications>`_
3. Click on the "New Application" button.

    .. image:: /images/discord_create_app_button.png
        :alt: The new application button.

4. Give the application a name and click "Create".

    .. image:: /images/discord_create_app_form.png
        :alt: The new application form filled in.

5. Create a Bot User by navigating to the "Bot" tab and clicking "Add Bot".

    - Click "Yes, do it!" to continue.

    .. image:: /images/discord_create_bot_user.png
        :alt: The Add Bot button.
6. Make sure that **Public Bot** is ticked if you want others to invite your bot.

    - You should also make sure that **Require OAuth2 Code Grant** is unchecked unless you
      are developing a service that needs it. If you're unsure, then **leave it unchecked**.

    .. image:: /images/discord_bot_user_options.png
        :alt: How the Bot User options should look like for most people.

7. Copy the token using the "Copy" button.

    - **This is not the Client Secret at the General Information page.**

    .. warning::

        It should be worth noting that this token is essentially your bot's
        password. You should **never** share this to someone else. In doing so,
        someone can log in to your bot and do malicious things, such as leaving
        servers, ban all members inside a server, or pinging everyone maliciously.

        The possibilities are endless, so **do not share this token.**

        If you accidentally leaked your token, click the "Regenerate" button as soon
        as possible. This revokes your old token and re-generates a new one.
        Now you need to use the new token to login.

And that's it. You now have a bot account and you can login with that token.

.. _discord_invite_bot:

Inviting Your Bot
-------------------

So you've made a Bot User but it's not actually in any server.

If you want to invite your bot you must create an invite URL for it.

1. Make sure you're logged on to the `Discord website <https://discord.com>`_.
2. Navigate to the `application page <https://discord.com/developers/applications>`_
3. Click on your bot's page.
4. Go to the "OAuth2" tab.

    .. image:: /images/discord_oauth2.png
        :alt: How the OAuth2 page should look like.

5. Tick the "bot" checkbox under "scopes".

    .. image:: /images/discord_oauth2_scope.png
        :alt: The scopes checkbox with "bot" ticked.

6. Tick the permissions required for your bot to function under "Bot Permissions".

    - Please be aware of the consequences of requiring your bot to have the "Administrator" permission.

    - Bot owners must have 2FA enabled for certain actions and permissions when added in servers that have Server-Wide 2FA enabled. Check the `2FA support page <https://support.discord.com/hc/en-us/articles/219576828-Setting-up-Two-Factor-Authentication>`_ for more information.

    .. image:: /images/discord_oauth2_perms.png
        :alt: The permission checkboxes with some permissions checked.

7. Now the resulting URL can be used to add your bot to a server. Copy and paste the URL into your browser, choose a server to invite the bot to, and click "Authorize".


.. note::

    The person adding the bot needs "Manage Server" permissions to do so.

If you want to generate this URL dynamically at run-time inside your bot and using the
:class:`discord.Permissions` interface, you can use :func:`discord.utils.oauth_url`.
