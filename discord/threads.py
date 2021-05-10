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
from discord.types.threads import ThreadMember
from typing import Dict, Optional, TYPE_CHECKING

from .mixins import Hashable
from .abc import Messageable
from .enums import ChannelType, try_enum
from .utils import MISSING, parse_time, _get_as_snowflake

__all__ = (
    'Thread',
    'ThreadMember',
)

if TYPE_CHECKING:
    from .types.threads import (
        Thread as ThreadPayload,
        ThreadMember as ThreadMemberPayload,
        ThreadMetadata,
        ThreadArchiveDuration,
    )
    from .guild import Guild
    from .channel import TextChannel
    from .member import Member
    from .message import Message
    from .abc import Snowflake
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
        The thread ID.
    parent_id: :class:`int`
        The parent :class:`TextChannel` ID this thread belongs to.
    owner_id: :class:`int`
        The user's ID that created this thread.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this thread. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this thread. A value of `0` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    message_count: :class:`int`
        An approximate number of messages in this thread. This caps at 50.
    member_count: :class:`int`
        An approximate number of members in this thread. This caps at 50.
    me: Optional[:class:`ThreadMember`]
        A thread member representing yourself, if you've joined the thread.
        This could not be available.
    archived: :class:`bool`
        Whether the thread is archived.
    locked: :class:`bool`
        Whether the thread is locked.
    archiver_id: Optional[:class:`int`]
        The user's ID that archived this thread.
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
        'message_count',
        'member_count',
        'slowmode_delay',
        'me',
        'locked',
        'archived',
        'archiver_id',
        'auto_archive_duration',
        'archive_timestamp',
    )

    def __init__(self, *, guild: Guild, data: ThreadPayload):
        self._state: ConnectionState = guild._state
        self.guild = guild
        self._members: Dict[int, ThreadMember] = {}
        self._from_data(data)

    async def _get_channel(self):
        return self

    def __repr__(self) -> str:
        return (
            f'<Thread id={self.id!r} name={self.name!r} parent={self.parent}'
            f' owner_id={self.owner_id!r} locked={self.locked} archived={self.archived}>'
        )

    def _from_data(self, data: ThreadPayload):
        self.id = int(data['id'])
        self.parent_id = int(data['parent_id'])
        self.owner_id = int(data['owner_id'])
        self.name = data['name']
        self._type = try_enum(ChannelType, data['type'])
        self.last_message_id = _get_as_snowflake(data, 'last_message_id')
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._unroll_metadata(data['thread_metadata'])

        try:
            member = data['member']
        except KeyError:
            self.me = None
        else:
            self.me = ThreadMember(self, member)

    def _unroll_metadata(self, data: ThreadMetadata):
        self.archived = data['archived']
        self.archiver_id = _get_as_snowflake(data, 'archiver_id')
        self.auto_archive_duration = data['auto_archive_duration']
        self.archive_timestamp = parse_time(data['archive_timestamp'])
        self.locked = data.get('locked', False)

    def _update(self, data):
        try:
            self.name = data['name']
        except KeyError:
            pass

        try:
            self._unroll_metadata(data['thread_metadata'])
        except KeyError:
            pass

    @property
    def parent(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: The parent channel this thread belongs to."""
        return self.guild.get_channel(self.parent_id)

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member this thread belongs to."""
        return self.guild.get_member(self.owner_id)

    @property
    def last_message(self) -> Optional[Message]:
        """Fetches the last message from this channel in cache.

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

    async def edit(
        self,
        *,
        name: str = MISSING,
        archived: bool = MISSING,
        locked: bool = MISSING,
        slowmode_delay: int = MISSING,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
    ):
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
        auto_archive_duration: :class:`int`
            The new duration to auto archive threads for inactivity.
            Must be one of ``60``, ``1440``, ``4320``, or ``10080``.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this thread, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the thread.
        HTTPException
            Editing the thread failed.
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
        if slowmode_delay is not MISSING:
            payload['rate_limit_per_user'] = slowmode_delay

        await self._state.http.edit_channel(self.id, **payload)

    async def join(self):
        """|coro|

        Joins this thread.

        You must have :attr:`~Permissions.send_messages` and :attr:`~Permissions.use_threads`
        to join a public thread. If the thread is private then :attr:`~Permissions.send_messages`
        and either :attr:`~Permissions.use_private_threads` or :attr:`~Permissions.manage_messages`
        is required to join the thread.

        Raises
        -------
        Forbidden
            You do not have permissions to join the thread.
        HTTPException
            Joining the thread failed.
        """
        await self._state.http.join_thread(self.id)

    async def leave(self):
        """|coro|

        Leaves this thread.

        Raises
        -------
        HTTPException
            Leaving the thread failed.
        """
        await self._state.http.leave_thread(self.id)

    async def add_user(self, user: Snowflake):
        """|coro|

        Adds a user to this thread.

        You must have :attr:`~Permissions.send_messages` and :attr:`~Permissions.use_threads`
        to add a user to a public thread. If the thread is private then :attr:`~Permissions.send_messages`
        and either :attr:`~Permissions.use_private_threads` or :attr:`~Permissions.manage_messages`
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

    async def remove_user(self, user: Snowflake):
        """|coro|

        Removes a user from this thread.

        You must have :attr:`~Permissions.manage_threads` or be the creator of the thread to remove a user.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to add to the thread.

        Raises
        -------
        Forbidden
            You do not have permissions to remove the user from the thread.
        HTTPException
            Removing the user from the thread failed.
        """
        await self._state.http.remove_user_from_thread(self.id, user.id)

    async def delete(self):
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

    def _add_member(self, member: ThreadMember) -> None:
        self._members[member.id] = member

    def _pop_member(self, member_id: int) -> Optional[ThreadMember]:
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
    joined_at: :class:`datetime.datetime`
        The time the member joined the thread in UTC.
    """

    __slots__ = (
        'id',
        'thread_id',
        'joined_at',
        'flags',
        '_state',
        'parent',
    )

    def __init__(self, parent: Thread, data: ThreadMemberPayload):
        self.parent = parent
        self._state = parent._state
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<ThreadMember id={self.id} thread_id={self.thread_id} joined_at={self.joined_at!r}>'

    def _from_data(self, data: ThreadMemberPayload):
        try:
            self.id = int(data['user_id'])
        except KeyError:
            assert self._state.self_id is not None
            self.id = self._state.self_id

        try:
            self.thread_id = int(data['id'])
        except KeyError:
            self.thread_id = self.parent.id

        self.joined_at = parse_time(data['join_timestamp'])
        self.flags = data['flags']

    @property
    def thread(self) -> Thread:
        """:class:`Thread`: The thread this member belongs to."""
        return self.parent
