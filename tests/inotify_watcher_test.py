"""Test cases for the `inotify_watcher` module."""
from __future__ import annotations

import logging
import pathlib

from . import InotifyTest

logger = logging.getLogger(__name__)


class TestUpdated:
    """Test cases related to the updated event."""

    test_paths_config = {
        "parent_file": {"path": "file", "mode": 0o644},
        "parent_dir": {"path": "dir", "is_dir": True, "mode": 0o755},
        "child_file": {"path": "dir/file", "mode": 0o644},
        "child_dir": {"path": "dir/dir", "is_dir": True, "mode": 0o755},
    }

    def test_inotify_parent_file(
        self, test_paths: dict[str, pathlib.Path], inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a parent file."""
        parent_file = test_paths["parent_file"]
        parent_file.chmod(0o640)
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(path=parent_file, name=None, flags=["ATTRIB"])

    def test_inotify_parent_dir(
        self, test_paths: dict[str, pathlib.Path], inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a parent directory."""
        parent_dir = test_paths["parent_dir"]
        parent_dir.chmod(0o750)
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(path=parent_dir, name=None, flags=["ATTRIB", "ISDIR"])

    def test_inotify_child_file(
        self, test_paths: dict[str, pathlib.Path], inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a child file."""
        parent_dir = test_paths["parent_dir"]
        child_file = test_paths["child_file"]
        child_file.chmod(0o640)
        events = inotify_test.read_events()
        assert len(events) == 2
        assert events[0].match(path=parent_dir, name=child_file.name, flags=["ATTRIB"])
        assert events[1].match(path=child_file, name=None, flags=["ATTRIB"])

    def test_inotify_child_dir(
        self, test_paths: dict[str, pathlib.Path], inotify_test: InotifyTest
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
