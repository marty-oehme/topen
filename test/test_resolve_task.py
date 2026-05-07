from pathlib import Path
from unittest.mock import Mock, patch

from tasklib import Task
from topen import _resolve_task


class TestResolveTask:
    def test_regular_task_returns_itself(self):
        task = Mock()
        task.__getitem__ = Mock(
            side_effect=lambda k: {
                "uuid": "11111111-1111-1111-1111-111111111111",
                "parent": None,
            }[k]
        )
        result = _resolve_task(task, Path("/tmp"))
        assert result is task

    def test_recurring_instance_returns_parent(self):
        instance = Mock()
        instance.__getitem__ = Mock(
            side_effect=lambda k: {
                "uuid": "22222222-2222-2222-2222-222222222222",
                "parent": "11111111-1111-1111-1111-111111111111",
            }[k]
        )
        parent = Mock()

        with patch("topen.get_task", return_value=parent) as mock_get:
            result = _resolve_task(instance, Path("/tmp"))

        assert result is parent
        mock_get.assert_called_once_with(
            id="11111111-1111-1111-1111-111111111111",
            data_location=Path("/tmp"),
        )

    def test_recurring_instance_with_deleted_parent_returns_itself(self):
        instance = Mock()
        instance.__getitem__ = Mock(
            side_effect=lambda k: {
                "uuid": "22222222-2222-2222-2222-222222222222",
                "parent": "11111111-1111-1111-1111-111111111111",
            }[k]
        )

        with patch("topen.get_task", side_effect=Task.DoesNotExist):
            result = _resolve_task(instance, Path("/tmp"))

        assert result is instance

    def test_empty_parent_returns_itself(self):
        task = Mock()
        task.__getitem__ = Mock(
            side_effect=lambda k: {
                "uuid": "11111111-1111-1111-1111-111111111111",
                "parent": "",
            }[k]
        )
        result = _resolve_task(task, Path("/tmp"))
        assert result is task

    def test_string_none_parent_returns_itself(self):
        """tasklib returns the string 'None' for tasks without a parent."""
        task = Mock()
        task.__getitem__ = Mock(
            side_effect=lambda k: {
                "uuid": "11111111-1111-1111-1111-111111111111",
                "parent": "None",
            }[k]
        )
        result = _resolve_task(task, Path("/tmp"))
        assert result is task
