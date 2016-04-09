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

Version Related Info
---------------------

There are two main ways to query version information about the library.

.. data:: version_info

    A named tuple that is similar to `sys.version_info`_.

    Just like `sys.version_info`_ the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

    .. _sys.version_info: https://docs.python.org/3.5/library/sys.html#sys.version_info

.. data:: __version__

    A string representation of the version. e.g. ``'0.10.0-alpha0'``.


Client
-------

.. autoclass:: Client
    :members:


Voice
-----

.. autoclass:: VoiceClient
    :members:


Opus Library
~~~~~~~~~~~~~

.. autofunction:: discord.opus.load_opus

.. autofunction:: discord.opus.is_loaded

.. _discord-api-events:

Event Reference
---------------

This page outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import discord

    class MyClient(discord.Client):

        @asyncio.coroutine
        def on_message(self, message):
            yield from self.send_message(message.channel, 'Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignore the exception.

.. warning::

    All the events must be a |corourl|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must either be decorated
    with ``@asyncio.coroutine`` or in Python 3.5+ be defined using the ``async def``
    declaration.

    The following two functions are examples of coroutine functions: ::

        async def on_ready():
            pass

        @asyncio.coroutine
        def on_ready():
            pass

    Since this can be a potentially common mistake, there is a helper
    decorator, :meth:`Client.async_event` to convert a basic function
    into a coroutine and an event at the same time. Note that it is
    not necessary if you use ``async def``.

.. versionadded:: 0.7.0
    Subclassing to listen to events.

.. function:: on_ready()

    Called when the client is done preparing the data received from Discord. Usually after login is successful
    and the :attr:`Client.servers` and co. are filled up.

    .. warning::

        This function is not guaranteed to be the first event called.

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

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is received from the websocket, before
    it's processed.This event is always dispatched when a message is
    received and the passed data is not processed in any way.

    This is only really useful for grabbing the websocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
        websocket. The voice websocket will not trigger this event.

    :param msg: The message passed in from the websocket library.
                Could be ``bytes`` for a binary message or ``str``
                for a regular message.

.. function:: on_socket_raw_send(payload)

    Called whenever a send operation is done on the websocket before the
    message is sent. The passed parameter is the message that is to
    sent to the websocket.

    This is only really useful for grabbing the websocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
        websocket. The voice websocket will not trigger this event.

    :param payload: The message that is about to be passed on to the
                    websocket library. It can be ``bytes`` to denote a binary
                    message or ``str`` to denote a regular text message.

.. function:: on_message_delete(message)
              on_message_edit(before, after)

    Called when a message is deleted or edited from any given server. If the message is not found in the
    :attr:`Client.messages` cache, then these events will not be called. This happens if the message
    is too old or the client is participating in high traffic servers. To fix this, increase
    the ``max_length`` option of :class:`Client`.

    :param message: A :class:`Message` of the deleted message.
    :param before: A :class:`Message` of the previous version of the message.
    :param after: A :class:`Message` of the current version of the message.

.. function:: on_channel_delete(channel)
              on_channel_create(channel)

    Called whenever a channel is removed or added from a server.

    Note that you can get the server from :attr:`Channel.server`.
    :func:`on_channel_create` could also pass in a :class:`PrivateChannel` depending
    on the value of :attr:`Channel.is_private`.

    :param channel: The :class:`Channel` that got added or deleted.

.. function:: on_channel_update(before, after)

    Called whenever a channel is updated. e.g. changed name, topic, permissions.

    :param before: The :class:`Channel` that got updated with the old info.
    :param after: The :class:`Channel` that got updated with the updated info.

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
    - roles

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

.. function:: on_server_update(before, after)

    Called when a :class:`Server` updates, for example:

    - Changed name
    - Changed AFK channel
    - Changed AFK timeout
    - etc

    :param before: The :class:`Server` prior to being updated.
    :param after: The :class:`Server` after being updated.

.. function:: on_server_role_create(server, role)
              on_server_role_delete(server, role)

    Called when a :class:`Server` creates or deletes a new :class:`Role`.

    :param server: The :class:`Server` that was created or deleted.
    :param role: The :class:`Role` that was created or deleted.

.. function:: on_server_role_update(before, after)

    Called when a :class:`Role` is changed server-wide.

    :param before: The :class:`Role` that updated with the old info.
    :param after: The :class:`Role` that updated with the updated info

.. function:: on_server_available(server)
              on_server_unavailable(server)

    Called when a server becomes available or unavailable. The server must have
    existed in the :attr:`Client.servers` cache.

    :param server: The :class:`Server` that has changed availability.

.. function:: on_voice_state_update(before, after)

    Called when a :class:`Member` changes their voice state.

    The following, but not limited to, examples illustrate when this event is called:

    - A member joins a voice room.
    - A member leaves a voice room.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a server administrator.

    :param before: The :class:`Member` whose voice state changed prior to the changes.
    :param after: The :class:`Member` whose voice state changed after the changes.

.. function:: on_member_ban(member)

    Called when a :class:`Member` gets banned from a :class:`Server`.

    You can access the server that the member got banned from via :attr:`Member.server`.

    :param member: The member that got banned.

.. function:: on_member_unban(server, user)

    Called when a :class:`User` gets unbanned from a :class:`Server`.

    :param server: The server the user got unbanned from.
    :param user: The user that got unbanned.

.. function:: on_typing(channel, user, when)

    Called when someone begins typing a message.

    The ``channel`` parameter could either be a :class:`PrivateChannel` or a
    :class:`Channel`. If ``channel`` is a :class:`PrivateChannel` then the
    ``user`` parameter is a :class:`User`, otherwise it is a :class:`Member`.

    :param channel: The location where the typing originated from.
    :param user: The user that started typing.
    :param when: A ``datetime.datetime`` object representing when typing started.

.. _discord-api-utils:

Utility Functions
-----------------

.. autofunction:: discord.utils.find

.. autofunction:: discord.utils.get

.. autofunction:: discord.utils.snowflake_time

.. autofunction:: discord.utils.oauth_url

.. _discord-api-enums:

Enumerations
-------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of `enum`_.

.. _enum: https://docs.python.org/3/library/enum.html

.. class:: ChannelType

    Specifies the type of :class:`Channel`.

    .. attribute:: text

        A text channel.
    .. attribute:: voice

        A voice channel.

.. class:: ServerRegion

    Specifies the region a :class:`Server`'s voice server belongs to.

    .. attribute:: us_west

        The US West region.
    .. attribute:: us_east

        The US East region.
    .. attribute:: singapore

        The Singapore region.
    .. attribute:: london

        The London region.
    .. attribute:: sydney

        The Sydney region.
    .. attribute:: amsterdam

        The Amsterdam region.
    .. attribute:: frankfurt

        The Frankfurt region.

.. class:: Status

    Specifies a :class:`Member` 's status.

    .. attribute:: online

        The member is online.
    .. attribute:: offline

        The member is offline.
    .. attribute:: idle

        The member is idle.

.. _discord_api_data:

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


.. warning::

    Nearly all data classes here have ``__slots__`` defined which means that it is
    impossible to have dynamic attributes to the data classes. The only exception
    to this rule is :class:`Object` which was designed with dynamic attributes in
    mind.

    More information about ``__slots__`` can be found
    `in the official python documentation <https://docs.python.org/3/reference/datamodel.html#slots>`_.

Object
~~~~~~~

.. autoclass:: Object
    :members:

User
~~~~~

.. autoclass:: User
    :members:

Message
~~~~~~~

.. autoclass:: Message
    :members:

Server
~~~~~~

.. autoclass:: Server
    :members:

Member
~~~~~~

.. autoclass:: Member
    :members:

Colour
~~~~~~

.. autoclass:: Colour
    :members:

Game
~~~~

.. autoclass:: Game
    :members:

Role
~~~~~

.. autoclass:: Role
    :members:

Permissions
~~~~~~~~~~~~

.. autoclass:: Permissions
    :members:

Channel
~~~~~~~~

.. autoclass:: Channel
    :members:

PrivateChannel
~~~~~~~~~~~~~~~

.. autoclass:: PrivateChannel
    :members:

Invite
~~~~~~~

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

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: discord.opus.OpusError

.. autoexception:: discord.opus.OpusNotLoaded
