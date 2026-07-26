"""Checks on the scoreboard.

The registry is built from each game's own mode tables, so comparing the two
proves nothing -- both sides read the same dictionary. What can genuinely
break is the save key: a game writes "math_add", and the scoreboard has to
look under exactly that. So the real test finishes a round of every mode
through the game's own code and checks the key it records against the key
the scoreboard reads, plus that no game module is missing from the registry
altogether.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("RETRO_ARCADE_SAVE_DIR", "/tmp/retro-scoreboard-test")

import glob  # noqa: E402
import importlib  # noqa: E402

from games import (  # noqa: E402
    crystal_keys,
    logic_lab,
    math_blaster,
    pattern_power,
    scoreboard,
    word_rocket,
)
from retro import progress, sprites  # noqa: E402
from retro.app import App  # noqa: E402

# How to start a round of each game, so the test can finish one and see what
# key the game itself writes.
ROUND_FACTORIES = {
    math_blaster.GAME_KEY: lambda app, p, mode: math_blaster.MathRoundScene(app, p, mode, 2),
    word_rocket.GAME_KEY: lambda app, p, mode: word_rocket.WordRoundScene(app, p, mode),
    pattern_power.GAME_KEY: lambda app, p, mode: pattern_power.PatternRoundScene(app, p, mode),
    crystal_keys.GAME_KEY: lambda app, p, mode: crystal_keys.TypingRoundScene(app, p, mode),
    logic_lab.GAME_KEY: lambda app, p, mode: logic_lab.LogicRoundScene(app, p, mode, 2),
}


class TestRegistryCoversEveryGame(unittest.TestCase):
    def test_no_game_module_is_missing_from_the_scoreboard(self):
        """Found by scanning the games folder, not by reading the registry."""
        listed = {record[3] for record in scoreboard.GAME_RECORDS}
        found = set()
        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "games")
        for path in glob.glob(os.path.join(folder, "*.py")):
            name = os.path.splitext(os.path.basename(path))[0]
            if name.startswith("_") or name == "scoreboard":
                continue
            module = importlib.import_module(f"games.{name}")
            key = getattr(module, "GAME_KEY", None)
            if key:
                found.add(key)
        self.assertEqual(found, listed, "a game exists that the scoreboard never shows")

    def test_modes_have_labels_and_games_have_icons(self):
        for title, icon, _, _, per_round, modes in scoreboard.GAME_RECORDS:
            self.assertIn(icon, sprites.SPRITES, title)
            self.assertGreater(per_round, 0, title)
            for mode, label in modes:
                self.assertTrue(label.strip(), f"{title}/{mode} has no label")


class TestKeysMatchWhatGamesWrite(unittest.TestCase):
    """Finish a real round of every mode and follow the key it saves."""

    @classmethod
    def setUpClass(cls):
        cls.app = App()

    def test_every_mode_records_under_the_key_the_scoreboard_reads(self):
        player = progress.Player(progress.PROFILES[0][0])
        for record in scoreboard.GAME_RECORDS:
            _, _, _, prefix, per_round, modes = record
            factory = ROUND_FACTORIES[prefix]
            for mode, label in modes:
                self.app.scenes = []
                scene = factory(self.app, player, mode)
                self.app.push(scene)
                # Whatever each game calls the count it reports.
                for attribute in ("correct", "clean"):
                    if hasattr(scene, attribute):
                        setattr(scene, attribute, 1)
                finish = getattr(scene, "_finish", None) or scene._finish_round
                finish()
                results = self.app.scene
                self.assertEqual(
                    results.game_key,
                    f"{prefix}_{mode}",
                    f"{label}: saves under a key the scoreboard does not read",
                )
                self.assertEqual(
                    results.total, per_round, f"{label}: round length disagrees"
                )

    def test_a_finished_round_shows_up_on_the_scoreboard(self):
        """End to end: play, save, and read it back through the scoreboard."""
        player = progress.Player(progress.PROFILES[2][0])
        player.entry["best"] = {}
        player.entry["played"] = {}
        progress.save(player.data)
        record = next(r for r in scoreboard.GAME_RECORDS if r[3] == math_blaster.GAME_KEY)
        before = scoreboard.game_totals(player, record)[0]

        self.app.scenes = []
        scene = math_blaster.MathRoundScene(self.app, player, "multiply", 2)
        self.app.push(scene)
        scene.correct = 7
        # _finish replaces the scene, and pushing the results screen runs its
        # on_enter, which is what records the round. Calling on_enter here as
        # well would count the round twice.
        scene._finish()

        reloaded = progress.Player(progress.PROFILES[2][0])
        played, best, per_round = scoreboard.game_totals(reloaded, record)
        self.assertEqual(played, before + 1)
        self.assertEqual(best, 7)
        self.assertEqual(per_round, math_blaster.ROUND_LENGTH)


class TestTotals(unittest.TestCase):
    def setUp(self):
        self.player = progress.Player(progress.PROFILES[0][0])
        self.player.entry["best"] = {}
        self.player.entry["played"] = {}

    def test_empty_player_totals_to_zero(self):
        self.assertEqual(scoreboard.total_rounds(self.player), 0)
        for record in scoreboard.GAME_RECORDS:
            played, best, per_round = scoreboard.game_totals(self.player, record)
            self.assertEqual((played, best), (0, 0), record[0])
            self.assertGreater(per_round, 0)

    def test_rounds_and_best_are_summed_across_modes(self):
        self.player.entry["played"] = {"math_add": 3, "math_multiply": 2, "logic_matrix": 4}
        self.player.entry["best"] = {"math_add": 7, "math_multiply": 10, "logic_matrix": 5}
        math_record = next(r for r in scoreboard.GAME_RECORDS if r[3] == "math")
        played, best, per_round = scoreboard.game_totals(self.player, math_record)
        self.assertEqual(played, 5, "rounds should add up across modes")
        self.assertEqual(best, 10, "best should be the highest of any mode")
        self.assertEqual(per_round, math_blaster.ROUND_LENGTH)
        self.assertEqual(scoreboard.total_rounds(self.player), 9)

    def test_unknown_keys_in_a_save_are_ignored(self):
        """An old or hand-edited save must not break the totals."""
        self.player.entry["played"] = {"math_add": 2, "ghost_mode": 99}
        self.player.entry["best"] = {"ghost_mode": 50}
        self.assertEqual(scoreboard.total_rounds(self.player), 2)

    def test_best_never_exceeds_the_round_length_in_normal_play(self):
        for record in scoreboard.GAME_RECORDS:
            prefix, per_round, modes = record[3], record[4], record[5]
            self.player.entry["played"] = {f"{prefix}_{modes[0][0]}": 1}
            self.player.entry["best"] = {f"{prefix}_{modes[0][0]}": per_round}
            _, best, _ = scoreboard.game_totals(self.player, record)
            self.assertLessEqual(best / per_round, 1.0, record[0])


if __name__ == "__main__":
    unittest.main()
