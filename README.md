# Topen - super simple taskwarrior note editing

A script without bells and whistles.
Focuses on letting you quickly:

- create notes for taskwarrior tasks
- edit notes for taskwarrior tasks

Does both by simply being invoked with `topen <task-id>`.

Automatically appends a small 'Note' annotation to your task so you know you have notes.

Should just work as-is without additional configuration in most taskwarrior setups.
But can be configured through environment variables or cli options, see below.

Can be used as-is or directly from taskwarrior by being aliased:

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

## Configuration

```python
TASK_RC = os.getenv("TASKRC", "~/.config/task/taskrc") # not implemented yet
TASK_DATA_DIR = os.getenv("TASKDATA", "~/.local/share/task")
TOPEN_DIR = os.getenv("TOPEN_DIR", "~/.local/share/task/notes")
TOPEN_EXT = os.getenv("TOPEN_EXT", "md")
TOPEN_ANNOT = os.getenv("TOPEN_ANNOT", "Note")
TOPEN_EDITOR = os.getenv("EDITOR") or os.getenv("VISUAL", "nano")
TOPEN_QUIET = os.getenv("TOPEN_QUIET", False)
```

These are all environment variables offered, needs improved documentation.
<!-- TODO: IMPROVE DOC -->

Ultimately the goal would probably be to support reading from a taskwarrior 'taskrc' file,
which can then be optionally overwritten with env variables,
which can then be optionally overwritten with cli options.

This is not fully implemented -- we support the above environment variables
and cli options, that's it.
