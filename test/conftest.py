from pathlib import Path

import pytest

from topen import OPTIONS


@pytest.fixture
def fake_id(monkeypatch):
    monkeypatch.setattr("sys.argv", ["topen", "0"])


@pytest.fixture
def isolate_env(monkeypatch):
    # delete all existing env vars that could interfere
    monkeypatch.delenv("EDITOR", raising=False)
    monkeypatch.delenv("VISUAL", raising=False)
    for opt in OPTIONS.values():
        if opt.env:
            monkeypatch.delenv(opt.env, raising=False)


@pytest.fixture
def fake_rc(tmp_path: Path, monkeypatch):
    rc = tmp_path / "test.taskrc"
    monkeypatch.setattr(OPTIONS["task_rc"], "default", rc)
    return rc
