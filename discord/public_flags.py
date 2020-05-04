from .enums import UserFlags


class PublicFlags:
    """Wraps up the Discord public flags.

    .. versionadded :: 1.4
    .. container:: operations
        .. describe:: x == y

            Checks if two PublicFlags are equal.
        .. describe:: x != y

            Checks if two PublicFlags are not equal.
    """
    def __init__(self, user):
        self.user = user

    def __repr__(self):
        return '<PublicFlags all={0}>'.format(self.all)

    def __eq__(self, other):
        return isinstance(other, PublicFlags) and self.all == other.all

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def staff(self):
        """Indicates whether the user is a Discord Employee."""
        return self.user.has_flag(UserFlags.staff)

    @property
    def partner(self):
        """Indicates whether the user is a Discord Partner."""
        return self.user.has_flag(UserFlags.partner)

    @property
    def hypesquad(self):
        """Indicates whether the user is a HypeSquad Events member."""
        return self.user.has_flag(UserFlags.hypesquad)

    @property
    def bug_hunter(self):
        """Indicates whether the user is a Bug Hunter"""
        return self.user.has_flag(UserFlags.bug_hunter)

    @property
    def hypesquad_bravery(self):
        """Indicates whether the user is a HypeSquad Bravery member."""
        return self.user.has_flag(UserFlags.hypesquad_bravery)

    @property
    def hypesquad_brilliance(self):
        """Indicates whether the user is a HypeSquad Brilliance member."""
        return self.user.has_flag(UserFlags.hypesquad_brilliance)

    @property
    def hypesquad_balance(self):
        """Indicates whether the user is a HypeSquad Balance member."""
        return self.user.has_flag(UserFlags.hypesquad_balance)

    @property
    def early_supporter(self):
        """Indicates whether the user is an Early Supporter."""
        return self.user.has_flag(UserFlags.early_supporter)

    @property
    def team_user(self):
        """Indicates whether the user is a Team User."""
        return self.user.has_flag(UserFlags.team_user)

    @property
    def system(self):
        """Indicates whether the user is a system user (i.e. represents Discord officially)."""
        return self.user.has_flag(UserFlags.system)

    @property
    def bug_hunter_level_2(self):
        """Indicates whether the user is a Bug Hunter Level 2"""
        return self.user.has_flag(UserFlags.bug_hunter_level_2)

    @property
    def verified_bot(self):
        """Indicates whether the user is a Verified Bot."""
        return self.user.has_flag(UserFlags.verified_bot)

    @property
    def verified_bot_developer(self):
        """Indicates whether the user is a Verified Bot Developer."""
        return self.user.has_flag(UserFlags.verified_bot_developer)

    @property
    def all(self):
        """List[:class:`UserFlags`]: Returns all public flags the user has."""
        return [public_flag for public_flag in UserFlags if self.user.has_flag(public_flag)]
