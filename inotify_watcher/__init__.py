"""An easy way to use inotify with python.

This module implements only one `InotifyWatcher` class with a very simple usage.
"""
from __future__ import annotations

import logging
import os
import pathlib
import select
import threading
from queue import Queue
from typing import Callable
from typing import NamedTuple
from typing import Union

import inotify_simple

logger = logging.getLogger(__name__)

__version__ = "0.0.0.dev1"

__all__ = ["InotifyWatcher"]

PathType = pathlib.Path
UserPathType = Union[pathlib.Path, str]

HandlerNoneType = Callable[[], None]
HandlerOneType = Callable[[PathType], None]
HandlerTwoType = Callable[[PathType, PathType], None]
HandlerType = Union[HandlerOneType, HandlerTwoType]


class Event(NamedTuple):
    name: str
    args: list[PathType]


class WatchedPath:
    def __init__(
        self,
        path: PathType,
        descriptor: int,
        event_queue: Queue[Event | None],
        parent: WatchedPath | None = None,
        initial: bool | None = None,
    ) -> None:
        self.__path = path
        self.__is_dir = path.is_dir()
        self.descriptor = descriptor
        self.__parent = parent
        self.__event_queue = event_queue
        self.__childs: list[WatchedPath] = list()

        if parent is not None:
            self.__path = path.relative_to(parent.path)

        if initial:
            self.__send_event("watched", self.path)
        else:
            self.__send_event("created", self.path)

    def __send_event(self, event_name: str, *paths: PathType) -> None:
        if self.__is_dir:
            event_name = f"dir_{event_name}"
        else:
            event_name = f"file_{event_name}"

        self.__event_queue.put(Event(event_name, list(paths)))

    @property
    def path(self) -> PathType:
        if self.__parent is not None:
            return self.__parent.path / self.__path
        return self.__path

    def add_path(
        self, path: PathType, descriptor: int, initial: bool | None = None
    ) -> WatchedPath:
        watched_path = WatchedPath(
            path, descriptor, self.__event_queue, initial=initial, parent=self
        )
        self.__childs.append(watched_path)
        return watched_path


class WatchManager:
    def __init__(self, event_queue: Queue[Event | None]) -> None:
        self.__event_queue = event_queue

        self.__inotify = inotify_simple.INotify()
        self.__read_fd, write_fd = os.pipe()
        self.__write = os.fdopen(write_fd, "wb")

        self.__watched_paths: list[WatchedPath] = list()

    def add_paths(self, *paths: UserPathType, initial: bool | None = None) -> None:
        for path in paths:
            self.add_path(path, initial=initial)

    def add_path(self, path: UserPathType, initial: bool | None = None) -> None:
        path = PathType(path)

        self.__add_path(path, initial=initial)

        if path.is_dir():
            for rootpath, dirnames, filenames in os.walk(path):
                root = PathType(rootpath)
                for dirname in dirnames:
                    self.__add_path(root / dirname, initial=initial)
                for filename in filenames:
                    self.__add_path(root / filename, initial=initial)

    def __add_path(self, path: PathType, initial: bool | None = None) -> None:
        descriptor = self.__inotify.add_watch(path, inotify_simple.masks.ALL_EVENTS)
        parent = self.get_path(path.parent)

        if parent is not None:
            watched_path = parent.add_path(path, descriptor, initial=initial)
        else:
            watched_path = WatchedPath(
                path, descriptor, self.__event_queue, initial=initial
            )

        self.__watched_paths.append(watched_path)

    def get_path(self, path_or_descriptor: PathType | int) -> WatchedPath | None:
        if isinstance(path_or_descriptor, PathType):
            for watched_path in self.__watched_paths:
                if watched_path.path == path_or_descriptor:
                    return watched_path
        elif isinstance(path_or_descriptor, int):
            for watched_path in self.__watched_paths:
                if watched_path.descriptor == path_or_descriptor:
                    return watched_path
        return None

    def close(self) -> None:
        if not self.__write.closed:
            self.__write.write(b"\x00")
            self.__write.close()

    def __del__(self) -> None:
        self.close()

    def watch(self) -> None:
        rlist, _, _ = select.select([self.__inotify.fileno(), self.__read_fd], [], [])

        if self.__inotify.fileno() in rlist:
            for event in self.__inotify.read(timeout=0):
                self.__handle_event(event)

        if self.__read_fd in rlist:
            os.close(self.__read_fd)
            for path in self.__watched_paths:
                self.__inotify.rm_watch(path.descriptor)
            self.__watched_paths.clear()
            self.__inotify.close()

    def __handle_event(self, event: inotify_simple.Event) -> None:
        pass  # TODO Handle the event.


class InotifyWatcher:
    """A class to watch inotify events.

    This class allow to watch inotify events for several files and directories
    simultaneously. The design is callback oriented and non-blocking.
    """

    def __init__(self, *paths: UserPathType, **handlers: HandlerType) -> None:
        """Construct the InotifyWatcher object.

        Parameters
        ----------
        *paths: pathlib.Path or str
            Files and / or directories to watch.
        **handlers: HandlerType
            The supported handlers are:
                - file_watched(path)
                - file_created(path)
                - file_updated(path)
                - file_modified(path)
                - file_moved(path, new_path)
                - file_deleted(path)
                - file_gone(path)
                - dir_watched(path)
                - dir_created(path)
                - dir_updated(path)
                - dir_moved(path, new_path)
                - dir_deleted(path)
                - dir_gone(path)
        """
        self.__threads: list[threading.Thread] = list()
        self.__closed = threading.Event()

        self.__handlers: dict[str, HandlerType] = dict()
        self.__handlers.update(handlers)

        self.__event_queue: Queue[Event | None] = Queue()

        self.__watch_manager = WatchManager(self.__event_queue)
        self.__watch_manager.add_paths(*paths, initial=True)

        self.__start()

    def __del__(self) -> None:
        """Ensure that every resources has been properly closed."""
        self.close()

    def __start(self) -> None:
        self.__threads.append(
            threading.Thread(target=self.__wrapper, args=[self.__watcher])
        )
        self.__threads.append(
            threading.Thread(target=self.__wrapper, args=[self.__runner])
        )

        self.__closed.clear()

        for thread in self.__threads:
            thread.start()

    def close(self) -> None:
        """Gracefully exit all threads.

        This method can be called multiple times.
        """
        self.__closed.set()
        self.__event_queue.put(None)
        self.__watch_manager.close()

        for thread in self.__threads:
            thread.join()

        self.__threads.clear()

    def wait(self, timeout: float | None = None) -> bool:
        """Block until the watcher has been closed.

        Block until the watcher has been closed, or until the optional
        `timeout` occurs.

        Parameters
        ----------
        timeout: float, optional
            Specify a timeout for the operation in seconds.

        Returns
        -------
        bool
            This method always returns `True` except if a timeout is given and
            the operation times out.

        See Also
        --------
        threading.Event.wait
        """
        return self.__closed.wait(timeout)

    def __wrapper(self, function: HandlerNoneType) -> None:
        while not self.__closed.is_set():
            try:
                function()

            except Exception as err:
                logger.error(err, exc_info=True)

    def __watcher(self) -> None:
        self.__watch_manager.watch()

    def __runner(self) -> None:
        event = self.__event_queue.get()

        if event is None:
            return

        if event.name in self.__handlers:
            self.__handlers[event.name](*event.args)
