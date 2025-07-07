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

from __future__ import annotations

from discord import app_commands
import discord
from discord.ext import commands


def test_group_with_commands():
    my_group = app_commands.Group(name='mygroup', description='My group')

    @my_group.command()
    async def my_command(interaction: discord.Interaction) -> None:
        ...

    assert my_command.binding is None
    assert my_command.parent is my_group
    assert my_group.commands[0] is my_command


def test_group_subclass_with_commands():
    class MyGroup(app_commands.Group, name='mygroup'):
        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    my_group = MyGroup()
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not my_group
    assert my_group.my_command is not MyGroup.my_command
    assert my_group.my_command.parent is my_group


def test_group_subclass_with_group():
    class MyGroup(app_commands.Group, name='mygroup'):
        sub_group = app_commands.Group(name='mysubgroup', description='My sub-group')

        @sub_group.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    my_group = MyGroup()
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not my_group
    assert MyGroup.sub_group.parent is None
    assert MyGroup.my_command.parent is MyGroup.sub_group
    assert my_group.sub_group is not MyGroup.sub_group
    assert my_group.my_command is not MyGroup.my_command
    assert my_group.sub_group.parent is my_group
    assert my_group.my_command.parent is my_group.sub_group
    assert my_group.my_command.binding is my_group


def test_group_subclass_with_group_subclass():
    class MySubGroup(app_commands.Group, name='mysubgroup'):
        @app_commands.command()
        async def my_sub_group_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyGroup(app_commands.Group, name='mygroup'):
        sub_group = MySubGroup()

        @app_commands.command()
        async def my_group_command(self, interaction: discord.Interaction) -> None:
            ...

    my_group = MyGroup()
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not my_group
    assert MySubGroup.__discord_app_commands_group_children__[0].parent is not my_group.sub_group
    assert my_group.sub_group is not MyGroup.sub_group
    assert my_group.my_group_command is not MyGroup.my_group_command
    assert my_group.sub_group.my_sub_group_command is not MySubGroup.my_sub_group_command
    assert my_group.sub_group.parent is my_group
    assert my_group.my_group_command.parent is my_group
    assert my_group.my_group_command.binding is my_group
    assert my_group.sub_group.my_sub_group_command.parent is my_group.sub_group
    assert not hasattr(my_group, 'my_sub_group_command')
    assert my_group.sub_group.my_sub_group_command.binding is my_group.sub_group


def test_cog_with_commands():
    class MyCog(commands.Cog):
        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert cog.my_command.parent is None
    assert cog.my_command.binding is cog


def test_cog_with_group_with_commands():
    class MyCog(commands.Cog):
        my_group = app_commands.Group(name='mygroup', description='My group')

        @my_group.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert cog.my_group is not MyCog.my_group
    assert cog.my_command is not MyCog.my_command
    assert cog.my_group.parent is None
    assert cog.my_command.parent is cog.my_group
    assert cog.my_command.binding is cog


def test_cog_with_nested_group_with_commands():
    class MyCog(commands.Cog):
        first = app_commands.Group(name='test', description='Test 1')
        second = app_commands.Group(name='test2', parent=first, description='Test 2')

        @first.command(name='cmd')
        async def test_cmd(self, interaction: discord.Interaction) -> None:
            ...

        @second.command(name='cmd2')
        async def test2_cmd(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()

    assert len(MyCog.__cog_app_commands__) == 1
    assert cog.first.parent is None
    assert cog.first is not MyCog.first
    assert cog.second is not MyCog.second
    assert cog.second.parent is cog.first
    assert cog.test_cmd.parent is cog.first
    assert cog.test2_cmd.parent is cog.second
    assert cog.test_cmd.binding is cog
    assert cog.test2_cmd.binding is cog


def test_cog_with_group_subclass_with_commands():
    class MyGroup(app_commands.Group, name='mygroup'):
        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyCog(commands.Cog):
        my_group = MyGroup()

        @my_group.command()
        async def my_cog_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not cog.my_group
    assert cog.my_group is not MyCog.my_group
    assert cog.my_group.my_command is not MyGroup.my_command
    assert cog.my_cog_command is not MyCog.my_cog_command
    assert not hasattr(cog.my_group, 'my_cog_command')
    assert cog.my_group.parent is None
    assert cog.my_group.my_command.parent is cog.my_group
    assert cog.my_group.my_command.binding is cog.my_group
    assert cog.my_cog_command.parent is cog.my_group
    assert cog.my_cog_command.binding is cog


def test_cog_with_group_subclass_with_group():
    class MyGroup(app_commands.Group, name='mygroup'):
        sub_group = app_commands.Group(name='mysubgroup', description='My sub-group')

        @sub_group.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyCog(commands.Cog):
        my_group = MyGroup()

        @my_group.command()
        async def my_cog_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not cog.my_group
    assert cog.my_group is not MyCog.my_group
    assert cog.my_group.sub_group is not MyGroup.sub_group
    assert cog.my_group.my_command is not MyGroup.my_command
    assert cog.my_cog_command is not MyCog.my_cog_command
    assert not hasattr(cog.my_group, 'my_cog_command')
    assert not hasattr(cog, 'sub_group')
    assert not hasattr(cog, 'my_command')
    assert cog.my_group.parent is None
    assert cog.my_group.sub_group.parent is cog.my_group
    assert cog.my_group.my_command.parent is cog.my_group.sub_group
    assert cog.my_group.my_command.binding is cog.my_group
    assert cog.my_cog_command.parent is cog.my_group
    assert cog.my_cog_command.binding is cog


def test_cog_with_group_subclass_with_group_subclass():
    class MySubGroup(app_commands.Group, name='mysubgroup'):
        @app_commands.command()
        async def my_sub_group_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyGroup(app_commands.Group, name='mygroup'):
        sub_group = MySubGroup()

        @app_commands.command()
        async def my_group_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyCog(commands.Cog):
        my_group = MyGroup()

        @my_group.command()
        async def my_cog_command(self, interaction: discord.Interaction) -> None:
            ...

        @my_group.sub_group.command()
        async def my_sub_group_cog_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not cog.my_group
    assert MySubGroup.__discord_app_commands_group_children__[0].parent is not cog.my_group.sub_group
    assert cog.my_group is not MyCog.my_group
    assert cog.my_group.my_group_command is not MyCog.my_group.my_group_command
    assert cog.my_group.sub_group is not MyGroup.sub_group
    assert cog.my_cog_command is not MyCog.my_cog_command
    assert not hasattr(cog.my_group, 'my_cog_command')
    assert not hasattr(cog, 'sub_group')
    assert not hasattr(cog, 'my_group_command')
    assert not hasattr(cog, 'my_sub_group_command')
    assert not hasattr(cog.my_group, 'my_sub_group_command')
    assert cog.my_group.sub_group.my_sub_group_command is not MyGroup.sub_group.my_sub_group_command
    assert cog.my_group.sub_group.my_sub_group_command is not MySubGroup.my_sub_group_command
    assert cog.my_group.sub_group.parent is cog.my_group
    assert cog.my_group.my_group_command.parent is cog.my_group
    assert cog.my_group.my_group_command.binding is cog.my_group
    assert cog.my_group.sub_group.my_sub_group_command.parent is cog.my_group.sub_group
    assert cog.my_group.sub_group.my_sub_group_command.binding is cog.my_group.sub_group
    assert cog.my_cog_command.parent is cog.my_group
    assert cog.my_cog_command.binding is cog
    assert cog.my_sub_group_cog_command.parent is cog.my_group.sub_group
    assert cog.my_sub_group_cog_command.binding is cog


def test_cog_group_with_commands():
    class MyCog(commands.GroupCog):
        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyCog.__cog_app_commands__[0].parent is not cog
    assert MyCog.__cog_app_commands__[0].parent is not cog.__cog_app_commands_group__
    assert cog.my_command is not MyCog.my_command
    assert cog.__cog_app_commands_group__ is not None
    assert cog.__cog_app_commands_group__.parent is None
    assert cog.my_command.parent is cog.__cog_app_commands_group__


def test_cog_group_with_group():
    class MyCog(commands.GroupCog):
        sub_group = app_commands.Group(name='mysubgroup', description='My sub-group')

        @sub_group.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyCog.__cog_app_commands__[0].parent is not cog
    assert MyCog.__cog_app_commands__[0].parent is not cog.__cog_app_commands_group__
    assert cog.sub_group is not MyCog.sub_group
    assert cog.my_command is not MyCog.my_command
    assert cog.__cog_app_commands_group__ is not None
    assert cog.__cog_app_commands_group__.parent is None
    assert cog.sub_group.parent is cog.__cog_app_commands_group__
    assert cog.my_command.parent is cog.sub_group


def test_cog_group_with_subclass_group():
    class MyGroup(app_commands.Group, name='mygroup'):
        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyCog(commands.GroupCog):
        sub_group = MyGroup()

        @sub_group.command()
        async def my_cog_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyCog.__cog_app_commands__[0].parent is not cog
    assert MyCog.__cog_app_commands__[0].parent is not cog.__cog_app_commands_group__
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not cog.sub_group
    assert cog.sub_group is not MyCog.sub_group
    assert cog.sub_group.my_command is not MyGroup.my_command
    assert cog.my_cog_command is not MyCog.my_cog_command
    assert not hasattr(cog.sub_group, 'my_cog_command')
    assert cog.__cog_app_commands_group__ is not None
    assert cog.__cog_app_commands_group__.parent is None
    assert cog.sub_group.parent is cog.__cog_app_commands_group__
    assert cog.sub_group.my_command.parent is cog.sub_group
    assert cog.my_cog_command.parent is cog.sub_group
    assert cog.my_cog_command.binding is cog


def test_cog_group_with_subclassed_subclass_group():
    class MyGroup(app_commands.Group):
        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    class MySubclassedGroup(MyGroup, name='mygroup'):
        ...

    class MyCog(commands.GroupCog):
        sub_group = MySubclassedGroup()

        @sub_group.command()
        async def my_cog_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert MyCog.__cog_app_commands__[0].parent is not cog
    assert MyCog.__cog_app_commands__[0].parent is not cog.__cog_app_commands_group__
    assert MyGroup.__discord_app_commands_group_children__[0].parent is not cog.sub_group
    assert MySubclassedGroup.__discord_app_commands_group_children__[0].parent is not cog.sub_group
    assert cog.sub_group is not MyCog.sub_group
    assert cog.sub_group.my_command is not MyGroup.my_command
    assert cog.sub_group.my_command is not MySubclassedGroup.my_command
    assert cog.my_cog_command is not MyCog.my_cog_command
    assert not hasattr(cog.sub_group, 'my_cog_command')
    assert cog.__cog_app_commands_group__ is not None
    assert cog.__cog_app_commands_group__.parent is None
    assert cog.sub_group.parent is cog.__cog_app_commands_group__
    assert cog.sub_group.my_command.parent is cog.sub_group
    assert cog.my_cog_command.parent is cog.sub_group
    assert cog.my_cog_command.binding is cog


def test_cog_group_with_custom_state_issue9383():
    class InnerGroup(app_commands.Group):
        def __init__(self):
            super().__init__()
            self.state: int = 20

        @app_commands.command()
        async def my_command(self, interaction: discord.Interaction) -> None:
            ...

    class MyCog(commands.GroupCog):
        inner = InnerGroup()

        @app_commands.command()
        async def my_regular_command(self, interaction: discord.Interaction) -> None:
            ...

        @inner.command()
        async def my_inner_command(self, interaction: discord.Interaction) -> None:
            ...

    cog = MyCog()
    assert cog.inner.state == 20
    assert cog.my_regular_command is not MyCog.my_regular_command

    # Basically the same tests as above... (superset?)
    assert MyCog.__cog_app_commands__[0].parent is not cog
    assert MyCog.__cog_app_commands__[0].parent is not cog.__cog_app_commands_group__
    assert InnerGroup.__discord_app_commands_group_children__[0].parent is not cog.inner
    assert InnerGroup.__discord_app_commands_group_children__[0].parent is not cog.inner
    assert cog.inner is not MyCog.inner
    assert cog.inner.my_command is not InnerGroup.my_command
    assert cog.inner.my_command is not InnerGroup.my_command
    assert cog.my_inner_command is not MyCog.my_inner_command
    assert not hasattr(cog.inner, 'my_inner_command')
    assert cog.__cog_app_commands_group__ is not None
    assert cog.__cog_app_commands_group__.parent is None
    assert cog.inner.parent is cog.__cog_app_commands_group__
    assert cog.inner.my_command.parent is cog.inner
    assert cog.my_inner_command.parent is cog.inner
    assert cog.my_inner_command.binding is cog


def test_cog_hybrid_group_manual_command():
    class MyCog(commands.Cog):
        @commands.hybrid_group()
        async def first(self, ctx: commands.Context) -> None:
            ...

        @first.command(name='both')
        async def second_both(self, ctx: commands.Context) -> None:
            ...

        @first.app_command.command(name='second')
        async def second_app(self, interaction: discord.Interaction) -> None:
            ...

    client = discord.Client(intents=discord.Intents.default())
    tree = app_commands.CommandTree(client)

    cog = MyCog()
    tree.add_command(cog.first.app_command)

    assert cog.first is not MyCog.first
    assert cog.second_both is not MyCog.second_both
    assert cog.second_app is not MyCog.second_app
    assert cog.first.parent is None
    assert cog.second_both.parent is cog.first
    assert cog.second_app.parent is cog.first.app_command
    assert cog.second_app.binding is cog
    assert tree.get_command('first') is cog.first.app_command

    first = tree.get_command('first')
    assert isinstance(first, app_commands.Group)
    both = first.get_command('both')
    assert isinstance(both, app_commands.Command)
    assert both.parent is first
    assert both.binding is cog

    second = first.get_command('second')
    assert isinstance(second, app_commands.Command)
    assert second.parent is first
    assert second.binding is cog


def test_cog_hybrid_group_manual_nested_command():
    class MyCog(commands.Cog):
        @commands.hybrid_group()
        async def first(self, ctx: commands.Context) -> None:
            pass

        @first.group()
        async def second(self, ctx: commands.Context) -> None:
            pass

        @second.app_command.command()
        async def third(self, interaction: discord.Interaction) -> None:
            pass

    client = discord.Client(intents=discord.Intents.default())
    tree = app_commands.CommandTree(client)

    cog = MyCog()
    tree.add_command(cog.first.app_command)

    assert cog.first is not MyCog.first
    assert cog.second is not MyCog.second
    assert cog.third is not MyCog.third
    assert cog.first.parent is None
    assert cog.second.parent is cog.first
    assert cog.third.parent is cog.second.app_command
    assert cog.third.binding is cog

    first = tree.get_command('first')
    assert isinstance(first, app_commands.Group)

    second = first.get_command('second')
    assert isinstance(second, app_commands.Group)

    third = second.get_command('third')
    assert isinstance(third, app_commands.Command)
    assert third.parent is second
    assert third.binding is cog


def test_cog_hybrid_group_wrapped_instance():
    class MyCog(commands.Cog):
        @commands.hybrid_group(fallback='fallback')
        async def first(self, ctx: commands.Context) -> None:
            pass

        @first.command()
        async def second(self, ctx: commands.Context) -> None:
            pass

        @first.group()
        async def nested(self, ctx: commands.Context) -> None:
            pass

        @nested.app_command.command()
        async def child(self, interaction: discord.Interaction) -> None:
            pass

    cog = MyCog()

    fallback = cog.first.app_command.get_command('fallback')
    assert fallback is not None
    assert getattr(fallback, 'wrapped', None) is cog.first
    assert fallback.parent is cog.first.app_command
    assert cog.second.app_command is not None
    assert cog.second.app_command.wrapped is cog.second
