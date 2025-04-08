#!/usr/bin/env python
"""
.. include:: ./README.md

# Usage as library

While normal operation is intended through the commandline to open or create
note files for taskwarrior tasks, the topen.py file can be used as a library to
open and edit taskwarrior notes programmatically.

You can make use of the open editor and utility functions to find and edit
notes, either filling in the required configuration manually or passing around
a TConf configuration object containing them all. If choosing the latter, you can
read the configuration in part from a `taskrc` file using the utility function
`parse_conf()`.

"""

import argparse
import configparser
import os
import subprocess
import sys
from collections import namedtuple
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Self, cast

from tasklib import Task, TaskWarrior


def main():
    """Runs the cli interface.

    First sets up the correct options, with overrides in the following order:
    `defaults -> taskrc -> env vars -> cli opts`
    with cli options having the highest priority.

    Then uses those options to get the task corresponding to the task id passed
    in as an argument, finds the matching notes file path and opens an editor
    pointing to the file.

    If the task does not yet have a note annotation it also adds it automatically.
    """
    opts_override = {"task_rc": TConf(0).task_rc} | parse_env() | parse_cli()
    conf_file = _real_path(opts_override["task_rc"])
    opts: dict = parse_conf(conf_file) | opts_override
    cfg = TConf.from_dict(opts)

    if not cfg.task_id:
        _ = sys.stderr.write("Please provide task ID as argument.\n")
    if cfg.notes_quiet:
        global IS_QUIET
        IS_QUIET = True

    task = get_task(id=cfg.task_id, data_location=cfg.task_data)
    uuid = task["uuid"]
    if not uuid:
        _ = sys.stderr.write(f"Could not find task for ID: {cfg.task_id}.")
        sys.exit(1)

    fpath = get_notes_file(uuid, notes_dir=cfg.notes_dir, notes_ext=cfg.notes_ext)

    if not fpath.parent.exists():
        fpath.parent.mkdir(parents=True, exist_ok=True)
    open_editor(fpath, editor=cfg.notes_editor)

    if fpath.exists():
        add_annotation_if_missing(task, annotation_content=cfg.notes_annot)


def get_task(id: str | int, data_location: Path) -> Task:
    """Finds a taskwarrior task from an id.

    `id` can be either a taskwarrior id or uuid.
    """
    tw = TaskWarrior(data_location)
    try:
        t = tw.tasks.get(id=id)
    except Task.DoesNotExist:
        t = tw.tasks.get(uuid=id)

    return t


def get_notes_file(uuid: str, notes_dir: Path, notes_ext: str) -> Path:
    """Finds the notes file corresponding to a taskwarrior task."""
    return Path(notes_dir).joinpath(f"{uuid}.{notes_ext}")


def open_editor(file: Path, editor: str) -> None:
    """Opens a file with the chosen editor."""
    _ = whisper(f"Editing note: {file}")
    proc = subprocess.Popen(f"{editor} {file}", shell=True)
    _ = proc.wait()


def add_annotation_if_missing(task: Task, annotation_content: str) -> None:
    """Conditionally adds an annotation to a task.

    Only adds the annotation if the task does not yet have an
    annotation with exactly that content (i.e. avoids
    duplication).
    """
    for annot in task["annotations"] or []:
        if annot["description"] == annotation_content:
            return
    task.add_annotation(annotation_content)
    _ = whisper(f"Added annotation: {annotation_content}")


@dataclass()
class TConf:
    """Topen Configuration

    Contains all the configuration options that can affect Topen note creation.
    """

    task_id: int
    """The id (or uuid) of the task to edit a note for."""
    task_rc: Path
    _task_rc: Path | None = field(init=False, repr=False, default=None)
    """The path to the taskwarrior taskrc file. Can be absolute or relative to cwd."""

    @property
    def task_rc(self) -> Path:
        if self._task_rc:
            return self._task_rc
        elif _real_path("~/.taskrc").exists():
            return _real_path("~/.taskrc")
        elif _real_path("$XDG_CONFIG_HOME/task/taskrc").exists():
            return _real_path("$XDG_CONFIG_HOME/task/taskrc")
        else:
            return _real_path("~/.config/task/taskrc")

    @task_rc.setter
    def task_rc(self, value: Path | property | None):
        if type(value) is property:
            value = TConf._notes_dir
        self._task_rc = cast(Path, value)

    task_data: Path = Path("~/.task")
    """The path to the taskwarrior data directory. Can be absolute or relative to cwd."""

    notes_dir: Path
    """The path to the notes directory."""
    _notes_dir: Path | None = field(init=False, repr=False, default=None)

    @property
    def notes_dir(self) -> Path:
        return self._notes_dir if self._notes_dir else self.task_data.joinpath("notes")

    @notes_dir.setter
    def notes_dir(self, value: Path | property | None):
        if type(value) is property:
            value = TConf._notes_dir
        self._notes_dir = cast(Path, value)

    notes_ext: str = "md"
    """The extension of note files."""
    notes_annot: str = "Note"
    """The annotation to add to taskwarrior tasks with notes."""
    notes_editor: str = os.getenv("EDITOR") or os.getenv("VISUAL") or "nano"
    """The editor to open note files with."""
    notes_quiet: bool = False
    """If set topen will give no feedback on note editing."""

    def __post_init__(self):
        self.task_rc = _real_path(self.task_rc)
        self.task_data = _real_path(self.task_data)
        self.notes_dir = _real_path(self.notes_dir)

    def __or__(self, other: Any, /) -> Self:
        return self.__class__(**asdict(self) | asdict(other))

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        """Generate a TConf class from a dictionary.

        Turns a dictionary containing all the necessary entries into a TConf configuration file.
        """
        return cls(**d)


def parse_cli() -> dict:
    """Parse cli options and arguments.

    Returns them as a simple dict object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Taskwarrior note editing made easy.",
        epilog="""Provide a taskwarrior task id or uuid and topen creates a
new note file for or lets you edit an existing one.
Additionally it adds a small annotation to the task
to let you see that there exists a note file next time
you view the task.
""",
    )
    _ = parser.add_argument(
        "id", help="The id/uuid of the taskwarrior task for which we edit notes"
    )
    _ = parser.add_argument(
        "-d",
        "--notes-dir",
        help="Location of topen notes files",
    )
    _ = parser.add_argument(
        "--quiet",
        action="store_true",
        help="Silence any verbose displayed information",
    )
    _ = parser.add_argument("--extension", help="Extension of note files")
    _ = parser.add_argument(
        "--annotation",
        help="Annotation content to set within taskwarrior",
    )
    _ = parser.add_argument("--editor", help="Program to open note files with")
    _ = parser.add_argument("--task-rc", help="Location of taskwarrior config file")
    _ = parser.add_argument(
        "--task-data", help="Location of taskwarrior data directory"
    )

    p = parser.parse_args()
    return _filtered_dict(
        {
            "task_id": p.id,
            "task_rc": p.task_rc,
            "task_data": p.task_data,
            "notes_dir": p.notes_dir,
            "notes_ext": p.extension,
            "notes_annot": p.annotation,
            "notes_editor": p.editor,
            "notes_quiet": p.quiet,
        }
    )


def parse_env() -> dict:
    """Parse environment variable options.

    Returns them as a simple dict object.
    """
    return _filtered_dict(
        {
            "task_rc": os.getenv("TASKRC"),
            "task_data": os.getenv("TASKDATA"),
            "notes_dir": os.getenv("TOPEN_NOTES_DIR"),
            "notes_ext": os.getenv("TOPEN_NOTES_EXT"),
            "notes_annot": os.getenv("TOPEN_NOTES_ANNOT"),
            "notes_editor": os.getenv("TOPEN_NOTES_EDITOR"),
            "notes_quiet": os.getenv("TOPEN_NOTES_QUIET"),
        }
    )


def parse_conf(conf_file: Path) -> dict:
    """Parse taskrc configuration file options.

    Returns them as a simple dict object.
    Uses dot.annotation for options just like taskwarrior settings.
    """
    c = configparser.ConfigParser(allow_unnamed_section=True, allow_no_value=True)
    with open(conf_file.expanduser()) as f:
        c.read_string("[GENERAL]\n" + f.read())

    ConfTrans = namedtuple("ParsedToTConf", ["name", "tconf_name"])
    return _filtered_dict(
        {
            opt.tconf_name: c.get("GENERAL", opt.name)
            for opt in [
                ConfTrans("data.location", "task_data"),
                ConfTrans("notes.dir", "notes_dir"),
                ConfTrans("notes.ext", "notes_ext"),
                ConfTrans("notes.annot", "notes_annot"),
                ConfTrans("notes.editor", "notes_editor"),
                ConfTrans("notes.quiet", "notes_quiet"),
            ]
            if c.has_option("GENERAL", opt.name)
        }
    )


IS_QUIET = False


def whisper(text: str) -> None:
    if not IS_QUIET:
        print(text)


def _real_path(p: Path | str) -> Path:
    return Path(os.path.expandvars(p)).expanduser()


# A None-filtered dict which only contains
# keys which have a value.
def _filtered_dict(d: dict) -> dict:
    return {k: v for (k, v) in d.items() if v}


if __name__ == "__main__":
    main()
