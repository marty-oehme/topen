# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Place notes into `notes` subdirectory of taskwarrior data directory by default
- Only annotate tasks for which a note has actually been created

### Changed

- Default to same paths as taskwarrior defaults (e.g. `~/.taskrc` and `~/.task/`)
- Look for taskrc file both in xdg location and in home directory

### Fixed

- Create any necessary parent directories for notes directory.

## [0.1.0] - 2025-04-01

### Added

- Open task associated note files in specified editor
- Create command line interface for option setting
- Add license
- Take `taskrc` location as cli option
- Let user set `editor` or grab from `EDITOR`/`VISUAL` env vars
