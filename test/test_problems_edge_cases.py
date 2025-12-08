import configparser
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from topen import _ensure_parent_dir, get_notes_file, get_task, parse_env, parse_rc


class TestFSEdgeCases:
    """Test edge cases for TaskWarrior integration and file system operations."""

    def test_nonexistent_task_id(self, tmp_path):
        """Test raised error for non-existent task IDs."""
        with patch("tasklib.TaskWarrior") as mock_tw:
            mock_tw.return_value.tasks.get.side_effect = [
                Exception("Task not found"),
            ]

            with pytest.raises(
                Exception,
                match="Task matching query does not exist. Lookup parameters were {'uuid': '999999'}",
            ):
                get_task("999999", tmp_path)

    def test_read_only_notes_directory(self, tmp_path):
        """Test raised error when notes directory is read-only."""
        notes_dir = tmp_path / "read_only_notes"
        notes_dir.mkdir()

        # Make directory read-only
        os.chmod(notes_dir, 0o444)

        fpath = notes_dir / "subdir_cant_be_written" / "uuid.md"
        with pytest.raises(PermissionError):
            _ensure_parent_dir(fpath)

    def test_symlink_notes_directory(self, tmp_path):
        """Test behavior with symlinked notes directory,
        reading the linked dir instead of the real dir. """
        real_dir = tmp_path / "real_notes"
        real_dir.mkdir()
        link_dir = tmp_path / "linked_notes"
        link_dir.symlink_to(real_dir)

        fpath = get_notes_file("test-uuid", link_dir, "md")
        assert fpath.parent == link_dir

    def test_empty_taskrc_file(self, tmp_path):
        """Test functional handling of empty taskrc file."""
        fake_rc: Path = tmp_path / "empty.taskrc"
        fake_rc.touch()
        assert parse_rc(fake_rc) == {}

    def test_taskrc_with_invalid_syntax(self, tmp_path):
        """Test functional handling of taskrc with invalid syntax."""
        invalid_rc: Path = tmp_path / "invalid.taskrc"
        invalid_rc.write_text(
            "invalid line == [MMMM] with too many = = equals sign\ndata.location = valid_value\n"
        )

        assert parse_rc(invalid_rc)
