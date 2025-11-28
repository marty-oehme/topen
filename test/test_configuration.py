from pathlib import Path

import pytest

from topen import OPTIONS, TConf, parse_cli, parse_env, parse_rc


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
    monkeypatch.delenv("EDITOR", raising=False)
    monkeypatch.delenv("VISUAL", raising=False)
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


@pytest.fixture
def fake_rc(tmp_path: Path, monkeypatch):
    rc = tmp_path / "test.taskrc"
    monkeypatch.setattr(OPTIONS["task_rc"], "default", rc)
    return rc


class TestRcFile:
    def test_taskrc_parsing(self, fake_rc):
        fake_rc.write_text("""
        data.location=~/.taskies
        notes.dir=/there
        notes.ext=yaml
        notes.annot=Boo!
        notes.editor=micro
        notes.quiet=true
        """)
        rc_cfg = parse_rc(fake_rc)
        assert rc_cfg["task_data"] == Path("~/.taskies")
        assert rc_cfg["notes_dir"] == Path("/there")
        assert rc_cfg["notes_ext"] == "yaml"
        assert rc_cfg["notes_annot"] == "Boo!"
        assert rc_cfg["notes_editor"] == "micro"
        assert rc_cfg["notes_quiet"] is True


class TestTConf:
    def test_paths_are_expanded(self):
        cfg = TConf.from_dict(
            {
                "task_data": "~/somewhere/tasks",
                "task_id": 0,
                "task_rc": "$HOME/taskrc",
                "notes_dir": "$HOME/notes",
            }
        )
        assert cfg.task_data == Path("~/somewhere/tasks").expanduser()
        assert cfg.task_rc == Path("~/taskrc").expanduser()
        assert cfg.notes_dir == Path("~/notes").expanduser()

    def test_default_notes_sub_dir(self):
        cfg = TConf.from_dict({"task_data": "~/my/tasks", "task_id": 0})
        assert cfg.notes_dir == Path("~/my/tasks/notes").expanduser()

    @pytest.mark.parametrize(
        "env,expected",
        [
            ({"EDITOR": "vim"}, "vim"),
            ({"VISUAL": "emacs", "EDITOR": ""}, "emacs"),
            ({"VISUAL": "nvim", "EDITOR": "notepad"}, "notepad"),
        ],
    )
    def test_editor_env_resolution(isolate_env, monkeypatch, env, expected):
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        assert TConf(0).notes_editor == expected
