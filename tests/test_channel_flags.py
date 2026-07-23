import pytest

from discord.channel import StageChannel, TextChannel
from discord.flags import ChannelFlags


def test_spoiler_channel_flag():
    flags = ChannelFlags()

    assert flags.spoiler is False

    flags.spoiler = True

    assert flags.spoiler is True
    assert flags.value == 1 << 21


def test_spoiler_channel_flag_preserves_other_flags():
    flags = ChannelFlags._from_value((1 << 4) | (1 << 15))
    flags.spoiler = True

    assert flags.value == (1 << 4) | (1 << 15) | (1 << 21)


class _HTTP:
    async def edit_channel(self, channel_id, *, reason, **options):
        self.channel_id = channel_id
        self.reason = reason
        self.options = options
        return {
            'id': str(channel_id),
            'type': 0,
            'name': 'spoilers',
            'position': 0,
            'permission_overwrites': [],
            'flags': options['flags'],
        }


class _State:
    def __init__(self):
        self.http = _HTTP()


class _Guild:
    id = 1


@pytest.mark.asyncio
async def test_text_channel_edit_sets_spoiler_flag():
    state = _State()
    channel = TextChannel(
        state=state,
        guild=_Guild(),
        data={
            'id': '1',
            'type': 0,
            'name': 'spoilers',
            'position': 0,
            'permission_overwrites': [],
            'flags': 1 << 4,
        },
    )

    edited = await channel.edit(spoiler=True)

    assert state.http.options == {'flags': (1 << 4) | (1 << 21)}
    assert edited is not None
    assert edited.flags.spoiler is True
    assert edited.is_spoiler() is True


class _StageHTTP(_HTTP):
    async def edit_channel(self, channel_id, *, reason, **options):
        self.channel_id = channel_id
        self.reason = reason
        self.options = options
        return {
            'id': str(channel_id),
            'type': 13,
            'name': 'spoilers',
            'position': 0,
            'permission_overwrites': [],
            'bitrate': 64000,
            'user_limit': 0,
            'flags': options['flags'],
        }


@pytest.mark.asyncio
async def test_stage_channel_edit_sets_spoiler_flag():
    state = _State()
    state.http = _StageHTTP()
    channel = StageChannel(
        state=state,
        guild=_Guild(),
        data={
            'id': '1',
            'type': 13,
            'name': 'spoilers',
            'position': 0,
            'permission_overwrites': [],
            'bitrate': 64000,
            'user_limit': 0,
            'flags': 1 << 4,
        },
    )

    edited = await channel.edit(spoiler=True)

    assert state.http.options == {'flags': (1 << 4) | (1 << 21)}
    assert edited is not None
    assert edited.flags.spoiler is True
    assert edited.is_spoiler() is True
