"""Low level inotify event tests used to design the :obj:`inotify_watcher` module."""
# pylint: disable=duplicate-code
from __future__ import annotations

import logging

from . import InotifyTest
from .conftest import TestPathsType

logger = logging.getLogger(__name__)


class TestCreated:
    """Test cases related to the created event."""

    test_paths_config = {
        "root_dir": {"path": "root_dir", "is_dir": True},
    }

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when creating a child file."""
        root_dir = test_paths["root_dir"]
        child_file = root_dir / "child_file"
        child_file.touch()
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(path=root_dir, name=child_file.name, flags=["CREATE"])
        assert events[1].match(path=root_dir, name=child_file.name, flags=["OPEN"])
        assert events[2].match(
            path=root_dir, name=child_file.name, flags=["CLOSE_WRITE"]
        )

    def test_child_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when creating a child directory."""
        root_dir = test_paths["root_dir"]
        child_dir = root_dir / "child_dir"
        child_dir.mkdir()
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(
            path=root_dir, name=child_dir.name, flags=["CREATE", "ISDIR"]
        )


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
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        child_file.chmod(0o640)
        events = inotify_test.read_events()
        assert len(events) == 2
        assert events[0].match(path=root_dir, name=child_file.name, flags=["ATTRIB"])
        assert events[1].match(path=child_file, name=None, flags=["ATTRIB"])

    def test_child_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when updating a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        child_dir.chmod(0o750)
        events = inotify_test.read_events()
        assert len(events) == 2
        assert events[0].match(
            path=root_dir, name=child_dir.name, flags=["ATTRIB", "ISDIR"]
        )
        assert events[1].match(path=child_dir, name=None, flags=["ATTRIB", "ISDIR"])


class TestModified:
    """Test cases related to the modified event."""

    test_paths_config = {
        "parent_file": {"path": "parent_file"},
        "child_file.root": {"path": "child_file", "is_dir": True},
        "child_file": {"path": "child_file/child_file"},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when modifying a parent file."""
        parent_file = test_paths["parent_file"]
        with parent_file.open("a") as file:
            file.write("Hello world")
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(path=parent_file, name=None, flags=["OPEN"])
        assert events[1].match(path=parent_file, name=None, flags=["MODIFY"])
        assert events[2].match(path=parent_file, name=None, flags=["CLOSE_WRITE"])

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when modifying a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        with child_file.open("a") as file:
            file.write("Hello world")
        events = inotify_test.read_events()
        assert len(events) == 6
        assert events[0].match(path=root_dir, name=child_file.name, flags=["OPEN"])
        assert events[1].match(path=child_file, name=None, flags=["OPEN"])
        assert events[2].match(path=root_dir, name=child_file.name, flags=["MODIFY"])
        assert events[3].match(path=child_file, name=None, flags=["MODIFY"])
        assert events[4].match(
            path=root_dir, name=child_file.name, flags=["CLOSE_WRITE"]
        )
        assert events[5].match(path=child_file, name=None, flags=["CLOSE_WRITE"])


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
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when deleting a parent file."""
        parent_file = test_paths["parent_file"]
        parent_file.unlink()
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(path=parent_file, name=None, flags=["ATTRIB"])
        assert events[1].match(path=parent_file, name=None, flags=["DELETE_SELF"])
        assert events[2].match(path=parent_file, name=None, flags=["IGNORED"])

    def test_parent_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when deleting a parent directory."""
        parent_dir = test_paths["parent_dir"]
        parent_dir.rmdir()
        events = inotify_test.read_events()
        assert len(events) == 2
        assert events[0].match(path=parent_dir, name=None, flags=["DELETE_SELF"])
        assert events[1].match(path=parent_dir, name=None, flags=["IGNORED"])

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when deleting a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        child_file.unlink()
        events = inotify_test.read_events()
        assert len(events) == 4
        assert events[0].match(path=child_file, name=None, flags=["ATTRIB"])
        assert events[1].match(path=child_file, name=None, flags=["DELETE_SELF"])
        assert events[2].match(path=child_file, name=None, flags=["IGNORED"])
        assert events[3].match(path=root_dir, name=child_file.name, flags=["DELETE"])

    def test_child_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when deleting a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        child_dir.rmdir()
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(path=child_dir, name=None, flags=["DELETE_SELF"])
        assert events[1].match(path=child_dir, name=None, flags=["IGNORED"])
        assert events[2].match(
            path=root_dir, name=child_dir.name, flags=["DELETE", "ISDIR"]
        )


class TestMoved:
    """Test cases related to the moved event."""

    test_paths_config = {
        "parent_file": {"path": "parent_file"},
        "parent_dir": {"path": "parent_dir", "is_dir": True},
        "child_file.root": {"path": "child_file", "is_dir": True},
        "child_file": {"path": "child_file/child_file"},
        "child_dir.root": {"path": "child_dir", "is_dir": True},
        "child_dir": {"path": "child_dir/child_dir", "is_dir": True},
    }

    def test_parent_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when moving a parent file."""
        parent_file = test_paths["parent_file"]
        new_file = parent_file.with_name("new_file")
        parent_file.replace(new_file)
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(path=parent_file, name=None, flags=["MOVE_SELF"])

    def test_parent_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when moving a parent directory."""
        parent_dir = test_paths["parent_dir"]
        new_dir = parent_dir.with_name("new_dir")
        parent_dir.replace(new_dir)
        events = inotify_test.read_events()
        assert len(events) == 1
        assert events[0].match(path=parent_dir, name=None, flags=["MOVE_SELF"])

    def test_child_file(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when moving a child file."""
        root_dir = test_paths["child_file.root"]
        child_file = test_paths["child_file"]
        new_file = child_file.with_name("new_file")
        child_file.replace(new_file)
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(
            path=root_dir, name=child_file.name, flags=["MOVED_FROM"]
        )
        assert events[1].match(path=root_dir, name=new_file.name, flags=["MOVED_TO"])
        assert events[0].cookie == events[1].cookie != 0
        assert events[2].match(path=child_file, name=None, flags=["MOVE_SELF"])

    def test_child_dir(
        self, test_paths: TestPathsType, inotify_test: InotifyTest
    ) -> None:
        """Check inotify events when moving a child directory."""
        root_dir = test_paths["child_dir.root"]
        child_dir = test_paths["child_dir"]
        new_dir = child_dir.with_name("new_dir")
        child_dir.replace(new_dir)
        events = inotify_test.read_events()
        assert len(events) == 3
        assert events[0].match(
            path=root_dir, name=child_dir.name, flags=["MOVED_FROM", "ISDIR"]
        )
        assert events[1].match(
            path=root_dir, name=new_dir.name, flags=["MOVED_TO", "ISDIR"]
        )
        assert events[0].cookie == events[1].cookie != 0
        assert events[2].match(path=child_dir, name=None, flags=["MOVE_SELF"])
