"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Literal, Optional, Sequence, Union, TYPE_CHECKING
from datetime import datetime
import asyncio
import array
import copy

from .mixins import Hashable
from .abc import Messageable, GuildChannel, _purge_helper
from .enums import ChannelType, try_enum
from .errors import ClientException, InvalidData
from .flags import ChannelFlags
from .permissions import Permissions
from .utils import MISSING, parse_time, snowflake_time, _get_as_snowflake, _unique

__all__ = (
    'Thread',
    'ThreadMember',
)

if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self

    from .types.threads import (
        Thread as ThreadPayload,
        ThreadMember as ThreadMemberPayload,
        ThreadMetadata,
        ThreadArchiveDuration,
    )
    from .guild import Guild
    from .channel import TextChannel, CategoryChannel, ForumChannel, ForumTag
    from .member import Member
    from .message import Message, PartialMessage
    from .abc import Snowflake, SnowflakeTime
    from .role import Role
    from .state import ConnectionState


class Thread(Messageable, Hashable):
    """Represents a Discord thread.

    .. container:: operations

        .. describe:: x == y

            Checks if two threads are equal.

        .. describe:: x != y

            Checks if two threads are not equal.

        .. describe:: hash(x)

            Returns the thread's hash.

        .. describe:: str(x)

            Returns the thread's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The thread name.
    guild: :class:`Guild`
        The guild the thread belongs to.
    id: :class:`int`
        The thread ID. This is the same as the thread starter message ID.
    parent_id: :class:`int`
        The ID of the parent :class:`TextChannel` or :class:`ForumChannel` this thread belongs to.
    owner_id: :class:`int`
        The ID of the user that created this thread.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this thread. It may
        *not* point to an existing or valid message.
    last_pin_timestamp: Optional[:class:`datetime.datetime`]
        When the last pinned message was pinned. ``None`` if there are no pinned messages.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this thread. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    message_count: :class:`int`
        An approximate number of messages in this thread.
    member_count: :class:`int`
        An approximate number of members in this thread. This caps at 50.
    archived: :class:`bool`
        Whether the thread is archived.
    locked: :class:`bool`
        Whether the thread is locked.
    invitable: :class:`bool`
        Whether non-moderators can add other non-moderators to this thread.
        This is always ``True`` for public threads.
    auto_archive_duration: :class:`int`
        The duration in minutes until the thread is automatically archived due to inactivity.
        Usually a value of 60, 1440, 4320 and 10080.
    archive_timestamp: :class:`datetime.datetime`
        An aware timestamp of when the thread's archived status was last updated in UTC.
    """

    __slots__ = (
        'name',
        'id',
        'guild',
        '_type',
        '_state',
        '_members',
        'owner_id',
        'parent_id',
        'last_message_id',
        'last_pin_timestamp',
        'message_count',
        'member_count',
        'slowmode_delay',
        'locked',
        'archived',
        'invitable',
        'auto_archive_duration',
        'archive_timestamp',
        '_member_ids',
        '_created_at',
        '_flags',
        '_applied_tags',
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: ThreadPayload) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self._members: Dict[int, ThreadMember] = {}
        self._from_data(data)

    async def _get_channel(self) -> Self:
        return self

    def __repr__(self) -> str:
        return (
            f'<Thread id={self.id!r} name={self.name!r} parent={self.parent}'
            f' owner_id={self.owner_id!r} locked={self.locked} archived={self.archived}>'
        )

    def __str__(self) -> str:
        return self.name

    def _from_data(self, data: ThreadPayload):
        self.id: int = int(data['id'])
        self.parent_id: int = int(data['parent_id'])
        self.owner_id: int = int(data['owner_id'])
        self.name: str = data['name']
        self._type: ChannelType = try_enum(ChannelType, data['type'])
        self.last_message_id: Optional[int] = _get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime] = parse_time(data.get('last_pin_timestamp'))
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.message_count: int = data['message_count']
        self.member_count: int = data['member_count']
        self._member_ids: List[Union[str, int]] = data['member_ids_preview']
        self._flags: int = data.get('flags', 0)
        # SnowflakeList is sorted, but this would not be proper for applied tags, where order actually matters.
        self._applied_tags: array.array[int] = array.array('Q', map(int, data.get('applied_tags', [])))
        self._unroll_metadata(data['thread_metadata'])

    def _unroll_metadata(self, data: ThreadMetadata):
        self.archived: bool = data['archived']
        self.auto_archive_duration: int = data['auto_archive_duration']
        self.archive_timestamp: datetime = parse_time(data['archive_timestamp'])
        self.locked: bool = data.get('locked', False)
        self.invitable: bool = data.get('invitable', True)
        self._created_at: Optional[datetime] = parse_time(data.get('create_timestamp'))

    def _update(self, data):
        old = copy.copy(self)
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._flags: int = data.get('flags', 0)
        self._applied_tags: array.array[int] = array.array('Q', map(int, data.get('applied_tags', [])))

        if (meta := data.get('thread_metadata')) is not None:
            self._unroll_metadata(meta)
        if (name := data.get('name')) is not None:
            self.name = name
        if (last_message_id := _get_as_snowflake(data, 'last_message_id')) is not None:
            self.last_message_id = last_message_id
        if (message_count := data.get('message_count')) is not None:
            self.message_count = message_count
        if (member_count := data.get('member_count')) is not None:
            self.member_count = member_count
        if (member_ids := data.get('member_ids_preview')) is not None:
            self._member_ids = member_ids

        attrs = [x for x in self.__slots__ if not any(y in x for y in ('member', 'guild', 'state', 'count'))]

        if any(getattr(self, attr) != getattr(old, attr) for attr in attrs):
            return old

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return self._type

    @property
    def parent(self) -> Optional[Union[TextChannel, ForumChannel]]:
        """Optional[Union[:class:`ForumChannel`, :class:`TextChannel`]]: The parent channel this thread belongs to.

        There is an alias for this named :attr:`channel`.
        """
        return self.guild.get_channel(self.parent_id)  # type: ignore

    @property
    def channel(self) -> Optional[Union[TextChannel, ForumChannel]]:
        """Optional[Union[:class:`ForumChannel`, :class:`TextChannel`]]: The parent channel this thread belongs to.

        This is an alias of :attr:`parent`.
        """
        return self.parent

    @property
    def flags(self) -> ChannelFlags:
        """:class:`ChannelFlags`: The flags associated with this thread."""
        return ChannelFlags._from_value(self._flags)

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member this thread belongs to."""
        return self.guild.get_member(self.owner_id)

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the thread."""
        return f'<#{self.id}>'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the thread's creation time in UTC.

        .. note::

            This may be inaccurate for threads created before January 9th, 2022.
        """
        return self._created_at or snowflake_time(self.id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the thread."""
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'

    @property
    def members(self) -> List[ThreadMember]:
        """List[:class:`ThreadMember`]: A list of thread members in this thread.

        Initial members are not provided by Discord. You must call :func:`fetch_members`.
        """
        return list(self._members.values())

    @property
    def applied_tags(self) -> List[ForumTag]:
        """List[:class:`ForumTag`]: A list of tags applied to this thread."""
        tags = []
        if self.parent is None or self.parent.type != ChannelType.forum:
            return tags

        parent = self.parent
        for tag_id in self._applied_tags:
            tag = parent.get_tag(tag_id)  # type: ignore
            if tag is not None:
                tags.append(tag)

        return tags

    @property
    def starter_message(self) -> Optional[Message]:
        """Returns the thread starter message from the cache.

        The message might not be cached, valid, or point to an existing message.

        Note that the thread starter message ID is the same ID as the thread.

        Returns
        --------
        Optional[:class:`Message`]
            The thread starter message or ``None`` if not found.
        """
        return self._state._get_message(self.id)

    @property
    def last_message(self) -> Optional[Message]:
        """Returns the last message from this thread from the cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        ---------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    @property
    def category(self) -> Optional[CategoryChannel]:
        """The category channel the parent channel belongs to, if applicable.

        Raises
        -------
        ClientException
            The parent channel was not cached and returned ``None``.

        Returns
        -------
        Optional[:class:`CategoryChannel`]
            The parent channel's category.
        """

        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        return parent.category

    @property
    def category_id(self) -> Optional[int]:
        """The category channel ID the parent channel belongs to, if applicable.

        Raises
        -------
        ClientException
            The parent channel was not cached and returned ``None``.

        Returns
        -------
        Optional[:class:`int`]
            The parent channel's category ID.
        """

        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        return parent.category_id

    @property
    def me(self) -> Optional[ThreadMember]:
        """Optional[:class:`ThreadMember`]: A thread member representing yourself, if you've joined the thread.

        This might not be available.
        """
        self_id = self._state.self_id
        return self._members.get(self_id)  # type: ignore

    @me.setter
    def me(self, member) -> None:
        self._members[member.id] = member

    def is_private(self) -> bool:
        """:class:`bool`: Whether the thread is a private thread.

        A private thread is only viewable by those that have been explicitly
        invited or have :attr:`~.Permissions.manage_threads`.
        """
        return self._type is ChannelType.private_thread

    def is_news(self) -> bool:
        """:class:`bool`: Whether the thread is a news thread.

        A news thread is a thread that has a parent that is a news channel,
        i.e. :meth:`.TextChannel.is_news` is ``True``.
        """
        return self._type is ChannelType.news_thread

    def is_nsfw(self) -> bool:
        """:class:`bool`: Whether the thread is NSFW or not.

        An NSFW thread is a thread that has a parent that is an NSFW channel,
        i.e. :meth:`.TextChannel.is_nsfw` is ``True``.
        """
        parent = self.parent
        return parent is not None and parent.is_nsfw()

    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        """Handles permission resolution for the :class:`~discord.Member`
        or :class:`~discord.Role`.

        Since threads do not have their own permissions, they mostly
        inherit them from the parent channel with some implicit
        permissions changed.

        Parameters
        ----------
        obj: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Raises
        -------
        ClientException
            The parent channel was not cached and returned ``None``

        Returns
        -------
        :class:`~discord.Permissions`
            The resolved permissions for the member or role.
        """

        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')

        base = GuildChannel.permissions_for(parent, obj)

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages_in_threads:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        return base

    async def delete_messages(self, messages: Iterable[Snowflake], /, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        You must have :attr:`~Permissions.manage_messages` to use this (unless they're your own).

        .. note::
            Users do not have access to the message bulk-delete endpoint.
            Since messages are just iterated over and deleted one-by-one,
            it's easy to get ratelimited using this method.

        Parameters
        -----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.
        reason: Optional[:class:`str`]
            The reason for deleting the messages. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the messages.
        HTTPException
            Deleting the messages failed.
        """
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return  # Do nothing

        await self._state._delete_messages(self.id, messages, reason=reason)

    async def purge(
        self,
        *,
        limit: Optional[int] = 100,
        check: Callable[[Message], bool] = MISSING,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
        reason: Optional[str] = None,
    ) -> List[Message]:
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        Having :attr:`~Permissions.read_message_history` is needed to
        retrieve message history.

        Examples
        ---------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send(f'Deleted {len(deleted)} message(s)')

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: Callable[[:class:`Message`], :class:`bool`]
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``before`` in :meth:`history`.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``after`` in :meth:`history`.
        around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``around`` in :meth:`history`.
        oldest_first: Optional[:class:`bool`]
            Same as ``oldest_first`` in :meth:`history`.
        reason: Optional[:class:`str`]
            The reason for purging the messages. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have proper permissions to do the actions required.
        HTTPException
            Purging the messages failed.

        Returns
        --------
        List[:class:`.Message`]
            The list of messages that were deleted.
        """
        return await _purge_helper(
            self,
            limit=limit,
            check=check,
            before=before,
            after=after,
            around=around,
            oldest_first=oldest_first,
            reason=reason,
        )

    async def edit(
        self,
        *,
        name: str = MISSING,
        archived: bool = MISSING,
        locked: bool = MISSING,
        invitable: bool = MISSING,
        pinned: bool = MISSING,
        slowmode_delay: int = MISSING,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        applied_tags: Sequence[ForumTag] = MISSING,
        reason: Optional[str] = None,
    ) -> Thread:
        """|coro|

        Edits the thread.

        Editing the thread requires :attr:`.Permissions.manage_threads`. The thread
        creator can also edit ``name``, ``archived`` or ``auto_archive_duration``.
        Note that if the thread is locked then only those with :attr:`.Permissions.manage_threads`
        can unarchive a thread.

        The thread must be unarchived to be edited.

        Parameters
        ------------
        name: :class:`str`
            The new name of the thread.
        archived: :class:`bool`
            Whether to archive the thread or not.
        locked: :class:`bool`
            Whether to lock the thread or not.
        pinned: :class:`bool`
            Whether to pin the thread or not. This only works if the thread is part of a forum.
        invitable: :class:`bool`
            Whether non-moderators can add other non-moderators to this thread.
            Only available for private threads.
        auto_archive_duration: :class:`int`
            The new duration in minutes before a thread is automatically archived for inactivity.
            Must be one of ``60``, ``1440``, ``4320``, or ``10080``.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this thread, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.
        applied_tags: Sequence[:class:`ForumTag`]
            The new tags to apply to the thread. There can only be up to 5 tags applied to a thread.
        reason: Optional[:class:`str`]
            The reason for editing this thread. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the thread.
        HTTPException
            Editing the thread failed.

        Returns
        --------
        :class:`Thread`
            The newly edited thread.
        """
        payload = {}
        if name is not MISSING:
            payload['name'] = str(name)
        if archived is not MISSING:
            payload['archived'] = archived
        if auto_archive_duration is not MISSING:
            payload['auto_archive_duration'] = auto_archive_duration
        if locked is not MISSING:
            payload['locked'] = locked
        if invitable is not MISSING:
            payload['invitable'] = invitable
        if slowmode_delay is not MISSING:
            payload['rate_limit_per_user'] = slowmode_delay
        if pinned is not MISSING:
            flags = self.flags
            flags.pinned = pinned
            payload['flags'] = flags.value
        if applied_tags is not MISSING:
            payload['applied_tags'] = [str(tag.id) for tag in applied_tags]

        data = await self._state.http.edit_channel(self.id, **payload, reason=reason)
        # The data payload will always be a Thread payload
        return Thread(data=data, state=self._state, guild=self.guild)  # type: ignore

    async def add_tags(self, *tags: Snowflake, reason: Optional[str] = None) -> None:
        r"""|coro|

        Adds the given forum tags to a thread.

        You must have :attr:`~Permissions.manage_threads` to
        use this or the thread must be owned by you.

        Tags that have :attr:`ForumTag.moderated` set to ``True`` require
        :attr:`~Permissions.manage_threads` to be added.

        The maximum number of tags that can be added to a thread is 5.

        The parent channel must be a :class:`ForumChannel`.

        Parameters
        -----------
        \*tags: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`ForumTag`
            to add to the thread.
        reason: Optional[:class:`str`]
            The reason for adding these tags.

        Raises
        -------
        Forbidden
            You do not have permissions to add these tags.
        HTTPException
            Adding tags failed.
        """

        applied_tags = [str(tag) for tag in self._applied_tags]
        applied_tags.extend(str(tag.id) for tag in tags)

        await self._state.http.edit_channel(self.id, applied_tags=_unique(applied_tags), reason=reason)

    async def remove_tags(self, *tags: Snowflake, reason: Optional[str] = None) -> None:
        r"""|coro|

        Remove the given forum tags to a thread.

        You must have :attr:`~Permissions.manage_threads` to
        use this or the thread must be owned by you.

        The parent channel must be a :class:`ForumChannel`.

        Parameters
        -----------
        \*tags: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`ForumTag`
            to remove to the thread.
        reason: Optional[:class:`str`]
            The reason for removing these tags.

        Raises
        -------
        Forbidden
            You do not have permissions to remove these tags.
        HTTPException
            Removing tags failed.
        """

        # Once again, taking advantage of the fact that dicts are ordered since 3.7
        applied_tags: Dict[str, Literal[None]] = {str(tag): None for tag in self._applied_tags}

        for tag in tags:
            applied_tags.pop(str(tag.id), None)

        await self._state.http.edit_channel(self.id, applied_tags=list(applied_tags.keys()), reason=reason)

    async def join(self) -> None:
        """|coro|

        Joins this thread.

        You must have :attr:`~Permissions.send_messages_in_threads` to join a thread.
        If the thread is private, :attr:`~Permissions.manage_threads` is also needed.

        Raises
        -------
        Forbidden
            You do not have permissions to join the thread.
        HTTPException
            Joining the thread failed.
        """
        await self._state.http.join_thread(self.id)

    async def leave(self) -> None:
        """|coro|

        Leaves this thread.

        Raises
        -------
        HTTPException
            Leaving the thread failed.
        """
        await self._state.http.leave_thread(self.id)

    async def add_user(self, user: Snowflake, /) -> None:
        """|coro|

        Adds a user to this thread.

        You must have :attr:`~Permissions.send_messages_in_threads` to add a user to a thread.
        If the thread is private and :attr:`invitable` is ``False`` then :attr:`~Permissions.manage_messages`
        is required to add a user to the thread.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to add to the thread.

        Raises
        -------
        Forbidden
            You do not have permissions to add the user to the thread.
        HTTPException
            Adding the user to the thread failed.
        """
        await self._state.http.add_user_to_thread(self.id, user.id)

    async def remove_user(self, user: Snowflake, /) -> None:
        """|coro|

        Removes a user from this thread.

        You must have :attr:`~Permissions.manage_threads` or be the creator of the thread to remove a user.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to remove from the thread.

        Raises
        -------
        Forbidden
            You do not have permissions to remove the user from the thread.
        HTTPException
            Removing the user from the thread failed.
        """
        await self._state.http.remove_user_from_thread(self.id, user.id)

    async def fetch_members(self) -> List[ThreadMember]:
        """|coro|

        Retrieves all :class:`ThreadMember` that are in this thread,
        along with their respective :class:`Member`.

        Raises
        -------
        InvalidData
            Discord didn't respond with the members.

        Returns
        --------
        List[:class:`ThreadMember`]
            All thread members in the thread.
        """
        state = self._state
        await state.ws.request_lazy_guild(self.parent.guild.id, thread_member_lists=[self.id])  # type: ignore
        future = state.ws.wait_for('thread_member_list_update', lambda d: int(d['thread_id']) == self.id)
        try:
            data = await asyncio.wait_for(future, timeout=15)
        except asyncio.TimeoutError as exc:
            raise InvalidData('Didn\'t receieve a response from Discord') from exc

        members = [ThreadMember(self, {'member': member}) for member in data['members']]  # type: ignore
        for m in members:
            self._add_member(m)

        return self.members  # Includes correct self.me

    async def delete(self) -> None:
        """|coro|

        Deletes this thread.

        You must have :attr:`~Permissions.manage_threads` to delete threads.

        Raises
        -------
        Forbidden
            You do not have permissions to delete this thread.
        HTTPException
            Deleting the thread failed.
        """
        await self._state.http.delete_channel(self.id)

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        Parameters
        ------------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        ---------
        :class:`PartialMessage`
            The partial message.
        """
        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)

    def _add_member(self, member: ThreadMember, /) -> None:
        if member.id != self._state.self_id:
            self._members[member.id] = member

    def _pop_member(self, member_id: int, /) -> Optional[ThreadMember]:
        return self._members.pop(member_id, None)


class ThreadMember(Hashable):
    """Represents a Discord thread member.

    .. container:: operations

        .. describe:: x == y

            Checks if two thread members are equal.

        .. describe:: x != y

            Checks if two thread members are not equal.

        .. describe:: hash(x)

            Returns the thread member's hash.

        .. describe:: str(x)

            Returns the thread member's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The thread member's ID.
    thread_id: :class:`int`
        The thread's ID.
    joined_at: Optional[:class:`datetime.datetime`]
        The time the member joined the thread in UTC.
        Only reliably available for yourself or members joined while the user is connected to the gateway.
    flags: :class:`int`
        The thread member's flags. Will be its own class in the future.
        Only reliably available for yourself or members joined while the user is connected to the gateway.
    """

    __slots__ = (
        'id',
        'thread_id',
        'joined_at',
        'flags',
        '_state',
        'parent',
    )

    def __init__(self, parent: Thread, data: ThreadMemberPayload) -> None:
        self.parent: Thread = parent
        self._state: ConnectionState = parent._state
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<ThreadMember id={self.id} thread_id={self.thread_id} joined_at={self.joined_at!r}>'

    def _from_data(self, data: ThreadMemberPayload) -> None:
        state = self._state

        self.id: int
        try:
            self.id = int(data['user_id'])
        except KeyError:
            self.id = state.self_id  # type: ignore

        self.thread_id: int
        try:
            self.thread_id = int(data['id'])
        except KeyError:
            self.thread_id = self.parent.id

        self.joined_at = parse_time(data.get('join_timestamp'))
        self.flags = data.get('flags')

        if (mdata := data.get('member')) is not None:
            guild = self.parent.guild
            mdata['guild_id'] = guild.id
            self.id = user_id = int(data['user_id'])
            mdata['presence'] = data.get('presence')
            if guild.get_member(user_id) is not None:
                state.parse_guild_member_update(mdata)
            else:
                state.parse_guild_member_add(mdata)

    @property
    def thread(self) -> Thread:
        """:class:`Thread`: The thread this member belongs to."""
        return self.parent

    @property
    def member(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member this :class:`ThreadMember` represents. If the member
        is not cached then this will be ``None``.
        """
        return self.parent.guild.get_member(self.id)
