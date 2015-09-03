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
        currently available permissions. You should query permissions via the properties provided rather
        than using this raw value.

    The properties provided are two way. You can set and retrieve individual bits using the properties as if they
    were regular bools. This allows you to edit permissions.
    """

    def __init__(self, permissions):
        self.value = permissions

    def _bit(self, index):
        return bool((self.value >> index) & 1)

    def _set(self, index, value):
        if value == True:
            self.value |= (1 << index)
        elif value == False:
            self.value &= ~(1 << index)
        else:
            raise TypeError('Value to set for Permissions must be a bool.')

    @property
    def can_create_instant_invite(self):
        """Returns True if the user can create instant invites."""
        return self._bit(0)

    @can_create_instant_invite.setter
    def can_create_instant_invite(self, value):
        self._set(0, value)

    @property
    def can_ban_members(self):
        """Returns True if the user can ban users from the server."""
        return self._bit(1)

    @can_ban_members.setter
    def can_ban_members(self, value):
        self._set(1, value)

    @property
    def can_kick_members(self):
        """Returns True if a user can kick users from the server."""
        return self._bit(2)

    @can_kick_members.setter
    def can_kick_members(self, value):
        self._set(2, value)

    @property
    def can_manage_roles(self):
        """Returns True if a user can manage server roles. This role overrides all other permissions."""
        return self._bit(3)

    @can_manage_roles.setter
    def can_manage_roles(self, value):
        self._set(3, value)

    @property
    def can_manage_channels(self):
        """Returns True if a user can edit, delete, or create channels in the server."""
        return self._bit(4)

    @can_manage_channels.setter
    def can_manage_channels(self, value):
        self._set(4, value)

    @property
    def can_manage_server(self):
        """Returns True if a user can edit server properties."""
        return self._bit(5)

    @can_manage_server.setter
    def can_manage_server(self, value):
        self._set(5, value)

    # 4 unused

    @property
    def can_read_messages(self):
        """Returns True if a user can read messages from all or specific text channels."""
        return self._bit(10)

    @can_read_messages.setter
    def can_read_messages(self, value):
        self._set(10, value)

    @property
    def can_send_messages(self):
        """Returns True if a user can send messages from all or specific text channels."""
        return self._bit(11)

    @can_send_messages.setter
    def can_send_messages(self, value):
        self._set(11, value)

    @property
    def can_send_tts_messages(self):
        """Returns True if a user can send TTS messages from all or specific text channels."""
        return self._bit(12)

    @can_send_tts_messages.setter
    def can_send_tts_messages(self, value):
        self._set(12, value)

    @property
    def can_manage_messages(self):
        """Returns True if a user can delete messages from a text channel. Note that there are currently no ways to edit other people's messages."""
        return self._bit(13)

    @can_manage_messages.setter
    def can_manage_messages(self, value):
        self._set(13, value)

    @property
    def can_embed_links(self):
        """Returns True if a user's messages will automatically be embedded by Discord."""
        return self._bit(14)

    @can_embed_links.setter
    def can_embed_links(self, value):
        self._set(14, value)

    @property
    def can_attach_files(self):
        """Returns True if a user can send files in their messages."""
        return self._bit(15)

    @can_attach_files.setter
    def can_attach_files(self, value):
        self._set(15, value)

    @property
    def can_read_message_history(self):
        """Returns True if a user can read a text channel's previous messages."""
        return self._bit(16)

    @can_read_message_history.setter
    def can_read_message_history(self, value):
        self._set(16, value)

    @property
    def can_mention_everyone(self):
        """Returns True if a user's @everyone will mention everyone in the text channel."""
        return self._bit(17)

    @can_mention_everyone.setter
    def can_mention_everyone(self, value):
        self._set(17, value)

    # 2 unused

    @property
    def can_connect(self):
        """Returns True if a user can connect to a voice channel."""
        return self._bit(20)

    @can_connect.setter
    def can_connect(self, value):
        self._set(20, value)

    @property
    def can_speak(self):
        """Returns True if a user can speak in a voice channel."""
        return self._bit(21)

    @can_speak.setter
    def can_speak(self, value):
        self._set(21, value)

    @property
    def can_mute_members(self):
        """Returns True if a user can mute other users."""
        return self._bit(22)

    @can_mute_members.setter
    def can_mute_members(self, value):
        self._set(22, value)

    @property
    def can_deafen_members(self):
        """Returns True if a user can deafen other users."""
        return self._bit(23)

    @can_deafen_members.setter
    def can_deafen_members(self, value):
        self._set(23, value)

    @property
    def can_move_members(self):
        """Returns True if a user can move users between other voice channels."""
        return self._bit(24)

    @can_move_members.setter
    def can_move_members(self, value):
        self._set(24, value)

    @property
    def can_use_voice_activation(self):
        """Returns True if a user can use voice activation in voice channels."""
        return self._bit(25)

    @can_use_voice_activation.setter
    def can_use_voice_activation(self, value):
        self._set(25, value)

    # 6 unused
