"""Test cases for the :obj:`inotify_watcher` module."""
# pylint: disable=duplicate-code
from __future__ import annotations

import logging

# noreorder
from inotify_watcher import InotifyWatcher

from . import InotifyTracker
from .conftest import TestPathsType

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
        with InotifyWatcher(
            parent_file, **tracker.handlers_kwargs(watched=True)
        ) as watcher:
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_watched[0] == parent_file

    def test_parent_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(
            parent_dir, **tracker.handlers_kwargs(watched=True)
        ) as watcher:
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_watched[0] == parent_dir

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(
            root_dir, **tracker.handlers_kwargs(watched=True)
        ) as watcher:
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 2
            assert tracker.dir_watched[0] == root_dir
            assert tracker.file_watched[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(
            root_dir, **tracker.handlers_kwargs(watched=True)
        ) as watcher:
            watcher.wait(timeout=0.1)
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
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            child_file.touch()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_created[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when creating a child directory."""
        root_dir = test_paths["root_dir"]
        child_dir = root_dir / "child_dir"
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            child_dir.mkdir()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_created[0] == child_dir

    def test_tree(self, test_paths: TestPathsType, tracker: InotifyTracker) -> None:
        """Check inotify events when creating a tree."""
        root_dir = test_paths["root_dir"]
        tree_file = root_dir / "dir1" / "dir2" / "dir3" / "tree_file"
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            tree_file.parent.mkdir(parents=True)
            tree_file.touch()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 4
            assert tracker.dir_created[0] == tree_file.parent.parent.parent
            assert tracker.dir_created[1] == tree_file.parent.parent
            assert tracker.dir_created[2] == tree_file.parent
            assert tracker.file_created[0] == tree_file


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
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs()) as watcher:
            parent_file.chmod(0o640)
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_updated[0] == parent_file

    def test_parent_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs()) as watcher:
            parent_dir.chmod(0o750)
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_updated[0] == parent_dir

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            child_file.chmod(0o640)
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_updated[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when updating a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            child_dir.chmod(0o750)
            watcher.wait(timeout=0.1)
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
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs()) as watcher:
            with parent_file.open("a") as file:
                file.write("Hello world")
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_modified[0] == parent_file

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when modifying a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            with child_file.open("a") as file:
                file.write("Hello world")
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.file_modified[0] == child_file


class TestDeleted:
    """Test cases related to the deleted event."""

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
        """Check inotify events when deleting a parent file."""
        parent_file = test_paths["parent_file"]
        with InotifyWatcher(parent_file, **tracker.handlers_kwargs()) as watcher:
            parent_file.unlink()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 2
            assert tracker.file_updated[0] == parent_file
            assert tracker.file_deleted[0] == parent_file

    def test_parent_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when deleting a parent directory."""
        parent_dir = test_paths["parent_dir"]
        with InotifyWatcher(parent_dir, **tracker.handlers_kwargs()) as watcher:
            parent_dir.rmdir()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_deleted[0] == parent_dir

    def test_child_file(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when deleting a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            child_file.unlink()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 2
            assert tracker.file_updated[0] == child_file
            assert tracker.file_deleted[0] == child_file

    def test_child_dir(
        self, test_paths: TestPathsType, tracker: InotifyTracker
    ) -> None:
        """Check inotify events when deleting a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        with InotifyWatcher(root_dir, **tracker.handlers_kwargs()) as watcher:
            child_dir.rmdir()
            watcher.wait(timeout=0.1)
            assert tracker.event_count == 1
            assert tracker.dir_deleted[0] == child_dir
