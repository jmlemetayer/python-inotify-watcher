import sys
import tempfile

from inotify_watcher import InotifyWatcher


def main() -> int:
    with tempfile.TemporaryDirectory() as watched_dir:
        try:
            watcher = InotifyWatcher(
                watched_dir,
                file_created=lambda p: print(f"file {p} created"),
                file_modified=lambda p: print(f"file {p} modified"),
                file_moved=lambda p, n: print(f"file {p} moved to {n}"),
                file_deleted=lambda p: print(f"file {p} deleted"),
                file_gone=lambda p: print(f"file {p} gone"),
                dir_created=lambda p: print(f"directory {p} created"),
                dir_moved=lambda p, n: print(f"directory {p} moved to {n}"),
                dir_deleted=lambda p: print(f"directory {p} deleted"),
                dir_gone=lambda p: print(f"directory {p} gone"),
            )

            print(f"watched directory: {watched_dir}")

            watcher.wait()

        except KeyboardInterrupt:
            watcher.terminate()

    return 0


if __name__ == "__main__":
    sys.exit(main())
