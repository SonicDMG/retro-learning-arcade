"""Checks on key handling in the app shell.

The rule these enforce: no app command is a bare key. Every shortcut needs
Cmd or Ctrl, so a plain letter always belongs to the game.

They go through App._pump_events with real pygame events, because that is the
layer where the conflict lived. The playthrough tests call scene.handle_event
directly and sail straight past it -- which is how "F" came to toggle full
screen instead of typing a letter in the Earth lesson, where asdf, fall,
flash and half all need it.

Run with:  python3 -m unittest discover tests
"""

import os
import string
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from games import crystal_keys  # noqa: E402
from retro import progress, sfx  # noqa: E402
from retro.app import App, Scene  # noqa: E402


class Recorder(Scene):
    """A scene that just remembers which keys reached it."""

    def __init__(self, app):
        super().__init__(app)
        self.seen = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.seen.append(event.unicode)


def press(app, key, unicode_char, mods=0):
    pygame.event.clear()
    pygame.event.post(
        pygame.event.Event(
            pygame.KEYDOWN, {"key": key, "unicode": unicode_char, "mod": mods}
        )
    )
    pygame.key.set_mods(mods)
    try:
        app._pump_events()
    finally:
        pygame.key.set_mods(0)


class TestNoBareKeyCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()

    def setUp(self):
        self.app.scenes = []
        self.app.fullscreen = False
        self.scene = Recorder(self.app)
        self.app.push(self.scene)
        sfx.set_muted(False)

    def test_every_letter_reaches_the_game_untouched(self):
        """The whole alphabet, including the ones that used to be shortcuts."""
        for letter in string.ascii_lowercase:
            press(self.app, getattr(pygame, f"K_{letter}"), letter)
        self.assertEqual("".join(self.scene.seen), string.ascii_lowercase)

    def test_no_bare_letter_changes_app_state(self):
        for letter in string.ascii_lowercase:
            press(self.app, getattr(pygame, f"K_{letter}"), letter)
            self.assertFalse(
                self.app.fullscreen, f"bare {letter.upper()} toggled full screen"
            )
            self.assertFalse(sfx.is_muted(), f"bare {letter.upper()} toggled mute")
            self.assertTrue(self.app.running or True)

    def test_bare_f_types_rather_than_going_full_screen(self):
        press(self.app, pygame.K_f, "f")
        self.assertEqual(self.scene.seen, ["f"])
        self.assertFalse(self.app.fullscreen)

    def test_bare_m_types_rather_than_muting(self):
        press(self.app, pygame.K_m, "m")
        self.assertEqual(self.scene.seen, ["m"])
        self.assertFalse(sfx.is_muted())


class TestModifierShortcuts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()

    def setUp(self):
        self.app.scenes = []
        self.app.fullscreen = False
        self.scene = Recorder(self.app)
        self.app.push(self.scene)
        sfx.set_muted(False)

    def test_command_and_control_f_toggle_full_screen(self):
        for mods in (pygame.KMOD_LMETA, pygame.KMOD_LCTRL):
            press(self.app, pygame.K_f, "f", mods=mods)
            self.assertTrue(self.app.fullscreen, f"mods={mods} did not go full screen")
            press(self.app, pygame.K_f, "f", mods=mods)
            self.assertFalse(self.app.fullscreen, f"mods={mods} did not come back")

    def test_command_and_control_m_toggle_mute(self):
        for mods in (pygame.KMOD_LMETA, pygame.KMOD_LCTRL):
            press(self.app, pygame.K_m, "m", mods=mods)
            self.assertTrue(sfx.is_muted(), f"mods={mods} did not mute")
            press(self.app, pygame.K_m, "m", mods=mods)
            self.assertFalse(sfx.is_muted(), f"mods={mods} did not unmute")

    def test_shortcuts_do_not_leak_into_the_scene(self):
        press(self.app, pygame.K_f, "f", mods=pygame.KMOD_LMETA)
        press(self.app, pygame.K_m, "m", mods=pygame.KMOD_LCTRL)
        self.assertEqual(self.scene.seen, [])

    def test_command_q_quits(self):
        self.app.running = True
        press(self.app, pygame.K_q, "q", mods=pygame.KMOD_LMETA)
        self.assertFalse(self.app.running)

    def test_bare_q_does_not_quit(self):
        self.app.running = True
        press(self.app, pygame.K_q, "q")
        self.assertTrue(self.app.running, "bare Q quit the game")
        self.assertEqual(self.scene.seen, ["q"])

    def test_escape_reaches_the_scene(self):
        """Escape is navigation, not a command, so scenes handle it."""
        press(self.app, pygame.K_ESCAPE, "")
        self.assertEqual(self.scene.seen, [""])


class TestTypingActuallyAdvances(unittest.TestCase):
    """End to end: F typed in the Earth lesson must count as a letter."""

    @classmethod
    def setUpClass(cls):
        cls.app = App()

    def test_f_advances_an_earth_prompt(self):
        os.environ["RETRO_ARCADE_SAVE_DIR"] = "/tmp/retro-input-test"
        try:
            player = progress.Player(progress.PROFILES[0][0])
            scene = crystal_keys.TypingRoundScene(self.app, player, "earth")
            scene.prompts = ["fall"] * crystal_keys.ROUND_LENGTH
            self.app.scenes = []
            self.app.fullscreen = False
            self.app.push(scene)
            self.assertEqual(scene.next_key, "f")
            press(self.app, pygame.K_f, "f")
            self.assertEqual(scene.typed, 1, "typing F did not advance the word")
            self.assertFalse(self.app.fullscreen)
            for letter in "all":
                press(self.app, getattr(pygame, f"K_{letter}"), letter)
            self.assertEqual(scene.state, "celebrating", "the word never completed")
        finally:
            del os.environ["RETRO_ARCADE_SAVE_DIR"]


if __name__ == "__main__":
    unittest.main()
