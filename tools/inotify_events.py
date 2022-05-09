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
from typing import NamedTuple

from inotify_simple import Event as InotifyEvent
from inotify_simple import flags as InotifyFlags
from inotify_simple import INotify as Inotify
from inotify_simple import masks as InotifyMasks

logger = logging.getLogger(__name__)


class TemporaryPath(NamedTuple):
    """An abstract class to describe a temporary path."""

    path: str
    mode: int = 0


class TemporaryFile(TemporaryPath):
    """A class to describe a temporary file."""

    mode: int = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH


class TemporaryDirectory(TemporaryPath):
    """A class to describe a temporary directory."""

    mode: int = (
        stat.S_IRUSR
        | stat.S_IWUSR
        | stat.S_IXUSR
        | stat.S_IRGRP
        | stat.S_IXGRP
        | stat.S_IROTH
        | stat.S_IXOTH
    )


TEMPORARY_TEST_FILE = [
    TemporaryFile("test_file"),
]

TEMPORARY_ROOT_DIR_TEST_FILE = [
    TemporaryDirectory("root_dir"),
    TemporaryFile("root_dir/test_file"),
]

TEMPORARY_ROOT_DIR_SUB_DIR_TEST_FILE = [
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
    TemporaryFile("root_dir/sub_dir/test_file"),
]

TEMPORARY_ALT_DIR_TEST_FILE = [
    TemporaryDirectory("alt_dir"),
    TemporaryFile("test_file"),
]

TEMPORARY_ALT_DIR_ROOT_DIR_TEST_FILE = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("root_dir"),
    TemporaryFile("root_dir/test_file"),
]

TEMPORARY_ALT_DIR_ROOT_DIR_SUB_DIR_TEST_FILE = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
    TemporaryFile("root_dir/sub_dir/test_file"),
]

TEMPORARY_ALT_DIR_TEST_FILE_ROOT_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryFile("alt_dir/test_file"),
    TemporaryDirectory("root_dir"),
]

TEMPORARY_ALT_DIR_TEST_FILE_ROOT_DIR_SUB_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryFile("alt_dir/test_file"),
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
]

TEMPORARY_TEST_DIR = [
    TemporaryDirectory("test_dir"),
]

TEMPORARY_ROOT_DIR_TEST_DIR = [
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/test_dir"),
]

TEMPORARY_ROOT_DIR_SUB_DIR = [
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
]

TEMPORARY_ROOT_DIR_SUB_DIR_TEST_DIR = [
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
    TemporaryDirectory("root_dir/sub_dir/test_dir"),
]

TEMPORARY_ALT_DIR_TEST_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("test_dir"),
]

TEMPORARY_ALT_DIR_ROOT_DIR_TEST_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/test_dir"),
]

TEMPORARY_ALT_DIR_ROOT_DIR_SUB_DIR_TEST_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
    TemporaryDirectory("root_dir/sub_dir/test_dir"),
]

TEMPORARY_ALT_DIR_TEST_DIR_ROOT_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("alt_dir/test_dir"),
    TemporaryDirectory("root_dir"),
]

TEMPORARY_ALT_DIR_TEST_DIR_ROOT_DIR_SUB_DIR = [
    TemporaryDirectory("alt_dir"),
    TemporaryDirectory("alt_dir/test_dir"),
    TemporaryDirectory("root_dir"),
    TemporaryDirectory("root_dir/sub_dir"),
]


class TemporaryTree:
    """A class to create default temporary tree.

    This is for test purpose.
    """

    def __init__(self, paths: list[type[TemporaryPath]]) -> None:
        """Construct the TemporaryTree object.

        A temporary root directory is created and populated with the specified
        files and directories. The root directory is finally deleted automatically.

        Parameters
        ----------
        paths: List[TemporaryPath]
            The specified files and directories.
        """
        self.__temp_dir = tempfile.TemporaryDirectory()
        self.paths: list[str] = list()

        for path in paths:
            self.paths.append(self.__add_path(path))

    def __add_path(self, temporary_path: type[TemporaryPath]) -> str:
        if isinstance(temporary_path, TemporaryFile):
            return self.__add_file(temporary_path)
        elif isinstance(temporary_path, TemporaryDirectory):
            return self.__add_directory(temporary_path)
        else:
            raise Exception("Invalid temporary type")

    def __add_file(self, temporary_file: TemporaryFile) -> str:
        file = os.path.join(self.__temp_dir.name, temporary_file.path)
        open(file, "x").close()
        os.chmod(file, temporary_file.mode)
        return str(file)

    def __add_directory(self, temporary_directory: TemporaryDirectory) -> str:
        directory = os.path.join(self.__temp_dir.name, temporary_directory.path)
        os.mkdir(directory)
        os.chmod(directory, temporary_directory.mode)
        return str(directory)

    def __del__(self) -> None:
        """Destroy the object."""
        self.cleanup()

    def __enter__(self) -> tuple[str, ...]:
        """Enter the runtime context related to this object.

        Returns
        -------
        Tuple[str, ...]
            The temporary files and directories.
        """
        return tuple(self.paths)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object."""
        self.cleanup()

    def cleanup(self) -> None:
        """Delete the root directory."""
        self.__temp_dir.cleanup()


class InotifyEventWrapper:
    """A class to wrap the InotifyEvent.

    This wrapper is used to pretty print the InotifyEvent.
    """

    def __init__(self, event: InotifyEvent) -> None:
        """Construct the InotifyEventWrapper object.

        Parameters
        ----------
        event: InotifyEvent
            The original InotifyEvent.
        """
        self.__event = event

    def __str__(self) -> str:
        """Pretty print the InotifyEvent."""
        flags = " ".join([str(f) for f in InotifyFlags.from_mask(self.__event.mask)])
        return f"{self.__event} {flags}"


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

    def __init__(self, *paths: str) -> None:
        """Construct the InotifySimpleWatcher object.

        Parameters
        ----------
        *paths: str
            The paths to watch.
        """
        self.__inotify = Inotify()
        self.__wds: list[int] | None = list()
        for path in paths:
            wd = self.__inotify.add_watch(path, InotifyMasks.ALL_EVENTS)
            self.__wds.append(wd)
            logger.debug(f"wd={wd} path={path}")

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
            if self.__wds is not None:
                try:
                    for wd in self.__wds:
                        self.__inotify.rm_watch(wd)
                except OSError:
                    pass
                self.__wds = None
            self.__inotify.close()

    def read_events(self) -> list[InotifyEventWrapper]:
        """Read the inotify events and wrap them."""
        return [
            InotifyEventWrapper(e)
            for e in self.__inotify.read(timeout=100, read_delay=100)
        ]


class TestParentFile:
    """A class to test all parent file related use cases."""

    def test_self_updated(self):
        """Check for inotify events that occur when self is updated."""
        with TemporaryTree(TEMPORARY_TEST_FILE) as (test_file,):
            with InotifySimpleWatcher(test_file) as watcher:
                os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_modified(self):
        """Check for inotify events that occur when self is modified."""
        with TemporaryTree(TEMPORARY_TEST_FILE) as (test_file,):
            with InotifySimpleWatcher(test_file) as watcher:
                with open(test_file, "a") as f:
                    f.write("This file is test")
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_deleted(self):
        """Check for inotify events that occur when self is deleted."""
        with TemporaryTree(TEMPORARY_TEST_FILE) as (test_file,):
            with InotifySimpleWatcher(test_file) as watcher:
                os.remove(test_file)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_moved(self):
        """Check for inotify events that occur when self is moved."""
        with TemporaryTree(TEMPORARY_ALT_DIR_TEST_FILE) as (
            alt_dir,
            test_file,
        ):
            with InotifySimpleWatcher(test_file) as watcher:
                os.rename(test_file, os.path.join(alt_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)


class TestParentDirectory:
    """A class to test all parent directory related use cases."""

    def test_self_updated(self):
        """Check for inotify events that occur when self is updated."""
        with TemporaryTree(TEMPORARY_TEST_DIR) as (test_dir,):
            with InotifySimpleWatcher(test_dir) as watcher:
                os.chmod(test_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_deleted(self):
        """Check for inotify events that occur when self is deleted."""
        with TemporaryTree(TEMPORARY_TEST_DIR) as (test_dir,):
            with InotifySimpleWatcher(test_dir) as watcher:
                os.rmdir(test_dir)
                for event in watcher.read_events():
                    logger.info(event)

    def test_self_moved(self):
        """Check for inotify events that occur when self is moved."""
        with TemporaryTree(TEMPORARY_ALT_DIR_TEST_DIR) as (
            alt_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(test_dir) as watcher:
                os.rename(test_dir, os.path.join(alt_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)


class TestChildFile:
    """A class to test all child file related use cases."""

    def test_file_created(self):
        """Check for inotify events that occur when a file is created."""
        with TemporaryTree(TEMPORARY_TEST_DIR) as (root_dir,):
            with InotifySimpleWatcher(root_dir) as watcher:
                open(os.path.join(root_dir, "test_file"), "x").close()
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_updated(self):
        """Check for inotify events that occur when a file is updated."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_FILE) as (
            root_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_modified(self):
        """Check for inotify events that occur when a file is modified."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_FILE) as (
            root_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                with open(test_file, "a") as f:
                    f.write("This file is root")
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_moved(self):
        """Check for inotify events that occur when a file is moved."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_FILE) as (
            root_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rename(test_file, os.path.join(root_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_deleted(self):
        """Check for inotify events that occur when a file is deleted."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_FILE) as (
            root_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.remove(test_file)
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_moved_outside(self):
        """Check for inotify events that occur when a file is moved outside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_ROOT_DIR_TEST_FILE) as (
            alt_dir,
            root_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rename(test_file, os.path.join(alt_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_file_moved_inside(self):
        """Check for inotify events that occur when a file is moved inside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_TEST_FILE_ROOT_DIR) as (
            alt_dir,
            test_file,
            root_dir,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rename(test_file, os.path.join(root_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)


class TestChildDirectory:
    """A class to test all child directory related use cases."""

    def test_directory_created(self):
        """Check for inotify events that occur when a directory is created."""
        with TemporaryTree(TEMPORARY_TEST_DIR) as (root_dir,):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.mkdir(os.path.join(root_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_updated(self):
        """Check for inotify events that occur when a directory is updated."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_DIR) as (
            root_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.chmod(test_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_moved(self):
        """Check for inotify events that occur when a directory is moved."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_DIR) as (
            root_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rename(test_dir, os.path.join(root_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_deleted(self):
        """Check for inotify events that occur when a directory is deleted."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_TEST_DIR) as (
            root_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rmdir(test_dir)
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_moved_outside(self):
        """Check for inotify events that occur when a directory is moved outside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_ROOT_DIR_TEST_DIR) as (
            alt_dir,
            root_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rename(test_dir, os.path.join(alt_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_directory_moved_inside(self):
        """Check for inotify events that occur when a directory is moved inside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_TEST_DIR_ROOT_DIR) as (
            alt_dir,
            test_dir,
            root_dir,
        ):
            with InotifySimpleWatcher(root_dir) as watcher:
                os.rename(test_dir, os.path.join(root_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)


class TestTreeFile:
    """A class to test all tree file related use cases."""

    def test_tree_file_created(self):
        """Check for inotify events that occur when a file is created."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR) as (
            root_dir,
            sub_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir) as watcher:
                open(os.path.join(sub_dir, "test_file"), "x").close()
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_file_updated(self):
        """Check for inotify events that occur when a file is updated."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_FILE) as (
            root_dir,
            sub_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_file) as watcher:
                os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_file_modified(self):
        """Check for inotify events that occur when a file is modified."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_FILE) as (
            root_dir,
            sub_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_file) as watcher:
                with open(test_file, "a") as f:
                    f.write("This file is watched")
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_file_moved(self):
        """Check for inotify events that occur when a file is moved."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_FILE) as (
            root_dir,
            sub_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_file) as watcher:
                os.rename(test_file, os.path.join(root_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_file_deleted(self):
        """Check for inotify events that occur when a file is deleted."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_FILE) as (
            root_dir,
            sub_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_file) as watcher:
                os.remove(test_file)
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_file_moved_outside(self):
        """Check for inotify events that occur when a file is moved outside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_ROOT_DIR_SUB_DIR_TEST_FILE) as (
            alt_dir,
            root_dir,
            sub_dir,
            test_file,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_file) as watcher:
                os.rename(test_file, os.path.join(alt_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_file_moved_inside(self):
        """Check for inotify events that occur when a file is moved inside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_TEST_FILE_ROOT_DIR_SUB_DIR) as (
            alt_dir,
            test_file,
            root_dir,
            sub_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir) as watcher:
                os.rename(test_file, os.path.join(sub_dir, "test_file"))
                for event in watcher.read_events():
                    logger.info(event)


class TestTreeDirectory:
    """A class to test all tree directory related use cases."""

    def test_tree_directory_created(self):
        """Check for inotify events that occur when a directory is created."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR) as (
            root_dir,
            sub_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir) as watcher:
                os.mkdir(os.path.join(sub_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_directory_updated(self):
        """Check for inotify events that occur when a directory is updated."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_DIR) as (
            root_dir,
            sub_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_dir) as watcher:
                os.chmod(test_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_directory_moved(self):
        """Check for inotify events that occur when a directory is moved."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_DIR) as (
            root_dir,
            sub_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_dir) as watcher:
                os.rename(test_dir, os.path.join(root_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_directory_deleted(self):
        """Check for inotify events that occur when a directory is deleted."""
        with TemporaryTree(TEMPORARY_ROOT_DIR_SUB_DIR_TEST_DIR) as (
            root_dir,
            sub_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_dir) as watcher:
                os.rmdir(test_dir)
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_directory_moved_outside(self):
        """Check for inotify events that occur when a directory is moved outside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_ROOT_DIR_SUB_DIR_TEST_DIR) as (
            alt_dir,
            root_dir,
            sub_dir,
            test_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir, test_dir) as watcher:
                os.rename(test_dir, os.path.join(alt_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)

    def test_tree_directory_moved_inside(self):
        """Check for inotify events that occur when a directory is moved inside."""
        with TemporaryTree(TEMPORARY_ALT_DIR_TEST_DIR_ROOT_DIR_SUB_DIR) as (
            alt_dir,
            test_dir,
            root_dir,
            sub_dir,
        ):
            with InotifySimpleWatcher(root_dir, sub_dir) as watcher:
                os.rename(test_dir, os.path.join(sub_dir, "test_dir"))
                for event in watcher.read_events():
                    logger.info(event)
