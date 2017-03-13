#!/bin/bash
set -e
# set -ex

# the directory of the script
# DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# the temp directory used, within $DIR
WORK_DIR=`mktemp -d`

if hash pyenv 2>/dev/null; then
    PYTHON=`pyenv which python`
    UWSGI=`pyenv which uwsgi`
else
    PYTHON=`which python`
    UWSGI=`which uwsgi`
fi

function cleanup {
  $UWSGI --stop "$WORK_DIR/uwsgi.pid"
  killall uwsgi || true
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

function error() {
  # from http://stackoverflow.com/a/185900/194586
  local parent_lineno="$1"
  local message="$2"
  local code="${3:-1}"
  if [[ -n "$message" ]] ; then
    echo "Error on or near line ${parent_lineno}: ${message}; exiting with status ${code}"
  else
    echo "Error on or near line ${parent_lineno}; exiting with status ${code}"
  fi
  exit "${code}"
}

# register the cleanup function to be called on the EXIT signal
trap cleanup EXIT
trap 'error ${LINENO}' ERR

export DJANGO_SETTINGS_MODULE="resource_manager.settings_test"
export TEMP_DATABASE="$WORK_DIR/db.sqlite"

$PYTHON manage.py migrate
$UWSGI --http :8002 --module central_authentication_service.wsgi --pidfile "$WORK_DIR/uwsgi.pid" &

# sleep 5
python tests/wait_net_service.py -p 8002

echo -e "\n == Django running ==\n"

$PYTHON tests/functional_tests.py
