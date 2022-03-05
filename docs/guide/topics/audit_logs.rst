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

Getting Audit Logs
~~~~~~~~~~~~~~~~~~~~

Audit logs can be retrieved via :func:`guild.audit_logs`, assuming you have the :attr:`~Permissions.view_audit_log` permission. 

Note that this function returns an :term:`AsyncIterator` and so to properly go through the audit logs retrieved, you will need to do the following:

.. code-block:: python3

    async for entry in guild.audit_logs():
        print('{0.user} did {0.action} to {0.target}'.format(entry))

Each entry is an instance of :class:`AuditLogEntry`, which contains information about that particular entry, including:

- Reason
- When it was created
- What category the action falls into
- A list of changes in this entry
- The state of the target before and after this action occurred
- Any extra data provided about the action


It is possible to sort the audit logs by oldest first, as well as to filter the audit logs by:

- Limiting the number of entries with the :code:`limit` parameter
- Date/time using either :class:`abc.Snowflake` or :code:`datetime.datetime` with the :code:`before` or :code:`after` parameters
- User the entry was created by
- A specific :class:`AuditLogAction`

You can find more information on the audit logs in the documentation for :meth:`~Guild.audit_logs`, :class:`AuditLogEntry`, :class:`AuditLogAction`, :class:`AuditLogActionCategory`, :class:`AuditLogChanges`, and :class:`AuditLogDiff`.