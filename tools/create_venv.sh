#!/bin/sh

# Ensure we are sourced
if [ -z "${BASH}" ] || [ "${0}" = "${BASH_SOURCE}" ]
then
	echo >&2 "This script needs to be sourced from a bash shell"
	false

# Ensure we are not already in a virtual environment
elif [ ${VIRTUAL_ENV:-no} != no ]
then
	echo >&2 "Already in a virtual environment"
	true

else
	ROOT_DIR=$(dirname $(dirname $(readlink -f ${BASH_SOURCE})))
	VENV_DIR=${ROOT_DIR}/.venv
	HAVE_VENV=$(test -d ${VENV_DIR} && echo 1)

	# Create the virtual environment
	if [ ${HAVE_VENV:-0} = 0 ]
	then
		python3 -m venv ${VENV_DIR}
	fi

	# Activate the virtual environment
	. ${VENV_DIR}/bin/activate

	# Install the dependencies
	if [ ${HAVE_VENV:-0} = 0 ]
	then
		pip3 install -e ${ROOT_DIR}
		pip3 install ${ROOT_DIR}[development]
		pip3 install ${ROOT_DIR}[documentation]
		pip3 install ${ROOT_DIR}[tests]
		pip3 install build
	fi

	# Install the pre-commit
	( cd ${ROOT_DIR} && pre-commit install )
fi
