"""
Example showing how to use DAVE E2EE voice encryption with discord.py.

This requires:
1. discord.py with binary WebSocket support (v2.7+)
2. Dave4Py library: pip install pydave
3. PyNaCl: pip install pynacl

DAVE (Discord's Audio/Video E2EE) provides end-to-end encryption for voice channels.
"""

import discord
from discord.ext import commands
import asyncio
import logging

# Import Dave4Py integration
try:
    from pydave.integrations import DiscordVoiceDAVE
    HAVE_DAVE = True
except ImportError:
    HAVE_DAVE = False
    print("Dave4Py not installed. Install with: pip install pydave")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dave_bot')


class DAVEVoiceBot(commands.Bot):
    """A Discord bot with DAVE E2EE voice encryption support."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Track DAVE handlers per guild
        self.dave_handlers = {}
    
    async def setup_hook(self):
        """Called when the bot is starting up."""
        if not HAVE_DAVE:
            logger.warning("Dave4Py not available - voice encryption disabled")
        else:
            logger.info("Dave4Py loaded - voice encryption available")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')


bot = DAVEVoiceBot()


@bot.command(name='join')
async def join_voice(ctx: commands.Context):
    """Join a voice channel with DAVE encryption."""
    if not HAVE_DAVE:
        await ctx.send("❌ Dave4Py not installed!")
        return
    
    if not ctx.author.voice:
        await ctx.send('❌ You need to be in a voice channel!')
        return
    
    channel = ctx.author.voice.channel
    
    try:
        # Connect to voice
        voice_client = await channel.connect()
        
        # Create DAVE handler
        dave_handler = DiscordVoiceDAVE(
            user_id=bot.user.id,
            channel_id=channel.id,
        )
        
        # Setup binary message handler
        async def handle_dave_message(opcode: int, payload: bytes):
            """Handle incoming DAVE messages."""
            try:
                await dave_handler.handle_binary_message(opcode, payload)
                logger.info(f"Handled DAVE opcode {opcode}")
            except Exception as e:
                logger.error(f"Error handling DAVE message: {e}")
        
        voice_client.add_binary_message_handler(handle_dave_message)
        
        # Setup WebSocket send callbacks
        async def send_ws_message(data: dict):
            """Send JSON message to voice gateway."""
            # For IDENTIFY messages, inject DAVE protocol version
            if data.get('op') == 0:  # IDENTIFY
                dave_identify = dave_handler.get_identify_payload()
                data['d'].update(dave_identify)
                logger.info(f"Added DAVE to IDENTIFY: {dave_identify}")
            
            # discord.py automatically sends JSON messages
            # This is just for logging/monitoring
            logger.debug(f"WS message: {data}")
        
        async def send_binary_message(opcode: int, payload: bytes):
            """Send binary message to voice gateway."""
            await voice_client.send_binary_message(opcode, payload)
            logger.info(f"Sent DAVE binary message: opcode={opcode}, len={len(payload)}")
        
        # Attach callbacks to DAVE handler
        dave_handler.on_send_ws = send_ws_message
        dave_handler.on_send_binary = send_binary_message
        
        # Store handler
        bot.dave_handlers[ctx.guild.id] = dave_handler
        
        await ctx.send(f'✅ Joined {channel.name} with DAVE encryption!\n'
                      f'📊 DAVE Protocol: v{dave_handler.max_protocol_version}\n'
                      f'🔒 E2EE Status: {"Enabled" if dave_handler.ready else "Initializing..."}')
        
    except Exception as e:
        await ctx.send(f'❌ Failed to join voice: {e}')
        logger.exception("Failed to join voice channel")


@bot.command(name='leave')
async def leave_voice(ctx: commands.Context):
    """Leave the voice channel."""
    if ctx.guild.id in bot.dave_handlers:
        # Clean up DAVE handler
        dave_handler = bot.dave_handlers.pop(ctx.guild.id)
        dave_handler.reset()
        logger.info("DAVE handler cleaned up")
    
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('✅ Disconnected from voice')
    else:
        await ctx.send('❌ Not in a voice channel')


@bot.command(name='dave_status')
async def dave_status(ctx: commands.Context):
    """Check DAVE encryption status."""
    if ctx.guild.id not in bot.dave_handlers:
        await ctx.send('❌ Not using DAVE encryption')
        return
    
    dave = bot.dave_handlers[ctx.guild.id]
    
    status_msg = [
        '📊 **DAVE Encryption Status**',
        f'🔒 Protocol Version: v{dave.max_protocol_version}',
        f'✅ Ready: {dave.ready}',
        f'👥 Connected Users: {len(dave.clients)}',
    ]
    
    if dave.clients:
        status_msg.append('\n**Connected Clients:**')
        for user_id in dave.clients:
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f'User {user_id}'
            status_msg.append(f'  • {name}')
    
    await ctx.send('\n'.join(status_msg))


@bot.command(name='dave_info')
async def dave_info(ctx: commands.Context):
    """Show information about DAVE encryption."""
    info = [
        '🔐 **DAVE (Discord Audio/Video E2EE)**',
        '',
        'DAVE provides end-to-end encryption for Discord voice channels.',
        '',
        '**Features:**',
        '• End-to-end encrypted voice using MLS (Message Layer Security)',
        '• Automatic key management and rotation',
        '• Perfect forward secrecy',
        '• Post-compromise security',
        '',
        '**Commands:**',
        '• `!join` - Join voice with DAVE encryption',
        '• `!leave` - Leave voice channel',
        '• `!dave_status` - Check encryption status',
        '',
        '**Requirements:**',
        '• discord.py 2.7+ with binary WebSocket support',
        '• Dave4Py: `pip install pydave`',
        '• PyNaCl: `pip install pynacl`',
    ]
    
    await ctx.send('\n'.join(info))


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment")
        print("Create a .env file with: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)
    
    bot.run(token)
