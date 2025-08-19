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

import copy
import time
import secrets
import asyncio
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from .object import OLDEST_OBJECT, Object
from .context_managers import Typing
from .enums import ChannelType, InviteTarget
from .errors import ClientException, NotFound
from .mentions import AllowedMentions
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .invite import Invite
from .file import File
from .http import handle_message_parameters
from .voice_client import VoiceClient, VoiceProtocol
from .sticker import GuildSticker, StickerItem
from . import utils
from .flags import InviteFlags
import warnings

__all__ = (
    'Snowflake',
    'User',
    'PrivateChannel',
    'GuildChannel',
    'Messageable',
    'Connectable',
)

T = TypeVar('T', bound=VoiceProtocol)

if TYPE_CHECKING:
    from typing_extensions import Self, Unpack

    from .client import Client
    from .user import ClientUser
    from .asset import Asset
    from .state import ConnectionState
    from .guild import Guild
    from .member import Member
    from .channel import CategoryChannel
    from .embeds import Embed
    from .message import Message, MessageReference, PartialMessage
    from .channel import (
        TextChannel,
        DMChannel,
        GroupChannel,
        PartialMessageable,
        VocalGuildChannel,
        VoiceChannel,
        StageChannel,
    )
    from .poll import Poll
    from .threads import Thread
    from .ui.view import BaseView, View, LayoutView
    from .types.channel import (
        PermissionOverwrite as PermissionOverwritePayload,
        Channel as ChannelPayload,
        GuildChannel as GuildChannelPayload,
        OverwriteType,
    )
    from .types.guild import (
        ChannelPositionUpdate,
    )
    from .types.snowflake import (
        SnowflakeList,
    )
    from .permissions import _PermissionOverwriteKwargs

    PartialMessageableChannel = Union[TextChannel, VoiceChannel, StageChannel, Thread, DMChannel, PartialMessageable]
    MessageableChannel = Union[PartialMessageableChannel, GroupChannel]
    SnowflakeTime = Union['Snowflake', datetime]

    class PinnedMessage(Message):
        pinned_at: datetime
        pinned: Literal[True]


MISSING = utils.MISSING


class _Undefined:
    def __repr__(self) -> str:
        return 'see-below'


_undefined: Any = _Undefined()


class _PinsIterator:
    def __init__(self, iterator: AsyncIterator[PinnedMessage]) -> None:
        self.__iterator: AsyncIterator[PinnedMessage] = iterator

    def __await__(self) -> Generator[Any, None, List[PinnedMessage]]:
        warnings.warn(
            '`await <channel>.pins()` is deprecated; use `async for message in <channel>.pins()` instead.',
            DeprecationWarning,
            stacklevel=2,
        )

        async def gather() -> List[PinnedMessage]:
            return [msg async for msg in self.__iterator]

        return gather().__await__()

    def __aiter__(self) -> AsyncIterator[PinnedMessage]:
        return self.__iterator


async def _single_delete_strategy(messages: Iterable[Message], *, reason: Optional[str] = None):
    for m in messages:
        try:
            await m.delete()
        except NotFound as exc:
            if exc.code == 10008:
                continue  # bulk deletion ignores not found messages, single deletion does not.
            # several other race conditions with deletion should fail without continuing,
            # such as the channel being deleted and not found.
            raise


async def _purge_helper(
    channel: Union[Thread, TextChannel, VocalGuildChannel],
    *,
    limit: Optional[int] = 100,
    check: Callable[[Message], bool] = MISSING,
    before: Optional[SnowflakeTime] = None,
    after: Optional[SnowflakeTime] = None,
    around: Optional[SnowflakeTime] = None,
    oldest_first: Optional[bool] = None,
    bulk: bool = True,
    reason: Optional[str] = None,
) -> List[Message]:
    if check is MISSING:
        check = lambda m: True

    iterator = channel.history(limit=limit, before=before, after=after, oldest_first=oldest_first, around=around)
    ret: List[Message] = []
    count = 0

    minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
    strategy = channel.delete_messages if bulk else _single_delete_strategy

    async for message in iterator:
        if count == 100:
            to_delete = ret[-100:]
            await strategy(to_delete, reason=reason)
            count = 0
            await asyncio.sleep(1)

        if not check(message):
            continue

        if message.id < minimum_time:
            # older than 14 days old
            if count == 1:
                await ret[-1].delete()
            elif count >= 2:
                to_delete = ret[-count:]
                await strategy(to_delete, reason=reason)

            count = 0
            strategy = _single_delete_strategy

        count += 1
        ret.append(message)

    # Some messages remaining to poll
    if count >= 2:
        # more than 2 messages -> bulk delete
        to_delete = ret[-count:]
        await strategy(to_delete, reason=reason)
    elif count == 1:
        # delete a single message
        await ret[-1].delete()

    return ret


@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    If you want to create a snowflake on your own, consider using
    :class:`.Object`.

    Attributes
    -----------
    id: :class:`int`
        The model's unique ID.
    """

    id: int


@runtime_checkable
class User(Snowflake, Protocol):
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`~discord.User`
    - :class:`~discord.ClientUser`
    - :class:`~discord.Member`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    discriminator: :class:`str`
        The user's discriminator. This is a legacy concept that is no longer used.
    global_name: Optional[:class:`str`]
        The user's global nickname.
    bot: :class:`bool`
        If the user is a bot account.
    system: :class:`bool`
        If the user is a system account.
    """

    name: str
    discriminator: str
    global_name: Optional[str]
    bot: bool
    system: bool

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name."""
        raise NotImplementedError

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        raise NotImplementedError

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`~discord.Asset`]: Returns an Asset that represents the user's avatar, if present."""
        raise NotImplementedError

    @property
    def avatar_decoration(self) -> Optional[Asset]:
        """Optional[:class:`~discord.Asset`]: Returns an Asset that represents the user's avatar decoration, if present.

        .. versionadded:: 2.4
        """
        raise NotImplementedError

    @property
    def avatar_decoration_sku_id(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns an integer that represents the user's avatar decoration SKU ID, if present.

        .. versionadded:: 2.4
        """
        raise NotImplementedError

    @property
    def default_avatar(self) -> Asset:
        """:class:`~discord.Asset`: Returns the default avatar for a given user."""
        raise NotImplementedError

    @property
    def display_avatar(self) -> Asset:
        """:class:`~discord.Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        raise NotImplementedError

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the user is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`~discord.Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """
        raise NotImplementedError


class PrivateChannel:
    """An ABC that details the common operations on a private Discord channel.

    The following implement this ABC:

    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    me: :class:`~discord.ClientUser`
        The user presenting yourself.
    """

    __slots__ = ()

    id: int
    me: ClientUser


class _Overwrites:
    __slots__ = ('id', 'allow', 'deny', 'type')

    ROLE = 0
    MEMBER = 1

    def __init__(self, data: PermissionOverwritePayload) -> None:
        self.id: int = int(data['id'])
        self.allow: int = int(data.get('allow', 0))
        self.deny: int = int(data.get('deny', 0))
        self.type: OverwriteType = data['type']

    def _asdict(self) -> PermissionOverwritePayload:
        return {
            'id': self.id,
            'allow': str(self.allow),
            'deny': str(self.deny),
            'type': self.type,
        }

    def is_role(self) -> bool:
        return self.type == 0

    def is_member(self) -> bool:
        return self.type == 1


class GuildChannel:
    """An ABC that details the common operations on a Discord guild channel.

    The following implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.CategoryChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.ForumChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`~discord.Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    """

    __slots__ = ()

    id: int
    name: str
    guild: Guild
    type: ChannelType
    position: int
    category_id: Optional[int]
    _state: ConnectionState
    _overwrites: List[_Overwrites]

    if TYPE_CHECKING:

        def __init__(self, *, state: ConnectionState, guild: Guild, data: GuildChannelPayload): ...

    def __str__(self) -> str:
        return self.name

    @property
    def _sorting_bucket(self) -> int:
        raise NotImplementedError

    def _update(self, guild: Guild, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def _move(
        self,
        position: int,
        parent_id: Optional[Any] = None,
        lock_permissions: bool = False,
        *,
        reason: Optional[str],
    ) -> None:
        if position < 0:
            raise ValueError('Channel position cannot be less than 0.')

        http = self._state.http
        bucket = self._sorting_bucket
        channels: List[GuildChannel] = [c for c in self.guild.channels if c._sorting_bucket == bucket]

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # not there somehow lol
            return
        else:
            index = next((i for i, c in enumerate(channels) if c.position >= position), len(channels))
            # add ourselves at our designated position
            channels.insert(index, self)

        payload = []
        for index, c in enumerate(channels):
            d: Dict[str, Any] = {'id': c.id, 'position': index}
            if parent_id is not _undefined and c.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await http.bulk_channel_update(self.guild.id, payload, reason=reason)

    async def _edit(self, options: Dict[str, Any], reason: Optional[str]) -> Optional[ChannelPayload]:
        try:
            parent = options.pop('category')
        except KeyError:
            parent_id = _undefined
        else:
            parent_id = parent and parent.id

        try:
            options['rate_limit_per_user'] = options.pop('slowmode_delay')
        except KeyError:
            pass

        try:
            options['default_thread_rate_limit_per_user'] = options.pop('default_thread_slowmode_delay')
        except KeyError:
            pass

        try:
            rtc_region = options.pop('rtc_region')
        except KeyError:
            pass
        else:
            options['rtc_region'] = None if rtc_region is None else str(rtc_region)

        try:
            video_quality_mode = options.pop('video_quality_mode')
        except KeyError:
            pass
        else:
            options['video_quality_mode'] = int(video_quality_mode)

        lock_permissions = options.pop('sync_permissions', False)

        try:
            position = options.pop('position')
        except KeyError:
            if parent_id is not _undefined:
                if lock_permissions:
                    category = self.guild.get_channel(parent_id)
                    if category:
                        options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
                options['parent_id'] = parent_id
            elif lock_permissions and self.category_id is not None:
                # if we're syncing permissions on a pre-existing channel category without changing it
                # we need to update the permissions to point to the pre-existing category
                category = self.guild.get_channel(self.category_id)
                if category:
                    options['permission_overwrites'] = [c._asdict() for c in category._overwrites]
        else:
            await self._move(position, parent_id=parent_id, lock_permissions=lock_permissions, reason=reason)

        overwrites = options.get('overwrites', None)
        if overwrites is not None:
            perms = []
            for target, perm in overwrites.items():
                if not isinstance(perm, PermissionOverwrite):
                    raise TypeError(f'Expected PermissionOverwrite received {perm.__class__.__name__}')

                allow, deny = perm.pair()
                payload = {
                    'allow': allow.value,
                    'deny': deny.value,
                    'id': target.id,
                }

                if isinstance(target, Role):
                    payload['type'] = _Overwrites.ROLE
                elif isinstance(target, Object):
                    payload['type'] = _Overwrites.ROLE if target.type is Role else _Overwrites.MEMBER
                else:
                    payload['type'] = _Overwrites.MEMBER

                perms.append(payload)
            options['permission_overwrites'] = perms

        try:
            ch_type = options['type']
        except KeyError:
            pass
        else:
            if not isinstance(ch_type, ChannelType):
                raise TypeError('type field must be of type ChannelType')
            options['type'] = ch_type.value

        try:
            status = options.pop('status')
        except KeyError:
            pass
        else:
            await self._state.http.edit_voice_channel_status(status, channel_id=self.id, reason=reason)

        if options:
            return await self._state.http.edit_channel(self.id, reason=reason, **options)

    def _fill_overwrites(self, data: GuildChannelPayload) -> None:
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get('permission_overwrites', [])):
            overwrite = _Overwrites(overridden)
            self._overwrites.append(overwrite)

            if overwrite.type == _Overwrites.MEMBER:
                continue

            if overwrite.id == everyone_id:
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
    def changed_roles(self) -> List[Role]:
        """List[:class:`~discord.Role`]: Returns a list of roles that have been overridden from
        their default values in the :attr:`~discord.Guild.roles` attribute."""
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def overwrites_for(self, obj: Union[Role, User, Object]) -> PermissionOverwrite:
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        -----------
        obj: Union[:class:`~discord.Role`, :class:`~discord.abc.User`, :class:`~discord.Object`]
            The role or user denoting whose overwrite to get.

        Returns
        ---------
        :class:`~discord.PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, User):
            predicate = lambda p: p.is_member()
        elif isinstance(obj, Role):
            predicate = lambda p: p.is_role()
        else:
            predicate = lambda p: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    @property
    def overwrites(self) -> Dict[Union[Role, Member, Object], PermissionOverwrite]:
        """Returns all of the channel's overwrites.

        This is returned as a dictionary where the key contains the target which
        can be either a :class:`~discord.Role` or a :class:`~discord.Member` and the value is the
        overwrite as a :class:`~discord.PermissionOverwrite`.

        .. versionchanged:: 2.0
            Overwrites can now be type-aware :class:`~discord.Object` in case of cache lookup failure

        Returns
        --------
        Dict[Union[:class:`~discord.Role`, :class:`~discord.Member`, :class:`~discord.Object`], :class:`~discord.PermissionOverwrite`]
            The channel's permission overwrites.
        """
        ret = {}
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)
            target = None

            if ow.is_role():
                target = self.guild.get_role(ow.id)
            elif ow.is_member():
                target = self.guild.get_member(ow.id)

            if target is None:
                target_type = Role if ow.is_role() else User
                target = Object(id=ow.id, type=target_type)  # type: ignore

            ret[target] = overwrite
        return ret

    @property
    def category(self) -> Optional[CategoryChannel]:
        """Optional[:class:`~discord.CategoryChannel`]: The category this channel belongs to.

        If there is no category then this is ``None``.
        """
        return self.guild.get_channel(self.category_id)  # type: ignore # These are coerced into CategoryChannel

    @property
    def permissions_synced(self) -> bool:
        """:class:`bool`: Whether or not the permissions for this channel are synced with the
        category it belongs to.

        If there is no category then this is ``False``.

        .. versionadded:: 1.3
        """
        if self.category_id is None:
            return False

        category = self.guild.get_channel(self.category_id)
        return bool(category and category.overwrites == self.overwrites)

    def _apply_implicit_permissions(self, base: Permissions) -> None:
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

    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        """Handles permission resolution for the :class:`~discord.Member`
        or :class:`~discord.Role`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides
        - Implicit permissions
        - Member timeout
        - User installed app

        If a :class:`~discord.Role` is passed, then it checks the permissions
        someone with that role would have, which is essentially:

        - The default role permissions
        - The permissions of the role used as a parameter
        - The default role permission overwrites
        - The permission overwrites of the role used as a parameter

        .. versionchanged:: 2.0
            The object passed in can now be a role object.

        .. versionchanged:: 2.0
            ``obj`` parameter is now positional-only.

        .. versionchanged:: 2.4
            User installed apps are now taken into account.
            The permissions returned for a user installed app mirrors the
            permissions Discord returns in :attr:`~discord.Interaction.app_permissions`,
            though it is recommended to use that attribute instead.

        Parameters
        ----------
        obj: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Returns
        -------
        :class:`~discord.Permissions`
            The resolved permissions for the member or role.
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

        if self.guild.owner_id == obj.id:
            return Permissions.all()

        default = self.guild.default_role
        if default is None:
            if self._state.self_id == obj.id:
                return Permissions._user_installed_permissions(in_guild=True)
            else:
                return Permissions.none()

        base = Permissions(default.permissions.value)

        # Handle the role case first
        if isinstance(obj, Role):
            base.value |= obj._permissions

            if base.administrator:
                return Permissions.all()

            # Apply @everyone allow/deny first since it's special
            try:
                maybe_everyone = self._overwrites[0]
                if maybe_everyone.id == self.guild.id:
                    base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
            except IndexError:
                pass

            if obj.is_default():
                return base

            overwrite = utils.get(self._overwrites, type=_Overwrites.ROLE, id=obj.id)
            if overwrite is not None:
                base.handle_overwrite(overwrite.allow, overwrite.deny)

            return base

        roles = obj._roles
        get_role = self.guild.get_role

        # Apply guild roles that the member has.
        for role_id in roles:
            role = get_role(role_id)
            if role is not None:
                base.value |= role._permissions

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

        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_role() and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == obj.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        if obj.is_timed_out():
            # Timeout leads to every permission except VIEW_CHANNEL and READ_MESSAGE_HISTORY
            # being explicitly denied
            # N.B.: This *must* come last, because it's a conclusive mask
            base.value &= Permissions._timeout_mask()

        return base

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the channel.

        You must have :attr:`~discord.Permissions.manage_channels` to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this channel.
            Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to delete the channel.
        ~discord.NotFound
            The channel was not found or was already deleted.
        ~discord.HTTPException
            Deleting the channel failed.
        """
        await self._state.http.delete_channel(self.id, reason=reason)

    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        overwrite: Optional[Union[PermissionOverwrite, _Undefined]] = ...,
        reason: Optional[str] = ...,
    ) -> None: ...

    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        reason: Optional[str] = ...,
        **permissions: Unpack[_PermissionOverwriteKwargs],
    ) -> None: ...

    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        overwrite: Any = _undefined,
        reason: Optional[str] = None,
        **permissions: Unpack[_PermissionOverwriteKwargs],
    ) -> None:
        r"""|coro|

        Sets the channel specific permission overwrites for a target in the
        channel.

        The ``target`` parameter should either be a :class:`~discord.Member` or a
        :class:`~discord.Role` that belongs to guild.

        The ``overwrite`` parameter, if given, must either be ``None`` or
        :class:`~discord.PermissionOverwrite`. For convenience, you can pass in
        keyword arguments denoting :class:`~discord.Permissions` attributes. If this is
        done, then you cannot mix the keyword arguments with the ``overwrite``
        parameter.

        If the ``overwrite`` parameter is ``None``, then the permission
        overwrites are deleted.

        You must have :attr:`~discord.Permissions.manage_roles` to do this.

        .. note::

            This method *replaces* the old overwrites with the ones given.

        Examples
        ----------

        Setting allow and deny: ::

            await message.channel.set_permissions(message.author, read_messages=True,
                                                                  send_messages=False)

        Deleting overwrites ::

            await channel.set_permissions(member, overwrite=None)

        Using :class:`~discord.PermissionOverwrite` ::

            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages = False
            overwrite.read_messages = True
            await channel.set_permissions(member, overwrite=overwrite)

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.


        Parameters
        -----------
        target: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The member or role to overwrite permissions for.
        overwrite: Optional[:class:`~discord.PermissionOverwrite`]
            The permissions to allow and deny to the target, or ``None`` to
            delete the overwrite.
        \*\*permissions
            A keyword argument list of permissions to set for ease of use.
            Cannot be mixed with ``overwrite``.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have permissions to edit channel specific permissions.
        ~discord.HTTPException
            Editing channel specific permissions failed.
        ~discord.NotFound
            The role or member being edited is not part of the guild.
        TypeError
            The ``overwrite`` parameter was invalid or the target type was not
            :class:`~discord.Role` or :class:`~discord.Member`.
        ValueError
            The ``overwrite`` parameter and ``positions`` parameters were both
            unset.
        """

        http = self._state.http

        if isinstance(target, User):
            perm_type = _Overwrites.MEMBER
        elif isinstance(target, Role):
            perm_type = _Overwrites.ROLE
        else:
            raise ValueError('target parameter must be either Member or Role')

        if overwrite is _undefined:
            if len(permissions) == 0:
                raise ValueError('No overwrite provided.')
            try:
                overwrite = PermissionOverwrite(**permissions)
            except (ValueError, TypeError):
                raise TypeError('Invalid permissions given to keyword arguments.')
        else:
            if len(permissions) > 0:
                raise TypeError('Cannot mix overwrite and keyword arguments.')

        if overwrite is None:
            await http.delete_channel_permissions(self.id, target.id, reason=reason)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            await http.edit_channel_permissions(
                self.id, target.id, str(allow.value), str(deny.value), perm_type, reason=reason
            )
        else:
            raise TypeError('Invalid overwrite type provided.')

    async def _clone_impl(
        self,
        base_attrs: Dict[str, Any],
        *,
        name: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        reason: Optional[str] = None,
    ) -> Self:
        base_attrs['permission_overwrites'] = [x._asdict() for x in self._overwrites]
        base_attrs['parent_id'] = self.category_id
        base_attrs['name'] = name or self.name
        if category is not None:
            base_attrs['parent_id'] = category.id

        guild_id = self.guild.id
        cls = self.__class__
        data = await self._state.http.create_channel(guild_id, self.type.value, reason=reason, **base_attrs)
        obj = cls(state=self._state, guild=self.guild, data=data)

        # temporarily add it to the cache
        self.guild._channels[obj.id] = obj  # type: ignore # obj is a GuildChannel
        return obj

    async def clone(
        self,
        *,
        name: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        reason: Optional[str] = None,
    ) -> Self:
        """|coro|

        Clones this channel. This creates a channel with the same properties
        as this channel.

        You must have :attr:`~discord.Permissions.manage_channels` to do this.

        .. versionadded:: 1.1

        Parameters
        ------------
        name: Optional[:class:`str`]
            The name of the new channel. If not provided, defaults to this
            channel name.
        category: Optional[:class:`~discord.CategoryChannel`]
            The category the new channel belongs to.
            This parameter is ignored if cloning a category channel.

            .. versionadded:: 2.5
        reason: Optional[:class:`str`]
            The reason for cloning this channel. Shows up on the audit log.

        Raises
        -------
        ~discord.Forbidden
            You do not have the proper permissions to create this channel.
        ~discord.HTTPException
            Creating the channel failed.

        Returns
        --------
        :class:`.abc.GuildChannel`
            The channel that was created.
        """
        raise NotImplementedError

    @overload
    async def move(
        self,
        *,
        beginning: bool,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: Optional[str] = MISSING,
    ) -> None: ...

    @overload
    async def move(
        self,
        *,
        end: bool,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None: ...

    @overload
    async def move(
        self,
        *,
        before: Snowflake,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None: ...

    @overload
    async def move(
        self,
        *,
        after: Snowflake,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None: ...

    async def move(self, **kwargs: Any) -> None:
        """|coro|

        A rich interface to help move a channel relative to other channels.

        If exact position movement is required, ``edit`` should be used instead.

        You must have :attr:`~discord.Permissions.manage_channels` to do this.

        .. note::

            Voice channels will always be sorted below text channels.
            This is a Discord limitation.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` or
            :exc:`ValueError` instead of ``InvalidArgument``.

        Parameters
        ------------
        beginning: :class:`bool`
            Whether to move the channel to the beginning of the
            channel list (or category if given).
            This is mutually exclusive with ``end``, ``before``, and ``after``.
        end: :class:`bool`
            Whether to move the channel to the end of the
            channel list (or category if given).
            This is mutually exclusive with ``beginning``, ``before``, and ``after``.
        before: :class:`~discord.abc.Snowflake`
            Whether to move the channel before the given channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``after``.
        after: :class:`~discord.abc.Snowflake`
            Whether to move the channel after the given channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``before``.
        offset: :class:`int`
            The number of channels to offset the move by. For example,
            an offset of ``2`` with ``beginning=True`` would move
            it 2 after the beginning. A positive number moves it below
            while a negative number moves it above. Note that this
            number is relative and computed after the ``beginning``,
            ``end``, ``before``, and ``after`` parameters.
        category: Optional[:class:`~discord.abc.Snowflake`]
            The category to move this channel under.
            If ``None`` is given then it moves it out of the category.
            This parameter is ignored if moving a category channel.
        sync_permissions: :class:`bool`
            Whether to sync the permissions with the category (if given).
        reason: :class:`str`
            The reason for the move.

        Raises
        -------
        ValueError
            An invalid position was given.
        TypeError
            A bad mix of arguments were passed.
        Forbidden
            You do not have permissions to move the channel.
        HTTPException
            Moving the channel failed.
        """

        if not kwargs:
            return

        beginning, end = kwargs.get('beginning'), kwargs.get('end')
        before, after = kwargs.get('before'), kwargs.get('after')
        offset = kwargs.get('offset', 0)
        if sum(bool(a) for a in (beginning, end, before, after)) > 1:
            raise TypeError('Only one of [before, after, end, beginning] can be used.')

        bucket = self._sorting_bucket
        parent_id = kwargs.get('category', MISSING)
        # fmt: off
        channels: List[GuildChannel]
        if parent_id not in (MISSING, None):
            parent_id = parent_id.id
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket
                and ch.category_id == parent_id
            ]
        else:
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket
                and ch.category_id == self.category_id
            ]
        # fmt: on

        channels.sort(key=lambda c: (c.position, c.id))

        try:
            # Try to remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # If we're not there then it's probably due to not being in the category
            pass

        index = None
        if beginning:
            index = 0
        elif end:
            index = len(channels)
        elif before:
            index = next((i for i, c in enumerate(channels) if c.id == before.id), None)
        elif after:
            index = next((i + 1 for i, c in enumerate(channels) if c.id == after.id), None)

        if index is None:
            raise ValueError('Could not resolve appropriate move position')

        channels.insert(max((index + offset), 0), self)
        payload: List[ChannelPositionUpdate] = []
        lock_permissions = kwargs.get('sync_permissions', False)
        reason = kwargs.get('reason')
        for index, channel in enumerate(channels):
            d: ChannelPositionUpdate = {'id': channel.id, 'position': index}
            if parent_id is not MISSING and channel.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await self._state.http.bulk_channel_update(self.guild.id, payload, reason=reason)

    async def create_invite(
        self,
        *,
        reason: Optional[str] = None,
        max_age: int = 0,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        target_type: Optional[InviteTarget] = None,
        target_user: Optional[User] = None,
        target_application_id: Optional[int] = None,
        guest: bool = False,
    ) -> Invite:
        """|coro|

        Creates an instant invite from a text or voice channel.

        You must have :attr:`~discord.Permissions.create_instant_invite` to do this.

        Parameters
        ------------
        max_age: :class:`int`
            How long the invite should last in seconds. If it's 0 then the invite
            doesn't expire. Defaults to ``0``.
        max_uses: :class:`int`
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to ``0``.
        temporary: :class:`bool`
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to ``False``.
        unique: :class:`bool`
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to ``False`` then it will return a previously created
            invite.
        reason: Optional[:class:`str`]
            The reason for creating this invite. Shows up on the audit log.
        target_type: Optional[:class:`.InviteTarget`]
            The type of target for the voice channel invite, if any.

            .. versionadded:: 2.0

        target_user: Optional[:class:`User`]
            The user whose stream to display for this invite, required if ``target_type`` is :attr:`.InviteTarget.stream`. The user must be streaming in the channel.

            .. versionadded:: 2.0

        target_application_id:: Optional[:class:`int`]
            The id of the embedded application for the invite, required if ``target_type`` is :attr:`.InviteTarget.embedded_application`.

            .. versionadded:: 2.0
        guest: :class:`bool`
            Whether the invite is a guest invite.

            .. versionadded:: 2.6

        Raises
        -------
        ~discord.HTTPException
            Invite creation failed.

        ~discord.NotFound
            The channel that was passed is a category or an invalid channel.

        Returns
        --------
        :class:`~discord.Invite`
            The invite that was created.
        """
        if target_type is InviteTarget.unknown:
            raise ValueError('Cannot create invite with an unknown target type')

        flags: Optional[InviteFlags] = None
        if guest:
            flags = InviteFlags._from_value(0)
            flags.guest = True

        data = await self._state.http.create_invite(
            self.id,
            reason=reason,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_type=target_type.value if target_type else None,
            target_user_id=target_user.id if target_user else None,
            target_application_id=target_application_id,
            flags=flags.value if flags else None,
        )
        return Invite.from_incomplete(data=data, state=self._state)

    async def invites(self) -> List[Invite]:
        """|coro|

        Returns a list of all active instant invites from this channel.

        You must have :attr:`~discord.Permissions.manage_channels` to get this information.

        Raises
        -------
        ~discord.Forbidden
            You do not have proper permissions to get the information.
        ~discord.HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`~discord.Invite`]
            The list of invites that are currently active.
        """

        state = self._state
        data = await state.http.invites_from_channel(self.id)
        guild = self.guild
        return [Invite(state=state, data=invite, channel=self, guild=guild) for invite in data]


class Messageable:
    """An ABC that details the common operations on a model that can send messages.

    The following classes implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
    - :class:`~discord.PartialMessageable`
    - :class:`~discord.User`
    - :class:`~discord.Member`
    - :class:`~discord.ext.commands.Context`
    - :class:`~discord.Thread`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    @overload
    async def send(
        self,
        *,
        file: File = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: LayoutView,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        *,
        files: Sequence[File] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: LayoutView,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[Embed] = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[Embed] = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message: ...

    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[Embed] = None,
        embeds: Optional[Sequence[Embed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        view: Optional[BaseView] = None,
        suppress_embeds: bool = False,
        silent: bool = False,
        poll: Optional[Poll] = None,
    ) -> Message:
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~discord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~discord.File` objects.
        **Specifying both parameters will lead to an exception**.

        To upload a single embed, the ``embed`` parameter should be used with a
        single :class:`~discord.Embed` object. To upload multiple embeds, the ``embeds``
        parameter should be used with a :class:`list` of :class:`~discord.Embed` objects.
        **Specifying both parameters will lead to an exception**.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` or
            :exc:`ValueError` instead of ``InvalidArgument``.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content of the message to send.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        embeds: List[:class:`~discord.Embed`]
            A list of embeds to upload. Must be a maximum of 10.

            .. versionadded:: 2.0
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: :class:`int`
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4

        reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`, :class:`~discord.PartialMessage`]
            A reference to the :class:`~discord.Message` to which you are referencing, this can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`.
            In the event of a replying reference, you can control whether this mentions the author of the referenced
            message using the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions`` or by
            setting ``mention_author``.

            .. versionadded:: 1.6

        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

            .. versionadded:: 1.6
        view: Union[:class:`discord.ui.View`, :class:`discord.ui.LayoutView`]
            A Discord UI View to add to the message.

            .. versionadded:: 2.0
        stickers: Sequence[Union[:class:`~discord.GuildSticker`, :class:`~discord.StickerItem`]]
            A list of stickers to upload. Must be a maximum of 3.

            .. versionadded:: 2.0
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This sends the message without any embeds if set to ``True``.

            .. versionadded:: 2.0
        silent: :class:`bool`
            Whether to suppress push and desktop notifications for the message. This will increment the mention counter
            in the UI, but will not actually send a notification.

            .. versionadded:: 2.2
        poll: :class:`~discord.Poll`
            The poll to send with this message.

            .. versionadded:: 2.4

        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.NotFound
            You sent a message with the same nonce as one that has been explicitly
            deleted shortly earlier.
        ValueError
            The ``files`` or ``embeds`` list is not of the appropriate size.
        TypeError
            You specified both ``file`` and ``files``,
            or you specified both ``embed`` and ``embeds``,
            or the ``reference`` object is not a :class:`~discord.Message`,
            :class:`~discord.MessageReference` or :class:`~discord.PartialMessage`.

        Returns
        ---------
        :class:`~discord.Message`
            The message that was sent.
        """

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None
        previous_allowed_mention = state.allowed_mentions

        if stickers is not None:
            sticker_ids: SnowflakeList = [sticker.id for sticker in stickers]
        else:
            sticker_ids = MISSING

        if reference is not None:
            try:
                reference_dict = reference.to_message_reference_dict()
            except AttributeError:
                raise TypeError('reference parameter must be Message, MessageReference, or PartialMessage') from None
        else:
            reference_dict = MISSING

        if view and not hasattr(view, '__discord_ui_view__'):
            raise TypeError(f'view parameter must be View not {view.__class__.__name__}')

        if suppress_embeds or silent:
            from .message import MessageFlags  # circular import

            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = silent
        else:
            flags = MISSING

        if nonce is None:
            nonce = secrets.randbits(64)

        with handle_message_parameters(
            content=content,
            tts=tts,
            file=file if file is not None else MISSING,
            files=files if files is not None else MISSING,
            embed=embed if embed is not None else MISSING,
            embeds=embeds if embeds is not None else MISSING,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            message_reference=reference_dict,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=mention_author,
            stickers=sticker_ids,
            view=view,
            flags=flags,
            poll=poll,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)

        ret = state.create_message(channel=channel, data=data)
        if view and not view.is_finished() and view.is_dispatchable():
            state.store_view(view, ret.id)

        if poll:
            poll._update(ret)

        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret

    def typing(self) -> Typing:
        """Returns an asynchronous context manager that allows you to send a typing indicator to
        the destination for an indefinite period of time, or 10 seconds if the context manager
        is called using ``await``.

        Example Usage: ::

            async with channel.typing():
                # simulate something heavy
                await asyncio.sleep(20)

            await channel.send('Done!')

        Example Usage: ::

            await channel.typing()
            # Do some computational magic for about 10 seconds
            await channel.send('Done!')

        .. versionchanged:: 2.0
            This no longer works with the ``with`` syntax, ``async with`` must be used instead.

        .. versionchanged:: 2.0
            Added functionality to ``await`` the context manager to send a typing indicator for 10 seconds.
        """
        return Typing(self)

    async def fetch_message(self, id: int, /) -> Message:
        """|coro|

        Retrieves a single :class:`~discord.Message` from the destination.

        Parameters
        ------------
        id: :class:`int`
            The message ID to look for.

        Raises
        --------
        ~discord.NotFound
            The specified message was not found.
        ~discord.Forbidden
            You do not have the permissions required to get a message.
        ~discord.HTTPException
            Retrieving the message failed.

        Returns
        --------
        :class:`~discord.Message`
            The message asked for.
        """

        channel = await self._get_channel()
        data = await self._state.http.get_message(channel.id, id)
        return self._state.create_message(channel=channel, data=data)

    async def __pins(
        self,
        *,
        limit: Optional[int] = 50,
        before: Optional[SnowflakeTime] = None,
        oldest_first: bool = False,
    ) -> AsyncIterator[PinnedMessage]:
        channel = await self._get_channel()
        state = self._state
        max_limit: int = 50

        time: Optional[str] = (
            (before if isinstance(before, datetime) else utils.snowflake_time(before.id)).isoformat()
            if before is not None
            else None
        )

        while True:
            retrieve = max_limit if limit is None else min(limit, max_limit)
            if retrieve < 1:
                break

            data = await self._state.http.pins_from(
                channel_id=channel.id,
                limit=retrieve,
                before=time,
            )

            items = data and data['items']
            if items:
                if limit is not None:
                    limit -= len(items)

                time = items[-1]['pinned_at']

            # Terminate loop on next iteration; there's no data left after this
            if len(items) < max_limit or not data['has_more']:
                limit = 0

            if oldest_first:
                items = reversed(items)

            count = 0
            for count, m in enumerate(items, start=1):
                message: Message = state.create_message(channel=channel, data=m['message'])
                message._pinned_at = utils.parse_time(m['pinned_at'])
                yield message  # pyright: ignore[reportReturnType]

            if count < max_limit:
                break

    def pins(
        self,
        *,
        limit: Optional[int] = 50,
        before: Optional[SnowflakeTime] = None,
        oldest_first: bool = False,
    ) -> _PinsIterator:
        """Retrieves an :term:`asynchronous iterator` of the pinned messages in the channel.

        You must have :attr:`~discord.Permissions.view_channel` and
        :attr:`~discord.Permissions.read_message_history` in order to use this.

        .. versionchanged:: 2.6

            Due to a change in Discord's API, this now returns a paginated iterator instead of a list.

            For backwards compatibility, you can still retrieve a list of pinned messages by
            using ``await`` on the returned object. This is however deprecated.

        .. note::

            Due to a limitation with the Discord API, the :class:`.Message`
            object returned by this method does not contain complete
            :attr:`.Message.reactions` data.

        Examples
        ---------

        Usage ::

            counter = 0
            async for message in channel.pins(limit=250):
                counter += 1

        Flattening into a list: ::

            messages = [message async for message in channel.pins(limit=50)]
            # messages is now a list of Message...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[int]
            The number of pinned messages to retrieve. If ``None``, it retrieves
            every pinned message in the channel. Note, however, that this would
            make it a slow operation.
            Defaults to ``50``.

            .. versionadded:: 2.6
        before: Optional[Union[:class:`datetime.datetime`, :class:`.abc.Snowflake`]]
            Retrieve pinned messages before this time or snowflake.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.

            .. versionadded:: 2.6
        oldest_first: :class:`bool`
            If set to ``True``, return messages in oldest pin->newest pin order.
            Defaults to ``False``.

            .. versionadded:: 2.6

        Raises
        -------
        ~discord.Forbidden
            You do not have the permission to retrieve pinned messages.
        ~discord.HTTPException
            Retrieving the pinned messages failed.

        Yields
        -------
        :class:`~discord.Message`
            The pinned message with :attr:`.Message.pinned_at` set.
        """
        return _PinsIterator(self.__pins(limit=limit, before=before, oldest_first=oldest_first))

    async def history(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
    ) -> AsyncIterator[Message]:
        """Returns an :term:`asynchronous iterator` that enables receiving the destination's message history.

        You must have :attr:`~discord.Permissions.read_message_history` to do this.

        Examples
        ---------

        Usage ::

            counter = 0
            async for message in channel.history(limit=200):
                if message.author == client.user:
                    counter += 1

        Flattening into a list: ::

            messages = [message async for message in channel.history(limit=123)]
            # messages is now a list of Message...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of messages to retrieve.
            If ``None``, retrieves every message in the channel. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages before this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages after this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        around: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages around this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            When using this argument, the maximum limit is 101. Note that if the limit is an
            even number then this will return at most limit + 1 messages.
        oldest_first: Optional[:class:`bool`]
            If set to ``True``, return messages in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.

        Raises
        ------
        ~discord.Forbidden
            You do not have permissions to get channel message history.
        ~discord.HTTPException
            The request to get message history failed.

        Yields
        -------
        :class:`~discord.Message`
            The message with the message data parsed.
        """

        async def _around_strategy(retrieve: int, around: Optional[Snowflake], limit: Optional[int]):
            if not around:
                return [], None, 0

            around_id = around.id if around else None
            data = await self._state.http.logs_from(channel.id, retrieve, around=around_id)

            return data, None, 0

        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await self._state.http.logs_from(channel.id, retrieve, after=after_id)

            if data:
                if limit is not None:
                    limit -= len(data)

                after = Object(id=int(data[0]['id']))

            return data, after, limit

        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await self._state.http.logs_from(channel.id, retrieve, before=before_id)

            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[-1]['id']))

            return data, before, limit

        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=utils.time_snowflake(after, high=True))
        if isinstance(around, datetime):
            around = Object(id=utils.time_snowflake(around))

        if oldest_first is None:
            reverse = after is not None
        else:
            reverse = oldest_first

        after = after or OLDEST_OBJECT
        predicate = None

        if around:
            if limit is None:
                raise ValueError('history does not support around with limit=None')
            if limit > 101:
                raise ValueError('history max limit 101 when specifying around parameter')

            # Strange Discord quirk
            limit = 100 if limit == 101 else limit

            strategy, state = _around_strategy, around

            if before and after:
                predicate = lambda m: after.id < int(m['id']) < before.id
            elif before:
                predicate = lambda m: int(m['id']) < before.id
            elif after:
                predicate = lambda m: after.id < int(m['id'])
        elif reverse:
            strategy, state = _after_strategy, after
            if before:
                predicate = lambda m: int(m['id']) < before.id
        else:
            strategy, state = _before_strategy, before
            if after and after != OLDEST_OBJECT:
                predicate = lambda m: int(m['id']) > after.id

        channel = await self._get_channel()

        while True:
            retrieve = 100 if limit is None else min(limit, 100)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            if reverse:
                data = reversed(data)
            if predicate:
                data = filter(predicate, data)

            count = 0

            for count, raw_message in enumerate(data, 1):
                yield self._state.create_message(channel=channel, data=raw_message)

            if count < 100:
                # There's no data left after this
                break


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    """

    __slots__ = ()
    _state: ConnectionState

    def _get_voice_client_key(self) -> Tuple[int, str]:
        raise NotImplementedError

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        raise NotImplementedError

    async def connect(
        self,
        *,
        timeout: float = 30.0,
        reconnect: bool = True,
        cls: Callable[[Client, Connectable], T] = VoiceClient,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> T:
        """|coro|

        Connects to voice and creates a :class:`~discord.VoiceClient` to establish
        your connection to the voice server.

        This requires :attr:`~discord.Intents.voice_states`.

        Parameters
        -----------
        timeout: :class:`float`
            The timeout in seconds to wait the connection to complete.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`~discord.VoiceProtocol`]
            A type that subclasses :class:`~discord.VoiceProtocol` to connect with.
            Defaults to :class:`~discord.VoiceClient`.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.

            .. versionadded:: 2.0
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.

            .. versionadded:: 2.0

        Raises
        -------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~discord.ClientException
            You are already connected to a voice channel.
        ~discord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        --------
        :class:`~discord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """

        key_id, _ = self._get_voice_client_key()
        state = self._state

        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel.')

        client = state._get_client()
        voice: T = cls(client, self)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError('Type must meet VoiceProtocol abstract base class.')

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf, self_mute=self_mute)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # we don't care if disconnect failed because connection failed
                pass
            raise  # re-raise

        return voice
