.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py.


Client
-------

.. autoclass:: Client
    :members:

.. _discord-api-events:

Event Reference
~~~~~~~~~~~~~~~~

This page outlines the different types of events listened to by
:meth:`Client.event`.

If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to log a traceback and ignore the exception.

.. note::

    If the Python logging module is not configured, the logs will not be
    output anywhere. Meaning that exceptions in handlers will be
    silently ignored. See :ref:`logging` for more information on how to
    set up and use the logging module with discord.py.

.. function:: on_ready()

    Called when the client is done preparing the data received from Discord. Usually after login is successful
    and the :attr:`Client.servers` and co. are filled up.

.. function:: on_disconnect()

    Called when the client disconnects for whatever reason. Be it error or manually.

.. function:: on_error(event, \*args, \*\*kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    logged and the exception is ignored. If you want to change this
    behaviour and handle the exception for whatever reason yourself,
    this event can be overridden. Which, when done, will supress the
    default logging done.

    The information of the exception rasied and the exception itself can
    be retreived with a standard call to ``sys.exc_info()``.

    If you want exception to propogate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    ``raise`` statement.  Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    :param event: The name of the event that raised the exception.
    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        execption.

.. function:: on_message(message)

    Called when a message is created and sent to a server.

    :param message: A :class:`Message` of the current message.

.. function:: on_response(response)

    Called whenever a message is received from the websocket. Used mainly for debugging purposes.
    The parameter passed is raw data that was parsed via ``json.loads``. Note that this is called
    before the :class:`Client` processes the event.

    :param response: The received message response after gone through ``json.loads``.

.. function:: on_message_delete(message)
              on_message_edit(before, after)

    Called when a message is deleted or edited from any given server. If the message is not found in the
    :attr:`Client.messages` cache, then these events will not be called. This happens if the message
    is too old or the client is participating in high traffic servers. To fix this, increase
    the ``max_length`` option of :class:`Client`.

    :param message: A :class:`Message` of the deleted message.
    :param before: A :class:`Message` of the previous version of the message.
    :param after: A :class:`Message` of the current version of the message.

.. function:: on_status(member)

    Called whenever a :class:`Member` changes their status or game playing status.

    :param server: The :class:`Member` who has had their status changed.

.. function:: on_channel_delete(channel)
              on_channel_create(channel)

    Called whenever a channel is removed or added from a server.

    Note that you can get the server from :attr:`Channel.server`.
    :func:`on_channel_create` could also pass in a :class:`PrivateChannel` depending
    on the value of :attr:`Channel.is_private`.

    :param channel: The :class:`Channel` that got added or deleted.

.. function:: on_channel_update(channel)

    Called whenever a channel is updated. e.g. changed name, topic, permissions.

    :param channel: The :class:`Channel` that got updated.

.. function:: on_member_join(member)
              on_member_remove(member)

    Called when a :class:`Member` leaves or joins a :class:`Server`.

    :param member: The :class:`Member` that joined or left.

.. function:: on_member_update(member)

    Called when a :class:`Member` updates their profile.

    :param member: The :class:`Member` that updated their profile with the updated info.

.. function:: on_server_create(server)
              on_server_delete(server)

    Called when a :class:`Server` is created or deleted.

    Note that the server that is created must belong to the :class:`Client` and the server
    that got deleted must have been part of the client's participating servers.

    :param server: The :class:`Server` that got created or deleted.


Utility Functions
-----------------

.. autofunction:: discord.utils.find


Data Classes
--------------

Some classes are just there to be data containers, this lists them. It should be assumed that *all* classes in this category are immutable and should not be modified.

.. autoclass:: User
    :members:

.. autoclass:: Message
    :members:

.. autoclass:: Server
    :members:

.. autoclass:: Member
    :members:

.. autoclass:: Role
    :members:

.. autoclass:: Permissions
    :members:

.. autoclass:: Channel
    :members:

.. autoclass:: PrivateChannel
    :members:

.. autoclass:: Invite
    :members:

Exceptions
------------

The following exceptions are thrown by the library.


.. autoclass:: InvalidEventName
    :members:

.. autoclass:: InvalidDestination
    :members:

.. autoclass:: GatewayNotFound
    :members:

