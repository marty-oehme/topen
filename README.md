# Topen - super simple taskwarrior note editing

A script without bells and whistles.
Focuses on letting you quickly:

- create notes for taskwarrior tasks
- edit notes for taskwarrior tasks

Does both by simply being invoked with `topen <task-id>`.

Automatically appends a small 'Note' annotation to your task so you know you have notes.

<!-- TODO: Implement configuration options -->
Should just work as-is without additional configuration in most taskwarrior setups.
But can be configured through environment variables or cli options, see below.

Can be used as-is or directly from taskwarrior by being aliased:

```conf
alias.note=exec topen
```

And you can open any note with your usual taskwarrior workflow,
by doing `task note <id>`.

That's all there is to it.

## Configuration

<!-- TODO: Stub section -->

`TOPEN_DIR`

`TOPEN_EXT`

`TASKRC`

`TASK_DATA`

`TOPEN_ANNOT`
