import asyncio
import subprocess
import sys
from unittest.mock import Mock, call

import pytest

from discord import FFmpegOpusAudio


def test_fallback_timeout_kills_and_reaps_process(monkeypatch):
    timeout = subprocess.TimeoutExpired('ffmpeg', 20)
    process = Mock()
    process.communicate.side_effect = [timeout, (b'', None)]
    monkeypatch.setattr('discord.player.subprocess.Popen', Mock(return_value=process))

    with pytest.raises(subprocess.TimeoutExpired) as exc:
        FFmpegOpusAudio._probe_codec_fallback('placeholder')

    assert exc.value is timeout
    assert process.mock_calls == [call.communicate(timeout=20), call.kill(), call.communicate()]


def test_fallback_success_does_not_kill_process(monkeypatch):
    process = Mock()
    process.communicate.return_value = (b'Stream #0:0: Audio: opus, 48000 Hz, stereo, 128 kb/s', None)
    monkeypatch.setattr('discord.player.subprocess.Popen', Mock(return_value=process))
    assert FFmpegOpusAudio._probe_codec_fallback('placeholder') == ('opus', 128)
    process.kill.assert_not_called()
    process.communicate.assert_called_once_with(timeout=20)


def test_fallback_reaps_a_real_local_process(monkeypatch):
    popen = subprocess.Popen
    processes = []

    def start_process(*args, **kwargs):
        process = popen([sys.executable, '-c', 'import time; time.sleep(30)'], **kwargs)
        processes.append(process)
        communicate = process.communicate

        def short_communicate(*, timeout=None):
            return communicate(timeout=0.05 if timeout == 20 else timeout)

        process.communicate = short_communicate
        return process

    monkeypatch.setattr('discord.player.subprocess.Popen', start_process)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            FFmpegOpusAudio._probe_codec_fallback('unused')
        assert processes[0].returncode is not None
        assert processes[0].stdout.closed
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()


@pytest.mark.asyncio
@pytest.mark.parametrize('cancel_fallback', [False, True])
async def test_probe_propagates_task_cancellation(monkeypatch, cancel_fallback):
    loop = asyncio.get_running_loop()
    entered = asyncio.Event()
    submissions = []

    def run_in_executor(executor, callback):
        submissions.append(callback)
        future = loop.create_future()
        if cancel_fallback and len(submissions) == 1:
            future.set_exception(OSError('native failed'))
        elif len(submissions) == (2 if cancel_fallback else 1):
            entered.set()
        else:
            future.set_result(('opus', 128))
        return future

    monkeypatch.setattr(loop, 'run_in_executor', run_in_executor)
    task = asyncio.create_task(FFmpegOpusAudio.probe('placeholder'))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    assert len(submissions) == (2 if cancel_fallback else 1)


@pytest.mark.asyncio
@pytest.mark.parametrize('fallback_fails', [False, True])
async def test_probe_retains_error_fallback(monkeypatch, fallback_fails):
    def fail(*args):
        raise OSError('probe failed')

    fallback = Mock(side_effect=fail if fallback_fails else None, return_value=('opus', 128))
    monkeypatch.setattr(FFmpegOpusAudio, '_probe_codec_fallback', fallback)
    result = await FFmpegOpusAudio.probe('placeholder', method=fail)
    assert result == ((None, None) if fallback_fails else ('opus', 128))
    fallback.assert_called_once_with('placeholder', 'ffmpeg')
