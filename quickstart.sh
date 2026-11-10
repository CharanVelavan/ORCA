#!/bin/sh
# Run from any working directory; Python 3.12 is required by the pinned stack.
set -eu
ORCA_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ORCA_ROOT"
if command -v python3.12 >/dev/null 2>&1; then
  ORCA_PYTHON=python3.12
elif [ -x "$ORCA_ROOT/.venv/bin/python3.12" ]; then
  ORCA_PYTHON="$ORCA_ROOT/.venv/bin/python3.12"
else
  printf '%s\n' 'Python 3.12 was not found. Install Python 3.12, then run ./quickstart.sh again.' >&2
  exit 1
fi
exec "$ORCA_PYTHON" scripts/judge_setup.py "$@"
