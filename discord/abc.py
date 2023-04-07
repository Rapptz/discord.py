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
import asyncio
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Collection,
    Dict,
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
from .enums import AppCommandType, ChannelType
from .errors import ClientException
from .mentions import AllowedMentions
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .invite import Invite
from .file import File
from .http import handle_message_parameters
from .voice_client import VoiceClient, VoiceProtocol
from .sticker import GuildSticker, StickerItem
from .settings import ChannelSettings
from .commands import ApplicationCommand, BaseCommand, SlashCommand, UserCommand, MessageCommand, _command_factory
from . import utils

__all__ = (
    'Snowflake',
    'User',
    'PrivateChannel',
    'GuildChannel',
    'Messageable',
    'Connectable',
    'ApplicationCommand',
)

T = TypeVar('T', bound=VoiceProtocol)

if TYPE_CHECKING:
    from typing_extensions import Self
    from .client import Client
    from .user import ClientUser, User
    from .asset import Asset
    from .state import ConnectionState
    from .guild import Guild
    from .member import Member
    from .message import Message, MessageReference, PartialMessage
    from .channel import (
        TextChannel,
        DMChannel,
        GroupChannel,
        PartialMessageable,
        VocalGuildChannel,
        VoiceChannel,
        StageChannel,
        CategoryChannel,
    )
    from .threads import Thread
    from .enums import InviteTarget
    from .types.channel import (
        PermissionOverwrite as PermissionOverwritePayload,
        Channel as ChannelPayload,
        GuildChannel as GuildChannelPayload,
        OverwriteType,
    )
    from .types.snowflake import (
        SnowflakeList,
    )

    MessageableChannel = Union[TextChannel, VoiceChannel, StageChannel, Thread, DMChannel, PartialMessageable, GroupChannel]
    VocalChannel = Union[VoiceChannel, StageChannel, DMChannel, GroupChannel]
    SnowflakeTime = Union["Snowflake", datetime]

MISSING = utils.MISSING


class _Undefined:
    def __repr__(self) -> str:
        return 'see-below'


_undefined: Any = _Undefined()


async def _purge_helper(
    channel: Union[Thread, TextChannel, VocalGuildChannel],
    *,
    limit: Optional[int] = 100,
    check: Callable[[Message], bool] = MISSING,
    before: Optional[SnowflakeTime] = None,
    after: Optional[SnowflakeTime] = None,
    around: Optional[SnowflakeTime] = None,
    oldest_first: Optional[bool] = None,
    reason: Optional[str] = None,
) -> List[Message]:
    if check is MISSING:
        check = lambda m: True

    state = channel._state
    channel_id = channel.id
    iterator = channel.history(limit=limit, before=before, after=after, oldest_first=oldest_first, around=around)
    ret: List[Message] = []
    count = 0

    async for message in iterator:
        if count == 50:
            to_delete = ret[-50:]
            await state._delete_messages(channel_id, to_delete, reason=reason)
            count = 0
        if not check(message):
            continue

        count += 1
        ret.append(message)

    # Some messages remaining to poll
    to_delete = ret[-count:]
    await state._delete_messages(channel_id, to_delete, reason=reason)
    return ret


@overload
def _handle_commands(
    messageable: Messageable,
    type: Literal[AppCommandType.chat_input],
    *,
    query: Optional[str] = ...,
    limit: Optional[int] = ...,
    command_ids: Optional[Collection[int]] = ...,
    application: Optional[Snowflake] = ...,
    with_applications: bool = ...,
    target: Optional[Snowflake] = ...,
) -> AsyncIterator[SlashCommand]:
    ...


@overload
def _handle_commands(
    messageable: Messageable,
    type: Literal[AppCommandType.user],
    *,
    query: Optional[str] = ...,
    limit: Optional[int] = ...,
    command_ids: Optional[Collection[int]] = ...,
    application: Optional[Snowflake] = ...,
    with_applications: bool = ...,
    target: Optional[Snowflake] = ...,
) -> AsyncIterator[UserCommand]:
    ...


@overload
def _handle_commands(
    messageable: Message,
    type: Literal[AppCommandType.message],
    *,
    query: Optional[str] = ...,
    limit: Optional[int] = ...,
    command_ids: Optional[Collection[int]] = ...,
    application: Optional[Snowflake] = ...,
    with_applications: bool = ...,
    target: Optional[Snowflake] = ...,
) -> AsyncIterator[MessageCommand]:
    ...


async def _handle_commands(
    messageable: Union[Messageable, Message],
    type: AppCommandType,
    *,
    query: Optional[str] = None,
    limit: Optional[int] = None,
    command_ids: Optional[Collection[int]] = None,
    application: Optional[Snowflake] = None,
    with_applications: bool = True,
    target: Optional[Snowflake] = None,
) -> AsyncIterator[BaseCommand]:
    if limit is not None and limit < 0:
        raise ValueError('limit must be greater than or equal to 0')
    if query and command_ids:
        raise TypeError('Cannot specify both query and command_ids')

    state = messageable._state
    endpoint = state.http.search_application_commands
    channel = await messageable._get_channel()
    _, cls = _command_factory(type.value)
    cmd_ids = list(command_ids) if command_ids else None

    application_id = application.id if application else None
    if channel.type == ChannelType.private:
        recipient: User = channel.recipient  # type: ignore
        if not recipient.bot:
            raise TypeError('Cannot fetch commands in a DM with a non-bot user')
        application_id = recipient.id
        target = recipient
    elif channel.type == ChannelType.group:
        return

    prev_cursor = MISSING
    cursor = MISSING
    while True:
        # We keep two cursors because Discord just sends us an infinite loop sometimes
        retrieve = min((25 if not cmd_ids else 0) if limit is None else limit, 25)

        if not application_id and limit is not None:
            limit -= retrieve
        if (not cmd_ids and retrieve < 1) or cursor is None or (prev_cursor is not MISSING and prev_cursor == cursor):
            return

        data = await endpoint(
            channel.id,
            type.value,
            limit=retrieve if not application_id else None,
            query=query if not cmd_ids and not application_id else None,
            command_ids=cmd_ids if not application_id and not cursor else None,  # type: ignore
            application_id=application_id,
            include_applications=with_applications if (not application_id or with_applications) else None,
            cursor=cursor,
        )
        prev_cursor = cursor
        cursor = data['cursor'].get('next')
        cmds = data['application_commands']
        apps: Dict[int, dict] = {int(app['id']): app for app in data.get('applications') or []}

        for cmd in cmds:
            # Handle faked parameters
            if application_id and query and query.lower() not in cmd['name']:
                continue
            elif application_id and (not cmd_ids or int(cmd['id']) not in cmd_ids) and limit == 0:
                continue

            # We follow Discord behavior
            if application_id and limit is not None and (not cmd_ids or int(cmd['id']) not in cmd_ids):
                limit -= 1

            try:
                cmd_ids.remove(int(cmd['id'])) if cmd_ids else None
            except ValueError:
                pass

            cmd['application'] = apps.get(int(cmd['application_id']))
            yield cls(state=state, data=cmd, channel=channel, target=target)

        cmd_ids = None
        if application_id or len(cmds) < min(limit if limit else 25, 25) or len(cmds) == limit == 25:
            return


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
        The user's discriminator.
    bot: :class:`bool`
        If the user is a bot account.
    system: :class:`bool`
        If the user is a system account.
    """

    name: str
    discriminator: str
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

        .. versionadded:: 2.0
        """
        raise NotImplementedError

    @property
    def default_avatar(self) -> Asset:
        """:class:`~discord.Asset`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
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

    def _add_call(self, **kwargs):
        raise NotImplementedError

    def _update(self, *args) -> None:
        raise NotImplementedError


class _Overwrites:
    __slots__ = ('id', 'allow', 'deny', 'type')

    ROLE = 0
    MEMBER = 1

    def __init__(self, data: PermissionOverwritePayload):
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

        def __init__(self, *, state: ConnectionState, guild: Guild, data: GuildChannelPayload):
            ...

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
                # If we're syncing permissions on a pre-existing channel category without changing it
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
    def notification_settings(self) -> ChannelSettings:
        """:class:`~discord.ChannelSettings`: Returns the notification settings for this channel.

        If not found, an instance is created with defaults applied. This follows Discord behaviour.

        .. versionadded:: 2.0
        """
        guild = self.guild
        return guild.notification_settings._channel_overrides.get(
            self.id, self._state.default_channel_settings(guild.id, self.id)
        )

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
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'

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
        # Guild owner get all permissions -- no questions asked
        # The @everyone role gets the first application
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together
        # After the role permissions are resolved, the member permissions
        # have to take into effect
        # After all that is done, you have to do the following:

        # If manage permissions is True, then all permissions are set to True

        # The operation first takes into consideration the denied
        # and then the allowed

        if self.guild.owner_id == obj.id:
            return Permissions.all()

        default = self.guild.default_role
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
    ) -> None:
        ...

    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        reason: Optional[str] = ...,
        **permissions: Optional[bool],
    ) -> None:
        ...

    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        overwrite: Any = _undefined,
        reason: Optional[str] = None,
        **permissions: Optional[bool],
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

        # TODO: wait for event

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
        reason: Optional[str] = None,
    ) -> Self:
        base_attrs['permission_overwrites'] = [x._asdict() for x in self._overwrites]
        base_attrs['parent_id'] = self.category_id
        base_attrs['name'] = name or self.name
        guild_id = self.guild.id
        cls = self.__class__
        data = await self._state.http.create_channel(guild_id, self.type.value, reason=reason, **base_attrs)
        obj = cls(state=self._state, guild=self.guild, data=data)

        # Temporarily add it to the cache
        self.guild._channels[obj.id] = obj  # type: ignore # obj is a GuildChannel
        return obj

    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> Self:
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
    ) -> None:
        ...

    @overload
    async def move(
        self,
        *,
        end: bool,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None:
        ...

    @overload
    async def move(
        self,
        *,
        before: Snowflake,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None:
        ...

    @overload
    async def move(
        self,
        *,
        after: Snowflake,
        offset: int = MISSING,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = MISSING,
        reason: str = MISSING,
    ) -> None:
        ...

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
            The channel that should be before our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``after``.
        after: :class:`~discord.abc.Snowflake`
            The channel that should be after our current channel.
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
        payload = []
        lock_permissions = kwargs.get('sync_permissions', False)
        reason = kwargs.get('reason')
        for index, channel in enumerate(channels):
            d = {'id': channel.id, 'position': index}
            if parent_id is not MISSING and channel.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await self._state.http.bulk_channel_update(self.guild.id, payload, reason=reason)

    async def create_invite(  # TODO: add validate
        self,
        *,
        reason: Optional[str] = None,
        max_age: int = 0,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        validate: Optional[Union[Invite, str]],
        target_type: Optional[InviteTarget] = None,
        target_user: Optional[User] = None,
        target_application: Optional[Snowflake] = None,
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
        validate: Union[:class:`.Invite`, :class:`str`]
            The existing channel invite to validate and return for reuse.
            If this invite is invalid, a new invite will be created according to the parameters and returned.

            .. versionadded:: 2.0
        target_type: Optional[:class:`.InviteTarget`]
            The type of target for the voice channel invite, if any.

            .. versionadded:: 2.0

        target_user: Optional[:class:`User`]
            The user whose stream to display for this invite, required if ``target_type`` is :attr:`.InviteTarget.stream`. The user must be streaming in the channel.

            .. versionadded:: 2.0

        target_application:: Optional[:class:`.Application`]
            The embedded application for the invite, required if ``target_type`` is :attr:`.InviteTarget.embedded_application`.

            .. versionadded:: 2.0

        reason: Optional[:class:`str`]
            The reason for creating this invite. Shows up on the audit log.

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

        data = await self._state.http.create_invite(
            self.id,
            reason=reason,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            validate=utils.resolve_invite(validate).code if validate else None,
            target_type=target_type.value if target_type else None,
            target_user_id=target_user.id if target_user else None,
            target_application_id=target_application.id if target_application else None,
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

    The following implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
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
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        suppress_embeds: bool = False,
        silent: bool = False,
    ) -> Message:
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then a sticker or file must be sent.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~discord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~discord.File` objects.
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
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: :class:`int`
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value. Generates one by default.
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
            A reference to the :class:`~discord.Message` to which you are replying, this can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.

            .. versionadded:: 1.6

        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

            .. versionadded:: 1.6
        stickers: Sequence[Union[:class:`~discord.GuildSticker`, :class:`~discord.StickerItem`]]
            A list of stickers to upload. Must be a maximum of 3.

            .. versionadded:: 2.0
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This sends the message without any embeds if set to ``True``.

            .. versionadded:: 2.0
        silent: :class:`bool`
            Whether to suppress push and desktop notifications for the message. This will increment the mention counter
            in the UI, but will not actually send a notification.

            .. versionadded:: 2.0

        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ValueError
            The ``files`` list is not of the appropriate size.
        TypeError
            You specified both ``file`` and ``files``,
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

        if nonce is MISSING:
            nonce = utils._generate_nonce()

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

        if suppress_embeds or silent:
            from .message import MessageFlags  # circular import

            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = silent
        else:
            flags = MISSING

        with handle_message_parameters(
            content=content,
            tts=tts,
            file=file if file is not None else MISSING,
            files=files if files is not None else MISSING,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            message_reference=reference_dict,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=mention_author,
            stickers=sticker_ids,
            flags=flags,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)

        ret = state.create_message(channel=channel, data=data)

        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret

    async def greet(
        self,
        sticker: Union[GuildSticker, StickerItem],
        *,
        allowed_mentions: AllowedMentions = MISSING,
        reference: Union[Message, MessageReference, PartialMessage] = MISSING,
        mention_author: bool = MISSING,
    ) -> Message:
        """|coro|

        Sends a sticker greeting to the destination.

        A sticker greeting is used to begin a new DM or reply to a system message.

        .. versionadded:: 2.0

        Parameters
        ------------
        sticker: Union[:class:`~discord.GuildSticker`, :class:`~discord.StickerItem`]
            The sticker to greet with.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead. In the case of greeting, only :attr:`~discord.AllowedMentions.replied_user` is
            considered.
        reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`, :class:`~discord.PartialMessage`]
            A reference to the :class:`~discord.Message` to which you are replying, this can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.
        mention_author: :class:`bool`
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message, or this is not a valid greet context.
        TypeError
            The ``reference`` object is not a :class:`~discord.Message`,
            :class:`~discord.MessageReference` or :class:`~discord.PartialMessage`.

        Returns
        ---------
        :class:`~discord.Message`
            The sticker greeting that was sent.
        """
        channel = await self._get_channel()
        state = self._state
        previous_allowed_mention = state.allowed_mentions

        if reference:
            try:
                reference_dict = reference.to_message_reference_dict()
            except AttributeError:
                raise TypeError('reference parameter must be Message, MessageReference, or PartialMessage') from None
        else:
            reference_dict = MISSING

        if allowed_mentions:
            if previous_allowed_mention:
                allowed_mentions = previous_allowed_mention.merge(allowed_mentions)
        if mention_author is not MISSING:
            if not allowed_mentions:
                allowed_mentions = AllowedMentions()
            allowed_mentions.replied_user = mention_author
        if allowed_mentions and allowed_mentions.replied_user:
            # No point sending them
            allowed_mentions = MISSING

        data = await state.http.send_greet(
            channel.id, sticker.id, message_reference=reference_dict, allowed_mentions=allowed_mentions
        )
        return state.create_message(channel=channel, data=data)

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

    async def ack(self) -> None:
        """|coro|

        Marks every message in this channel as read.

        Raises
        -------
        ~discord.HTTPException
            Acking the channel failed.
        """
        channel = await self._get_channel()
        await self._state.http.ack_message(channel.id, channel.last_message_id or utils.time_snowflake(utils.utcnow()))

    async def ack_pins(self) -> None:
        """|coro|

        Marks a channel's pins as viewed.

        Raises
        -------
        ~discord.HTTPException
            Acking the pinned messages failed.
        """
        channel = await self._get_channel()
        await self._state.http.ack_pins(channel.id)

    async def pins(self) -> List[Message]:
        """|coro|

        Retrieves all messages that are currently pinned in the channel.

        .. note::

            Due to a limitation with the Discord API, the :class:`.Message`
            objects returned by this method do not contain complete
            :attr:`.Message.reactions` data.

        Raises
        -------
        ~discord.Forbidden
            You do not have the permission to retrieve pinned messages.
        ~discord.HTTPException
            Retrieving the pinned messages failed.

        Returns
        --------
        List[:class:`~discord.Message`]
            The messages that are currently pinned.
        """
        channel = await self._get_channel()
        state = self._state
        data = await state.http.pins_from(channel.id)
        return [state.create_message(channel=channel, data=m) for m in data]

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
                return []

            around_id = around.id if around else None
            data = await self._state.http.logs_from(channel.id, retrieve, around=around_id)

            return data, None, limit

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
                raise ValueError("history max limit 101 when specifying around parameter")

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

    def slash_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[SlashCommand]:
        """Returns a :term:`asynchronous iterator` of the slash commands available in the channel.

        Examples
        ---------

        Usage ::

            async for command in channel.slash_commands():
                print(command.name)

        Flattening into a list ::

            commands = [command async for command in channel.slash_commands()]
            # commands is now a list of SlashCommand...

        All parameters are optional.

        Parameters
        ----------
        query: Optional[:class:`str`]
            The query to search for. Specifying this limits results to 25 commands max.

            This parameter is faked if ``application`` is specified.
        limit: Optional[:class:`int`]
            The maximum number of commands to send back. Defaults to 0 if ``command_ids`` is passed, else 25.
            If ``None``, returns all commands.

            This parameter is faked if ``application`` is specified.
        command_ids: Optional[List[:class:`int`]]
            List of up to 100 command IDs to search for. If the command doesn't exist, it won't be returned.

            If ``limit`` is passed alongside this parameter, this parameter will serve as a "preferred commands" list.
            This means that the endpoint will return the found commands + up to ``limit`` more, if available.
        application: Optional[:class:`~discord.abc.Snowflake`]
            Whether to return this application's commands. Always set to DM recipient in a private channel context.
        with_applications: :class:`bool`
            Whether to include applications in the response. Defaults to ``True``.

        Raises
        ------
        TypeError
            Both query and command_ids are passed.
            Attempted to fetch commands in a DM with a non-bot user.
        ValueError
            The limit was not greater than or equal to 0.
        HTTPException
            Getting the commands failed.
        ~discord.Forbidden
            You do not have permissions to get the commands.
        ~discord.HTTPException
            The request to get the commands failed.

        Yields
        -------
        :class:`.SlashCommand`
            A slash command.
        """
        return _handle_commands(
            self,
            AppCommandType.chat_input,
            query=query,
            limit=limit,
            command_ids=command_ids,
            application=application,
            with_applications=with_applications,
        )

    def user_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[UserCommand]:
        """Returns a :term:`asynchronous iterator` of the user commands available to use on the user.

        Examples
        ---------

        Usage ::

            async for command in user.user_commands():
                print(command.name)

        Flattening into a list ::

            commands = [command async for command in user.user_commands()]
            # commands is now a list of UserCommand...

        All parameters are optional.

        Parameters
        ----------
        query: Optional[:class:`str`]
            The query to search for. Specifying this limits results to 25 commands max.

            This parameter is faked if ``application`` is specified.
        limit: Optional[:class:`int`]
            The maximum number of commands to send back. Defaults to 0 if ``command_ids`` is passed, else 25.
            If ``None``, returns all commands.

            This parameter is faked if ``application`` is specified.
        command_ids: Optional[List[:class:`int`]]
            List of up to 100 command IDs to search for. If the command doesn't exist, it won't be returned.

            If ``limit`` is passed alongside this parameter, this parameter will serve as a "preferred commands" list.
            This means that the endpoint will return the found commands + up to ``limit`` more, if available.
        application: Optional[:class:`~discord.abc.Snowflake`]
            Whether to return this application's commands. Always set to DM recipient in a private channel context.
        with_applications: :class:`bool`
            Whether to include applications in the response. Defaults to ``True``.

        Raises
        ------
        TypeError
            Both query and command_ids are passed.
            Attempted to fetch commands in a DM with a non-bot user.
        ValueError
            The limit was not greater than or equal to 0.
        HTTPException
            Getting the commands failed.
        ~discord.Forbidden
            You do not have permissions to get the commands.
        ~discord.HTTPException
            The request to get the commands failed.

        Yields
        -------
        :class:`.UserCommand`
            A user command.
        """
        return _handle_commands(
            self,
            AppCommandType.user,
            query=query,
            limit=limit,
            command_ids=command_ids,
            application=application,
            with_applications=with_applications,
        )


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
    - :class:`~discord.User`
    - :class:`~discord.Member`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> VocalChannel:
        raise NotImplementedError

    def _get_voice_client_key(self) -> Tuple[int, str]:
        raise NotImplementedError

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        raise NotImplementedError

    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, VocalChannel], T] = VoiceClient,
        _channel: Optional[Connectable] = None,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> T:
        """|coro|

        Connects to voice and creates a :class:`~discord.VoiceClient` to establish
        your connection to the voice server.

        Parameters
        -----------
        timeout: :class:`float`
            The timeout in seconds to wait for the voice endpoint.
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
        connectable = _channel or self
        channel = await connectable._get_channel()

        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel')

        voice: T = cls(state.client, channel)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError('Type must meet VoiceProtocol abstract base class')

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf, self_mute=self_mute)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                pass  # We don't care if disconnect failed because connection failed
            raise  # Re-raise

        return voice
