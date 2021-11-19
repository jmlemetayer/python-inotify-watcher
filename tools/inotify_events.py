#!/usr/bin/env pytest
"""Inotify event reference.

This tool is used to show all the inotify events occurring for
multiple use cases: file creation, file modification ...
and in multiple inotify contexts: parent directory, child file ...
"""
from __future__ import annotations

import logging
import os
import stat
import tempfile
from typing import List
from typing import Tuple

from inotify_simple import Event
from inotify_simple import flags
from inotify_simple import INotify
from inotify_simple import masks

logger = logging.getLogger(__name__)


class InotifyEventWrapper:
    """A class to wrap the inotify_simple.Event.

    This wrapper is used to pretty print the inotify_simple.Event.
    """

    def __init__(self, event: Event) -> None:
        """Construct the InotifyEventWrapper object.

        Parameters
        ----------
        event: Event
            The original inotify_simple.Event.
        """
        self.__event = event

    def __str__(self) -> str:
        """Pretty print the inotify_simple.Event."""
        event_flags = " ".join([str(f) for f in flags.from_mask(self.__event.mask)])
        return f"{self.__event} {event_flags}"


class InotifySimpleWatcher:
    """A class to handle the inotify context.

    This class is designed to be used as a context manager using the `with`
    keyword.

    Examples
    --------
    >>> with InotifySimpleWatcher(path) as watcher:
    >>>     for event in watcher.read_events():
    >>>         print(event)
    """

    def __init__(self, path: str) -> None:
        """Construct the InotifySimpleWatcher object.

        Parameters
        ----------
        path: str
            The path to watch.
        """
        self.__inotify = INotify()
        self.__wd = self.__inotify.add_watch(path, masks.ALL_EVENTS)

    def __del__(self) -> None:
        """Destroy the object."""
        self.close()

    def __enter__(self) -> InotifySimpleWatcher:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object."""
        self.close()

    def close(self) -> None:
        """Properly close the inotify object..

        This method can be called multiple times.
        """
        if not self.__inotify.closed:
            if self.__wd is not None:
                try:
                    self.__inotify.rm_watch(self.__wd)
                except OSError:
                    pass
                self.__wd = None
            self.__inotify.close()

    def read_events(self) -> List[InotifyEventWrapper]:
        """Read the inotify events and wrap them."""
        return [
            InotifyEventWrapper(e)
            for e in self.__inotify.read(timeout=100, read_delay=100)
        ]


class TemporaryFileDirectory:
    """A class to create default temporary files and directories.

    This is for test purpose.
    """

    def __init__(self) -> None:
        """Construct the TemporaryFileDirectory object.

        A root temporary directory is created with a sub-file and a
        sub-directory. The root directory is deleted automatically.
        """
        self.__temp_dir = tempfile.TemporaryDirectory()

        self.temp_file = os.path.join(self.__temp_dir.name, "file")
        open(self.temp_file, "x").close()
        os.chmod(
            self.temp_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
        )

        self.temp_dir = os.path.join(self.__temp_dir.name, "dir")
        os.mkdir(self.temp_dir)
        os.chmod(
            self.temp_dir,
            stat.S_IRUSR
            | stat.S_IWUSR
            | stat.S_IRGRP
            | stat.S_IROTH
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH,
        )

    def __del__(self) -> None:
        """Destroy the object."""
        self.cleanup()

    def __enter__(self) -> Tuple[str, str, str]:
        """Enter the runtime context related to this object.

        Returns
        -------
        str
            The temporary root directory.
        str
            The temporary file.
        str
            The temporary directory.
        """
        return (self.__temp_dir.name, self.temp_file, self.temp_dir)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object."""
        self.cleanup()

    def cleanup(self) -> None:
        """Delete the root directory."""
        self.__temp_dir.cleanup()


class TestParentFile:
    """A class to test all parent file related use cases."""

    def test_self_updated(self):
        """Check for inotify events that occur when self is updated."""
        with TemporaryFileDirectory() as (_, watched_file, _):
            with InotifySimpleWatcher(watched_file) as watcher:
                os.chmod(watched_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_modified(self):
        """Check for inotify events that occur when self is modified."""
        with TemporaryFileDirectory() as (_, watched_file, _):
            with InotifySimpleWatcher(watched_file) as watcher:
                with open(watched_file, "a") as f:
                    f.write("This file is watched")
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_deleted(self):
        """Check for inotify events that occur when self is deleted."""
        with TemporaryFileDirectory() as (_, watched_file, _):
            with InotifySimpleWatcher(watched_file) as watcher:
                os.remove(watched_file)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_moved(self):
        """Check for inotify events that occur when self is moved."""
        with TemporaryFileDirectory() as (root_dir, watched_file, _):
            with InotifySimpleWatcher(watched_file) as watcher:
                os.rename(watched_file, os.path.join(root_dir, "new_file"))
                for event in watcher.read_events():
                    logger.info(event)


class TestParentDirectory:
    """A class to test all parent directory related use cases."""

    def test_self_updated(self):
        """Check for inotify events that occur when self is updated."""
        with TemporaryFileDirectory() as (_, _, watched_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.chmod(watched_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_deleted(self):
        """Check for inotify events that occur when self is deleted."""
        with TemporaryFileDirectory() as (_, _, watched_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rmdir(watched_dir)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_moved(self):
        """Check for inotify events that occur when self is moved."""
        with TemporaryFileDirectory() as (root_dir, _, watched_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(watched_dir, os.path.join(root_dir, "new_dir"))
                for event in watcher.read_events():
                    logger.info(event)


class TestChildFile:
    """A class to test all child file related use cases."""

    def test_file_created(self):
        """Check for inotify events that occur when a file is created."""
        with TemporaryFileDirectory() as (watched_dir, _, _):
            with InotifySimpleWatcher(watched_dir) as watcher:
                open(os.path.join(watched_dir, "new_file"), "x").close()
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_updated(self):
        """Check for inotify events that occur when a file is updated."""
        with TemporaryFileDirectory() as (watched_dir, child_file, _):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.chmod(child_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_modified(self):
        """Check for inotify events that occur when a file is modified."""
        with TemporaryFileDirectory() as (watched_dir, child_file, _):
            with InotifySimpleWatcher(watched_dir) as watcher:
                with open(child_file, "a") as f:
                    f.write("This file is watched")
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_moved(self):
        """Check for inotify events that occur when a file is moved."""
        with TemporaryFileDirectory() as (watched_dir, child_file, _):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(child_file, os.path.join(watched_dir, "new_file"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_deleted(self):
        """Check for inotify events that occur when a file is deleted."""
        with TemporaryFileDirectory() as (watched_dir, child_file, _):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.remove(child_file)
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_moved_outside(self):
        """Check for inotify events that occur when a file is moved outside."""
        with TemporaryFileDirectory() as (watched_dir, child_file, child_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(child_file, os.path.join(child_dir, "new_file"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_moved_inside(self):
        """Check for inotify events that occur when a file is moved inside."""
        with TemporaryFileDirectory() as (_, child_file, watched_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(child_file, os.path.join(watched_dir, "new_file"))
                for event in watcher.read_events():
                    logger.info(event)


class TestChildDirectory:
    """A class to test all child directory related use cases."""

    def test_directory_created(self):
        """Check for inotify events that occur when a directory is created."""
        with TemporaryFileDirectory() as (watched_dir, _, _):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.mkdir(os.path.join(watched_dir, "new_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_updated(self):
        """Check for inotify events that occur when a directory is updated."""
        with TemporaryFileDirectory() as (watched_dir, _, child_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.chmod(child_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_moved(self):
        """Check for inotify events that occur when a directory is moved."""
        with TemporaryFileDirectory() as (watched_dir, _, child_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(child_dir, os.path.join(watched_dir, "new_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_deleted(self):
        """Check for inotify events that occur when a directory is deleted."""
        with TemporaryFileDirectory() as (watched_dir, _, child_dir):
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rmdir(child_dir)
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_moved_outside(self):
        """Check for inotify events that occur when a directory is moved outside."""
        with TemporaryFileDirectory() as (watched_dir, _, child_dir):
            alt_dir = os.path.join(watched_dir, "alt_dir")
            os.mkdir(alt_dir)
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(child_dir, os.path.join(alt_dir, "new_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_moved_inside(self):
        """Check for inotify events that occur when a directory is moved inside."""
        with TemporaryFileDirectory() as (root_dir, _, watched_dir):
            alt_dir = os.path.join(root_dir, "alt_dir")
            os.mkdir(alt_dir)
            with InotifySimpleWatcher(watched_dir) as watcher:
                os.rename(alt_dir, os.path.join(watched_dir, "new_dir"))
                for event in watcher.read_events():
                    logger.info(event)
