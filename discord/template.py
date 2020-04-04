from .utils import parse_time, snowflake_time, _get_as_snowflake
from .enums import VoiceRegion, ChannelType, try_enum, VerificationLevel, ContentFilter, NotificationLevel
from .guild import Guild


class TemplateChannel:
    def __init__(self, *, guild, data):
        self.guild = guild
        self.id = int(data['id'])
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.topic = data.get('topic')
        self.position = data['position']
        self.bitrate = data.get('bitrate')
        self.user_limit = data.get('user_limit')
        self.nsfw = data.get('nsfw', False)
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._type = data.get('type', self._type)

    


class TemplateRole:
    def __init__(self, *, guild, data):
        self.guild = guild
        self.id = int(data['id'])
        self.name = data['name']
        self._permissions = data.get('permissions', 0)
        self.position = data.get('position', 0)
        self._colour = data.get('color', 0)
        self.hoist = data.get('hoist', False)
        self.managed = data.get('managed', False)
        self.mentionable = data.get('mentionable', False)


class TemplateGuild:
    def __init__(self, *, id, data):
        self.id = id
        self.name = data['name']
        self.description = data.get('description')
        self.verification_level = try_enum(VerificationLevel, data.get('verification_level'))
        self.default_notifications = try_enum(NotificationLevel, data.get('default_message_notifications'))
        self.explicit_content_filter = try_enum(ContentFilter, data.get('explicit_content_filter', 0))
        self.afk_timeout = data.get('afk_timeout')
        self.preferred_locale = data.get('preferred_locale')
        self.afk_channel = self.get_channel(utils._get_as_snowflake(guild, 'afk_channel_id'))
        self._system_channel_id = utils._get_as_snowflake(guild, 'system_channel_id')
        self._system_channel_flags = guild.get('system_channel_flags', 0)

        self.roles = []

        for role in data.get('roles', []):
            self.roles.append(TemplateRole(guild=self, data=role))

        self.channels = []

        for channel in data.get('channels', []):
            self.channels.append(TemplateChannel(guild=self, data=channel))     


class Template:
    def __init__(self, *, state, data):
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

    async def create_guild(self, name, region=None, icon=None):
        if icon is not None:
            icon = utils._bytes_to_base64_data(icon)

        if region is None:
            region = VoiceRegion.us_west.value
        else:
            region = region.value

        data = await self._state.http.create_from_template(self.code, name, region, icon)
        return Guild(data=data, state=self._sate)
