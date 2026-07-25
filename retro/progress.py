"""Per-player progress, stored as one small JSON file.

Kids collect stars. Nothing here can fail loudly: a missing or corrupt save
file is treated as "brand new player" rather than an error, because a crash
at launch is far worse than a lost star count.

Where the file lives depends on how the game was started. Run from a checkout
it sits in `saves/` next to the code, which keeps it obvious and easy to
delete. Installed as a package -- `uvx`, `pip install` -- it goes to the
platform's user data directory instead, because writing into site-packages
would put a child's progress somewhere that a reinstall quietly erases.
"""

import json
import os
import sys

from . import levels

APP_NAME = "RetroLearningArcade"


def _default_save_dir():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # A checkout has project files next to the packages; an install does not.
    for marker in ("pyproject.toml", ".git"):
        if os.path.exists(os.path.join(root, marker)):
            return os.path.join(root, "saves")
    if sys.platform == "darwin":
        return os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, APP_NAME)
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "retro-learning-arcade")


# RETRO_ARCADE_SAVE_DIR overrides everything, which is handy for testing and
# for putting one shared save file on a family machine.
SAVE_DIR = os.environ.get("RETRO_ARCADE_SAVE_DIR") or _default_save_dir()
SAVE_PATH = os.path.join(SAVE_DIR, "progress.json")

# Fixed profile slots. Kids pick an avatar instead of typing a name.
PROFILES = [
    ("Juni", "rocket"),
    ("Sage", "cat"),
    ("Other", "star"),
]


def _blank():
    return {
        name: {"stars": 0, "best": {}, "played": {}, "crystals": {}, "age": None}
        for name, _ in PROFILES
    }


def load():
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return _blank()
    if not isinstance(data, dict):
        return _blank()
    base = _blank()
    for name in base:
        entry = data.get(name)
        if isinstance(entry, dict):
            base[name]["stars"] = int(entry.get("stars", 0) or 0)
            if isinstance(entry.get("best"), dict):
                base[name]["best"] = entry["best"]
            if isinstance(entry.get("played"), dict):
                base[name]["played"] = entry["played"]
            if isinstance(entry.get("crystals"), dict):
                base[name]["crystals"] = entry["crystals"]
            age = entry.get("age")
            if isinstance(age, int) and levels.MIN_AGE <= age <= levels.MAX_AGE:
                base[name]["age"] = age
    return base


def save(data):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(SAVE_PATH, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
    except OSError:
        pass  # A read-only disk should not interrupt play.


class Player:
    """Convenience wrapper around one profile's slice of the save file."""

    def __init__(self, name):
        self.name = name
        self.data = load()
        self.entry = self.data.setdefault(name, {"stars": 0, "best": {}, "played": {}})

    @property
    def stars(self):
        return self.entry.get("stars", 0)

    def add_stars(self, count):
        self.entry["stars"] = self.stars + count
        save(self.data)

    @property
    def age(self):
        """The player's age, or None until they have been asked."""
        return self.entry.get("age")

    def set_age(self, age):
        self.entry["age"] = max(levels.MIN_AGE, min(levels.MAX_AGE, int(age)))
        save(self.data)

    def tier(self, nudge=0):
        """How hard this player's games should be right now."""
        return levels.tier_for(self.age, nudge)

    @property
    def crystals(self):
        """Elemental crystals, keyed by element name."""
        return self.entry.setdefault("crystals", {})

    def add_crystals(self, element, count):
        crystals = self.crystals
        crystals[element] = crystals.get(element, 0) + count
        save(self.data)

    def total_crystals(self):
        return sum(self.crystals.values())

    def record_round(self, game_key, correct, total):
        """Remember the best score for a game and bump the play counter."""
        best = self.entry.setdefault("best", {})
        played = self.entry.setdefault("played", {})
        played[game_key] = played.get(game_key, 0) + 1
        previous = best.get(game_key, 0)
        is_record = correct > previous
        if is_record:
            best[game_key] = correct
        save(self.data)
        return is_record

    def best(self, game_key):
        return self.entry.get("best", {}).get(game_key, 0)
