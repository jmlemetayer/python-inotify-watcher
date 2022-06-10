"""Test package for the `inotify_watcher` package.

Please check the `Good Integration Practices`_.

.. _Good Integration Practices:
   https://docs.pytest.org/en/latest/explanation/goodpractices.html
"""
from __future__ import annotations

import logging
import pathlib
from typing import Any

import inotify_simple

from inotify_watcher import HandlerType
from inotify_watcher import PathType

logger = logging.getLogger(__name__)


class InotifyEventTest:
    """A wrapper of the `inotify_simple.Event`.

    This wrapper is used to add some extra features to the
    `inotify_simple.Event`.

    See Also
    --------
    inotify_simple.Event
    """

    def __init__(
        self, event: inotify_simple.Event, wd_paths: dict[int | str, pathlib.Path]
    ) -> None:
        """Create the `inotify_simple.Event` wrapper object.

        Parameters
        ----------
        event: inotify_simple.Event
            The original inotify event object.
        wd_paths: dict[int, pathlib.Path]
            The watch descriptor vs path lookup table.

            The key represent the watch descriptor (`int`) and the value the
            path (`pathlib.Path`).

            If available the watch descriptor ``"root"`` represents the root
            path to allow the pretty print to use a relative path.
        """
        self.__event = event
        self.__wd_paths = wd_paths

        self.wd = self.__event.wd
        self.mask = self.__event.mask
        self.cookie = self.__event.cookie
        self.name = self.__event.name or None
        self.path = self.__wd_paths[self.wd]
        self.flags = [f.name for f in inotify_simple.flags.from_mask(self.mask)]

    def __str__(self) -> str:
        """Pretty print the object.

        Returns
        -------
        object_string: str
            The object representation string.
        """
        root = self.__wd_paths.get("root")
        path = self.path.relative_to(root) if root else self.path

        return (
            "InotifyEventTest("
            f"wd={self.wd} "
            f"path={path} "
            f"name={self.name} "
            f"mask={self.mask} "
            f"flags={self.flags} "
            f"cookie={self.cookie}"
            ")"
        )

    def __repr__(self) -> str:
        """Return the object representation string."""
        return str(self)

    def match(self, **kwargs: Any) -> bool:
        """Test the object for matching criteria.

        Parameters
        ----------
        kwargs
            Key-value pairs to be compared to the object's attributes.

        Returns
        -------
        matching_status: bool
            Indicates if the object meets the criteria.

        Raises
        ------
        ValueError
            If a criterion key is not part of the object's attributes.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                if getattr(self, key) != value:
                    return False
            else:
                raise ValueError(f"Invalid criterion key: {key}")

        return True


class InotifyTest:
    """A wrapper of the `inotify_simple.INotify`.

    This wrapper is used to simplify some usage of the `inotify_simple.INotify`.

    See Also
    --------
    inotify_simple.INotify
    """

    def __init__(self, root: pathlib.Path | None = None) -> None:
        """Create the `inotify_simple.INotify` wrapper object.

        Parameters
        ----------
        root: pathlib.Path, optional
            If this argument is provided the pretty print of the generated
            events will use relative path to this root path.
        """
        self.__inotify = inotify_simple.INotify()
        self.__wd_paths: dict[int | str, pathlib.Path] = dict()

        if root is not None:
            self.__wd_paths["root"] = root

    def add_watch(self, path: pathlib.Path) -> None:
        """Add a path to the watch list.

        Parameters
        ----------
        path: pathlib.Path
            The path to add to the watch list.
        """
        wd = self.__inotify.add_watch(path, inotify_simple.masks.ALL_EVENTS)
        self.__wd_paths[wd] = path

    def read_events(self) -> list[InotifyEventTest]:
        """Read the `inotify_simple.Event` and wrap them.

        Returns
        -------
        events: list[InotifyEventTest]
            The list of events that have been read.
        """
        return [
            InotifyEventTest(e, self.__wd_paths)
            for e in self.__inotify.read(timeout=100, read_delay=100)
        ]


class InotifyTracker:
    """A class to track the inotify events during a test."""

    def __init__(self) -> None:
        self.file_watched: list[PathType] = list()
        self.file_created: list[PathType] = list()
        self.file_updated: list[PathType] = list()
        self.file_modified: list[PathType] = list()
        self.file_moved: list[tuple[PathType, PathType]] = list()
        self.file_deleted: list[PathType] = list()
        self.file_gone: list[PathType] = list()
        self.dir_watched: list[PathType] = list()
        self.dir_created: list[PathType] = list()
        self.dir_updated: list[PathType] = list()
        self.dir_moved: list[tuple[PathType, PathType]] = list()
        self.dir_deleted: list[PathType] = list()
        self.dir_gone: list[PathType] = list()

    def file_watched_handle(self, path: PathType) -> None:
        """Handle for the file_watched events."""
        self.file_watched.append(path)

    def file_created_handle(self, path: PathType) -> None:
        """Handle for the file_created events."""
        self.file_created.append(path)

    def file_updated_handle(self, path: PathType) -> None:
        """Handle for the file_updated events."""
        self.file_updated.append(path)

    def file_modified_handle(self, path: PathType) -> None:
        """Handle for the file_modified events."""
        self.file_modified.append(path)

    def file_moved_handle(self, path: PathType, new_path: PathType) -> None:
        """Handle for the file_moved events."""
        self.file_moved.append((path, new_path))

    def file_deleted_handle(self, path: PathType) -> None:
        """Handle for the file_deleted events."""
        self.file_deleted.append(path)

    def file_gone_handle(self, path: PathType) -> None:
        """Handle for the file_gone events."""
        self.file_gone.append(path)

    def dir_watched_handle(self, path: PathType) -> None:
        """Handle for the dir_watched events."""
        self.dir_watched.append(path)

    def dir_created_handle(self, path: PathType) -> None:
        """Handle for the dir_created events."""
        self.dir_created.append(path)

    def dir_updated_handle(self, path: PathType) -> None:
        """Handle for the dir_updated events."""
        self.dir_updated.append(path)

    def dir_moved_handle(self, path: PathType, new_path: PathType) -> None:
        """Handle for the dir_moved events."""
        self.dir_moved.append((path, new_path))

    def dir_deleted_handle(self, path: PathType) -> None:
        """Handle for the dir_deleted events."""
        self.dir_deleted.append(path)

    def dir_gone_handle(self, path: PathType) -> None:
        """Handle for the dir_gone events."""
        self.dir_gone.append(path)

    def handlers_kwargs(
        self,
        watched: bool | None = None,
        no_file: bool | None = None,
        no_dir: bool | None = None,
    ) -> dict[str, HandlerType]:
        """Return a dictionary with all the handlers pre-configured."""
        handlers: dict[str, HandlerType] = dict()
        if no_file is not True and watched is True:
            handlers["file_watched"] = self.file_watched_handle
        if no_file is not True:
            handlers["file_created"] = self.file_created_handle
        if no_file is not True:
            handlers["file_updated"] = self.file_updated_handle
        if no_file is not True:
            handlers["file_modified"] = self.file_modified_handle
        if no_file is not True:
            handlers["file_moved"] = self.file_moved_handle
        if no_file is not True:
            handlers["file_deleted"] = self.file_deleted_handle
        if no_file is not True:
            handlers["file_gone"] = self.file_gone_handle
        if no_dir is not True and watched is True:
            handlers["dir_watched"] = self.dir_watched_handle
        if no_dir is not True:
            handlers["dir_created"] = self.dir_created_handle
        if no_dir is not True:
            handlers["dir_updated"] = self.dir_updated_handle
        if no_dir is not True:
            handlers["dir_moved"] = self.dir_moved_handle
        if no_dir is not True:
            handlers["dir_deleted"] = self.dir_deleted_handle
        if no_dir is not True:
            handlers["dir_gone"] = self.dir_gone_handle
        return handlers

    @property
    def event_count(self) -> int:
        """Return the total number of event received."""
        return (
            len(self.file_watched)
            + len(self.file_created)
            + len(self.file_updated)
            + len(self.file_modified)
            + len(self.file_moved)
            + len(self.file_deleted)
            + len(self.file_gone)
            + len(self.dir_watched)
            + len(self.dir_created)
            + len(self.dir_updated)
            + len(self.dir_moved)
            + len(self.dir_deleted)
            + len(self.dir_gone)
        )
