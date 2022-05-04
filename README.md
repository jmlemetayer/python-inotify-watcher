# inotify_watcher

[![Package Status][package-badge]][package-link]
[![Documentation Status][documentation-badge]][documentation-link]
[![License Status][license-badge]][license-link]
[![Build Status][build-badge]][build-link]
[![Quality Status][pre-commit-badge]][pre-commit-link]

*An easy way to use inotify*

This module implements only one `InotifyWatcher` class with a very simple usage.

## Features
- inotify event manager and cookie tracking
- callback oriented design
- non blocking design (using threading.Thread)
- recursive directory watching

[package-badge]: https://img.shields.io/pypi/v/inotify-watcher
[package-link]: https://pypi.org/project/inotify-watcher
[documentation-badge]: https://img.shields.io/readthedocs/inotify-watcher
[documentation-link]: https://inotify-watcher.readthedocs.io/en/latest
[license-badge]: https://img.shields.io/github/license/jmlemetayer/inotify_watcher
[license-link]: https://github.com/jmlemetayer/inotify_watcher/blob/main/LICENSE.md
[build-badge]: https://img.shields.io/github/workflow/status/jmlemetayer/inotify_watcher/inotify_watcher/main
[build-link]: https://github.com/jmlemetayer/inotify_watcher/actions
[pre-commit-badge]: https://results.pre-commit.ci/badge/github/jmlemetayer/inotify_watcher/main.svg
[pre-commit-link]: https://results.pre-commit.ci/latest/github/jmlemetayer/inotify_watcher/main
