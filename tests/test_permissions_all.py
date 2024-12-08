import discord

from functools import reduce
from operator import or_

def test_permissions_all():
    assert discord.Permissions.all().value == reduce(or_, discord.Permissions.VALID_FLAGS.values())
