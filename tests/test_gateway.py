import logging
import types

from discord import gateway


def test_blocked_heartbeat_logging_with_percent_in_stack(caplog):
    # Pins the logging contract: the traceback must travel as a logging
    # argument (``%s``), never interpolated into the %-style format string,
    # otherwise ``%`` in the traceback breaks formatting.
    assert gateway._log.name == 'discord.gateway'

    ws = types.SimpleNamespace(loop=None, thread_id=12345, _max_heartbeat_timeout=60.0)
    handler = gateway.KeepAliveHandler(ws=ws, interval=20.0, shard_id=0)

    # Fake stack containing literal % characters, as seen in real tracebacks
    # e.g. `msg = msg % self.args` from logging internals.
    stack = '  File "x.py", line 1, in f\n    msg = msg % self.args\n'
    assert '%' in stack

    # Mirror the fixed construction from KeepAliveHandler.run
    msg = f'{handler.block_msg}\nLoop thread traceback (most recent call last):\n%s'
    assert msg.endswith('%s')

    shard_id = handler.shard_id
    total = 10

    with caplog.at_level(logging.WARNING, logger=gateway._log.name):
        gateway._log.warning(msg, shard_id, total, stack)

    assert caplog.records, 'expected a log record to be captured'
    formatted = caplog.records[0].getMessage()
    assert stack in formatted
    assert 'msg = msg % self.args' in formatted
