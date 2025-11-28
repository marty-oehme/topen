from pathlib import Path

import pytest

from topen import OPTIONS, parse_cli, parse_env, parse_rc


class TestCli:
    def test_cli_minimum_id(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["topen", "42"])
        assert parse_cli() == {"task_id": "42"}

    def test_cli_options(self, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            [
                "topen",
                "123",
                "--extension",
                "txt",
                "--editor",
                "vim",
                "--quiet",
                "True",
            ],
        )
        assert parse_cli() == {
            "task_id": "123",
            "notes_ext": "txt",
            "notes_editor": "vim",
            "notes_quiet": True,
        }


@pytest.fixture
def isolate_env(monkeypatch):
    # delete all existing env vars that could interfere
    for opt in OPTIONS.values():
        if opt.env:
            monkeypatch.delenv(opt.env, raising=False)


class TestEnv:
    def test_env_notes_ext(self, isolate_env, monkeypatch):
        monkeypatch.setenv("TOPEN_NOTES_DIR", "/blablubb")
        monkeypatch.setenv("TOPEN_NOTES_EXT", "rst")
        monkeypatch.setenv("TOPEN_NOTES_ANNOT", "qmd")
        monkeypatch.setenv("TOPEN_NOTES_EDITOR", "vim")
        monkeypatch.setenv("TOPEN_NOTES_QUIET", "true")
        env = parse_env()
        assert env["notes_dir"] == Path("/blablubb")
        assert env["notes_ext"] == "rst"
        assert env["notes_annot"] == "qmd"
        assert env["notes_editor"] == "vim"
        assert env["notes_quiet"] is True

    def test_env_task_rc(self, isolate_env, monkeypatch):
        monkeypatch.setenv("TASKRC", "/a/dir/that/dont/exist/file")
        monkeypatch.setenv("TASKDATA", "~/somewhere/tasks")
        env = parse_env()
        assert env["task_rc"] == Path("/a/dir/that/dont/exist/file")
        assert env["task_data"] == Path("~/somewhere/tasks")
