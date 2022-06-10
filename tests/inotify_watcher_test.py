"""Test cases for the `inotify_watcher` module."""
from __future__ import annotations

import logging

from . import InotifyTracker
from .conftest import TestPathsType
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
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent file."""
        parent_file = test_paths["parent_file"]
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs(watched=True)):
            assert tracker.event_count == 1
            assert tracker.file_watched[0] == parent_file

    def test_parent_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs(watched=True)):
            assert tracker.event_count == 1
            assert tracker.dir_watched[0] == parent_dir

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child file."""
        parent_dir = test_paths["child_file.parent"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs(watched=True)):
            assert tracker.event_count == 2
            assert tracker.dir_watched[0] == parent_dir
            assert tracker.file_watched[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child directory."""
        parent_dir = test_paths["child_dir.parent"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs(watched=True)):
            assert tracker.event_count == 2
            assert tracker.dir_watched[0] == parent_dir
            assert tracker.dir_watched[1] == child_dir


class TestCreated:
    """Test cases related to the created event."""

    test_paths_config = {
        "parent_dir": {"path": "dir", "is_dir": True},
    }

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when creating a child file."""
        parent_dir = test_paths["parent_dir"]
        child_file = parent_dir / "child_file"
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs()):
            child_file.touch()
            assert tracker.event_count == 1
            assert tracker.file_created[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when creating a child directory."""
        parent_dir = test_paths["parent_dir"]
        child_dir = parent_dir / "child_dir"
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs()):
            child_dir.mkdir()
            assert tracker.event_count == 1
            assert tracker.dir_created[0] == child_dir
