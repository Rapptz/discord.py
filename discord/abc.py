# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import abc
import io
import os
import asyncio

from collections import namedtuple

from .iterators import LogsFromIterator
from .context_managers import Typing
from .errors import ClientException, NoMoreMessages, InvalidArgument
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from . import utils, compat

class _Undefined:
    def __repr__(self):
        return 'see-below'

_undefined = _Undefined()

class Snowflake(metaclass=abc.ABCMeta):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def created_at(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Snowflake:
            mro = C.__mro__
            for attr in ('created_at', 'id'):
                for base in mro:
                    if attr in base.__dict__:
                        break
                else:
                    return NotImplemented
            return True
        return NotImplemented

class User(metaclass=abc.ABCMeta):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def display_name(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def mention(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is User:
            if Snowflake.__subclasshook__(C) is NotImplemented:
                return NotImplemented

            mro = C.__mro__
            for attr in ('display_name', 'mention', 'name', 'avatar', 'discriminator', 'bot'):
                for base in mro:
                    if attr in base.__dict__:
                        break
                else:
                    return NotImplemented
            return True
        return NotImplemented

class PrivateChannel(metaclass=abc.ABCMeta):
    __slots__ = ()

    @classmethod
    def __subclasshook__(cls, C):
        if cls is PrivateChannel:
            if Snowflake.__subclasshook__(C) is NotImplemented:
                return NotImplemented

            mro = C.__mro__
            for base in mro:
                if 'me' in base.__dict__:
                    return True
            return NotImplemented
        return NotImplemented

_Overwrites = namedtuple('_Overwrites', 'id allow deny type')

class GuildChannel:
    __slots__ = ()

    def __str__(self):
        return self.name

    @asyncio.coroutine
    def _move(self, position):
        if position < 0:
            raise InvalidArgument('Channel position cannot be less than 0.')

        http = self._state.http
        url = '{0}/{1.guild.id}/channels'.format(http.GUILDS, self)
        channels = [c for c in self.guild.channels if isinstance(c, type(self))]

        if position >= len(channels):
            raise InvalidArgument('Channel position cannot be greater than {}'.format(len(channels) - 1))

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # not there somehow lol
            return
        else:
            # add ourselves at our designated position
            channels.insert(position, self)

        payload = [{'id': c.id, 'position': index } for index, c in enumerate(channels)]
        yield from http.patch(url, json=payload, bucket='move_channel')

    def _fill_overwrites(self, data):
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get('permission_overwrites', [])):
            overridden_id = int(overridden.pop('id'))
            self._overwrites.append(_Overwrites(id=overridden_id, **overridden))

            if overridden['type'] == 'member':
                continue

            if overridden_id == everyone_id:
                # the @everyone role is not guaranteed to be the first one
                # in the list of permission overwrites, however the permission
                # resolution code kind of requires that it is the first one in
                # the list since it is special. So we need the index so we can
                # swap it to be the first one.
                everyone_index = index

        # do the swap
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    @property
    def changed_roles(self):
        """Returns a list of :class:`Roles` that have been overridden from
        their default values in the :attr:`Guild.roles` attribute."""
        ret = []
        for overwrite in filter(lambda o: o.type == 'role', self._overwrites):
            role = utils.get(self.guild.roles, id=overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def is_default(self):
        """bool : Indicates if this is the default channel for the :class:`Guild` it belongs to."""
        return self.guild.id == self.id

    @property
    def mention(self):
        """str : The string that allows you to mention the channel."""
        return '<#{0.id}>'.format(self)

    @property
    def created_at(self):
        """Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def overwrites_for(self, obj):
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        -----------
        obj
            The :class:`Role` or :class:`Member` or :class:`Object` denoting
            whose overwrite to get.

        Returns
        ---------
        :class:`PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, Member):
            predicate = lambda p: p.type == 'member'
        elif isinstance(obj, Role):
            predicate = lambda p: p.type == 'role'
        else:
            predicate = lambda p: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    @property
    def overwrites(self):
        """Returns all of the channel's overwrites.

        This is returned as a list of two-element tuples containing the target,
        which can be either a :class:`Role` or a :class:`Member` and the overwrite
        as the second element as a :class:`PermissionOverwrite`.

        Returns
        --------
        List[Tuple[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]]:
            The channel's permission overwrites.
        """
        ret = []
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)

            if ow.type == 'role':
                # accidentally quadratic
                target = utils.find(lambda r: r.id == ow.id, self.guild.roles)
            elif ow.type == 'member':
                target = self.guild.get_member(ow.id)

            ret.append((target, overwrite))
        return ret

    def permissions_for(self, member):
        """Handles permission resolution for the current :class:`Member`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides
        - Whether the channel is the default channel.

        Parameters
        ----------
        member : :class:`Member`
            The member to resolve permissions for.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions for the member.
        """

        # The current cases can be explained as:
        # Guild owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done.. you have to do the following:

        # If manage permissions is True, then all permissions are set to
        # True. If the channel is the default channel then everyone gets
        # read permissions regardless.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if member.id == self.guild.owner.id:
            return Permissions.all()

        default = self.guild.default_role
        base = Permissions(default.permissions.value)

        # Apply guild roles that the member has.
        for role in member.roles:
            base.value |= role.permissions.value

        # Guild-wide Administrator -> True for everything
        # Bypass all channel-specific overrides
        if base.administrator:
            return Permissions.all()

        member_role_ids = set(map(lambda r: r.id, member.roles))
        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in self._overwrites:
            if overwrite.type == 'role' and overwrite.id in member_role_ids:
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in self._overwrites:
            if overwrite.type == 'member' and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        # default channels can always be read
        if self.is_default:
            base.read_messages = True

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        return base

    @asyncio.coroutine
    def delete(self):
        """|coro|

        Deletes the channel.

        You must have Manage Channel permission to use this.

        Raises
        -------
        Forbidden
            You do not have proper permissions to delete the channel.
        NotFound
            The channel was not found or was already deleted.
        HTTPException
            Deleting the channel failed.
        """
        yield from self._state.http.delete_channel(self.id)

    @asyncio.coroutine
    def set_permissions(self, target, *, overwrite=_undefined, **permissions):
        """|coro|

        Sets the channel specific permission overwrites for a target in the
        channel.

        The ``target`` parameter should either be a :class:`Member` or a
        :class:`Role` that belongs to guild.

        The ``overwrite`` parameter, if given, must either be ``None`` or
        :class:`PermissionOverwrite`. For convenience, you can pass in
        keyword arguments denoting :class:`Permissions` attributes. If this is
        done, then you cannot mix the keyword arguments with the ``overwrite``
        parameter.

        If the ``overwrite`` parameter is ``None``, then the permission
        overwrites are deleted.

        You must have :attr:`Permissions.manage_roles` permission to use this.

        Examples
        ----------

        Setting allow and deny: ::

            await message.channel.set_permissions(message.author, read_messages=True,
                                                                  send_messages=False)

        Deleting overwrites ::

            await channel.set_permissions(member, overwrite=None)

        Using :class:`PermissionOverwrite` ::

            overwrite = PermissionOverwrite()
            overwrite.send_messages = False
            overwrite.read_messages = True
            await channel.set_permissions(member, overwrite=overwrite)

        Parameters
        -----------
        target
            The :class:`Member` or :class:`Role` to overwrite permissions for.
        overwrite: :class:`PermissionOverwrite`
            The permissions to allow and deny to the target.
        \*\*permissions
            A keyword argument list of permissions to set for ease of use.
            Cannot be mixed with ``overwrite``.

        Raises
        -------
        Forbidden
            You do not have permissions to edit channel specific permissions.
        HTTPException
            Editing channel specific permissions failed.
        InvalidArgument
            The overwrite parameter invalid or the target type was not
            :class:`Role` or :class:`Member`.
        """

        http = self._state.http

        if isinstance(target, User):
            perm_type = 'member'
        elif isinstance(target, Role):
            perm_type = 'role'
        else:
            raise InvalidArgument('target parameter must be either Member or Role')

        if isinstance(overwrite, _Undefined):
            if len(permissions) == 0:
                raise InvalidArgument('No overwrite provided.')
            try:
                overwrite = PermissionOverwrite(**permissions)
            except:
                raise InvalidArgument('Invalid permissions given to keyword arguments.')
        else:
            if len(permissions) > 0:
                raise InvalidArgument('Cannot mix overwrite and keyword arguments.')

        # TODO: wait for event

        if overwrite is None:
            yield from http.delete_channel_permissions(self.id, target.id)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            yield from http.edit_channel_permissions(self.id, target.id, allow.value, deny.value, perm_type)
        else:
            raise InvalidArgument('Invalid overwrite type provided.')


class Messageable(metaclass=abc.ABCMeta):
    __slots__ = ()

    @asyncio.coroutine
    @abc.abstractmethod
    def _get_channel(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _get_guild_id(self):
        raise NotImplementedError

    @asyncio.coroutine
    def send(self, content=None, *, tts=False, embed=None, file=None, filename=None, delete_after=None):
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        The ``file`` parameter should be either a string denoting the location for a
        file or a *file-like object*. The *file-like object* passed is **not closed**
        at the end of execution. You are responsible for closing it yourself.

        .. note::

            If the file-like object passed is opened via ``open`` then the modes
            'rb' should be used.

        The ``filename`` parameter is the filename of the file.
        If this is not given then it defaults to ``file.name`` or if ``file`` is a string
        then the ``filename`` will default to the string given. You can overwrite
        this value by passing this in.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type.

        Parameters
        ------------
        content
            The content of the message to send.
        tts: bool
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`Embed`
            The rich embed for the content.
        file: file-like object or filename
            The *file-like object* or file path to send.
        filename: str
            The filename of the file. Defaults to ``file.name`` if it's available.
            If this is provided, you must also provide the ``file`` parameter or it
            is silently ignored.
        delete_after: float
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.

        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.

        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel = yield from self._get_channel()
        guild_id = self._get_guild_id()
        state = self._state
        content = str(content) if content is not None else None
        if embed is not None:
            embed = embed.to_dict()

        if file is not None:
            try:
                with open(file, 'rb') as f:
                    buffer = io.BytesIO(f.read())
                    if filename is None:
                        _, filename = os.path.split(file)
            except TypeError:
                buffer = file

            data = yield from state.http.send_file(channel.id, buffer, guild_id=guild_id, filename=filename,
                                                   content=content, tts=tts, embed=embed)
        else:
            data = yield from state.http.send_message(channel.id, content, guild_id=guild_id, tts=tts, embed=embed)

        ret = state.create_message(channel=channel, data=data)
        if delete_after is not None:
            @asyncio.coroutine
            def delete():
                yield from asyncio.sleep(delete_after, loop=state.loop)
                try:
                    yield from ret.delete()
                except:
                    pass
            compat.create_task(delete(), loop=state.loop)
        return ret

    @asyncio.coroutine
    def trigger_typing(self):
        """|coro|

        Triggers a *typing* indicator to the destination.

        *Typing* indicator will go away after 10 seconds, or after a message is sent.
        """

        channel = yield from self._get_channel()
        yield from self._state.http.send_typing(channel.id)

    def typing(self):
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        .. note::

            This is both a regular context manager and an async context manager.
            This means that both ``with`` and ``async with`` work with this.

        Example Usage: ::

            with channel.typing():
                # do expensive stuff here
                await channel.send_message('done!')

        """
        return Typing(self)

    @asyncio.coroutine
    def get_message(self, id):
        """|coro|

        Retrieves a single :class:`Message` from the destination.

        This can only be used by bot accounts.

        Parameters
        ------------
        id: int
            The message ID to look for.

        Returns
        --------
        :class:`Message`
            The message asked for.

        Raises
        --------
        NotFound
            The specified message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.
        """

        channel = yield from self._get_channel()
        data = yield from self._state.http.get_message(channel.id, id)
        return state.create_message(channel=channel, data=data)

    @asyncio.coroutine
    def delete_messages(self, messages):
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        Usable only by bot accounts.

        Parameters
        -----------
        messages : iterable of :class:`Message`
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete is less than 2 or more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
        HTTPException
            Deleting the messages failed.
        """

        messages = list(messages)
        if len(messages) > 100 or len(messages) < 2:
            raise ClientException('Can only delete messages in the range of [2, 100]')

        message_ids = [m.id for m in messages]
        channel = yield from self._get_channel()
        guild_id = self._get_guild_id()

        yield from self._state.http.delete_messages(channel.id, message_ids, guild_id)

    @asyncio.coroutine
    def pins(self):
        """|coro|

        Returns a list of :class:`Message` that are currently pinned.

        Raises
        -------
        HTTPException
            Retrieving the pinned messages failed.
        """

        channel = yield from self._get_channel()
        state = self._state
        data = yield from state.http.pins_from(channel.id)
        return [state.create_message(channel=channel, data=m) for m in data]

    def history(self, *, limit=100, before=None, after=None, around=None, reverse=None):
        """Return an async iterator that enables receiving the destination's message history.

        You must have Read Message History permissions to use this.

        All parameters are optional.

        Parameters
        -----------
        limit: int
            The number of messages to retrieve.
        before: :class:`Message` or `datetime`
            Retrieve messages before this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: :class:`Message` or `datetime`
            Retrieve messages after this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        around: :class:`Message` or `datetime`
            Retrieve messages around this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
            When using this argument, the maximum limit is 101. Note that if the limit is an
            even number then this will return at most limit + 1 messages.
        reverse: bool
            If set to true, return messages in oldest->newest order. If unspecified,
            this defaults to ``False`` for most cases. However if passing in a
            ``after`` parameter then this is set to ``True``. This avoids getting messages
            out of order in the ``after`` case.

        Raises
        ------
        Forbidden
            You do not have permissions to get channel message history.
        HTTPException
            The request to get message history failed.

        Yields
        -------
        :class:`Message`
            The message with the message data parsed.

        Examples
        ---------

        Usage ::

            counter = 0
            async for message in channel.history(limit=200):
                if message.author == client.user:
                    counter += 1

        Python 3.4 Usage ::

            count = 0
            iterator = channel.history(limit=200)
            while True:
                try:
                    message = yield from iterator.get()
                except discord.NoMoreMessages:
                    break
                else:
                    if message.author == client.user:
                        counter += 1
        """
        return LogsFromIterator(self, limit=limit, before=before, after=after, around=around, reverse=reverse)

    @asyncio.coroutine
    def purge(self, *, limit=100, check=None, before=None, after=None, around=None):
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have :attr:`Permissions.manage_messages` permission to
        delete messages even if they are your own. The
        :attr:`Permissions.read_message_history` permission is also needed to
        retrieve message history.

        Usable only by bot accounts.

        Parameters
        -----------
        limit: int
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: predicate
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before
            Same as ``before`` in :meth:`history`.
        after
            Same as ``after`` in :meth:`history`.
        around
            Same as ``around`` in :meth:`history`.

        Raises
        -------
        Forbidden
            You do not have proper permissions to do the actions required or
            you're not using a bot account.
        HTTPException
            Purging the messages failed.

        Examples
        ---------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send_message('Deleted {} message(s)'.format(len(deleted)))

        Returns
        --------
        list
            The list of messages that were deleted.
        """

        if check is None:
            check = lambda m: True

        iterator = self.history(limit=limit, before=before, after=after, around=around)
        ret = []
        count = 0

        while True:
            try:
                msg = yield from iterator.get()
            except NoMoreMessages:
                # no more messages to poll
                if count >= 2:
                    # more than 2 messages -> bulk delete
                    to_delete = ret[-count:]
                    yield from self.delete_messages(to_delete)
                elif count == 1:
                    # delete a single message
                    yield from ret[-1].delete()

                return ret
            else:
                if count == 100:
                    # we've reached a full 'queue'
                    to_delete = ret[-100:]
                    yield from self.delete_messages(to_delete)
                    count = 0
                    yield from asyncio.sleep(1)

                if check(msg):
                    count += 1
                    ret.append(msg)
