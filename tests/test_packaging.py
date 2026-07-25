"""Checks on how the game installs and where it keeps a child's progress.

These exist because packaging bugs are quiet: the game still starts, and the
only symptom is that stars vanish between sessions.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    tomllib = None


def load_pyproject():
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as handle:
        return tomllib.load(handle)


@unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
class TestProjectMetadata(unittest.TestCase):
    def test_entry_point_resolves_to_a_real_function(self):
        scripts = load_pyproject()["project"]["scripts"]
        target = scripts["retro-arcade"]
        self.assertEqual(target, "launcher:main")
        module_name, function_name = target.split(":")
        module = __import__(module_name)
        self.assertTrue(callable(getattr(module, function_name)))

    def test_wheel_ships_every_module_the_game_imports(self):
        included = load_pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"][
            "only-include"
        ]
        for needed in ("retro", "games", "launcher.py"):
            self.assertIn(needed, included)

    def test_declared_dependency_matches_requirements_txt(self):
        """requirements.txt is the no-uv fallback; the two must not drift."""
        declared = load_pyproject()["project"]["dependencies"]
        with open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8") as handle:
            fallback = [
                line.strip()
                for line in handle
                if line.strip() and not line.startswith("#")
            ]
        self.assertEqual(sorted(declared), sorted(fallback))


class TestSaveLocation(unittest.TestCase):
    def test_a_checkout_saves_next_to_the_code(self):
        from retro import progress

        # This test run is itself a checkout, so the marker logic should fire.
        self.assertEqual(progress._default_save_dir(), os.path.join(ROOT, "saves"))

    def test_an_installed_copy_never_writes_into_site_packages(self):
        """Simulate an install by pointing the lookup at a marker-free dir."""
        import retro.progress as progress

        fake_site_packages = os.path.join(ROOT, "tests")  # no pyproject.toml, no .git
        original = progress.__file__
        try:
            progress.__file__ = os.path.join(fake_site_packages, "retro", "progress.py")
            resolved = progress._default_save_dir()
        finally:
            progress.__file__ = original
        self.assertNotIn("site-packages", resolved)
        self.assertNotEqual(resolved, os.path.join(ROOT, "saves"))
        self.assertTrue(os.path.isabs(resolved))

    def test_environment_variable_wins(self):
        # SAVE_DIR is read at import time, so check the mechanism directly.
        import importlib

        import retro.progress as progress

        os.environ["RETRO_ARCADE_SAVE_DIR"] = "/tmp/retro-arcade-test-save"
        try:
            reloaded = importlib.reload(progress)
            self.assertEqual(reloaded.SAVE_DIR, "/tmp/retro-arcade-test-save")
            self.assertTrue(reloaded.SAVE_PATH.endswith("progress.json"))
        finally:
            del os.environ["RETRO_ARCADE_SAVE_DIR"]
            importlib.reload(progress)


if __name__ == "__main__":
    unittest.main()
