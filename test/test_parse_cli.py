from pathlib import Path

from topen import parse_cli


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
                "--annotation",
                "HERENOTE",
            ],
        )
        assert parse_cli() == {
            "task_id": "123",
            "notes_ext": "txt",
            "notes_editor": "vim",
            "notes_annot": "HERENOTE",
        }

    def test_cli_notes_quiet_is_flag(self, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            [
                "topen",
                "123",
                "--quiet",
            ],
        )
        assert parse_cli()["notes_quiet"] is True

    def test_cli_parses_paths(self, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            ["topen", "123", "--notes-dir", "/somewhere/else"],
        )
        assert parse_cli()["notes_dir"] == Path("/somewhere/else")
