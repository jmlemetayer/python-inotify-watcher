#!/bin/sh -e

cd ${0%/*}/..

# Ensure we are in a virtual environment
if [ ${VIRTUAL_ENV:-no} = no ]
then
	echo >&2 "Not in a virtual environment"
	exit 1
fi

pre-commit run -a || pre-commit run -a

python -m build --sdist --wheel --outdir dist .

rm -rf docs/_build docs/_autosummary

make -C docs html

pytest --cov inotify_watcher --cov-report xml tests
