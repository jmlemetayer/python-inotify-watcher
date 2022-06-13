"""Low level inotify event tests used to design the `inotify_watcher` module."""
from __future__ import annotations

import logging

from . import InotifyTest
from .conftest import TestPathsType

logger = logging.getLogger(__name__)


class TestCreated:
    """Test cases related to the created event."""

    test_paths_config = {
        "parent_dir": {"path": "dir", "is_dir": True},
    }

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when creating a child file."""
        parent_dir = test_paths["parent_dir"]
        child_file = parent_dir / "child_file"
        child_file.touch()
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(path=parent_dir, name=child_file.name, flags=["CREATE"])
        assert events[1].match(path=parent_dir, name=child_file.name, flags=["OPEN"])
        assert events[2].match(
            path=parent_dir, name=child_file.name, flags=["CLOSE_WRITE"]
        )

    def test_child_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when creating a child directory."""
        parent_dir = test_paths["parent_dir"]
        child_dir = parent_dir / "child_dir"
        child_dir.mkdir()
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(
            path=parent_dir, name=child_dir.name, flags=["CREATE", "ISDIR"]
        )


class TestUpdated:
    """Test cases related to the updated event."""

    test_paths_config = {
        "parent_file": {"path": "file", "mode": 0o644},
        "parent_dir": {"path": "dir", "is_dir": True, "mode": 0o755},
        "child_file": {"path": "dir/file", "mode": 0o644},
        "child_dir": {"path": "dir/dir", "is_dir": True, "mode": 0o755},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a parent file."""
        parent_file = test_paths["parent_file"]
        parent_file.chmod(0o640)
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(path=parent_file, name=None, flags=["ATTRIB"])

    def test_parent_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        parent_dir.chmod(0o750)
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(path=parent_dir, name=None, flags=["ATTRIB", "ISDIR"])

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a child file."""
        parent_dir = test_paths["parent_dir"]
        child_file = test_paths["child_file"]
        child_file.chmod(0o640)
        events = inotify_test.read_events()
        assert len(events) == 2
        assert events[0].match(path=parent_dir, name=child_file.name, flags=["ATTRIB"])
        assert events[1].match(path=child_file, name=None, flags=["ATTRIB"])

    def test_child_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a child directory."""
        parent_dir = test_paths["parent_dir"]
        child_dir = test_paths["child_dir"]
        child_dir.chmod(0o750)
        events = inotify_test.read_events()
        assert len(events) == 2
        assert events[0].match(
            path=parent_dir, name=child_dir.name, flags=["ATTRIB", "ISDIR"]
        )
        assert events[1].match(path=child_dir, name=None, flags=["ATTRIB", "ISDIR"])


class TestModified:
    """Test cases related to the modified event."""

    test_paths_config = {
        "parent_file": {"path": "file"},
        "parent_dir": {"path": "dir", "is_dir": True},
        "child_file": {"path": "dir/file"},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when modifying a parent file."""
        parent_file = test_paths["parent_file"]
        with parent_file.open("a") as f:
            f.write("Hello world")
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(path=parent_file, name=None, flags=["OPEN"])
        assert events[1].match(path=parent_file, name=None, flags=["MODIFY"])
        assert events[2].match(path=parent_file, name=None, flags=["CLOSE_WRITE"])

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when modifying a child file."""
        parent_dir = test_paths["parent_dir"]
        child_file = test_paths["child_file"]
        with child_file.open("a") as f:
            f.write("Hello world")
        events = inotify_test.read_events()
        assert len(events) == 6
        assert events[0].match(path=parent_dir, name=child_file.name, flags=["OPEN"])
        assert events[1].match(path=child_file, name=None, flags=["OPEN"])
        assert events[2].match(path=parent_dir, name=child_file.name, flags=["MODIFY"])
        assert events[3].match(path=child_file, name=None, flags=["MODIFY"])
        assert events[4].match(
            path=parent_dir, name=child_file.name, flags=["CLOSE_WRITE"]
        )
        assert events[5].match(path=child_file, name=None, flags=["CLOSE_WRITE"])
