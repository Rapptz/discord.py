# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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
import copy
import asyncio

from collections import namedtuple

from .iterators import HistoryIterator
from .context_managers import Typing
from .errors import InvalidArgument, ClientException
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .invite import Invite
from .file import File
from .voice_client import VoiceClient
from . import utils, compat

class _Undefined:
    def __repr__(self):
        return 'see-below'

_undefined = _Undefined()

class Snowflake(metaclass=abc.ABCMeta):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    Attributes
    -----------
    id: :class:`int`
        The model's unique ID.
    """
    __slots__ = ()

    @property
    @abc.abstractmethod
    def created_at(self):
        """Returns the model's creation time in UTC."""
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
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`User`
    - :class:`ClientUser`
    - :class:`Member`

    This ABC must also implement :class:`abc.Snowflake`.

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    discriminator: :class:`str`
        The user's discriminator.
    avatar: Optional[:class:`str`]
        The avatar hash the user has.
    bot: :class:`bool`
        If the user is a bot account.
    """
    __slots__ = ()

    @property
    @abc.abstractmethod
    def display_name(self):
        """Returns the user's display name."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def mention(self):
        """Returns a string that allows you to mention the given user."""
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
    """An ABC that details the common operations on a private Discord channel.

    The following implement this ABC:

    - :class:`DMChannel`
    - :class:`GroupChannel`

    This ABC must also implement :class:`abc.Snowflake`.

    Attributes
    -----------
    me: :class:`ClientUser`
        The user presenting yourself.
    """
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
    """An ABC that details the common operations on a Discord guild channel.

    The following implement this ABC:

    - :class:`TextChannel`
    - :class:`VoiceChannel`
    - :class:`CategoryChannel`

    This ABC must also implement :class:`abc.Snowflake`.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    """
    __slots__ = ()

    def __str__(self):
        return self.name

    @asyncio.coroutine
    def _move(self, position, parent_id=None, lock_permissions=False, *, reason):
        if position < 0:
            raise InvalidArgument('Channel position cannot be less than 0.')

        http = self._state.http
        cls = type(self)
        channels = [c for c in self.guild.channels if isinstance(c, cls)]

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

        payload = []
        for index, c in enumerate(channels):
            d = {'id': c.id, 'position': index}
            if parent_id is not _undefined and c.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        yield from http.bulk_channel_update(self.guild.id, payload, reason=reason)
        self.position = position
        if parent_id is not _undefined:
            self.category_id = int(parent_id) if parent_id else None

    @asyncio.coroutine
    def _edit(self, options, reason):
        try:
            parent = options.pop('category')
        except KeyError:
            parent_id = _undefined
        else:
            parent_id = parent and parent.id

        lock_permissions = options.pop('sync_permissions', False)

        try:
            position = options.pop('position')
        except KeyError:
            if parent_id is not _undefined:
                if lock_permissions:
                    category = self.guild.get_channel(parent_id)
                    options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
                options['parent_id'] = parent_id
            elif lock_permissions and self.category_id is not None:
                # if we're syncing permissions on a pre-existing channel category without changing it
                # we need to update the permissions to point to the pre-existing category
                category = self.guild.get_channel(self.category_id)
                options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
        else:
            yield from self._move(position, parent_id=parent_id, lock_permissions=lock_permissions, reason=reason)

        if options:
            data = yield from self._state.http.edit_channel(self.id, reason=reason, **options)
            self._update(self.guild, data)

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
        """Returns a :class:`list` of :class:`Roles` that have been overridden from
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
    def mention(self):
        """:class:`str` : The string that allows you to mention the channel."""
        return '<#%s>' % self.id

    @property
    def created_at(self):
        """Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def overwrites_for(self, obj):
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        -----------
        obj
            The :class:`Role` or :class:`abc.User` denoting
            whose overwrite to get.

        Returns
        ---------
        :class:`PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, User):
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

    @property
    def category(self):
        """Optional[:class:`CategoryChannel`]: The category this channel belongs to.

        If there is no category then this is ``None``.
        """
        return self.guild.get_channel(self.category_id)

    def permissions_for(self, member):
        """Handles permission resolution for the current :class:`Member`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides

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

        # If manage permissions is True, then all permissions are set to True.

        # The operation first takes into consideration the denied
        # and then the allowed.

        o = self.guild.owner
        if o is not None and member.id == o.id:
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

        # Apply @everyone allow/deny first since it's special
        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites

        member_role_ids = set(map(lambda r: r.id, member.roles))
        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.type == 'role' and overwrite.id in member_role_ids:
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.type == 'member' and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

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
    def delete(self, *, reason=None):
        """|coro|

        Deletes the channel.

        You must have :attr:`~.Permissions.manage_channels` permission to use this.

        Parameters
        -----------
        reason: Optional[str]
            The reason for deleting this channel.
            Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have proper permissions to delete the channel.
        NotFound
            The channel was not found or was already deleted.
        HTTPException
            Deleting the channel failed.
        """
        yield from self._state.http.delete_channel(self.id, reason=reason)

    @asyncio.coroutine
    def set_permissions(self, target, *, overwrite=_undefined, reason=None, **permissions):
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

        You must have the :attr:`~Permissions.manage_roles` permission to use this.

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
        reason: Optional[str]
            The reason for doing this action. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to edit channel specific permissions.
        HTTPException
            Editing channel specific permissions failed.
        NotFound
            The role or member being edited is not part of the guild.
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
            yield from http.delete_channel_permissions(self.id, target.id, reason=reason)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            yield from http.edit_channel_permissions(self.id, target.id, allow.value, deny.value, perm_type, reason=reason)
        else:
            raise InvalidArgument('Invalid overwrite type provided.')

    @asyncio.coroutine
    def create_invite(self, *, reason=None, **fields):
        """|coro|

        Creates an instant invite.

        You must have :attr:`~.Permissions.create_instant_invite` permission to
        do this.

        Parameters
        ------------
        max_age : int
            How long the invite should last. If it's 0 then the invite
            doesn't expire. Defaults to 0.
        max_uses : int
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to 0.
        temporary : bool
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to False.
        unique: bool
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to False then it will return a previously created
            invite.
        reason: Optional[str]
            The reason for creating this invite. Shows up on the audit log.

        Raises
        -------
        HTTPException
            Invite creation failed.

        Returns
        --------
        :class:`Invite`
            The invite that was created.
        """

        data = yield from self._state.http.create_invite(self.id, reason=reason, **fields)
        return Invite.from_incomplete(data=data, state=self._state)

    @asyncio.coroutine
    def invites(self):
        """|coro|

        Returns a list of all active instant invites from this channel.

        You must have :attr:`~.Permissions.manage_guild` to get this information.

        Raises
        -------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`Invite`]
            The list of invites that are currently active.
        """

        state = self._state
        data = yield from state.http.invites_from_channel(self.id)
        result = []

        for invite in data:
            invite['channel'] = self
            invite['guild'] = self.guild
            result.append(Invite(state=state, data=invite))

        return result

class Messageable(metaclass=abc.ABCMeta):
    """An ABC that details the common operations on a model that can send messages.

    The following implement this ABC:

    - :class:`TextChannel`
    - :class:`DMChannel`
    - :class:`GroupChannel`
    - :class:`User`
    - :class:`Member`
    - :class:`~ext.commands.Context`

    This ABC must also implement :class:`abc.Snowflake`.
    """

    __slots__ = ()

    @asyncio.coroutine
    @abc.abstractmethod
    def _get_channel(self):
        raise NotImplementedError

    @asyncio.coroutine
    def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`File` objects.
        **Specifying both parameters will lead to an exception**.

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
        file: :class:`File`
            The file to upload.
        files: List[:class:`File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: int
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
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
        InvalidArgument
            The ``files`` list is not of the appropriate size or
            you specified both ``file`` and ``files``.

        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel = yield from self._get_channel()
        state = self._state
        content = str(content) if content is not None else None
        if embed is not None:
            embed = embed.to_dict()

        if file is not None and files is not None:
            raise InvalidArgument('cannot pass both file and files parameter to send()')

        if file is not None:
            if not isinstance(file, File):
                raise InvalidArgument('file parameter must be File')

            try:
                data = yield from state.http.send_files(channel.id, files=[(file.open_file(), file.filename)],
                                                        content=content, tts=tts, embed=embed, nonce=nonce)
            finally:
                file.close()

        elif files is not None:
            if len(files) > 10:
                raise InvalidArgument('files parameter must be a list of up to 10 elements')

            try:
                param = [(f.open_file(), f.filename) for f in files]
                data = yield from state.http.send_files(channel.id, files=param, content=content, tts=tts,
                                                        embed=embed, nonce=nonce)
            finally:
                for f in files:
                    f.close()
        else:
            data = yield from state.http.send_message(channel.id, content, tts=tts, embed=embed, nonce=nonce)

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

            async with channel.typing():
                # do expensive stuff here
                await channel.send('done!')

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
        return self._state.create_message(channel=channel, data=data)

    @asyncio.coroutine
    def pins(self):
        """|coro|

        Returns a :class:`list` of :class:`Message` that are currently pinned.

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
        """Return an :class:`AsyncIterator` that enables receiving the destination's message history.

        You must have :attr:`~.Permissions.read_message_history` permissions to use this.

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[int]
            The number of messages to retrieve.
            If ``None``, retrieves every message in the channel. Note, however,
            that this would make it a slow operation.
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

        Flattening into a list: ::

            messages = await channel.history(limit=123).flatten()
            # messages is now a list of Message...

        Python 3.4 Usage ::

            count = 0
            iterator = channel.history(limit=200)
            while True:
                try:
                    message = yield from iterator.next()
                except discord.NoMoreItems:
                    break
                else:
                    if message.author == client.user:
                        counter += 1
        """
        return HistoryIterator(self, limit=limit, before=before, after=after, around=around, reverse=reverse)


class Connectable(metaclass=abc.ABCMeta):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`VoiceChannel`
    """
    __slots__ = ()

    @abc.abstractmethod
    def _get_voice_client_key(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _get_voice_state_pair(self):
        raise NotImplementedError

    @asyncio.coroutine
    def connect(self, *, timeout=60.0, reconnect=True):
        """|coro|

        Connects to voice and creates a :class:`VoiceClient` to establish
        your connection to the voice server.

        Parameters
        -----------
        timeout: float
            The timeout in seconds to wait for the voice endpoint.
        reconnect: bool
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.

        Raises
        -------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ClientException
            You are already connected to a voice channel.
        OpusNotLoaded
            The opus library has not been loaded.

        Returns
        -------
        :class:`VoiceClient`
            A voice client that is fully connected to the voice server.
        """
        key_id, key_name = self._get_voice_client_key()
        state = self._state

        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel.')

        voice = VoiceClient(state=state, timeout=timeout, channel=self)
        state._add_voice_client(key_id, voice)

        try:
            yield from voice.connect(reconnect=reconnect)
        except asyncio.TimeoutError as e:
            try:
                yield from voice.disconnect(force=True)
            except:
                # we don't care if disconnect failed because connection failed
                pass
            raise e # re-raise

        return voice
