.. currentmodule:: discord

``discord.app_commands`` -- Slash commands framework
=====================================================

.. versionadded:: 2.0

Appliation commands provide a robust framework for developing interactive slash commands. Unlike :ref:`discord.ext.commands <ext_commands_commands>`, aka prefix commands, ``discord.app_commands`` utilizes :ref:`Discord's Interactions API <discord_interactions_api>`.

This implementation makes extensive use of webhooks to offer advanced features and interaction mechanisms. App commands provide advanced features such as:

- Auto-completetion of command arguments
- Argument desciptors while the user is typing the command
- Messages that are only visible to the user invoking the interaction
    - Created using ``ephemeral=True`` and only if the type of webhook is :attr:`WebhookType.application`
