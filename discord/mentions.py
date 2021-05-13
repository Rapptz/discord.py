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

__all__ = (
    'AllowedMentions',
)


class _FakeBool:
    def __repr__(self):
        return 'True'

    def __eq__(self, other):
        return other is True

    def __bool__(self):
        return True


default = _FakeBool()


class AllowedMentions:
    """A class that represents what mentions are allowed in a message.

    This class can be set during :class:`Client` initialisation to apply
    to every message sent. It can also be applied on a per message basis
    via :meth:`abc.Messageable.send` for more fine-grained control.

    Attributes
    ------------
    everyone: :class:`bool`
        Whether to allow everyone and here mentions. Defaults to ``True``.
    users: Union[:class:`bool`, List[:class:`abc.Snowflake`]]
        Controls the users being mentioned. If ``True`` (the default) then
        users are mentioned based on the message content. If ``False`` then
        users are not mentioned at all. If a list of :class:`abc.Snowflake`
        is given then only the users provided will be mentioned, provided those
        users are in the message content.
    roles: Union[:class:`bool`, List[:class:`abc.Snowflake`]]
        Controls the roles being mentioned. If ``True`` (the default) then
        roles are mentioned based on the message content. If ``False`` then
        roles are not mentioned at all. If a list of :class:`abc.Snowflake`
        is given then only the roles provided will be mentioned, provided those
        roles are in the message content.
    replied_user: :class:`bool`
        Whether to mention the author of the message being replied to. Defaults
        to ``True``.

        .. versionadded:: 1.6
    """

    __slots__ = ('everyone', 'users', 'roles', 'replied_user')

    def __init__(self, *, everyone=default, users=default, roles=default, replied_user=default):
        self.everyone = everyone
        self.users = users
        self.roles = roles
        self.replied_user = replied_user

    @classmethod
    def all(cls):
        """A factory method that returns a :class:`AllowedMentions` with all fields explicitly set to ``True``

        .. versionadded:: 1.5
        """
        return cls(everyone=True, users=True, roles=True, replied_user=True)

    @classmethod
    def none(cls):
        """A factory method that returns a :class:`AllowedMentions` with all fields set to ``False``

        .. versionadded:: 1.5
        """
        return cls(everyone=False, users=False, roles=False, replied_user=False)

    def to_dict(self):
        parse = []
        data = {}

        if self.everyone:
            parse.append('everyone')

        if self.users == True:
            parse.append('users')
        elif self.users != False:
            data['users'] = [x.id for x in self.users]

        if self.roles == True:
            parse.append('roles')
        elif self.roles != False:
            data['roles'] = [x.id for x in self.roles]

        if self.replied_user:
            data['replied_user'] = True

        data['parse'] = parse
        return data

    def merge(self, other):
        # Creates a new AllowedMentions by merging from another one.
        # Merge is done by using the 'self' values unless explicitly
        # overridden by the 'other' values.
        everyone = self.everyone if other.everyone is default else other.everyone
        users = self.users if other.users is default else other.users
        roles = self.roles if other.roles is default else other.roles
        replied_user = self.replied_user if other.replied_user is default else other.replied_user
        return AllowedMentions(everyone=everyone, roles=roles, users=users, replied_user=replied_user)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(everyone={self.everyone}, '
            f'users={self.users}, roles={self.roles}, replied_user={self.replied_user})'
        )
