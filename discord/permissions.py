# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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

class Permissions(object):
    """Wraps up the Discord permission value.

    Instance attributes:

    .. attribute:: value

        The raw value. This value is a bit array field of a 32-bit integer representing the
        currently available permissions. You should query permissions via the member functions provided rather
        than using this raw value.
    """

    def __init__(self, permissions):
        self.value = permissions

    def _bit(self, index):
        return bool((self.value >> index) & 1)

    def can_create_instant_invite(self):
        """Returns True if the user can create instant invites."""
        return self._bit(0)

    def can_ban_members(self):
        """Returns True if the user can ban users from the server."""
        return self._bit(1)

    def can_kick_members(self):
        """Returns True if a user can kick users from the server."""
        return self._bit(2)

    def can_manage_roles(self):
        """Returns True if a user can manage server roles. This role overrides all other permissions."""
        return self._bit(3)

    def can_manage_channels(self):
        """Returns True if a user can edit, delete, or create channels in the server."""
        return self._bit(4)

    def can_manage_server(self):
        """Returns True if a user can edit server properties."""
        return self._bit(5)

    # 4 unused

    def can_read_messages(self):
        """Returns True if a user can read messages from all or specific text channels."""
        return self._bit(10)

    def can_send_messages(self):
        """Returns True if a user can send messages from all or specific text channels."""
        return self._bit(11)

    def can_send_tts_messages(self):
        """Returns True if a user can send TTS messages from all or specific text channels."""
        return self._bit(12)

    def can_manage_messages(self):
        """Returns True if a user can delete messages from a text channel.

        Note that there are currently no ways to edit other people's messages."""
        return self._bit(13)

    def can_embed_links(self):
        """Returns True if a user's messages will automatically be embedded by Discord."""
        return self._bit(14)

    def can_attach_files(self):
        """Returns True if a user can send files in their messages."""
        return self._bit(15)

    def can_read_message_history(self):
        """Returns True if a user can read a text channel's previous messages."""
        return self._bit(16)

    def can_mention_everyone(self):
        """Returns True if a user's @everyone will mention everyone in the text channel."""
        return self._bit(17)

    # 2 unused

    def can_connect(self):
        """Returns True if a user can connect to a voice channel."""
        return self._bit(20)

    def can_speak(self):
        """Returns True if a user can speak in a voice channel."""
        return self._bit(21)

    def can_mute_members(self):
        """Returns True if a user can mute other users."""
        return self._bit(22)

    def can_deafen_members(self):
        """Returns True if a user can deafen other users."""
        return self._bit(23)

    def can_move_members(self):
        """Returns True if a user can move users between other voice channels."""
        return self._bit(24)

    def can_use_voice_activation(self):
        """Returns True if a user can use voice activation in voice channels."""
        return self._bit(25)

    # 6 unused
