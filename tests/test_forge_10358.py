import pytest
from discord import app_commands
from discord.ext import commands


class RaceFlags(commands.FlagConverter):
    goal: str | None = None
    when: str | None = None
    streaming_required: bool = False
    race_info: str | None = None
    announce: bool = False


def test_flag_converter_usable_in_app_commands():
    """Regression test for issue #10358.

    Using a FlagConverter subclass as a parameter annotation in an
    app_commands.command() should not raise TypeError.
    """

    class MyCog:
        @app_commands.command()
        async def communityrace(
            self,
            interaction: "Interaction",  # noqa: F821 - string annotation for test
            *,
            flags: RaceFlags,
        ) -> None:
            pass

    # If we get here without a TypeError, the bug is fixed.
    assert MyCog.communityrace is not None