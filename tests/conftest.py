"""Pytest fixtures for testing the `inotify_watcher` module."""
from __future__ import annotations

import logging
import pathlib

import pytest

from . import InotifyTest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def test_paths(
    request: pytest.FixtureRequest, tmp_path: pathlib.Path
) -> dict[str, pathlib.Path]:
    """Generate a test tree based on a configuration.

    The configuration is a dictionary with keys:

    ``<path_id>``
        The path configuration (`dict`).

        Each path configuration are dictionaries with keys:

        ``"path"``
            The required path relative to a temporary path (`str`).

            Parent directories are created automatically with the default
            permissions.

        ``"is_dir"``
            Specific if the path is a directory or a regular file (`bool`).

        ``"mode"``
            Specify the path mode. (`int`)

    The configuration dictionary must be named ``"test_paths_config"`` and
    should be specified either at the module level or at the class level.

    Parameters
    ----------
    request: pytest.FixtureRequest
        The pytest `request` fixture providing information on the executing
        test function (:obj:`pytest.FixtureRequest`).
    tmp_path: pathlib.Path
        The pytest `tmp_path` fixture providing a path object to a temporary
        directory which is unique to each test function
        (:obj:`_pytest.tmpdir.tmp_path`).

    Returns
    -------
    test_paths: dict[str, pathlib.Path]
        A dictionary with the ``<path_id>`` from the configuration as keys and
        the resulting path as values.

    See Also
    --------
    pathlib.Path.mkdir

    Examples
    --------
    >>> test_paths_config = {
    ...     "test_file": {"path": "my_file"},
    ...     "test_dir": {"path": "my_dir", "is_dir": True, "mode": 0o750},
    ... }
    >>>
    >>> def test_module(test_paths: Dict[str, pathlib.Path]) -> None:
    ...     print(test_paths["test_file"])
    /tmp/pytest-of-user/pytest-42/test_module0/my_file

    >>> class TestClass:
    ...     test_paths_config = {
    ...         "test_file": {"path": "class_dir/class_file"},
    ...     }
    ...
    ...     def test_class(test_paths: Dict[str, pathlib.Path]) -> None:
    ...         print(test_paths["test_file"])
    /tmp/pytest-of-user/pytest-42/test_class0/class_dir/class_file
    """
    test_paths: dict[str, pathlib.Path] = dict()

    if request.cls:
        test_paths_config = request.cls.test_paths_config or dict()
    else:
        test_paths_config = request.module.test_paths_config or dict()

    for key, value in test_paths_config.items():
        path = pathlib.Path(tmp_path) / value["path"]

        if value.get("is_dir", False):
            path.mkdir(parents=True, exist_ok=True, mode=value.get("mode", 0o755))

        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True, mode=value.get("mode", 0o644))

        test_paths[key] = path

    return test_paths


@pytest.fixture(scope="function")
def inotify_test(
    test_paths: dict[str, pathlib.Path], tmp_path: pathlib.Path
) -> InotifyTest:
    """Generate a pre-configured test instance of `inotify_simple.INotify`.

    Parameters
    ----------
    test_paths: dict[str, pathlib.Path]
        The test fixture that generates test files based on configuration
        (:obj:`test_paths`).
    tmp_path: pathlib.Path
        The pytest `tmp_path` fixture providing a path object to a temporary
        directory which is unique to each test function
        (:obj:`_pytest.tmpdir.tmp_path`).

    Returns
    -------
    inotify_simple: InotifyTest
        A pre-configured `InotifyTest` object with the specified test paths.
    """
    inotify = InotifyTest(tmp_path)

    for key, path in test_paths.items():
        inotify.add_watch(path)

    return inotify
