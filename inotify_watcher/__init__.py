"""An easy way to use inotify with python.

This module implements only one `InotifyWatcher` class with a very simple usage.
"""
from __future__ import annotations

import logging
import pathlib
import threading
from queue import Queue
from typing import Callable
from typing import NamedTuple
from typing import Union

logger = logging.getLogger(__name__)

__version__ = "0.0.0.dev1"

__all__ = ["InotifyWatcher"]

HandlerNoneType = Callable[[], None]
HandlerOneType = Callable[[str], None]
HandlerTwoType = Callable[[str, str], None]
HandlerType = Union[HandlerOneType, HandlerTwoType]

PathType = Union[pathlib.Path, str]


class Event(NamedTuple):
    name: str
    args: list[str]


class WatchManager:
    def __init__(self, event_queue: Queue[Event | None]) -> None:
        self.__event_queue = event_queue

    def add_paths(self, *paths: PathType) -> None:
        for path in paths:
            self.add_path(path)

    def add_path(self, path: PathType) -> None:
        pass  # TODO Add the path to the inotify watch.

    def close(self) -> None:
        pass  # TODO Gracefully exit the watch.

    def watch(self) -> None:
        pass  # TODO Continuously watch the inotify events.


class InotifyWatcher:
    """A class to watch inotify events.

    This class allow to watch inotify events for several files and directories
    simultaneously. The design is callback oriented and non-blocking.
    """

    def __init__(self, *paths: PathType, **handlers: HandlerType) -> None:
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
        self.__watch_manager.add_paths(*paths)

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
