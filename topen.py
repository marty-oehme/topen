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
from typing import Any, Callable, Self, cast

from tasklib import Task, TaskWarrior

NON_EXISTENT_PATH = Path("%%%%I_DONT_EXIST_%%%%")


def main(cfg: "TConf | None" = None, io: "_IO | None" = None) -> int:
    """Runs the cli interface.

    First sets up the correct options, with overrides in the following order:
    `defaults -> taskrc -> env vars -> cli opts`
    with cli options having the highest priority.

    Then uses those options to get the task corresponding to the task id passed
    in as an argument, finds the matching notes file path and opens an editor
    pointing to the file.

    If the task does not yet have a note annotation it also adds it automatically.

    Returns the status code as int, 0 for success, 1 for error.
    """
    if not cfg:
        cfg = build_config()
    if not io:
        io = _IO(quiet=cfg.notes_quiet)

    if not cfg.task_id:
        io.err("Please provide task ID as argument.\n")
        return 1

    try:
        task = get_task(id=cfg.task_id, data_location=cfg.task_data)
        uuid = cast(str, task["uuid"])
    except Task.DoesNotExist:
        io.err(f"Could not find task for ID: {cfg.task_id}.\n")
        return 1

    fpath = get_notes_file(uuid, notes_dir=cfg.notes_dir, notes_ext=cfg.notes_ext)

    try:
        _ensure_parent_dir(fpath)
    except PermissionError:
        io.err(f"Could not write required directories for path: {fpath}.\n")
        return 1

    io.out(f"Editing note: {fpath}")
    open_editor(fpath, editor=cfg.notes_editor, io=io)

    if fpath.exists():
        if is_annotation_missing(task, annotation_content=cfg.notes_annot):
            add_annotation(task, annotation_content=cfg.notes_annot)
            io.out(f"Added annotation: {cfg.notes_annot}")
        return 0
    io.out("No note file, doing nothing.")
    return 0


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


def open_editor(file: Path, editor: str, io: "_IO | None" = None) -> None:
    """Opens a file with the chosen editor."""
    try:
        _ = subprocess.run([editor, str(file)], check=True)
    except subprocess.CalledProcessError:
        if io:
            io.err("Editor exited with an error, aborting.\n")


def is_annotation_missing(task: Task, annotation_content: str) -> bool:
    """Checks if the task is missing the annotation.

    Only succeeds if the _complete_ annatotation is found,
    and not just as a substring.

    Returns True if annotation was added, otherwise False.
    """
    for annot in task["annotations"] or []:
        if annot["description"] == annotation_content:
            return False
    return True


def add_annotation(task: Task, annotation_content: str) -> None:
    """Adds an annotation to a task."""
    task.add_annotation(annotation_content)


@dataclass()
class Opt:
    """Assembled metadata for a single configuration option."""

    cli: tuple[str, ...] | None
    env: str | None
    rc: str | None
    default: Any = None
    metavar: str | None = None
    cast: type | Callable = str
    help_text: str = ""
    is_flag: bool = False


def _expand_path(p: Path | str) -> Path:
    return Path(os.path.expandvars(p)).expanduser()


def _ensure_parent_dir(file: Path) -> None:
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)


def _determine_default_task_rc() -> Path:
    if _expand_path("~/.taskrc").exists():
        return _expand_path("~/.taskrc")
    if _expand_path("$XDG_CONFIG_HOME/task/taskrc").exists():
        return _expand_path("$XDG_CONFIG_HOME/task/taskrc")
    return _expand_path("~/.config/task/taskrc")


def _strtobool(val: str) -> bool:
    """Convert a string representation of truth.

    Coverts either to True or False, raising an error if it does not find a
    valid value.
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values are 'n',
    'no', 'f', 'false', 'off', and '0'.
    Raises ValueError if 'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Invalid boolean value {val}")


OPTIONS: dict[str, Opt] = {
    "task_id": Opt(None, None, None, default=None),
    "task_rc": Opt(
        ("--task-rc",),
        "TASKRC",
        None,  # taskrc has no key for this
        default=_determine_default_task_rc(),
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
        default="nano",
        metavar="CMD",
        help_text="Program to open note files with",
    ),
    "notes_quiet": Opt(
        ("--quiet",),
        "TOPEN_NOTES_QUIET",
        "notes.quiet",
        default=False,
        cast=_strtobool,
        help_text="Silence any verbosely displayed information",
        is_flag=True,
    ),
}


@dataclass()
class TConf:
    """Topen Configuration

    Contains all the configuration options that can affect Topen note creation.
    """

    task_id: int
    """The id (or uuid) of the task to edit a note for."""
    task_rc: Path = OPTIONS["task_rc"].default
    """The path to the taskwarrior taskrc file. Can be absolute or relative to cwd."""

    task_data: Path = OPTIONS["task_data"].default
    """The path to the taskwarrior data directory. Can be absolute or relative to cwd."""

    notes_dir: Path = NON_EXISTENT_PATH
    """The path to the notes directory."""

    notes_ext: str = OPTIONS["notes_ext"].default
    """The extension of note files."""
    notes_annot: str = OPTIONS["notes_annot"].default
    """The annotation to add to taskwarrior tasks with notes."""
    notes_editor: str = ""  # added in post-init
    """The editor to open note files with."""
    notes_quiet: bool = OPTIONS["notes_quiet"].default
    """If set topen will give no feedback on note editing."""

    def __post_init__(self):
        self.task_rc = _expand_path(self.task_rc)
        self.task_data = _expand_path(self.task_data)
        if self.notes_dir == NON_EXISTENT_PATH:
            self.notes_dir = self._default_notes_dir()
        self.notes_dir = _expand_path(self.notes_dir)
        if not self.notes_editor:
            self.notes_editor = (
                os.getenv("EDITOR")
                or os.getenv("VISUAL")
                or OPTIONS["notes_editor"].default
            )

    def __or__(self, other: Any, /) -> Self:
        return self.__class__(**asdict(self) | asdict(other))

    def _default_notes_dir(self) -> Path:
        return self.task_data.joinpath("notes")

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        """Generate a TConf class from a dictionary.

        Turns a dictionary containing all the necessary entries into a TConf configuration file.
        """
        return cls(**d)


def build_config() -> TConf:
    """Return final configuration object."""
    defaults = {k: opt.default for k, opt in OPTIONS.items()}
    env = parse_env()
    cli = parse_cli()

    rc_path = Path(
        cli.get("task_rc") or env.get("task_rc") or OPTIONS["task_rc"].default
    ).expanduser()
    defaults["task_rc"] = rc_path  # use XDG-included paths
    rc = parse_rc(rc_path) if rc_path.exists() else {}

    merged = defaults | rc | env | cli  # later wins
    return TConf.from_dict({k: v for k, v in merged.items() if v is not None})


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
        if opt.is_flag:
            parser.add_argument(
                *opt.cli,
                dest=key,
                help=opt.help_text,
                default=None,
                action="store_true",
            )
            continue
        parser.add_argument(
            *opt.cli,
            dest=key,
            metavar=opt.metavar,
            help=opt.help_text,
            type=opt.cast or str,
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


class _IO:
    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def out(self, text: str) -> None:
        if not self.quiet:
            print(text)

    def err(self, text: str) -> None:
        sys.stderr.write(text)


if __name__ == "__main__":
    exit = main()
    sys.exit(exit)
