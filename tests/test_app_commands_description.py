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

import discord
from discord import app_commands
from discord.ext import commands


def test_descriptions_describe():
    @app_commands.command(description='This is the short description that will appear.')
    @app_commands.describe(arg='Decorator description of arg.')
    @app_commands.describe(arg2='Decorator description of arg2.')
    async def describe(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        ...

    assert describe.description == 'This is the short description that will appear.'
    assert describe.get_parameter('arg').description == 'Decorator description of arg.'  # type: ignore
    assert describe.get_parameter('arg2').description == 'Decorator description of arg2.'  # type: ignore


def test_descriptions_no_args():
    @app_commands.command()
    async def no_args(interaction: discord.Interaction) -> None:
        """This is the short description that will appear."""

    assert no_args.description == 'This is the short description that will appear.'


def test_descriptions_numpy():
    @app_commands.command()
    async def numpy(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will not appear in the command description.

        Parameters
        ----------
        arg: str
            Docstring description of arg.
            This is the second line of the arg docstring.
        arg2: int
            Docstring description of arg2.
        """

    assert numpy.description == 'This is the short description that will appear.'
    assert numpy.get_parameter('arg').description == 'Docstring description of arg. This is the second line of the arg docstring.'  # type: ignore
    assert numpy.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_numpy_extras():
    @app_commands.command()
    async def numpy(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will not appear in the command description.

        Parameters
        ----------
        interaction: discord.Interaction
            The interaction object.
        arg: str
            Docstring description of arg.
            This is the second line of the arg docstring.
        arg2: int
            Docstring description of arg2.

        Returns
        -------
        NoneType
            This function does not return anything.
        """

    assert numpy.description == 'This is the short description that will appear.'
    assert numpy.get_parameter('arg').description == 'Docstring description of arg. This is the second line of the arg docstring.'  # type: ignore
    assert numpy.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_google():
    @app_commands.command()
    async def google(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will not appear in the command description.

        Args:
            arg: Docstring description of arg.
                This is the second line of the arg docstring.
            arg2 (int): Docstring description of arg2.
        """

    assert google.description == 'This is the short description that will appear.'
    assert google.get_parameter('arg').description == 'Docstring description of arg. This is the second line of the arg docstring.'  # type: ignore
    assert google.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_google_extras():
    @app_commands.command()
    async def google(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will not appear in the command description.

        Args:
            interaction: discord.Interaction
                The interaction object.
            arg: Docstring description of arg.
                This is the second line of the arg docstring.
            arg2 (int): Docstring description of arg2.

        Returns:
            NoneType
                This function does not return anything.
        """

    assert google.description == 'This is the short description that will appear.'
    assert google.get_parameter('arg').description == 'Docstring description of arg. This is the second line of the arg docstring.'  # type: ignore
    assert google.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_sphinx():
    @app_commands.command()
    async def sphinx(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will not appear in the command description.

        :param arg: Docstring description of arg.
            This is the second line of the arg docstring.
        :type arg: str
        :param arg2: Docstring description of arg2.
        :type arg2: int
        """

    assert sphinx.description == 'This is the short description that will appear.'
    assert sphinx.get_parameter('arg').description == 'Docstring description of arg. This is the second line of the arg docstring.'  # type: ignore
    assert sphinx.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_sphinx_extras():
    @app_commands.command()
    async def sphinx(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will not appear in the command description.

        :param interaction: The interaction object.
        :type interaction: :class:`discord.Interaction`
        :param arg: Docstring description of arg.
            This is the second line of the arg docstring.
        :type arg: :class:`str`
        :param arg2: Docstring description of arg2.
        :type arg2: :class:`int`
        :return: None
        :rtpye: NoneType
        """

    assert sphinx.description == 'This is the short description that will appear.'
    assert sphinx.get_parameter('arg').description == 'Docstring description of arg. This is the second line of the arg docstring.'  # type: ignore
    assert sphinx.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_docstring_and_describe():
    @app_commands.command(description='This is the short description that will appear.')
    @app_commands.describe(arg='Decorator description of arg.')
    async def describe(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """This description will not appear since it is overriden by the decorator.

        This extended description will not appear in the command description.

        Args:
            arg: Docstring description of arg.
                This will not be used since the decorator overrides it.
            arg2 (int): Docstring description of arg2.
        """

    assert describe.description == 'This is the short description that will appear.'
    assert describe.get_parameter('arg').description == 'Decorator description of arg.'  # type: ignore
    assert describe.get_parameter('arg2').description == 'Docstring description of arg2.'  # type: ignore


def test_descriptions_group_no_args():
    my_group = app_commands.Group(name='mygroup', description='My group')

    @my_group.command()
    async def my_command(interaction: discord.Interaction) -> None:
        """Test slash command"""

    assert my_command.description == 'Test slash command'


def test_descriptions_group_args():
    my_group = app_commands.Group(name='mygroup', description='My group')

    @my_group.command()
    async def my_command(interaction: discord.Interaction, arg: str, arg2: int) -> None:
        """Test slash command

        Parameters
        ----------
        arg: str
            Description of arg.
            This is the second line of the arg description.
        arg2: int
            Description of arg2.
        """

    assert my_command.description == 'Test slash command'
    assert my_command.get_parameter('arg').description == 'Description of arg. This is the second line of the arg description.'  # type: ignore
    assert my_command.get_parameter('arg2').description == 'Description of arg2.'  # type: ignore


def test_descriptions_cog_commands():
    class MyCog(commands.Cog):
        @app_commands.command()
        async def test(self, interaction: discord.Interaction, arg: str, arg2: int) -> None:
            """Test slash command

            Parameters
            ----------
            arg: str
                Description of arg.
                This is the second line of the arg description.
            arg2: int
                Description of arg2.
            """

    cog = MyCog()
    assert cog.test.description == 'Test slash command'
    assert cog.test.get_parameter('arg').description == 'Description of arg. This is the second line of the arg description.'  # type: ignore
    assert cog.test.get_parameter('arg2').description == 'Description of arg2.'  # type: ignore
