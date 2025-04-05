#!/usr/bin/env python
# Open or create a note file
# for a taskwarrior task.
# Takes a taskwarrior ID or UUID for a single task.
# Edits an existing task note file,
# or creates a new one.

# It currently assumes an XDG-compliant taskwarrior configuration by default.

import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path

from tasklib import Task, TaskWarrior

DEFAULTS_DICT = {
    "task_rc": "~/.config/task/taskrc",
    "task_data": "~/.local/share/task",
    "notes_dir": "~/.local/share/task/notes",
    "notes_ext": "md",
    "notes_annot": "Note",
    "notes_editor": os.getenv("EDITOR") or os.getenv("VISUAL") or "nano",
    "notes_quiet": "False",
}


def parse_conf(conf_file: Path) -> dict:
    c = configparser.ConfigParser(
        defaults=DEFAULTS_DICT, allow_unnamed_section=True, allow_no_value=True
    )
    with open(conf_file.expanduser()) as f:
        c.read_string("[DEFAULT]\n" + f.read())

    return _filtered_dict(
        {
            "notes_dir": c.get("DEFAULT", "notes_dir"),
            "notes_ext": c.get("DEFAULT", "notes_ext"),
            "notes_annot": c.get("DEFAULT", "notes_annot"),
            "notes_editor": c.get("DEFAULT", "notes_editor"),
            "notes_quiet": c.get("DEFAULT", "notes_quiet"),
            "task_data": c.get("DEFAULT", "data.location"),
        }
    )


def parse_env() -> dict:
    # TODO: This should not assume XDG compliance for
    # no-setup TW instances.
    return _filtered_dict(
        {
            "task_rc": os.getenv("TASKRC"),
            "task_data": os.getenv("TASKDATA"),
            "notes_dir": os.getenv("TOPEN_DIR"),
            "notes_ext": os.getenv("TOPEN_EXT"),
            "notes_annot": os.getenv("TOPEN_ANNOT"),
            "notes_editor": os.getenv("TOPEN_EDITOR"),
            "notes_quiet": os.getenv("TOPEN_QUIET"),
        }
    )


def parse_cli() -> dict:
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
    _ = parser.add_argument("--task-data", help="Location of taskwarrior data")

    p = parser.parse_args()
    return _filtered_dict(
        {
            "task_id": p.id,
            "task_data": p.task_data,
            "notes_dir": p.notes_dir,
            "notes_ext": p.extension,
            "notes_annot": p.annotation,
            "notes_editor": p.editor,
            "notes_quiet": p.quiet,
        }
    )


IS_QUIET = False


def whisper(text: str) -> None:
    if not IS_QUIET:
        print(text)


def main():
    # TODO: Don't forget to expand user (path.expanduser) and expand vars (os.path.expandvars)
    # Should probably be done when 'parsing' option object initially
    pre_cfg = parse_env() | parse_cli()
    conf_file = Path(pre_cfg.get("task_rc", DEFAULTS_DICT["task_rc"]))
    cfg = parse_conf(conf_file) | pre_cfg

    if not cfg["task_id"]:
        _ = sys.stderr.write("Please provide task ID as argument.\n")
    if cfg["notes_quiet"]:
        global IS_QUIET
        IS_QUIET = True

    task = get_task(id=cfg["task_id"], data_location=cfg["task_data"])
    uuid = task["uuid"]
    if not uuid:
        _ = sys.stderr.write(f"Could not find task for ID: {cfg['task_id']}.")
        sys.exit(1)
    fname = get_notes_file(uuid, notes_dir=cfg["notes_dir"], notes_ext=cfg["notes_ext"])

    open_editor(fname, editor=cfg["notes_editor"])

    add_annotation_if_missing(task, annotation_content=cfg["notes_annot"])


def get_task(id: str, data_location: str) -> Task:
    # FIXME: This expansion should not be done here
    tw = TaskWarrior(os.path.expandvars(data_location))
    try:
        t = tw.tasks.get(id=id)
    except Task.DoesNotExist:
        t = tw.tasks.get(uuid=id)

    return t


def get_notes_file(uuid: str, notes_dir: str, notes_ext: str) -> Path:
    return Path(notes_dir).joinpath(f"{uuid}.{notes_ext}")


def open_editor(file: Path, editor: str) -> None:
    _ = whisper(f"Editing note: {file}")
    proc = subprocess.Popen(f"{editor} {file}", shell=True)
    _ = proc.wait()


def add_annotation_if_missing(task: Task, annotation_content: str) -> None:
    for annot in task["annotations"] or []:
        if annot["description"] == annotation_content:
            return
    task.add_annotation(annotation_content)
    _ = whisper(f"Added annotation: {annotation_content}")


# A None-filtered dict which only contains
# keys which have a value.
def _filtered_dict(d: dict) -> dict:
    return {k: v for (k, v) in d.items() if v}


if __name__ == "__main__":
    main()
