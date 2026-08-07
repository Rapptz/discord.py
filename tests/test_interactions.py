from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock

import pytest
import discord
from discord.webhook.async_ import async_context
from discord.errors import ClientException
from discord.channel import PartialMessageable


@pytest.mark.asyncio
async def test_interaction_original_response_channel_fallback():
    state = MagicMock()
    data = {
        'id': '123456',
        'type': 2,
        'token': 'mock_token',
        'version': 1,
        'application_id': '987654',
        'user': {'id': '111', 'username': 'testuser', 'discriminator': '0000'},
        'attachment_size_limit': 10485760,
    }
    interaction = discord.Interaction(data=data, state=state)
    interaction.channel = None

    mock_adapter = AsyncMock()
    mock_adapter.get_original_interaction_response.return_value = {
        'id': '55555',
        'channel_id': '66666',
        'author': {'id': '111', 'username': 'testuser', 'discriminator': '0000'},
        'content': 'hello world',
        'type': 0,
        'timestamp': '2026-08-07T20:00:00+00:00',
        'tts': False,
        'mention_everyone': False,
        'mentions': [],
        'role_mentions': [],
        'attachments': [],
        'embeds': [],
        'pinned': False,
    }

    token = async_context.set(mock_adapter)
    try:
        msg = await interaction.original_response()
        assert isinstance(msg.channel, PartialMessageable)
        assert msg.channel.id == 66666
    finally:
        async_context.reset(token)


@pytest.mark.asyncio
async def test_interaction_original_response_channel_unresolvable_raises():
    state = MagicMock()
    data = {
        'id': '123456',
        'type': 2,
        'token': 'mock_token',
        'version': 1,
        'application_id': '987654',
        'user': {'id': '111', 'username': 'testuser', 'discriminator': '0000'},
        'attachment_size_limit': 10485760,
    }
    interaction = discord.Interaction(data=data, state=state)
    interaction.channel = None

    mock_adapter = AsyncMock()
    mock_adapter.get_original_interaction_response.return_value = {
        'id': '55555',
        'author': {'id': '111', 'username': 'testuser', 'discriminator': '0000'},
        'content': 'hello world',
        'type': 0,
        'timestamp': '2026-08-07T20:00:00+00:00',
        'tts': False,
        'mention_everyone': False,
        'mentions': [],
        'role_mentions': [],
        'attachments': [],
        'embeds': [],
        'pinned': False,
    }

    token = async_context.set(mock_adapter)
    try:
        with pytest.raises(ClientException, match='Channel for message could not be resolved'):
            await interaction.original_response()
    finally:
        async_context.reset(token)
