"""Per-player progress, stored as one small JSON file next to the app.

Kids collect stars. Nothing here can fail loudly: a missing or corrupt save
file is treated as "brand new player" rather than an error, because a crash
at launch is far worse than a lost star count.
"""

import json
import os

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
SAVE_PATH = os.path.join(SAVE_DIR, "progress.json")

# Fixed profile slots. Kids pick an avatar instead of typing a name.
PROFILES = [
    ("Rocket", "rocket"),
    ("Kitty", "cat"),
    ("Star", "star"),
]


def _blank():
    return {name: {"stars": 0, "best": {}, "played": {}} for name, _ in PROFILES}


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
