from pathlib import Path
from unittest.mock import Mock, patch

from topen import add_annotation, open_editor


def test_open_editor_escapes_shell():
    """Ensure filenames with spaces/metas do not allow shell injection."""
    with patch("subprocess.run") as run_mock:
        open_editor(Path("my note$1.txt"), "vim")
    run_mock.assert_called_once_with(["vim", "my note$1.txt"], check=True)


def test_add_annotation_calls_tasklib():
    task = Mock()
    add_annotation(task, "hello")
    task.add_annotation.assert_called_once_with("hello")
