# Simple taskwarrior note management

[Docs](https://marty-oehme.github.io/topen)
[Pypi](https://pypi.org/project/topen)

A script without bells and whistles.
Focuses on letting you quickly:

- create notes for taskwarrior tasks
- edit notes for taskwarrior tasks

It does both by simply being invoked with `topen <task-id>`.

Provide a taskwarrior task id or uuid and `topen` creates a new note file or lets
you edit an existing one. Additionally it adds a small annotation to the task
to let you see that there exists a note file next time you view the task.

Should just work as-is without additional configuration in most modern taskwarrior setups.

Can be configured through environment variables or cli options, see below.

Can be used as-is with the `topen` command or directly from taskwarrior by being aliased in your `taskrc`:

```conf
alias.note=exec topen
```

And you can open any note with your usual taskwarrior workflow,
by doing `task note <id>`.

That's all there is to it.

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
feel free to do so by invoking it e.g. with `uvx git+https://git.martyoeh.me/Marty/topen.git`.

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
TOPEN_NOTES_EDITOR= notes.editor # set the editor used to open notes
TOPEN_NOTES_QUIET= # set topen to hide all verbose information during use
```

### CLI options

Finally, each option can be set through the cli itself.

To find out all the available options use `topen --help`.
