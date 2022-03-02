.. currentmodule:: discord

.. _guide_audit_logs:

Audit Logs
============

Audit logs log various administrative actions taken in a guild. Examples include:

- When a channel is created, updated, or deleted
- When channel-specific permissions are created, updated, or deleted
- When a member is kicked, pruned, banned, unbanned, updated, has their roles changed, or is moved or disconnected from a voice channel
- When a bot is added to the guild
- When a role is created, updated, or deleted
- When an invite is created, updated, or deleted
- When a webhook is created, updated, or deleted
- When an emoji is created, updated, or deleted
- When a message is deleted, bulk-deleted, pinned, or unpinned
- When a guild integration is created, updated, or deleted
- When a stage instance is created, updated, or deleted
- When a sticker is created, updated, or deleted
- When a scheduled event is created, updated, or deleted
- When a thread is created, updated, or deleted
    
Depending on the action taken, an entry in the audit log may contain additional info about that specific action, including:

- The id of a channel, member, message, or role involved in the action
- The number of entities targeted by the action
- A number representing the number of days a member needed to be inactive for to be pruned
- The number of members removed by a prune action
- A role name
- A type representing what the changed entity is.

