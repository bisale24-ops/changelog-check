#!/bin/sh
# changelog-check without installing anything
export PYTHONPATH="$(dirname "$0")/src"
exec python3 -m changelogcheck.cli "$@"
