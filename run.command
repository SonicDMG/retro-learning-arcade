#!/bin/bash
# Double-click this file in Finder to play. It sets up a private virtual
# environment on first run, then launches the arcade every time after that.

cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed."
  echo "Install it from https://www.python.org/downloads/macos/ and try again."
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
