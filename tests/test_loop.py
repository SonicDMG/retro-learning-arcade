"""Checks on the frame loop, especially scenes that end themselves.

A round finishing replaces its own scene with the results screen, and it does
that from inside update(). Anything holding the pre-update scene will then
draw a scene that has already been torn down.

That crashed Crystal Keys in real play: the typing scene's prompt index had
moved past the end, so the prompt was "" and laying out its letters raised
ValueError. The playthrough harnesses missed it because they re-read
app.scene for both update and draw, which the real loop did not.

These tests go through App.advance -- the actual frame code -- so the harness
cannot diverge from the game again.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("RETRO_ARCADE_SAVE_DIR", "/tmp/retro-loop-test")

from games import (  # noqa: E402
    crystal_keys,
    math_blaster,
    pattern_power,
    word_rocket,
)
from retro import progress  # noqa: E402
from retro.app import App, Scene  # noqa: E402
from retro.results import ResultsScene  # noqa: E402


class SelfEndingScene(Scene):
    """Replaces itself during update, then explodes if drawn afterwards."""

    def __init__(self, app, replacement):
        super().__init__(app)
        self.replacement = replacement
        self.drawn_after_replacing = False
        self.replaced = False

    def update(self, dt):
        if not self.replaced:
            self.replaced = True
            self.app.replace(self.replacement)

    def draw(self, surface):
        if self.replaced:
            self.drawn_after_replacing = True
            raise AssertionError("a torn-down scene was drawn")


class Quiet(Scene):
    pass


class TestAdvanceDrawsTheCurrentScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()

    def test_a_scene_that_replaces_itself_is_not_drawn(self):
        replacement = Quiet(self.app)
        scene = SelfEndingScene(self.app, replacement)
        self.app.scenes = []
        self.app.push(scene)
        self.app.advance(1 / 60)  # Must not raise.
        self.assertIs(self.app.scene, replacement)
        self.assertFalse(scene.drawn_after_replacing)


def player():
    return progress.Player(progress.PROFILES[0][0])


class TestRoundsCanFinish(unittest.TestCase):
    """Play each game's final moment through the real frame loop."""

    @classmethod
    def setUpClass(cls):
        cls.app = App()

    def _run_out(self, scene, frames=240):
        self.app.scenes = []
        self.app.push(scene)
        for _ in range(frames):
            self.app.advance(1 / 60)
            if isinstance(self.app.scene, ResultsScene):
                return self.app.scene
        return self.app.scene

    def test_crystal_keys_round_ends_cleanly(self):
        """The exact crash: last prompt done, scene swapped, old one drawn."""
        scene = crystal_keys.TypingRoundScene(self.app, player(), "earth")
        scene.prompts = ["fall"] * crystal_keys.ROUND_LENGTH
        scene.index = crystal_keys.ROUND_LENGTH - 1
        scene.typed = len(scene.prompt)
        scene.state = "celebrating"
        scene.state_timer = 0.01
        result = self._run_out(scene)
        self.assertIsInstance(result, ResultsScene)

    def test_crystal_keys_survives_an_exhausted_prompt_list(self):
        """Drawing past the end must not raise even if it somehow happens."""
        scene = crystal_keys.TypingRoundScene(self.app, player(), "earth")
        scene.index = len(scene.prompts)  # No prompt left.
        self.assertEqual(scene.prompt, "")
        self.app.scenes = []
        self.app.push(scene)
        self.app.advance(1 / 60)  # Must not raise.

    def test_math_round_ends_cleanly(self):
        scene = math_blaster.MathRoundScene(self.app, player(), "add", 1)
        scene.on_enter()
        scene.index = math_blaster.ROUND_LENGTH
        scene.state = "celebrating"
        scene.state_timer = 0.01
        self.assertIsInstance(self._run_out(scene), ResultsScene)

    def test_word_round_ends_cleanly(self):
        scene = word_rocket.WordRoundScene(self.app, player(), "first")
        scene.on_enter()
        scene.index = word_rocket.ROUND_LENGTH
        scene.state = "celebrating"
        scene.state_timer = 0.01
        self.assertIsInstance(self._run_out(scene), ResultsScene)

    def test_pattern_round_ends_cleanly(self):
        scene = pattern_power.PatternRoundScene(self.app, player(), "picture")
        scene.on_enter()
        scene.index = pattern_power.ROUND_LENGTH
        scene.state = "celebrating"
        scene.state_timer = 0.01
        self.assertIsInstance(self._run_out(scene), ResultsScene)


if __name__ == "__main__":
    unittest.main()
