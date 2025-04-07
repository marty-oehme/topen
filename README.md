# Topen - simple taskwarrior note editing

A script without bells and whistles.
Focuses on letting you quickly:

- create notes for taskwarrior tasks
- edit notes for taskwarrior tasks

It does both by simply being invoked with `topen <task-id>`.

Provide a taskwarrior task id or uuid and topen creates a new note file or lets
you edit an existing one. Additionally it adds a small annotation to the task
to let you see that there exists a note file next time you view the task.

Should just work as-is without additional configuration in most modern taskwarrior setups.[^moderntw]

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
uv tool install git+https://git.martyoeh.me/Marty/topen.git
```

```bash
pipx install git+https://git.martyoeh.me/Marty/topen.git
```

```bash
pip install git+https://git.martyoeh.me/Marty/topen.git
```

Or just manually copy the `topen` file to a directory in your PATH.

If you just want to try the script out,
feel free to do so by invoking it e.g. with `uvx git+https://git.martyoeh.me/Marty/topen.git`.

Only has [tasklib](https://github.com/GothenburgBitFactory/tasklib) as a dependency.

## Configuration

By default the script generally assumes your taskwarrior setup follows the XDG
base directory suggestions.

That means, taskrc in `$XDG_CONFIG_HOME/task/taskrc`, usually
`~/.config/task/taskrc`. Furthermore, at the moment it assumes the taskwarrior
_data_ residing in the `$XDG_DATA_HOME/task` directory. This may diverge from
taskwarrior setups still.

This program can be configured in 3 different ways: options set in your regular taskwarrior `taskrc` file,
environment variables or options given on the command line.

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

<!-- TODO: IMPROVE DOC -->
Ultimately the goal would probably be to support reading from a taskwarrior 'taskrc' file,
which can then be optionally overwritten with env variables,
which can then be optionally overwritten with cli options.

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
