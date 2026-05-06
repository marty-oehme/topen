from pathlib import Path
from unittest.mock import Mock, patch

from topen import TConf, _IO, _cmd_clean


class TestCleanCommand:
    def test_clean_removes_completed_and_orphaned_notes(self, tmp_path):
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        pending_uuid = "11111111-1111-1111-1111-111111111111"
        completed_uuid = "22222222-2222-2222-2222-222222222222"
        orphaned_uuid = "33333333-3333-3333-3333-333333333333"

        (notes_dir / f"{pending_uuid}.md").write_text("pending")
        (notes_dir / f"{completed_uuid}.md").write_text("completed")
        (notes_dir / f"{orphaned_uuid}.md").write_text("orphaned")

        pending_task = Mock()
        pending_task.__getitem__ = lambda _s, k: {
            "uuid": pending_uuid,
            "status": "pending",
        }[k]
        completed_task = Mock()
        completed_task.__getitem__ = lambda _s, k: {
            "uuid": completed_uuid,
            "status": "completed",
        }[k]

        with patch("topen.TaskWarrior") as mock_tw:
            mock_tw.return_value.tasks.all.return_value = [pending_task, completed_task]

            cfg = TConf(
                notes_dir=notes_dir, task_data=tmp_path, task_rc=tmp_path / "rc"
            )
            io = _IO(quiet=False)
            result = _cmd_clean(cfg, io)

            assert result == 0
            assert (notes_dir / f"{pending_uuid}.md").exists()
            assert not (notes_dir / f"{completed_uuid}.md").exists()
            assert not (notes_dir / f"{orphaned_uuid}.md").exists()

    def test_clean_skips_non_uuid_files(self, tmp_path):
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        (notes_dir / "README.md").write_text("readme")
        (notes_dir / "some-uuid.md").write_text("not a real uuid")

        with patch("topen.TaskWarrior") as mock_tw:
            mock_tw.return_value.tasks.all.return_value = []

            cfg = TConf(
                notes_dir=notes_dir, task_data=tmp_path, task_rc=tmp_path / "rc"
            )
            io = _IO(quiet=False)
            result = _cmd_clean(cfg, io)

            assert result == 0
            assert (notes_dir / "README.md").exists()
            assert (notes_dir / "some-uuid.md").exists()

    def test_clean_skips_directories_inside_notes_dir(self, tmp_path):
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        subdir = notes_dir / "11111111-1111-1111-1111-111111111111.md"
        subdir.mkdir()

        with patch("topen.TaskWarrior") as mock_tw:
            mock_tw.return_value.tasks.all.return_value = []

            cfg = TConf(
                notes_dir=notes_dir, task_data=tmp_path, task_rc=tmp_path / "rc"
            )
            io = _IO(quiet=False)
            result = _cmd_clean(cfg, io)

            assert result == 0
            assert subdir.exists()

    def test_clean_handles_missing_notes_dir(self, tmp_path):
        notes_dir = tmp_path / "nonexistent" / "notes"

        cfg = TConf(notes_dir=notes_dir, task_data=tmp_path, task_rc=tmp_path / "rc")
        io = _IO(quiet=False)
        result = _cmd_clean(cfg, io)

        assert result == 0

    def test_clean_reports_permission_error_on_delete(self, tmp_path):
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        note_file = notes_dir / "11111111-1111-1111-1111-111111111111.md"
        note_file.write_text("note")

        with patch("topen.TaskWarrior") as mock_tw:
            mock_tw.return_value.tasks.all.return_value = []

            with patch.object(Path, "unlink", side_effect=PermissionError("denied")):
                cfg = TConf(
                    notes_dir=notes_dir,
                    task_data=tmp_path,
                    task_rc=tmp_path / "rc",
                    clean_delete=True,
                )
                io = _IO(quiet=False)
                result = _cmd_clean(cfg, io)

                assert result == 1
