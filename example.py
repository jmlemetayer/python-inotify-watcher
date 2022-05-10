"""Example script to show the basic `InotifyWatcher` usage.

This script prints every inotify events received from a temporary
directory. Once started, use a new terminal to do manually create,
modify, move or delete files or directories.
"""
from __future__ import annotations

import logging
import sys
import tempfile

from inotify_watcher import InotifyWatcher

logging.basicConfig(level=logging.DEBUG)


def main() -> int:
    """Show the basic usage of the `InotifyWatcher` class.

    This function creates a temporary directory and then print every
    inotify events received.
    """
    with tempfile.TemporaryDirectory() as watched_dir:
        try:
            watcher = InotifyWatcher(
                watched_dir,
                file_watched=lambda p: print(f"file {p} watched"),
                file_created=lambda p: print(f"file {p} created"),
                file_updated=lambda p: print(f"file {p} updated"),
                file_modified=lambda p: print(f"file {p} modified"),
                file_moved=lambda p, n: print(f"file {p} moved to {n}"),
                file_deleted=lambda p: print(f"file {p} deleted"),
                file_gone=lambda p: print(f"file {p} gone"),
                dir_watched=lambda p: print(f"directory {p} watched"),
                dir_created=lambda p: print(f"directory {p} created"),
                dir_updated=lambda p: print(f"directory {p} updated"),
                dir_moved=lambda p, n: print(f"directory {p} moved to {n}"),
                dir_deleted=lambda p: print(f"directory {p} deleted"),
                dir_gone=lambda p: print(f"directory {p} gone"),
            )

            print(f"watched directory: {watched_dir}")

            watcher.wait()

        except KeyboardInterrupt:
            watcher.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
