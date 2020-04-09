from .utils import parse_time, snowflake_time, _get_as_snowflake, get, _bytes_to_base64_data
from .enums import VoiceRegion, ChannelType, try_enum, VerificationLevel, ContentFilter, NotificationLevel
from .mixins import Hashable
from .guild import Guild
from .permissions import Permissions, PermissionOverwrite

class TemplateChannel(Hashable):
    """The base class for :class:`TemplateTextChannel`, :class:`TemplateVoiceChannel`, and :class:`TemplateCategoryChannel`.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`~discord.Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    category: Optional[:class:`TemplateCategoryChannel`]
        The category channel this channel belongs to, if applicable.
    """

    def __init__(self, *, guild, data):
        self.guild = guild
        self.id = int(data['id'])
        self.name = data['name']
        self.category_id = _get_as_snowflake(data, 'parent_id')
        self.category = guild.get_channel(self.category_id)
        self.position = data['position']
        self.nsfw = data.get('nsfw', False)
        self._type = data['type']
        self.type = try_enum(ChannelType, self._type)

        overwrites = data.get('permission_overwrites')
        self._overwrites = {}

        for overwrite in overwrites:
            role = guild.get_role(overwrite['id'])
            allow = Permissions(overwrite['allow'])
            deny = Permissions(overwrite['deny'])
            self._overwrites[role] = PermissionOverwrite.from_pair(allow, deny)

    @property
    def _sorting_bucket(self):
        return self.type.value

    def overwrites_for(self, obj):
        """Returns the channel-specific overwrites for a member or a role.
        
        Parameters
        -----------
        obj: Union[:class:`~discord.Role`, :class:`~discord.abc.User`]
            The role or user denoting
            whose overwrite to get.
        
        Returns
        ---------
        :class:`~discord.PermissionOverwrite`
            The permission overwrites for this object.
        """
        overwrites = self._overwrites.get(obj)
        
        return overwrites or PermissionOverwrite()

    @property
    def permissions_synced(self):
        """:class:`bool`: Whether or not the permissions for this channel are synced with the
        category it belongs to.

        If there is no category then this is ``False``.
        """
        return bool(self.category and self.category.overwrites == self.overwrites)

    def is_nsfw(self):
        """Checks if the channel is NSFW."""
        return self.nsfw

class TemplateTextChannel(TemplateChannel):
    """Represents a Discord guild template's text channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    topic: Optional[:class:`str`]
        The channel's topic. None if it doesn't exist.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of `0` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    """

    def __init__(self, *, guild, data):
        super().__init__(guild=guild, data=data)
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self.topic = data.get('topic')

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('news', self.is_news()),
            ('category_id', self.category_id)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

class TemplateVoiceChannel(TemplateChannel):
    """Represents a Discord guild template's voice channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a voice channel.
    """

    def __init__(self, *, guild, data):
        super().__init__(guild=guild, data=data)
        self.bitrate = data.get('bitrate')
        self.user_limit = data.get('user_limit')

    def __repr__(self):
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

class TemplateCategoryChannel(TemplateChannel):
    """Represents a Discord template guild's channel category.

    These are useful to group channels to logical compartments.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the category's name.

    Attributes
    -----------
    name: :class:`str`
        The category name.
    guild: :class:`Guild`
        The guild the category belongs to.
    id: :class:`int`
        The category channel ID.
    position: :class:`int`
        The position in the category list. This is a number that starts at 0. e.g. the
        top category is position 0.
    """

    def __repr__(self):
        return '<TemplateCategoryChannel id={0.id} name={0.name!r} position={0.position} nsfw={0.nsfw}>'.format(self)

    @property
    def channels(self):
        """List[:class:`abc.GuildChannel`]: Returns the channels that are under this category.
        
        These are sorted by the official Discord UI, which places voice channels below the text channels.
        """
        def comparator(channel):
            return (not isinstance(channel, TextChannel), channel.position)

        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret
        
    @property
    def text_channels(self):
        """List[:class:`TemplateTextChannel`]: Returns the text channels that are under this category."""
        ret = [c for c in self.guild.channels
            if c.category_id == self.id
            and isinstance(c, TemplateTextChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def voice_channels(self):
        """List[:class:`TemplateVoiceChannel`]: Returns the voice channels that are under this category."""
        ret = [c for c in self.guild.channels
            if c.category_id == self.id
            and isinstance(c, TemplateVoiceChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

class TemplateRole(Hashable):
    """Represents a Discord role in a :class:`TemplateGuild`.

    .. container:: operations

        .. describe:: x == y

            Checks if two roles are equal.

        .. describe:: x != y

            Checks if two roles are not equal.

        .. describe:: x > y

            Checks if a role is higher than another in the hierarchy.

        .. describe:: x < y

            Checks if a role is lower than another in the hierarchy.

        .. describe:: x >= y

            Checks if a role is higher or equal to another in the hierarchy.

        .. describe:: x <= y

            Checks if a role is lower or equal to another in the hierarchy.

        .. describe:: hash(x)

            Return the role's hash.

        .. describe:: str(x)

            Returns the role's name.

    Attributes
    ----------
    id: :class:`int`
        The ID for the role.
    name: :class:`str`
        The name of the role.
    guild: :class:`Guild`
        The guild the role belongs to.
    hoist: :class:`bool`
         Indicates if the role will be displayed separately from other members.
    position: :class:`int`
        The position of the role. This number is usually positive. The bottom
        role has a position of 0.
    mentionable: :class:`bool`
        Indicates if the role can be mentioned by users.
    """

    def __init__(self, *, guild, data):
        self.guild = guild
        self.id = int(data['id'])
        self.name = data['name']
        self._permissions = data.get('permissions', 0)
        self.position = data.get('position', 0)
        self._colour = data.get('color', 0)
        self.hoist = data.get('hoist', False)
        self.mentionable = data.get('mentionable', False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<TemplateRole id={0.id} name={0.name!r}>'.format(self)

    def __lt__(self, other):
        if not isinstance(other, TemplateRole) or not isinstance(self, TemplateRole):
            return NotImplemented

        if self.guild != other.guild:
            raise RuntimeError('cannot compare roles from two different guilds.')

        # the @everyone role is always the lowest role in hierarchy
        guild_id = self.guild.id
        if self.id == guild_id:
            # everyone_role < everyone_role -> False
            return other.id != guild_id

        if self.position < other.position:
            return True

        if self.position == other.position:
            return int(self.id) > int(other.id)

        return False

    def __le__(self, other):
        r = Role.__lt__(other, self)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def __gt__(self, other):
        return Role.__lt__(other, self)

    def __ge__(self, other):
        r = Role.__lt__(self, other)
        if r is NotImplemented:
            return NotImplemented
        return not r
    
    @property
    def permissions(self):
        """:class:`Permissions`: Returns the role's permissions."""
        return Permissions(self._permissions)

    @property
    def colour(self):
        """:class:`Colour`: Returns the role colour. An alias exists under ``color``."""
        return Colour(self._colour)

    @property
    def color(self):
        """:class:`Colour`: Returns the role color. An alias exists under ``colour``."""
        return self.colour


class TemplateGuild(Hashable):
    """Represents a Discord template's guild.

    This is referred to as a "server" in the official Discord UI.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    name: :class:`str`
        The source guild's name.
    afk_timeout: :class:`int`
        The timeout to get sent to the AFK channel.
    afk_channel: Optional[:class:`VoiceChannel`]
        The channel that denotes the AFK channel. None if it doesn't exist.
    id: :class:`int`
        The source guild's ID.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    default_notifications: :class:`NotificationLevel`
        The guild's notification settings.
    preferred_locale: Optional[:class:`str`]
        The preferred locale for the guild. Used when filtering Server Discovery
        results to a specific language.
    description: Optional[:class:`str`]
        The guild's description.
    """
    def __init__(self, *, id, data):
        self.id = id
        self.name = data['name']
        self.description = data.get('description')
        self.verification_level = try_enum(VerificationLevel, data.get('verification_level'))
        self.default_notifications = try_enum(NotificationLevel, data.get('default_message_notifications'))
        self.explicit_content_filter = try_enum(ContentFilter, data.get('explicit_content_filter', 0))
        self.afk_timeout = data.get('afk_timeout')
        self.preferred_locale = data.get('preferred_locale')
        self._system_channel_id = _get_as_snowflake(data, 'system_channel_id')
        self._system_channel_flags = data.get('system_channel_flags', 0)

        self._roles = {}

        for role in data.get('roles', []):
            r = TemplateRole(guild=self, data=role)
            self._roles[r.id] = r

        self._channels = {}

        for channel in data.get('channels', []):
            type = try_enum(ChannelType, channel['type'])
            if type == ChannelType.text:
                cls = TemplateTextChannel
            elif type == ChannelType.voice:
                cls = TemplateVoiceChannel
            elif type == ChannelType.category:
                cls = TemplateCategoryChannel
            else:
                cls = TemplateChannel
            
            c = cls(guild=self, data=channel)
            self._channels[c.id] = c

        self.afk_channel = self.get_channel(_get_as_snowflake(data, 'afk_channel_id'))

    def __repr__(self):
        return '<TemplateGuild id={0.id} name={0.name!r}>'.format(self)

    @property
    def channels(self):
        """List[:class:`TemplateChannel`]: A list of channels that belongs to this guild."""
        return self._channels.values()

    @property
    def voice_channels(self):
        """List[:class:`TemplateVoiceChannel`]: A list of voice channels that belongs to this guild.
        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TemplateVoiceChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def text_channels(self):
        """List[:class:`TemplateTextChannel`]: A list of text channels that belongs to this guild.
        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TemplateTextChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def categories(self):
        """List[:class:`TemplateCategoryChannel`]: A list of categories that belongs to this guild.
        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TemplateCategoryChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    def by_category(self):
        """Returns every :class:`TemplateCategoryChannel` and their associated channels.
        These channels and categories are sorted in the official Discord UI order.
        If the channels do not have a category, then the first element of the tuple is
        ``None``.
        Returns
        --------
        List[Tuple[Optional[:class:`TemplateCategoryChannel`], List[:class:`TemplateChannel`]]]:
            The categories and their associated channels.
        """
        grouped = defaultdict(list)
        for channel in self._channels.values():
            if isinstance(channel, TemplateCategoryChannel):
                continue

            grouped[channel.category_id].append(channel)

        def key(t):
            k, v = t
            return ((k.position, k.id) if k else (-1, -1), v)

        _get = self._channels.get
        as_list = [(_get(k), v) for k, v in grouped.items()]
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=lambda c: (c._sorting_bucket, c.position, c.id))
        return as_list

    def get_channel(self, channel_id):
        """Returns a channel with the given ID.
        Parameters
        -----------
        channel_id: :class:`int`
            The ID to search for.
        Returns
        --------
        Optional[:class:`TemplateChannel`]
            The returned channel or ``None`` if not found.
        """
        return self._channels.get(channel_id)

    @property
    def system_channel(self):
        """Optional[:class:`TemplateTextChannel`]: Returns the guild's channel used for system messages.
        If no channel is set, then this returns ``None``.
        """
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)

    @property
    def system_channel_flags(self):
        """:class:`SystemChannelFlags`: Returns the guild's system channel settings."""
        return SystemChannelFlags._from_value(self._system_channel_flags)

    @property
    def roles(self):
        """Returns a :class:`list` of the guild's roles in hierarchy order.
        The first element of this list will be the lowest role in the
        hierarchy.
        """
        return sorted(self._roles.values())

    def get_role(self, role_id):
        """Returns a role with the given ID.
        Parameters
        -----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`TemplateRole`]
            The role or ``None`` if not found.
        """
        return self._roles.get(role_id)

class Template:
    """Represents a Discord template.

    Attributes
    -----------
    code: :code:`str`
        The template code.
    uses: :class:`int`
        How many time the template has been used.
    name: :class:`str`
        The name of the template.
    description: :class:`str`
        The description of the template.
    creator: :class:`User`
        The creator of the template.
    created_at: :class:`datetime.datetime`
        When the template was created.
    updated_at: :class:`datetime.datetime`
        When the template was last updated. (Referred to as "last synced" in the client.)
    source_guild: :class:`TemplateGuild`
        The source guild.
    """

    def __init__(self, *, state, data, custom=False):
        self._state = state

        self.code = data['code']
        self.uses = data['usage_count']
        self.name =  data['name']
        self.description = data['description']
        creator_data = data.get('creator')
        self.creator = None if creator_data is None else self._state.store_user(creator_data)

        self.created_at = parse_time(data.get('created_at'))
        self.updated_at = parse_time(data.get('updated_at'))
        source_id = _get_as_snowflake(data, 'source_guild_id')
        source_serialised = data['serialized_source_guild']
        self.source_guild = TemplateGuild(id=source_id, data=source_serialised)

    def __repr__(self):
        return '<Template code={0.code!r} uses={0.uses} name={0.name!r} creator={0.creator!r} source_guild={0.source_guild!r}>'.format(self)

    async def create_guild(self, name, region=None, icon=None):
        """|coro|

        Creates a :class:`.Guild` using the template.

        Bot accounts in more than 10 guilds are not allowed to create guilds.

        Parameters
        ----------
        name: :class:`str`
            The name of the guild.
        region: :class:`.VoiceRegion`
            The region for the voice communication server.
            Defaults to :attr:`.VoiceRegion.us_west`.
        icon: :class:`bytes`
            The :term:`py:bytes-like object` representing the icon. See :meth:`.ClientUser.edit`
            for more details on what is expected.

        Raises
        ------
        :exc:`.HTTPException`
            Guild creation failed.
        :exc:`.InvalidArgument`
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`.Guild`
            The guild created. This is not the same guild that is
            added to cache.
        """
        if icon is not None:
            icon = _bytes_to_base64_data(icon)

        if region is None:
            region = VoiceRegion.us_west.value
        else:
            region = region.value

        data = await self._state.http.create_from_template(self.code, name, region, icon)
        return Guild(data=data, state=self._sate)
