# -*- coding: utf-8 -*-

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

from . import utils, enums
from .object import Object
from .permissions import PermissionOverwrite, Permissions
from .colour import Colour
from .invite import Invite
from .mixins import Hashable

def _transform_verification_level(entry, data):
    return enums.try_enum(enums.VerificationLevel, data)

def _transform_default_notifications(entry, data):
    return enums.try_enum(enums.NotificationLevel, data)

def _transform_explicit_content_filter(entry, data):
    return enums.try_enum(enums.ContentFilter, data)

def _transform_permissions(entry, data):
    return Permissions(data)

def _transform_color(entry, data):
    return Colour(data)

def _transform_snowflake(entry, data):
    return int(data)

def _transform_channel(entry, data):
    if data is None:
        return None
    return entry.guild.get_channel(int(data)) or Object(id=data)

def _transform_owner_id(entry, data):
    if data is None:
        return None
    return entry._get_member(int(data))

def _transform_inviter_id(entry, data):
    if data is None:
        return None
    return entry._get_member(int(data))

def _transform_overwrites(entry, data):
    overwrites = []
    for elem in data:
        allow = Permissions(elem['allow'])
        deny = Permissions(elem['deny'])
        ow = PermissionOverwrite.from_pair(allow, deny)

        ow_type = elem['type']
        ow_id = int(elem['id'])
        if ow_type == 'role':
            target = entry.guild.get_role(ow_id)
        else:
            target = entry._get_member(ow_id)

        if target is None:
            target = Object(id=ow_id)

        overwrites.append((target, ow))

    return overwrites

class AuditLogDiff:
    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__.items())

    def __repr__(self):
        values = ' '.join('%s=%r' % item for item in self.__dict__.items())
        return '<AuditLogDiff %s>' % values

class AuditLogChanges:
    TRANSFORMERS = {
        'verification_level':            (None, _transform_verification_level),
        'explicit_content_filter':       (None, _transform_explicit_content_filter),
        'allow':                         (None, _transform_permissions),
        'deny':                          (None, _transform_permissions),
        'permissions':                   (None, _transform_permissions),
        'id':                            (None, _transform_snowflake),
        'color':                         ('colour', _transform_color),
        'owner_id':                      ('owner', _transform_owner_id),
        'inviter_id':                    ('inviter', _transform_inviter_id),
        'channel_id':                    ('channel', _transform_channel),
        'afk_channel_id':                ('afk_channel', _transform_channel),
        'system_channel_id':             ('system_channel', _transform_channel),
        'widget_channel_id':             ('widget_channel', _transform_channel),
        'permission_overwrites':         ('overwrites', _transform_overwrites),
        'splash_hash':                   ('splash', None),
        'icon_hash':                     ('icon', None),
        'avatar_hash':                   ('avatar', None),
        'rate_limit_per_user':           ('slowmode_delay', None),
        'default_message_notifications': ('default_notifications', _transform_default_notifications),
    }

    def __init__(self, entry, data):
        self.before = AuditLogDiff()
        self.after = AuditLogDiff()

        for elem in data:
            attr = elem['key']

            # special cases for role add/remove
            if attr == '$add':
                self._handle_role(self.before, self.after, entry, elem['new_value'])
                continue
            elif attr == '$remove':
                self._handle_role(self.after, self.before, entry, elem['new_value'])
                continue

            transformer = self.TRANSFORMERS.get(attr)
            if transformer:
                key, transformer = transformer
                if key:
                    attr = key

            try:
                before = elem['old_value']
            except KeyError:
                before = None
            else:
                if transformer:
                    before = transformer(entry, before)

            setattr(self.before, attr, before)

            try:
                after = elem['new_value']
            except KeyError:
                after = None
            else:
                if transformer:
                    after = transformer(entry, after)

            setattr(self.after, attr, after)

        # add an alias
        if hasattr(self.after, 'colour'):
            self.after.color = self.after.colour
            self.before.color = self.before.colour

    def __repr__(self):
        return '<AuditLogChanges before=%r after=%r>' % (self.before, self.after)

    def _handle_role(self, first, second, entry, elem):
        if not hasattr(first, 'roles'):
            setattr(first, 'roles', [])

        data = []
        g = entry.guild

        for e in elem:
            role_id = int(e['id'])
            role = g.get_role(role_id)

            if role is None:
                role = Object(id=role_id)
                role.name = e['name']

            data.append(role)

        setattr(second, 'roles', data)

class AuditLogEntry(Hashable):
    r"""Represents an Audit Log entry.

    You retrieve these via :meth:`Guild.audit_logs`.

    .. container:: operations

        .. describe:: x == y

            Checks if two entries are equal.

        .. describe:: x != y

            Checks if two entries are not equal.

        .. describe:: hash(x)

            Returns the entry's hash.

    .. versionchanged:: 1.7
        Audit log entries are now comparable and hashable.

    Attributes
    -----------
    action: :class:`AuditLogAction`
        The action that was done.
    user: :class:`abc.User`
        The user who initiated this action. Usually a :class:`Member`\, unless gone
        then it's a :class:`User`.
    id: :class:`int`
        The entry ID.
    target: Any
        The target that got changed. The exact type of this depends on
        the action being done.
    reason: Optional[:class:`str`]
        The reason this action was done.
    extra: Any
        Extra information that this entry has that might be useful.
        For most actions, this is ``None``. However in some cases it
        contains extra information. See :class:`AuditLogAction` for
        which actions have this field filled out.
    """

    def __init__(self, *, users, data, guild):
        self._state = guild._state
        self.guild = guild
        self._users = users
        self._from_data(data)

    def _from_data(self, data):
        self.action = enums.try_enum(enums.AuditLogAction, data['action_type'])
        self.id = int(data['id'])

        # this key is technically not usually present
        self.reason = data.get('reason')
        self.extra = data.get('options')

        if isinstance(self.action, enums.AuditLogAction) and self.extra:
            if self.action is enums.AuditLogAction.member_prune:
                # member prune has two keys with useful information
                self.extra = type('_AuditLogProxy', (), {k: int(v) for k, v in self.extra.items()})()
            elif self.action is enums.AuditLogAction.member_move or self.action is enums.AuditLogAction.message_delete:
                channel_id = int(self.extra['channel_id'])
                elems = {
                    'count': int(self.extra['count']),
                    'channel': self.guild.get_channel(channel_id) or Object(id=channel_id)
                }
                self.extra = type('_AuditLogProxy', (), elems)()
            elif self.action is enums.AuditLogAction.member_disconnect:
                # The member disconnect action has a dict with some information
                elems = {
                    'count': int(self.extra['count']),
                }
                self.extra = type('_AuditLogProxy', (), elems)()
            elif self.action.name.endswith('pin'):
                # the pin actions have a dict with some information
                channel_id = int(self.extra['channel_id'])
                message_id = int(self.extra['message_id'])
                elems = {
                    'channel': self.guild.get_channel(channel_id) or Object(id=channel_id),
                    'message_id': message_id
                }
                self.extra = type('_AuditLogProxy', (), elems)()
            elif self.action.name.startswith('overwrite_'):
                # the overwrite_ actions have a dict with some information
                instance_id = int(self.extra['id'])
                the_type = self.extra.get('type')
                if the_type == 'member':
                    self.extra = self._get_member(instance_id)
                else:
                    role = self.guild.get_role(instance_id)
                    if role is None:
                        role = Object(id=instance_id)
                        role.name = self.extra.get('role_name')
                    self.extra = role

        # this key is not present when the above is present, typically.
        # It's a list of { new_value: a, old_value: b, key: c }
        # where new_value and old_value are not guaranteed to be there depending
        # on the action type, so let's just fetch it for now and only turn it
        # into meaningful data when requested
        self._changes = data.get('changes', [])

        self.user = self._get_member(utils._get_as_snowflake(data, 'user_id'))
        self._target_id = utils._get_as_snowflake(data, 'target_id')

    def _get_member(self, user_id):
        return self.guild.get_member(user_id) or self._users.get(user_id)

    def __repr__(self):
        return '<AuditLogEntry id={0.id} action={0.action} user={0.user!r}>'.format(self)

    @utils.cached_property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the entry's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @utils.cached_property
    def target(self):
        try:
            converter = getattr(self, '_convert_target_' + self.action.target_type)
        except AttributeError:
            return Object(id=self._target_id)
        else:
            return converter(self._target_id)

    @utils.cached_property
    def category(self):
        """Optional[:class:`AuditLogActionCategory`]: The category of the action, if applicable."""
        return self.action.category

    @utils.cached_property
    def changes(self):
        """:class:`AuditLogChanges`: The list of changes this entry has."""
        obj = AuditLogChanges(self, self._changes)
        del self._changes
        return obj

    @utils.cached_property
    def before(self):
        """:class:`AuditLogDiff`: The target's prior state."""
        return self.changes.before

    @utils.cached_property
    def after(self):
        """:class:`AuditLogDiff`: The target's subsequent state."""
        return self.changes.after

    def _convert_target_guild(self, target_id):
        return self.guild

    def _convert_target_channel(self, target_id):
        ch = self.guild.get_channel(target_id)
        if ch is None:
            return Object(id=target_id)
        return ch

    def _convert_target_user(self, target_id):
        return self._get_member(target_id)

    def _convert_target_role(self, target_id):
        role = self.guild.get_role(target_id)
        if role is None:
            return Object(id=target_id)
        return role

    def _convert_target_invite(self, target_id):
        # invites have target_id set to null
        # so figure out which change has the full invite data
        changeset = self.before if self.action is enums.AuditLogAction.invite_delete else self.after

        fake_payload = {
            'max_age': changeset.max_age,
            'max_uses': changeset.max_uses,
            'code': changeset.code,
            'temporary': changeset.temporary,
            'channel': changeset.channel,
            'uses': changeset.uses,
            'guild': self.guild,
        }

        obj = Invite(state=self._state, data=fake_payload)
        try:
            obj.inviter = changeset.inviter
        except AttributeError:
            pass
        return obj

    def _convert_target_emoji(self, target_id):
        return self._state.get_emoji(target_id) or Object(id=target_id)

    def _convert_target_message(self, target_id):
        return self._get_member(target_id)
