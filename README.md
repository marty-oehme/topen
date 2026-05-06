# Simple taskwarrior note management

[![Static Badge](https://img.shields.io/badge/pdoc-Docs-blue)](https://marty-oehme.github.io/topen)
[![PyPI - Version](https://img.shields.io/pypi/v/topen)](https://pypi.org/project/topen)
[![GitHub Release](https://img.shields.io/github/v/release/marty-oehme/topen)](https://github.com/marty-oehme/topen/releases/latest)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/marty-oehme/topen/release.yaml)

A script without bells and whistles.
Focuses on letting you quickly:

- create new notes for taskwarrior tasks
- edit existing notes for taskwarrior tasks

It does both by simply being invoked with `topen <task-id>`.

Or it can be used directly from taskwarrior by being aliased in your `taskrc`:

```conf
alias.note=exec topen
```

And you can open any note with your usual taskwarrior workflow,
by doing `task note <id>`.

Provide a taskwarrior task id or uuid and `topen` creates a new note file or lets
you edit an existing one. Additionally it adds a small annotation to the task
to let you see that there exists a note file next time you view the task.

That's all there is to it.

Everything should just work as-is without additional configuration in most modern taskwarrior setups.

But if you want, many settings can be configured through your taskrc file, environment variables, or cli options, see below.

## Installation

You can install the script with your favorite python environment manager:

```bash
uv tool install topen
```

```bash
pipx install topen
```

```bash
pip install topen
```

Or just manually copy the `topen` file to a directory in your PATH.
[tasklib](https://github.com/GothenburgBitFactory/tasklib) is the only dependency aside from the python standard library.

If you just want to try the script out,
feel free to do so by invoking it e.g. with `uvx topen`.

If you want to install the trunk version instead of a versioned release simply substitute for the git path:

```bash
uv tool install git+https://git.martyoeh.me/Marty/topen.git
```

## Configuration

Most taskwarrior setups should not need much further configuration and just work out of the box.
However, if you want to diverge from the defaults explained here,
use the below settings to configure everything to your preferences.

It looks for a taskrc file in the user's home directory (`~/.taskrc`) or the XDG base config directory (usually `~/.config/task/taskrc`).
The data directory also follows the taskwarrior defaults (`~/.task`) or is read from the taskrc `data.location` option.

The notes directory defaults to be in the `notes` subdirectory of where-ever your taskwarrior data location is,
but can be set to anywhere else independently as well.

This program can be configured in 3 different ways: options set in your regular taskwarrior `taskrc` file,
environment variables or options given on the command line.

CLI options override environment variables, which in turn override configuration set in the `taskrc` file.

### Taskrc configuration

All options can be changed directly in your taskrc file.
This may be most useful for settings which do not change often for you,
such as the note extension or notes directory.

The following settings are supported:

```ini
data.location # used for the taskwarrior data directory
notes.dir # set the notes directory itself
notes.ext # set the note file extension
notes.annot # set the annotation added to tasks with notes
notes.editor # set the editor used to open notes
notes.quiet # set topen to hide all verbose information during use
notes.clean.delete # set topen to (DESTRUCTIVELY) delete notes when cleaning
```

### Environment variables

Each option can be changed through setting the corresponding environment variable.

These are the same as the `taskrc` file options with a prepended `TOPEN_` and dots turned to underscores.

The following settings are supported:

```bash
TASKRC= # taskwarrior config file location
TASKDATA= # taskwarrior data directory location
TOPEN_NOTES_DIR= # set the notes directory itself
TOPEN_NOTES_EXT= # set the note file extension
TOPEN_NOTES_ANNOT= # set the annotation added to tasks with notes
TOPEN_NOTES_EDITOR= # set the editor used to open notes
TOPEN_NOTES_QUIET= # set topen to hide all verbose information during use
TOPEN_CLEAN_DELETE= # set topen to (DESTRUCTIVELY) delete notes when cleaning
```

### CLI options

Finally, each option can be set through the cli itself.
Finally, each of the above options can be set through the cli itself.

To find out all the available options use `topen --help`.

## Tips & Tricks

### Delete existing notes

If you want to clean up your notes directory the easiest way is with `topen clean`.
This command takes all notes belonging to taskwarrior tasks that are not pending (so, completed, deleted, or missing),
and archives them by adding them to the `archive/` directory within the notes directory.

You can also actually delete these notes instead with `topen clean --delete` but
_BE CAREFUL_ with this command as it is a __destructive__ operation - your notes will be __GONE__ after running it.

But what if you want to delete individual notes, manually selecting them?

Using the `topen path` subcommand, you can manually delete notes which you don't need anymore.

Simply use `rm -f $(topen path <note-id>)` to delete the file from the filesystem.
You can wrap this in a function if you need it more often:

```sh
rmtopen() {
  rm -f $(topen path "$1")
}
```
