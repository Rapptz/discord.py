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

from discord.ext import commands


def test_ext_commands_descriptions_explicit():
    @commands.command(help='This is the short description that will appear.')
    async def describe(
        ctx: commands.Context,
        arg: str = commands.param(description='Description of arg.'),
        arg2: int = commands.param(description='Description of arg2.'),
    ) -> None:
        ...

    assert describe.help == 'This is the short description that will appear.'
    assert describe.clean_params['arg'].description == 'Description of arg.'
    assert describe.clean_params['arg2'].description == 'Description of arg2.'


def test_ext_commands_descriptions_no_args():
    @commands.command()
    async def no_args(ctx: commands.Context) -> None:
        """This is the short description that will appear."""

    assert no_args.help == 'This is the short description that will appear.'


def test_ext_commands_descriptions_numpy():
    @commands.command()
    async def numpy(ctx: commands.Context, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will also appear in the command description.

        Parameters
        ----------
        arg: str
            Docstring description of arg.
            This is the second line of the arg docstring.
        arg2: int
            Docstring description of arg2.
        """

    assert (
        numpy.help
        == 'This is the short description that will appear.\nThis extended description will also appear in the command description.'
    )
    assert (
        numpy.clean_params['arg'].description
        == 'Docstring description of arg. This is the second line of the arg docstring.'
    )
    assert numpy.clean_params['arg2'].description == 'Docstring description of arg2.'


def test_ext_commands_descriptions_numpy_extras():
    @commands.command()
    async def numpy(ctx: commands.Context, arg: str, arg2: int) -> None:
        """This is the short description that will appear.

        This extended description will also appear in the command description.

        Parameters
        ----------
        ctx: commands.Context
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

    assert (
        numpy.help
        == 'This is the short description that will appear.\nThis extended description will also appear in the command description.'
    )
    assert (
        numpy.clean_params['arg'].description
        == 'Docstring description of arg. This is the second line of the arg docstring.'
    )
    assert numpy.clean_params['arg2'].description == 'Docstring description of arg2.'


def test_ext_commands_descriptions_cog_commands():
    class MyCog(commands.Cog):
        @commands.command()
        async def test(self, ctx: commands.Context, arg: str, arg2: int) -> None:
            """Test command

            Parameters
            ----------
            arg: str
                Description of arg.
                This is the second line of the arg description.
            arg2: int
                Description of arg2.
            """

    cog = MyCog()
    assert cog.test.help == 'Test command'
    assert cog.test.clean_params['arg'].description == 'Description of arg. This is the second line of the arg description.'
    assert cog.test.clean_params['arg2'].description == 'Description of arg2.'
