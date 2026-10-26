#!/usr/bin/env bash
set -eu
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
if [ -x "$APP_DIR/.venv/bin/python" ]; then
    COMMUNITY_PYTHON="$APP_DIR/.venv/bin/python"
else
    COMMUNITY_PYTHON=python3
fi
exec "$COMMUNITY_PYTHON" -E -s "$APP_DIR/main.py" "$@"
