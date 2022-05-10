"""Test plan for the `inotify_watcher` module."""
from __future__ import annotations

import logging
import pathlib
from typing import Any

import inotify_simple

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
