# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
from __future__ import annotations

import logging
import pathlib
import signal
import sys
import threading
import types

from inotify_watcher import InotifyWatcher

logging.basicConfig(level=logging.DEBUG)


class ExampleThread(threading.Thread):
    def __init__(self) -> None:
        threading.Thread.__init__(self)

        self.__cwd = pathlib.Path.cwd()
        self.__watcher = InotifyWatcher(
            self.__cwd,
            file_watched=lambda path: print(
                f"File {path.relative_to(self.__cwd)} watched"
            ),
            file_created=lambda path: print(
                f"File {path.relative_to(self.__cwd)} created"
            ),
            file_updated=lambda path: print(
                f"File {path.relative_to(self.__cwd)} updated"
            ),
            file_modified=self.__file_modified,
            file_moved=self.__file_moved,
            file_deleted=self.__file_deleted,
            file_gone=self.__file_gone,
            dir_watched=lambda path: print(
                f"Directory {path.relative_to(self.__cwd)} watched"
            ),
            dir_created=lambda path: print(
                f"Directory {path.relative_to(self.__cwd)} created"
            ),
            dir_updated=lambda path: print(
                f"Directory {path.relative_to(self.__cwd)} updated"
            ),
            dir_moved=self.__dir_moved,
            dir_deleted=self.__dir_deleted,
            dir_gone=self.__dir_gone,
        )

    def run(self) -> None:
        print(f"Inotify watcher is running on {self.__cwd}")
        self.__watcher.wait()

    def stop(self) -> None:
        self.__watcher.close()

    def __file_modified(self, path: pathlib.Path) -> None:
        print(f"File {path.relative_to(self.__cwd)} modified")

    def __file_moved(self, path: pathlib.Path, new_path: pathlib.Path) -> None:
        print(
            f"File {path.relative_to(self.__cwd)} "
            f"moved to {new_path.relative_to(self.__cwd)}"
        )

    def __file_deleted(self, path: pathlib.Path) -> None:
        print(f"File {path.relative_to(self.__cwd)} deleted")

    def __file_gone(self, path: pathlib.Path) -> None:
        print(f"File {path.relative_to(self.__cwd)} gone")

    def __dir_moved(self, path: pathlib.Path, new_path: pathlib.Path) -> None:
        print(
            f"Directory {path.relative_to(self.__cwd)} "
            f"moved to {new_path.relative_to(self.__cwd)}"
        )

    def __dir_deleted(self, path: pathlib.Path) -> None:
        print(f"Directory {path.relative_to(self.__cwd)} deleted")

    def __dir_gone(self, path: pathlib.Path) -> None:
        print(f"Directory {path.relative_to(self.__cwd)} gone")


def main() -> int:
    thread = ExampleThread()

    def sigint_handler(  # pylint: disable=unused-argument
        signum: int, frame: types.FrameType | None
    ) -> None:
        thread.stop()

    signal.signal(signal.SIGINT, sigint_handler)

    thread.start()
    thread.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
