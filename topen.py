#!/usr/bin/env python
# Open or create a note file
# for a taskwarrior task.
# Takes a taskwarrior ID or UUID for a single task.
# Edits an existing task note file,
# or creates a new one.

# It currently assumes an XDG-compliant taskwarrior configuration by default.

import argparse
import os
import subprocess
import sys
from pathlib import Path

from tasklib import Task, TaskWarrior

# TODO: This should not assume XDG compliance for
# no-setup TW instances.
TASK_RC = os.getenv("TASKRC", "~/.config/task/taskrc")
TASK_DATA_DIR = os.getenv("TASKDATA", "~/.local/share/task")

TOPEN_DIR = os.getenv("TOPEN_DIR", "~/.local/share/task/notes")
TOPEN_EXT = os.getenv("TOPEN_EXT", "md")
TOPEN_ANNOT = os.getenv("TOPEN_ANNOT", "Note")
TOPEN_EDITOR = os.getenv("EDITOR") or os.getenv("VISUAL", "nano")
TOPEN_QUIET = os.getenv("TOPEN_QUIET", False)


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Taskwarrior note editing made easy.")
    _ = parser.add_argument(
        "id", help="The id/uuid of the taskwarrior task for which we edit notes"
    )
    _ = parser.add_argument(
        "-d",
        "--notes-dir",
        default=TOPEN_DIR,
        help="Location of topen notes files",
    )
    _ = parser.add_argument(
        "--quiet",
        default=TOPEN_QUIET,
        action="store_true",
        help="Silence any verbose displayed information",
    )
    _ = parser.add_argument(
        "--extension", default=TOPEN_EXT, help="Extension of note files"
    )
    _ = parser.add_argument(
        "--annotation",
        default=TOPEN_ANNOT,
        help="Annotation content to set within taskwarrior",
    )
    _ = parser.add_argument(
        "--task-data", default=TASK_DATA_DIR, help="Location of taskwarrior data"
    )
    _ = parser.add_argument(
        "--editor", default=TOPEN_EDITOR, help="Program to open note files with"
    )

    return parser.parse_args()


IS_QUIET = False


def whisper(text: str) -> None:
    if not IS_QUIET:
        print(text)


def main():
    args = parse_cli()

    if not args.id:
        _ = sys.stderr.write("Please provide task ID as argument.\n")
    if args.quiet:
        global IS_QUIET
        IS_QUIET = True

    task = get_task(id=args.id, data_location=args.task_data)
    uuid = task["uuid"]
    if not uuid:
        _ = sys.stderr.write(f"Could not find task for ID: {args.id}.")
        sys.exit(1)
    fname = get_notes_file(uuid, notes_dir=args.notes_dir, notes_ext=args.extension)

    open_editor(fname, editor=args.editor)

    add_annotation_if_missing(task, annotation_content=args.annotation)


def get_task(id: str, data_location: str = TASK_DATA_DIR) -> Task:
    tw = TaskWarrior(data_location)
    try:
        t = tw.tasks.get(id=id)
    except Task.DoesNotExist:
        t = tw.tasks.get(uuid=id)

    return t


def get_notes_file(
    uuid: str, notes_dir: str = TOPEN_DIR, notes_ext: str = TOPEN_EXT
) -> Path:
    return Path(notes_dir).joinpath(f"{uuid}.{notes_ext}")


def open_editor(file: Path, editor: str = TOPEN_EDITOR) -> None:
    _ = whisper(f"Editing note: {file}")
    proc = subprocess.Popen(f"{editor} {file}", shell=True)
    _ = proc.wait()


def add_annotation_if_missing(
    task: Task, annotation_content: str = TOPEN_ANNOT
) -> None:
    for annot in task["annotations"] or []:
        if annot["description"] == annotation_content:
            return
    task.add_annotation(annotation_content)
    _ = whisper(f"Added annotation: {annotation_content}")


if __name__ == "__main__":
    main()
