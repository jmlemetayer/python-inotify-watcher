"""Test cases for the `inotify_watcher` module."""
from __future__ import annotations

import logging
import pathlib

from . import InotifyTracker
from inotify_watcher import InotifyWatcher

logger = logging.getLogger(__name__)


class TestWatched:
    """Test cases related to the watched event."""

    test_paths_config = {
        "parent_file": {"path": "parent_file"},
        "parent_dir": {"path": "parent_dir", "is_dir": True},
        "child_file.parent": {"path": "child_file.parent", "is_dir": True},
        "child_file": {"path": "child_file.parent/child_file"},
        "child_dir.parent": {"path": "child_dir.parent", "is_dir": True},
        "child_dir": {"path": "child_dir.parent/child_dir", "is_dir": True},
    }

    def test_parent_file(
        self, test_paths: dict[str, pathlib.Path], inotify_tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent file."""
        parent_file = test_paths["parent_file"]
        with InotifyWatcher(
            parent_file, **inotify_tracker.handlers_kwargs(watched=True)
        ):
            assert inotify_tracker.event_count == 1
            assert inotify_tracker.file_watched[0] == parent_file

    def test_parent_dir(
        self, test_paths: dict[str, pathlib.Path], inotify_tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(
            parent_dir, **inotify_tracker.handlers_kwargs(watched=True)
        ):
            assert inotify_tracker.event_count == 1
            assert inotify_tracker.dir_watched[0] == parent_dir

    def test_child_file(
        self, test_paths: dict[str, pathlib.Path], inotify_tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child file."""
        parent_dir = test_paths["child_file.parent"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(
            parent_dir, **inotify_tracker.handlers_kwargs(watched=True)
        ):
            assert inotify_tracker.event_count == 2
            assert inotify_tracker.dir_watched[0] == parent_dir
            assert inotify_tracker.file_watched[0] == child_file

    def test_child_dir(
        self, test_paths: dict[str, pathlib.Path], inotify_tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child directory."""
        parent_dir = test_paths["child_dir.parent"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(
            parent_dir, **inotify_tracker.handlers_kwargs(watched=True)
        ):
            assert inotify_tracker.event_count == 2
            assert inotify_tracker.dir_watched[0] == parent_dir
            assert inotify_tracker.dir_watched[1] == child_dir
