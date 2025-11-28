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
