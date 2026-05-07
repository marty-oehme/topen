from unittest.mock import Mock, patch

from topen import _IO, TConf, _cmd_edit, _cmd_path


def _make_task(uuid, status, parent=None):
    """Create a mock Task with the given uuid, status, and parent."""
    task = Mock()
    task.__getitem__ = Mock(
        side_effect=lambda k: {
            "uuid": uuid,
            "status": status,
            "parent": parent,
        }[k]
    )
    return task


class TestEditRecurring:
    """Test that _cmd_edit redirects recurring instances to the parent."""

    def test_edit_regular_task_uses_own_uuid(self, tmp_path):
        """A regular (non-recurring) task should use its own UUID for the note."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        task_uuid = "11111111-1111-1111-1111-111111111111"
        task = _make_task(task_uuid, "pending", parent="None")

        with (
            patch("topen.get_task", return_value=task),
            patch("topen.open_editor") as mock_editor,
        ):
            cfg = TConf(
                task_id="1",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=True)
            result = _cmd_edit(cfg, io)

        assert result == 0
        mock_editor.assert_called_once()
        called_path = mock_editor.call_args[0][0]
        assert called_path == notes_dir / f"{task_uuid}.md"

    def test_edit_recurring_instance_uses_parent_uuid(self, tmp_path):
        """A recurring instance should use the parent UUID for the note."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        parent_uuid = "11111111-1111-1111-1111-111111111111"
        instance_uuid = "22222222-2222-2222-2222-222222222222"

        parent_task = _make_task(parent_uuid, "recurring", parent="None")
        instance_task = _make_task(instance_uuid, "pending", parent=parent_uuid)

        with (
            patch("topen.get_task", side_effect=[instance_task, parent_task]),
            patch("topen.open_editor") as mock_editor,
        ):
            cfg = TConf(
                task_id="2",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=True)
            result = _cmd_edit(cfg, io)

        assert result == 0
        mock_editor.assert_called_once()
        called_path = mock_editor.call_args[0][0]
        assert called_path == notes_dir / f"{parent_uuid}.md"

    def test_edit_recurring_instance_notifies(self, tmp_path, capsys):
        """A recurring instance should print a redirect notification."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        parent_uuid = "11111111-1111-1111-1111-111111111111"
        instance_uuid = "22222222-2222-2222-2222-222222222222"

        parent_task = _make_task(parent_uuid, "recurring", parent="None")
        instance_task = _make_task(instance_uuid, "pending", parent=parent_uuid)

        with (
            patch("topen.get_task", side_effect=[instance_task, parent_task]),
            patch("topen.open_editor"),
        ):
            cfg = TConf(
                task_id="2",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=False)
            _cmd_edit(cfg, io)

        out = capsys.readouterr().out
        assert "recurring instance" in out

    def test_edit_regular_task_does_not_notify(self, tmp_path, capsys):
        """A regular task should not print any redirect notification."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        task_uuid = "11111111-1111-1111-1111-111111111111"
        task = _make_task(task_uuid, "pending", parent="None")

        with patch("topen.get_task", return_value=task), patch("topen.open_editor"):
            cfg = TConf(
                task_id="1",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=False)
            _cmd_edit(cfg, io)

        err = capsys.readouterr().out
        assert "recurring instance" not in err


class TestPathRecurring:
    """Test that _cmd_path redirects recurring instances to the parent."""

    def test_path_regular_task_uses_own_uuid(self, tmp_path, capsys):
        """A regular task should print its own UUID path."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        task_uuid = "11111111-1111-1111-1111-111111111111"
        task = _make_task(task_uuid, "pending", parent="None")

        with patch("topen.get_task", return_value=task):
            cfg = TConf(
                task_id="1",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=True)
            result = _cmd_path(cfg, io)

        assert result == 0
        out = capsys.readouterr().out
        assert task_uuid in out

    def test_path_recurring_instance_uses_parent_uuid(self, tmp_path, capsys):
        """A recurring instance should print the parent UUID path."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        parent_uuid = "11111111-1111-1111-1111-111111111111"
        instance_uuid = "22222222-2222-2222-2222-222222222222"

        parent_task = _make_task(parent_uuid, "recurring", parent="None")
        instance_task = _make_task(instance_uuid, "pending", parent=parent_uuid)

        with patch("topen.get_task", side_effect=[instance_task, parent_task]):
            cfg = TConf(
                task_id="2",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=True)
            result = _cmd_path(cfg, io)

        assert result == 0
        out = capsys.readouterr().out
        assert parent_uuid in out
        assert instance_uuid not in out

    def test_path_recurring_instance_notifies(self, tmp_path, capsys):
        """A recurring instance should print a redirect notification on stderr."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        parent_uuid = "11111111-1111-1111-1111-111111111111"
        instance_uuid = "22222222-2222-2222-2222-222222222222"

        parent_task = _make_task(parent_uuid, "recurring", parent="None")
        instance_task = _make_task(instance_uuid, "pending", parent=parent_uuid)

        with patch("topen.get_task", side_effect=[instance_task, parent_task]):
            cfg = TConf(
                task_id="2",
                notes_dir=notes_dir,
                task_data=tmp_path,
                task_rc=tmp_path / "rc",
            )
            io = _IO(quiet=False)
            _cmd_path(cfg, io)

        out = capsys.readouterr().out
        assert "recurring instance" in out
