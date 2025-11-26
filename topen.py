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
`parse_rc()`.

"""

import argparse
import configparser
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Self

from tasklib import Task, TaskWarrior

NON_EXISTENT_PATH = Path("%%%%I_DONT_EXIST_%%%%")


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
    opts: dict = parse_rc(conf_file) | opts_override
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
        return
    whisper("No note file, doing nothing.")


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
    whisper(f"Editing note: {file}")
    _ = subprocess.run(f"{editor} {file}", shell=True)


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
class Opt:
    """Assembled metadata for a single configuration option."""

    cli: tuple[str, ...] | None
    env: str | None
    rc: str | None
    default: Any = None
    metavar: str | None = None
    cast: type = str
    help_text: str = ""


OPTIONS: dict[str, Opt] = {
    "task_id": Opt(None, None, None, default=None),
    "task_rc": Opt(
        ("--task-rc",),
        "TASKRC",
        None,  # taskrc has no key for this
        default=Path("~/.taskrc"),
        metavar="FILE",
        cast=Path,
        help_text="Location of taskwarrior config file",
    ),
    "task_data": Opt(
        ("--task-data",),
        "TASKDATA",
        "data.location",
        default=Path("~/.task"),
        metavar="DIR",
        cast=Path,
        help_text="Location of taskwarrior data directory",
    ),
    "notes_dir": Opt(
        ("-d", "--notes-dir"),
        "TOPEN_NOTES_DIR",
        "notes.dir",
        default=None,  # resolved later in TConf.__post_init__
        metavar="DIR",
        cast=Path,
        help_text="Location of topen notes files",
    ),
    "notes_ext": Opt(
        ("--extension",),
        "TOPEN_NOTES_EXT",
        "notes.ext",
        default="md",
        metavar="EXT",
        help_text="Extension of note files",
    ),
    "notes_annot": Opt(
        ("--annotation",),
        "TOPEN_NOTES_ANNOT",
        "notes.annot",
        default="Note",
        metavar="NOTE",
        help_text="Annotation content to set within taskwarrior",
    ),
    "notes_editor": Opt(
        ("--editor",),
        "TOPEN_NOTES_EDITOR",
        "notes.editor",
        default=os.getenv("EDITOR") or os.getenv("VISUAL") or "nano",
        metavar="CMD",
        help_text="Program to open note files with",
    ),
    "notes_quiet": Opt(
        ("--quiet",),
        "TOPEN_NOTES_QUIET",
        "notes.quiet",
        default=False,
        cast=bool,
        help_text="Silence any verbose displayed information",
    ),
}


@dataclass()
class TConf:
    """Topen Configuration

    Contains all the configuration options that can affect Topen note creation.
    """

    task_id: int
    """The id (or uuid) of the task to edit a note for."""
    task_rc: Path = NON_EXISTENT_PATH
    """The path to the taskwarrior taskrc file. Can be absolute or relative to cwd."""

    task_data: Path = Path("~/.task")
    """The path to the taskwarrior data directory. Can be absolute or relative to cwd."""

    notes_dir: Path = NON_EXISTENT_PATH
    """The path to the notes directory."""

    notes_ext: str = "md"
    """The extension of note files."""
    notes_annot: str = "Note"
    """The annotation to add to taskwarrior tasks with notes."""
    notes_editor: str = os.getenv("EDITOR") or os.getenv("VISUAL") or "nano"
    """The editor to open note files with."""
    notes_quiet: bool = False
    """If set topen will give no feedback on note editing."""

    def __post_init__(self):
        if self.task_rc == NON_EXISTENT_PATH:
            self.task_rc = self._default_task_rc()
        self.task_rc = _real_path(self.task_rc)
        self.task_data = _real_path(self.task_data)
        if self.notes_dir == NON_EXISTENT_PATH:
            self.notes_dir = self._default_notes_dir()
        self.notes_dir = _real_path(self.notes_dir)

    def __or__(self, other: Any, /) -> Self:
        return self.__class__(**asdict(self) | asdict(other))

    def _default_task_rc(self) -> Path:
        if Path("~/.taskrc").exists():
            return Path("~/.taskrc")
        elif Path("$XDG_CONFIG_HOME/task/taskrc").exists():
            return Path("$XDG_CONFIG_HOME/task/taskrc")
        else:
            return Path("~/.config/task/taskrc")

    def _default_notes_dir(self) -> Path:
        return self.task_data.joinpath("notes")

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
    for key, opt in OPTIONS.items():
        if opt.cli is None:
            continue
        parser.add_argument(
            *opt.cli,
            dest=key,
            metavar=opt.metavar,
            help=opt.help_text,
            default=None,
        )
    args = parser.parse_args()
    cli_vals = {k: v for k, v in vars(args).items() if v is not None}
    cli_vals["task_id"] = cli_vals.pop("id")
    return cli_vals


def parse_env() -> dict[str, Any]:
    """Parse environment variable options.

    Returns them as a simple dict object.
    """
    out: dict[str, Any] = {}
    for key, opt in OPTIONS.items():
        if opt.env and (val := os.getenv(opt.env)) is not None:
            out[key] = opt.cast(val)
    return out


def parse_rc(rc_path: Path) -> dict:
    """Parse taskrc configuration file options.

    Returns them as a simple dict object.
    Uses dot.annotation for options just like taskwarrior settings.
    """
    cfg = configparser.ConfigParser(allow_unnamed_section=True, allow_no_value=True)
    with rc_path.expanduser().open() as fr:
        cfg.read_string("[GENERAL]\n" + fr.read())

    out: dict[str, Any] = {}
    for key, opt in OPTIONS.items():
        if opt.rc and cfg.has_option("GENERAL", opt.rc):
            raw = cfg.get("GENERAL", opt.rc)
            out[key] = opt.cast(raw)
    return out


IS_QUIET = False


def whisper(text: str) -> None:
    if not IS_QUIET:
        print(text)


def _real_path(p: Path | str) -> Path:
    return Path(os.path.expandvars(p)).expanduser()


if __name__ == "__main__":
    main()
