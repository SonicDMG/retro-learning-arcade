#!/bin/bash
# Double-click this file in Finder to play.
#
# If uv is installed it does the work: it resolves pygame and starts the game
# in one step, with no virtual environment to manage. Otherwise this falls
# back to a plain venv, so the game still runs on a Mac that has nothing but
# the system Python.

cd "$(dirname "$0")" || exit 1

if command -v uv >/dev/null 2>&1; then
  exec uv run retro-arcade
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed."
  echo "Install it from https://www.python.org/downloads/macos/ and try again,"
  echo "or install uv from https://docs.astral.sh/uv/ for a one-step setup."
  echo
  read -r -p "Press Return to close..."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "First run: setting up (this takes a minute)..."
  python3 -m venv .venv || exit 1
  ./.venv/bin/python -m pip install --quiet --upgrade pip
  ./.venv/bin/python -m pip install --quiet -r requirements.txt || {
    echo "Could not install pygame. Check your internet connection and try again."
    read -r -p "Press Return to close..."
    exit 1
  }
  echo "Ready!"
fi

exec ./.venv/bin/python launcher.py
