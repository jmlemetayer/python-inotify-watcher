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
        "child_file.root": {"path": "child_file", "is_dir": True},
        "child_file": {"path": "child_file/child_file"},
        "child_dir.root": {"path": "child_dir", "is_dir": True},
        "child_dir": {"path": "child_dir/child_dir", "is_dir": True},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent file."""
        parent_file = test_paths["parent_file"]
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs(watched=True)) as w:
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_watched[0] == parent_file

    def test_parent_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs(watched=True)) as w:
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_watched[0] == parent_dir

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs(watched=True)) as w:
            w.wait(timeout=0.1)
            assert tracker.event_count == 2
            assert tracker.dir_watched[0] == root_dir
            assert tracker.file_watched[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs(watched=True)) as w:
            w.wait(timeout=0.1)
            assert tracker.event_count == 2
            assert tracker.dir_watched[0] == root_dir
            assert tracker.dir_watched[1] == child_dir


class TestCreated:
    """Test cases related to the created event."""

    test_paths_config = {
        "root_dir": {"path": "root_dir", "is_dir": True},
    }

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when creating a child file."""
        root_dir = test_paths["root_dir"]
        child_file = root_dir / "child_file"
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as w:
            child_file.touch()
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_created[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when creating a child directory."""
        root_dir = test_paths["root_dir"]
        child_dir = root_dir / "child_dir"
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as w:
            child_dir.mkdir()
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_created[0] == child_dir


class TestUpdated:
    """Test cases related to the updated event."""

    test_paths_config = {
        "parent_file": {"path": "parent_file", "mode": 0o644},
        "parent_dir": {"path": "parent_dir", "is_dir": True, "mode": 0o755},
        "child_file.root": {"path": "child_file", "is_dir": True},
        "child_file": {"path": "child_file/child_file", "mode": 0o644},
        "child_dir.root": {"path": "child_dir", "is_dir": True},
        "child_dir": {"path": "child_dir/child_dir", "is_dir": True, "mode": 0o755},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent file."""
        parent_file = test_paths["parent_file"]
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs()) as w:
            parent_file.chmod(0o640)
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_updated[0] == parent_file

    def test_parent_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs()) as w:
            parent_dir.chmod(0o750)
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_updated[0] == parent_dir

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as w:
            child_file.chmod(0o640)
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_updated[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as w:
            child_dir.chmod(0o750)
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_updated[0] == child_dir


class TestModified:
    """Test cases related to the modified event."""

    test_paths_config = {
        "parent_file": {"path": "parent_file"},
        "child_file.root": {"path": "child_file", "is_dir": True},
        "child_file": {"path": "child_file/child_file"},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when modifying a parent file."""
        parent_file = test_paths["parent_file"]
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs()) as w:
            with parent_file.open("a") as f:
                f.write("Hello world")
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_modified[0] == parent_file

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when modifying a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as w:
            with child_file.open("a") as f:
                f.write("Hello world")
            w.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_modified[0] == child_file
