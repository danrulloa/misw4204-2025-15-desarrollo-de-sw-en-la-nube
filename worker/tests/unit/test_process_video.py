import types
from pathlib import Path
from unittest.mock import MagicMock, patch
import os

import tasks.process_video as pv


class DummyRetry(Exception):
    pass


def _mock_self():
    m = MagicMock()
    # Make self.retry raise so we can assert it was invoked
    def _retry(**kwargs):
        exc = kwargs.get("exc") or Exception("retry")
        raise DummyRetry(str(exc))
    m.retry.side_effect = _retry
    return m


def test_missing_input_path_raises_value_error(monkeypatch):
    task = pv.run
    self = _mock_self()
    # Call with no args/kwargs
    try:
        task.run(self)
    except Exception as e:
        assert isinstance(e, ValueError)
    else:
        assert False, "Expected ValueError when input_path is missing"


def test_ffmpeg_failure_invokes_retry(monkeypatch):
    task = pv.run
    self = _mock_self()

    # Environment
    monkeypatch.setenv("UPLOAD_DIR", "/app/storage/uploads")
    monkeypatch.setenv("PROCESSED_DIR", "/app/storage/processed")
    monkeypatch.setenv("ANB_INOUT_PATH", "/app/assets/inout.mp4")
    monkeypatch.setenv("ANB_WATERMARK_PATH", "/app/assets/watermark.png")

    # Mock Path.exists: source video and assets exist; output existence doesn't matter because ffmpeg fails
    def exists_side_effect(p):
        p = str(p)
        if p.endswith(".mp4") or p.endswith(".png"):
            return True
        return True

    monkeypatch.setattr(Path, "exists", lambda self: exists_side_effect(self))

    # Mock subprocess.run to simulate ffmpeg failure
    cp = types.SimpleNamespace(returncode=1, stdout=b"", stderr=b"boom")
    with patch("subprocess.run", return_value=cp):
        try:
            task.run(self, "/mnt/uploads/video.mp4")
        except DummyRetry as e:
            assert "ffmpeg failed" in str(e)
        else:
            assert False, "Expected retry due to ffmpeg failure"


def test_happy_path_moves_and_updates_db(monkeypatch):
    task = pv.run
    self = _mock_self()

    # Env
    monkeypatch.setenv("UPLOAD_DIR", "/app/storage/uploads")
    monkeypatch.setenv("PROCESSED_DIR", "/processed")
    monkeypatch.setenv("ANB_INOUT_PATH", "/app/assets/inout.mp4")
    monkeypatch.setenv("ANB_WATERMARK_PATH", "/app/assets/watermark.png")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")

    # Mock Path.exists: make input and assets exist; also the tmp output file check
    def exists_side_effect(p):
        s = str(p)
        if s.endswith("/output.mp4"):
            return True
        # Treat every checked asset and input as existing
        return True

    monkeypatch.setattr(Path, "exists", lambda self: exists_side_effect(self))

    # Mock subprocess.run success
    cp = types.SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"")
    monkeypatch.setattr("subprocess.run", lambda *a, **k: cp)

    # Mock shutil.move no-op
    moved = {}
    def _move(src, dst):
        moved["src"] = src
        moved["dst"] = dst
    monkeypatch.setattr("shutil.move", _move)

    # Mock psycopg.connect context manager
    class DummyCursor:
        rowcount = 1
        def execute(self, *a, **k):
            return None
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False

    class DummyConn:
        def cursor(self):
            return DummyCursor()
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False

    class DummyPsy:
        def __init__(self):
            self.calls = []
        def connect(self, dsn, autocommit=False):
            self.calls.append(dsn)
            return DummyConn()

    dummy_psy = DummyPsy()
    monkeypatch.setattr(pv, "psycopg", dummy_psy)

    res = task.run(self, "vid-1", "/mnt/uploads/folder/video.mp4", "corr-1")

    assert res["status"] == "ok"
    # Output should mirror uploads path under PROCESSED_DIR
    assert res["output"].endswith("/folder/video.mp4")
    # DB URL should have been converted from asyncpg to sync psycopg
    assert dummy_psy.calls and dummy_psy.calls[0].startswith("postgresql://")
    # Ensure file move destination matches the returned output path
    assert moved.get("dst") == res["output"]
