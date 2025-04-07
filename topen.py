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
from dataclasses import dataclass
from pathlib import Path

from tasklib import Task, TaskWarrior

DEFAULTS_DICT = {
    "task.rc": "~/.config/task/taskrc",
    "task.data": "~/.task",
    "notes.dir": "~/.task/notes",
    "notes.ext": "md",
    "notes.annot": "Note",
    "notes.editor": os.getenv("EDITOR") or os.getenv("VISUAL") or "nano",
    "notes.quiet": "False",
}


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
    opts_override = {"task.rc": DEFAULTS_DICT["task.rc"]} | parse_env() | parse_cli()
    conf_file = _real_path(opts_override["task.rc"])
    opts: dict = parse_conf(conf_file) | opts_override
    cfg = conf_from_dict(opts)

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
    fname = get_notes_file(uuid, notes_dir=cfg.notes_dir, notes_ext=cfg.notes_ext)

    open_editor(fname, editor=cfg.notes_editor)

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

    task_rc: Path
    """The path to the taskwarrior taskrc file."""
    task_data: Path
    """The path to the taskwarrior data directory."""
    task_id: int
    """The id (or uuid) of the task to edit a note for."""

    notes_dir: Path
    """The path to the notes directory."""
    notes_ext: str
    """The extension of note files."""
    notes_annot: str
    """The annotation to add to taskwarrior tasks with notes."""
    notes_editor: str
    """The editor to open note files with."""
    notes_quiet: bool
    """If set topen will give no feedback on note editing."""


def conf_from_dict(d: dict) -> TConf:
    """Generate a TConf class from a dictionary.

    Turns a dictionary containing all the necessary entries into a TConf configuration file.
    Will error if one any of the entries are missing.
    """
    return TConf(
        task_rc=_real_path(d["task.rc"]),
        task_data=_real_path(d["task.data"]),
        task_id=d["task.id"],
        notes_dir=_real_path(d["notes.dir"]),
        notes_ext=d["notes.ext"],
        notes_annot=d["notes.annot"],
        notes_editor=d["notes.editor"],
        notes_quiet=d["notes.quiet"],
    )


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
            "task.id": p.id,
            "task.rc": p.task_rc,
            "task.data": p.task_data,
            "notes.dir": p.notes_dir,
            "notes.ext": p.extension,
            "notes.annot": p.annotation,
            "notes.editor": p.editor,
            "notes.quiet": p.quiet,
        }
    )


def parse_env() -> dict:
    """Parse environment variable options.

    Returns them as a simple dict object.
    """
    return _filtered_dict(
        {
            "task.rc": os.getenv("TASKRC"),
            "task.data": os.getenv("TASKDATA"),
            "notes.dir": os.getenv("TOPEN_NOTES_DIR"),
            "notes.ext": os.getenv("TOPEN_NOTES_EXT"),
            "notes.annot": os.getenv("TOPEN_NOTES_ANNOT"),
            "notes.editor": os.getenv("TOPEN_NOTES_EDITOR"),
            "notes.quiet": os.getenv("TOPEN_NOTES_QUIET"),
        }
    )


def parse_conf(conf_file: Path) -> dict:
    """Parse taskrc configuration file options.

    Returns them as a simple dict object.
    Uses dot.annotation for options just like taskwarrior settings.
    """
    c = configparser.ConfigParser(
        defaults=DEFAULTS_DICT, allow_unnamed_section=True, allow_no_value=True
    )
    with open(conf_file.expanduser()) as f:
        c.read_string("[DEFAULT]\n" + f.read())

    return _filtered_dict(
        {
            "task.data": c.get("DEFAULT", "data.location"),
            "notes.dir": c.get("DEFAULT", "notes.dir"),
            "notes.ext": c.get("DEFAULT", "notes.ext"),
            "notes.annot": c.get("DEFAULT", "notes.annot"),
            "notes.editor": c.get("DEFAULT", "notes.editor"),
            "notes.quiet": c.get("DEFAULT", "notes.quiet"),
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
