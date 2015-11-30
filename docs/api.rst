.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    discord.py.


Client
-------

.. autoclass:: Client
    :members:

.. _discord-api-events:

Event Reference
~~~~~~~~~~~~~~~~

This page outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import discord

    class MyClient(discord.Client):
        def on_message(self, message):
            self.send_message(message.channel, 'Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignore the exception.

.. versionadded:: 0.7.0
    Subclassing to listen to events.


.. function:: on_ready()

    Called when the client is done preparing the data received from Discord. Usually after login is successful
    and the :attr:`Client.servers` and co. are filled up.

.. function:: on_error(event, \*args, \*\*kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    supress the default action of printing the traceback.

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

.. function:: on_socket_opened()

    Called whenever the websocket is successfully opened. This is not the same thing as being ready.
    For that, use :func:`on_ready`.

.. function:: on_socket_closed()

    Called whenever the websocket is closed, through an error or otherwise.

.. function:: on_socket_update(event, data)

    Called whenever a recognised websocket event is found. This function would normally be not be
    called as there are higher level events in the library such as :func:`on_message`.

    :param str event: The string of the event received. e.g. ``READY``.
    :param data: The data associated with the socket event. Usually a ``dict``.

.. function:: on_socket_response(response)

    Called whenever a message is received from the websocket. Used mainly for debugging purposes.
    The parameter passed is raw data that was parsed via ``json.loads``. Note that this is called
    before the :class:`Client` processes the event.

    :param response: The received message response after gone through ``json.loads``.

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is received from the websocket, before
    it's processed. Unlike ``on_socket_response`` this event is always
    dispatched when a message is received and the passed data is not
    processed in any way.

    This is only really useful for grabing the websocket stream and
    debugging purposes.

    :param msg: The message passed on from the ws4py library. Can be an
        instance of either ws4py.messaging.TextMessage, or
        ws4py.messaging.BinaryMessage.

.. function:: on_socket_raw_send(payload, binary=False)

    Called whenever a send operation is done on the websocket before the
    message is sent. The passed parameter is the message that is to
    sent to the websocket.

    This is only really useful for grabing the websocket stream and
    debugging purposes.

    .. note::

        If the ``payload`` parameter is mutable, and modified during the
        execution of this event, then the actual data sent out on the
        websocket will be mangled. This is especially true if
        ``payload`` is a generator, as reading them modifies their
        state.

    :param payload: The message that is about to be passed on to the
        ws4py library. It can be any of a string, a bytearray, an
        instance of ws4py.message.Message and a generator.
    :param bool binary: True if the message being sent out is marked as
        binary.

.. function:: on_message_delete(message)
              on_message_edit(before, after)

    Called when a message is deleted or edited from any given server. If the message is not found in the
    :attr:`Client.messages` cache, then these events will not be called. This happens if the message
    is too old or the client is participating in high traffic servers. To fix this, increase
    the ``max_length`` option of :class:`Client`.

    :param message: A :class:`Message` of the deleted message.
    :param before: A :class:`Message` of the previous version of the message.
    :param after: A :class:`Message` of the current version of the message.

.. function:: on_status(member, old_game_id, old_status)

    Called whenever a :class:`Member` changes their status or game playing status.

    :param member: The :class:`Member` who has had their status changed.
    :param old_game_id: The game ID the member had before it changed.
    :param old_status: The status the member had before it changed.

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

.. function:: on_member_update(before, after)

    Called when a :class:`Member` updates their profile.

    This is called when one or more of the following things change:

    - status
    - game playing
    - avatar
    - nickname

    :param before: The :class:`Member` that updated their profile with the old info.
    :param after: The :class:`Member` that updated their profile with the updated info.

.. function:: on_server_join(server)

    Called when a :class:`Server` is either created by the :class:`Client` or when the
    :class:`Client` joins a server.

    :param server: The class:`Server` that was joined.

.. function:: on_server_remove(server)

    Called when a :class:`Server` is removed from the :class:`Client`.

    This happens through, but not limited to, these circumstances:

    - The client got banned.
    - The client got kicked.
    - The client left the server.
    - The client or the server owner deleted the server.

    In order for this event to be invoked then the :class:`Client` must have
    been part of the server to begin with. (i.e. it is part of :attr:`Client.servers`)

    :param server: The :class:`Server` that got removed.

.. function:: on_server_role_create(server, role)
              on_server_role_delete(server, role)

    Called when a :class:`Server` creates or deletes a new :class:`Role`.

    :param server: The :class:`Server` that was created or deleted.
    :param role: The :class:`Role` that was created or deleted.

.. function:: on_server_role_update(role)

    Called when a :class:`Role` is changed server-wide.

    :param role: The :class:`Role` that was updated.

.. function:: on_server_available(server)
              on_server_unavailable(server)

    Called when a server becomes available or unavailable. The server must have
    existed in the :attr:`Client.servers` cache.

    :param server: The :class:`Server` that has changed availability.

.. function:: on_voice_state_update(member)

    Called when a :class:`Member` changes their voice state.

    The following, but not limited to, examples illustrate when this event is called:

    - A member joins a voice room.
    - A member leaves a voice room.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a server administrator.

    :param member: The :class:`Member` whose voice state changed.

.. function:: on_typing(channel, user, when)

    Called when someone begins typing a message.

    The ``channel`` parameter could either be a :class:`PrivateChannel` or a
    :class:`Channel`. If ``channel`` is a :class:`PrivateChannel` then the
    ``user`` parameter is a :class:`User`, otherwise it is a :class:`Member`.

    :param channel: The location where the typing originated from.
    :param user: The user that started typing.
    :param when: A ``datetime.datetime`` object representing when typing started.


Utility Functions
-----------------

.. autofunction:: discord.utils.find


Data Classes
--------------

Some classes are just there to be data containers, this lists them.

.. note::

    With the exception of :class:`Object`, :class:`Colour`, and :class:`Permissions` the
    data classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.

    If you want to get one of these data classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of data classes that you receive from the events specified in the
    :ref:`discord-api-events`.

.. autoclass:: Object
    :members:

.. autoclass:: User
    :members:

.. autoclass:: Message
    :members:

.. autoclass:: Server
    :members:

.. autoclass:: Member
    :members:

.. autoclass:: Colour
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

.. autoexception:: DiscordException

.. autoexception:: ClientException

.. autoexception:: LoginFailure

.. autoexception:: HTTPException
    :members:

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

