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

# list of all available sub-commands and cli aliases
SUBCOMMANDS = {
    "edit": "edit",
    "path": "path",
    "clean": "clean",
}


def main(cfg: "TConf | None" = None, io: "_IO | None" = None) -> int:
    """Runs the cli interface.

    First sets up the correct options, with overrides in the following order:
    `defaults -> taskrc -> env vars -> cli opts`
    with cli options having the highest priority.

    Then dispatches to the appropriate subcommand handler.

    Returns the status code as int, 0 for success, 1 for error.
    """
    if not cfg:
        cfg = build_config()
    if not io:
        io = _IO(quiet=cfg.notes_quiet)

    if cfg.command == SUBCOMMANDS["edit"]:
        return _cmd_edit(cfg, io)
    elif cfg.command == SUBCOMMANDS["path"]:
        return _cmd_path(cfg, io)
    elif cfg.command == SUBCOMMANDS["clean"]:
        return _cmd_clean(cfg, io)
    else:
        io.err(f"Unknown command: {cfg.command}\n")
        return 1


def _cmd_edit(cfg: "TConf", io: "_IO") -> int:
    """Open or create a note for a task.

    Uses the configured options to get the task corresponding to the task id
    passed in as an argument, finds the matching notes file path and opens an
    editor pointing to the file.

    If the task does not yet have a note annotation it also adds it automatically.

    Returns the status code as int, 0 for success, 1 for error.
    """
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


def _cmd_path(cfg: "TConf", io: "_IO") -> int:
    """Print the note file path for a task.

    It does not matter if the note file for a task already exists or not
    this always prints the path to its calculated file.
    """
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
    prev_quiet = io.quiet
    io.quiet = False
    io.out(str(fpath))
    io.quiet = prev_quiet
    return 0
 
 
def _cmd_clean(cfg: "TConf", io: "_IO") -> int:
    """Remove note files for tasks that no longer exist."""
    io.err("Not yet implemented.\n")
    return 1
 
 
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
    cli_subcommand: str | None = None  # which cli subcommand to add to as option


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
        cli_subcommand=SUBCOMMANDS["edit"],
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

    task_id: int | None = None
    """The id (or uuid) of the task to edit a note for."""
    command: str = "edit"
    """The subcommand to execute (edit, path, clean)."""
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

    rc_string = cli.get("task_rc") or env.get("task_rc") or defaults.get("task_rc")
    if not rc_string:
        raise ValueError("Cannot find correct rc file string.")
    rc_path = Path(rc_string).expanduser()
    defaults["task_rc"] = rc_path  # use XDG-included paths
    rc = parse_rc(rc_path) if rc_path.exists() else {}

    merged = defaults | rc | env | cli  # later wins
    return TConf.from_dict({k: v for k, v in merged.items() if v is not None})


def _add_opt_to_parser(parser: argparse.ArgumentParser, key: str, opt: Opt) -> None:
    """Add a single OPTIONS entry to an argparse parser."""
    if opt.cli is None:
        return
    if opt.is_flag:
        parser.add_argument(
            *opt.cli,
            dest=key,
            help=opt.help_text,
            default=None,
            action="store_true",
        )
    else:
        parser.add_argument(
            *opt.cli,
            dest=key,
            metavar=opt.metavar,
            help=opt.help_text,
            type=opt.cast or str,
            default=None,
        )


def parse_cli() -> dict:
    """Parse cli options and arguments.

    Returns them as a simple dict object.
    """
    # Inject 'edit' subcommand for backward compat: `topen 42` → `topen edit 42`
    if (
        len(sys.argv) > 1
        and sys.argv[1] not in SUBCOMMANDS.values()
        and sys.argv[1] not in ("-h", "--help")
    ):
        sys.argv.insert(1, "edit")

    # gather all shared options
    SHARED_OPTION_KEYS = [k for k, v in OPTIONS.items() if v.cli_subcommand is None]

    # Parent parser for options shared across all subcommands
    shared_parser = argparse.ArgumentParser(add_help=False)
    for key in SHARED_OPTION_KEYS:
        _add_opt_to_parser(shared_parser, key, OPTIONS[key])

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
    # Recognize shared options at root level: `topen --notes-dir /foo clean`
    for key in SHARED_OPTION_KEYS:
        _add_opt_to_parser(parser, key, OPTIONS[key])

    subparsers = parser.add_subparsers(dest="command")

    # edit subparser
    edit_parser = subparsers.add_parser(
        SUBCOMMANDS["edit"],
        help="Open or create a note for a task (default)",
        parents=[shared_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    edit_parser.add_argument(
        "id", help="The id/uuid of the taskwarrior task for which to edit note"
    )
    # Edit-specific options
    for opt_name, opt in {
        k: v for k, v in OPTIONS.items() if v.cli_subcommand == SUBCOMMANDS["edit"]
    }.items():
        _add_opt_to_parser(edit_parser, opt_name, opt)

    # path subparser
    path_parser = subparsers.add_parser(
        SUBCOMMANDS["path"],
        help="Print the note file path for a task",
        parents=[shared_parser],
    )
    path_parser.add_argument(
        "id", help="The id/uuid of the taskwarrior task for which to show path"
    )
    for opt_name, opt in {
        k: v for k, v in OPTIONS.items() if v.cli_subcommand == SUBCOMMANDS["path"]
    }.items():
        _add_opt_to_parser(path_parser, opt_name, opt)

    # clean subparser
    clean_parser = subparsers.add_parser(
        SUBCOMMANDS["clean"],
        help="Remove all note files for tasks that no longer exist",
        parents=[shared_parser],
    )
    for opt_name, opt in {
        k: v for k, v in OPTIONS.items() if v.cli_subcommand == SUBCOMMANDS["clean"]
    }.items():
        _add_opt_to_parser(clean_parser, opt_name, opt)

    args = parser.parse_args()
    cli_vals = {k: v for k, v in vars(args).items() if v is not None}
    if "id" in cli_vals:
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
