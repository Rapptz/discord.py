import concurrent.futures
import logging
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

from discord.gateway import KeepAliveHandler


def test_blocked_heartbeat_logging_with_percent():
    ws = SimpleNamespace(
        thread_id=threading.get_ident(),
        _max_heartbeat_timeout=60.0,
        HEARTBEAT=1,
        sequence=42,
        loop=Mock(),
    )
    handler = KeepAliveHandler(ws=ws, interval=0, shard_id=0)

    handler._stop_ev = Mock()
    handler._stop_ev.wait.side_effect = [False, True]

    future = Mock()
    future.result.side_effect = [
        concurrent.futures.TimeoutError(),
        None,
    ]

    stack = 'File "example.py", line 10\n    value = 50 % 3\n'

    def fake_run_coroutine_threadsafe(coro, loop):
        coro.close()
        return future

    # Avoid replacing sys._current_frames globally.
    with (
        patch(
            'discord.gateway.asyncio.run_coroutine_threadsafe',
            side_effect=fake_run_coroutine_threadsafe,
        ),
        patch(
            'discord.gateway.traceback.format_stack',
            return_value=[stack],
        ),
        patch('discord.gateway._log') as mock_logger,
    ):
        handler.run()

    assert future.result.call_count == 2
    assert mock_logger.warning.call_count == 1

    args = mock_logger.warning.call_args.args
    record = logging.LogRecord(
        name='discord.gateway',
        level=logging.WARNING,
        pathname=__file__,
        lineno=0,
        msg=args[0],
        args=args[1:],
        exc_info=None,
    )

    formatted = record.getMessage()
    assert 'heartbeat blocked' in formatted
    assert '50 % 3' in formatted
