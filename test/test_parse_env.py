from pathlib import Path

from topen import parse_env


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

    def test_env_parses_boolean_true(self, isolate_env, monkeypatch):
        monkeypatch.setenv("TOPEN_NOTES_QUIET", "true")
        env = parse_env()
        assert env["notes_quiet"] is True

    def test_env_parses_boolean_false(self, isolate_env, monkeypatch):
        monkeypatch.setenv("TOPEN_NOTES_QUIET", "false")
        env = parse_env()
        assert env["notes_quiet"] is False
