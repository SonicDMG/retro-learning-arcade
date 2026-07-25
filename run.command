#!/bin/bash
# Double-click this file in Finder to play.
#
# If uv is installed it does the work: it resolves pygame and starts the game
# in one step, with no virtual environment to manage. Otherwise this falls
# back to a plain venv, so the game still runs on a Mac that has nothing but
# the system Python.

cd "$(dirname "$0")" || exit 1

# Finder launches this with a minimal PATH, so a uv installed into
# ~/.local/bin is often invisible to `command -v`. Check the usual homes too.
find_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi
  for candidate in "$HOME/.local/bin/uv" "/opt/homebrew/bin/uv" "/usr/local/bin/uv"; do
    if [ -x "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

UV="$(find_uv)" || UV=""

# No uv yet: offer to fetch it, since it is the shortest path to playing.
# Declining is fine -- the virtualenv route below works without it.
if [ -z "$UV" ] && [ -t 0 ]; then
  echo "uv is not installed. It sets up Python and pygame for you in one step."
  echo "(The alternative is a virtual environment, which also works fine.)"
  echo
  read -r -p "Install uv now? [Y/n] " reply
  case "$reply" in
    [Nn]*)
      echo "No problem -- using a virtual environment instead."
      ;;
    *)
      echo "Installing uv from https://astral.sh/uv ..."
      if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        UV="$(find_uv)" || UV=""
      fi
      if [ -z "$UV" ]; then
        echo "uv did not install. Falling back to a virtual environment."
        echo "You can also install it with: brew install uv"
      fi
      ;;
  esac
  echo
fi

if [ -n "$UV" ]; then
  exec "$UV" run retro-arcade
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Neither uv nor Python 3 is installed, so there is nothing to run the"
  echo "game with. Install either one and try again:"
  echo "  uv      curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "  Python  https://www.python.org/downloads/macos/"
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
