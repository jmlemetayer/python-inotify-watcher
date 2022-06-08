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
            file_watched=lambda p: print(f"File {p.relative_to(self.__cwd)} watched"),
            file_created=lambda p: print(f"File {p.relative_to(self.__cwd)} created"),
            file_updated=lambda p: print(f"File {p.relative_to(self.__cwd)} updated"),
            file_modified=self.__file_modified,
            file_moved=self.__file_moved,
            file_deleted=self.__file_deleted,
            file_gone=self.__file_gone,
            dir_watched=lambda p: print(
                f"Directory {p.relative_to(self.__cwd)} watched"
            ),
            dir_created=lambda p: print(
                f"Directory {p.relative_to(self.__cwd)} created"
            ),
            dir_updated=lambda p: print(
                f"Directory {p.relative_to(self.__cwd)} updated"
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

    def __file_modified(self, p: pathlib.Path) -> None:
        print(f"File {p.relative_to(self.__cwd)} modified")

    def __file_moved(self, p: pathlib.Path, n: pathlib.Path) -> None:
        print(f"File {p.relative_to(self.__cwd)} moved to {n.relative_to(self.__cwd)}")

    def __file_deleted(self, p: pathlib.Path) -> None:
        print(f"File {p.relative_to(self.__cwd)} deleted")

    def __file_gone(self, p: pathlib.Path) -> None:
        print(f"File {p.relative_to(self.__cwd)} gone")

    def __dir_moved(self, p: pathlib.Path, n: pathlib.Path) -> None:
        print(
            f"Directory {p.relative_to(self.__cwd)} "
            f"moved to {n.relative_to(self.__cwd)}"
        )

    def __dir_deleted(self, p: pathlib.Path) -> None:
        print(f"Directory {p.relative_to(self.__cwd)} deleted")

    def __dir_gone(self, p: pathlib.Path) -> None:
        print(f"Directory {p.relative_to(self.__cwd)} gone")


def main() -> int:
    t = ExampleThread()

    def sigint_handler(signum: int, frame: types.FrameType | None) -> None:
        t.stop()

    signal.signal(signal.SIGINT, sigint_handler)

    t.start()
    t.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
