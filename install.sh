#!/usr/bin/env bash
# Explicit user installation only. No automatic package installation at startup.
set -eu
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != '--desktop' ]; }; then
    printf '%s\n' 'Usage : ./install.sh [--desktop]' >&2
    exit 2
fi
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
python3 -c 'import sys, tkinter; assert sys.version_info >= (3, 10), "Python 3.10+ requis"' || {
    printf '%s\n' 'Python 3.10+, venv et Tkinter sont requis. Sur Debian/Ubuntu : sudo apt install python3-venv python3-tk' >&2
    exit 1
}
if [ ! -d "$APP_DIR/.venv" ]; then
    python3 -m venv "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
"$APP_DIR/launch.sh" --check
if [ "${1:-}" = '--desktop' ]; then
    "$APP_DIR/.venv/bin/python" "$APP_DIR/scripts/install_desktop.py"
fi
printf '%s\n' 'Installation terminée. Lancez ./launch.sh dans une session graphique.'
