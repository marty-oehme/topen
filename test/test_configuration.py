# pyright: reportUnusedImport=false, reportUnusedParameter=false
# ruff: noqa: F401, F811
# ^ Turn off for implicit pytest fixture import
from pathlib import Path

import pytest

from topen import TConf, build_config


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
    def test_editor_env_resolution(self, isolate_env, monkeypatch, env, expected):
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        assert TConf(0).notes_editor == expected


class TestBuildConfigPrecedence:
    """
    All tests exercise the same key (notes_ext) to keep the assertions short.
    Each source sets a different value so we can be sure the right one wins.
    """

    def test_defaults_only(self, fake_rc, monkeypatch, isolate_env, fake_id):
        cfg = build_config()
        assert cfg.notes_ext == "md"

    def test_taskrc_overrides_defaults(
        self, fake_rc, monkeypatch, isolate_env, fake_id
    ):
        fake_rc.write_text("notes.ext=from-rc\n")
        cfg = build_config()
        assert cfg.notes_ext == "from-rc"

    def test_env_overrides_taskrc(self, fake_rc, monkeypatch, isolate_env, fake_id):
        fake_rc.write_text("notes.ext=from-rc\n")
        monkeypatch.setenv("TOPEN_NOTES_EXT", "from-env")
        cfg = build_config()
        assert cfg.notes_ext == "from-env"

    def test_circular_env_vars(self, isolate_env, monkeypatch, fake_id, fake_rc):
        """Test environment variables with circular references."""
        for k, v in {
            "TOPEN_NOTES_DIR": "$TOPEN_NOTES_DIR/subdir",
            "EDITOR": "${EDITOR}_backup",
        }.items():
            monkeypatch.setenv(k, v)
        cfg = build_config()
        assert cfg.notes_dir == Path("$TOPEN_NOTES_DIR/subdir/subdir")
        assert cfg.notes_editor == "nano"

    def test_cli_overrides_env(self, fake_rc, monkeypatch, isolate_env):
        fake_rc.write_text("notes.ext=from-rc\n")
        monkeypatch.setenv("TOPEN_NOTES_EXT", "from-env")
        monkeypatch.setattr("sys.argv", ["topen", "0", "--extension", "from-cli"])
        cfg = build_config()
        assert cfg.notes_ext == "from-cli"

    def test_cli_overrides_everything(self, fake_rc, monkeypatch, isolate_env):
        fake_rc.write_text("notes.ext=from-rc\nnotes.dir=/rc-dir\nnotes.editor=joe")
        monkeypatch.setenv("TOPEN_NOTES_EXT", "from-env")
        monkeypatch.setenv("TOPEN_NOTES_DIR", "/env-dir")
        monkeypatch.setenv("EDITOR", "emacs")
        # CLI wins
        monkeypatch.setattr(
            "sys.argv",
            [
                "topen",
                "0",
                "--extension",
                "cli-ext",
                "--notes-dir",
                "cli-dir",
                "--editor",
                "helix",
            ],
        )
        cfg = build_config()
        assert cfg.notes_ext == "cli-ext"
        assert cfg.notes_dir == Path("cli-dir")
        assert cfg.notes_editor == "helix"

    # sanity check that the task-id coming from CLI is preserved
    def test_cli_supplies_task_id(self, fake_rc, monkeypatch, isolate_env):
        monkeypatch.setattr("sys.argv", ["topen", "42"])
        cfg = build_config()
        assert cfg.task_id == "42"
