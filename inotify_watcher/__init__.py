"""An easy way to use inotify with python.

This module implements only one :obj:`InotifyWatcher` class with a very simple
usage.
"""
from __future__ import annotations

import logging
import os
import pathlib
import select
import threading
from queue import Queue
from types import TracebackType
from typing import Callable
from typing import NamedTuple
from typing import TypedDict
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


class HandlerKwargsType(TypedDict, total=False):
    """Type definition of the :obj:`InotifyWatcher` handlers as keyword arguments.

    Attributes
    ----------
    file_watched: `HandlerOneType`, optional
        Handler function called when a file is watched.
    file_created: `HandlerOneType`, optional
        Handler function called when a file is created.
    file_updated: `HandlerOneType`, optional
        Handler function called when a file is updated.
    file_modified: `HandlerOneType`, optional
        Handler function called when a file is modified.
    file_moved: `HandlerTwoType`, optional
        Handler function called when a file is moved.
    file_deleted: `HandlerOneType`, optional
        Handler function called when a file is deleted.
    file_gone: `HandlerOneType`, optional
        Handler function called when a file is gone.
    dir_watched: `HandlerOneType`, optional
        Handler function called when a directory is watched.
    dir_created: `HandlerOneType`, optional
        Handler function called when a directory is created.
    dir_updated: `HandlerOneType`, optional
        Handler function called when a directory is updated.
    dir_moved: `HandlerTwoType`, optional
        Handler function called when a directory is moved.
    dir_deleted: `HandlerOneType`, optional
        Handler function called when a directory is deleted.
    dir_gone: `HandlerOneType`, optional
        Handler function called when a directory is gone.
    """

    file_watched: HandlerOneType
    file_created: HandlerOneType
    file_updated: HandlerOneType
    file_modified: HandlerOneType
    file_moved: HandlerTwoType
    file_deleted: HandlerOneType
    file_gone: HandlerOneType
    dir_watched: HandlerOneType
    dir_created: HandlerOneType
    dir_updated: HandlerOneType
    dir_moved: HandlerTwoType
    dir_deleted: HandlerOneType
    dir_gone: HandlerOneType


class Event(NamedTuple):
    name: str
    args: list[PathType]


class WatchedPath:
    def __init__(
        self,
        manager: WatchManager,
        path: PathType,
        descriptor: int,
        parent: WatchedPath | None = None,
    ) -> None:
        self.__manager = manager
        self.__path = path
        self.__is_dir = path.is_dir()
        self.descriptor = descriptor
        self.__parent = parent
        self.children: list[WatchedPath] = list()

        if parent is not None:
            self.__path = path.relative_to(parent.path)

    @property
    def path(self) -> PathType:
        if self.__parent is not None:
            return self.__parent.path / self.__path
        return self.__path

    def add_path(self, path: PathType, descriptor: int) -> WatchedPath:
        watched_path = WatchedPath(self.__manager, path, descriptor, parent=self)
        self.children.append(watched_path)
        return watched_path

    def remove(self) -> None:
        for child in self.children:
            child.remove()
        if self.__parent is not None:
            self.__parent.children.remove(self)

    def send_event(
        self, event_name: str, secondary_path: PathType | None = None
    ) -> None:
        paths: list[PathType] = [self.path]

        if secondary_path is not None:
            paths.append(secondary_path)

        if self.__is_dir:
            event_name = f"dir_{event_name}"
        else:
            event_name = f"file_{event_name}"

        self.__manager.send_event(Event(event_name, paths))


class WatchManager:
    def __init__(self, event_queue: Queue[Event | None]) -> None:
        self.__event_queue = event_queue

        self.__inotify = inotify_simple.INotify()
        self.__read_fd, write_fd = os.pipe()
        self.__write = os.fdopen(write_fd, "wb")

        self.__watched_paths: list[WatchedPath] = list()

    def send_event(self, event: Event) -> None:
        self.__event_queue.put(event)

    def add_path(self, path: UserPathType, **kwargs: bool | None) -> None:
        path = PathType(path)

        self.__add_path(path, **kwargs)

        if path.is_dir():
            for rootpath, dirnames, filenames in os.walk(path):
                root = PathType(rootpath)
                for dirname in dirnames:
                    self.__add_path(root / dirname, **kwargs)
                for filename in filenames:
                    self.__add_path(root / filename, **kwargs)

    def __add_path(
        self, path: PathType, generate_watched_events: bool | None = None
    ) -> None:
        descriptor = self.__inotify.add_watch(path, inotify_simple.masks.ALL_EVENTS)
        parent = self.__get_path(path.parent)

        if parent is not None:
            watched_path = parent.add_path(path, descriptor)
        else:
            watched_path = WatchedPath(self, path, descriptor)

        self.__watched_paths.append(watched_path)

        if generate_watched_events is None:
            watched_path.send_event("created")
        elif generate_watched_events is True:
            watched_path.send_event("watched")

    def __get_path(self, path_or_descriptor: PathType | int) -> WatchedPath | None:
        if isinstance(path_or_descriptor, PathType):
            for watched_path in self.__watched_paths:
                if watched_path.path == path_or_descriptor:
                    return watched_path
        elif isinstance(path_or_descriptor, int):
            for watched_path in self.__watched_paths:
                if watched_path.descriptor == path_or_descriptor:
                    return watched_path
        return None

    def __rm_path(self, watched_path: WatchedPath) -> None:
        watched_path.remove()
        self.__watched_paths.remove(watched_path)

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
        event_owner = self.__get_path(event.wd)

        if event.mask & inotify_simple.flags.IGNORED:
            assert not event.name, "Invalid IGNORED event with name"
            if event_owner is not None:
                self.__rm_path(event_owner)
            return

        assert (
            event_owner is not None
        ), "No watched path associated with event descriptor"

        if event.mask & inotify_simple.flags.CREATE:
            assert event.name, "Invalid CREATE event without name"
            self.add_path(event_owner.path / event.name)

        elif event.mask & inotify_simple.flags.ATTRIB and not event.name:
            event_owner.send_event("updated")

        elif event.mask & inotify_simple.flags.MODIFY and not event.name:
            event_owner.send_event("modified")

        elif event.mask & inotify_simple.flags.DELETE_SELF:
            assert not event.name, "Invalid DELETE_SELF event with name"
            assert not event_owner.children, "Invalid DELETE_SELF event with children"
            event_owner.send_event("deleted")
            self.__rm_path(event_owner)


class InotifyWatcher:
    """A class to watch inotify events.

    This class allow to watch inotify events for several files and directories
    simultaneously. The design is callback oriented and non-blocking.
    """

    def __init__(self, *paths: UserPathType, **handlers: HandlerType) -> None:
        """Construct the `InotifyWatcher` object.

        Parameters
        ----------
        *paths: `UserPathType`
            Files and / or directories to watch.
        **handlers: `HandlerType`
            Function handlers.

            See :obj:`.HandlerKwargsType` for more details about the
            supported handlers.
        """
        self.__threads: list[threading.Thread] = list()
        self.__closed = threading.Event()

        self.__handlers: dict[str, HandlerType] = dict()
        self.__handlers.update(handlers)

        have_watched_handlers = False
        if handlers.get("file_watched") is not None:
            have_watched_handlers = True
        if handlers.get("dir_watched") is not None:
            have_watched_handlers = True

        self.__event_queue: Queue[Event | None] = Queue()

        self.__watch_manager = WatchManager(self.__event_queue)

        for path in paths:
            self.__watch_manager.add_path(
                path, generate_watched_events=have_watched_handlers
            )

        self.__start()

    def __del__(self) -> None:
        """Ensure that every resources has been properly closed."""
        self.close()

    def __enter__(self) -> InotifyWatcher:
        """Enter the runtime context related to this object.

        Returns
        -------
        InotifyWatcher
            The inotify watcher object.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the runtime context related to this object."""
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
