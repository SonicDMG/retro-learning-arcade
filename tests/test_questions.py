"""Checks on the question generators.

The maths here decides what a six-year-old sees, so the ranges matter: no
negative answers, no sums past the level cap, and the right answer must
always actually be among the choices.

Run with:  python3 -m unittest discover tests
"""

import os
import string
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The games import pygame for their scenes; a dummy driver keeps this headless.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from games import crystal_keys, math_blaster, pattern_power, word_rocket  # noqa: E402
from retro import sprites  # noqa: E402

REPEATS = 400


class TestMathQuestions(unittest.TestCase):
    def test_answer_is_always_offered(self):
        for mode in ("count", "add", "sub", "compare"):
            for difficulty in (1, 2, 3):
                for _ in range(REPEATS):
                    question = math_blaster.make_question(mode, difficulty)
                    self.assertIn(
                        question["answer"],
                        question["choices"],
                        f"{mode} d{difficulty}: {question}",
                    )

    def test_choices_are_distinct(self):
        for mode in ("count", "add", "sub", "compare"):
            for difficulty in (1, 2, 3):
                for _ in range(REPEATS):
                    choices = math_blaster.make_question(mode, difficulty)["choices"]
                    self.assertEqual(len(choices), len(set(choices)), choices)

    def test_no_negative_choices(self):
        for mode in ("count", "add", "sub", "compare"):
            for difficulty in (1, 2, 3):
                for _ in range(REPEATS):
                    for value in math_blaster.make_question(mode, difficulty)["choices"]:
                        self.assertGreaterEqual(value, 0)

    def test_addition_respects_the_level_cap(self):
        for difficulty, cap in math_blaster.ADD_CAP.items():
            for _ in range(REPEATS):
                question = math_blaster.make_question("add", difficulty)
                self.assertLessEqual(question["answer"], cap, question["prompt"])

    def test_subtraction_never_goes_below_zero(self):
        for difficulty in (1, 2, 3):
            for _ in range(REPEATS):
                question = math_blaster.make_question("sub", difficulty)
                self.assertGreaterEqual(question["answer"], 0, question["prompt"])

    def test_counting_matches_the_pictures_shown(self):
        for difficulty in (1, 2, 3):
            low, high = math_blaster.LIMITS["count"][difficulty]
            for _ in range(REPEATS):
                question = math_blaster.make_question("count", difficulty)
                self.assertEqual(question["count"], question["answer"])
                self.assertTrue(low <= question["count"] <= high)
                self.assertIn(question["sprite"], sprites.SPRITES)

    def test_compare_picks_the_right_extreme(self):
        for difficulty in (1, 2, 3):
            for _ in range(REPEATS):
                question = math_blaster.make_question("compare", difficulty)
                first, second = question["choices"]
                self.assertNotEqual(first, second)
                expected = (
                    max(first, second)
                    if question["prompt"] == "WHICH IS MORE?"
                    else min(first, second)
                )
                self.assertEqual(question["answer"], expected)


class TestWordQuestions(unittest.TestCase):
    def test_every_word_has_a_picture(self):
        for word, sprite in word_rocket.WORDS:
            self.assertIn(sprite, sprites.SPRITES, word)
            self.assertTrue(word.isalpha() and word.isupper(), word)

    def test_blanks_are_inside_the_word(self):
        for mode in ("first", "missing", "spell"):
            for _ in range(REPEATS):
                question = word_rocket.make_question(mode)
                for index in question["blanks"]:
                    self.assertTrue(0 <= index < len(question["word"]))
                if mode == "first":
                    self.assertEqual(question["blanks"], [0])
                if mode == "spell":
                    self.assertEqual(len(question["blanks"]), len(question["word"]))

    def test_letter_choices_contain_the_answer_once(self):
        for word, _ in word_rocket.WORDS:
            for index, letter in enumerate(word):
                choices = word_rocket._letter_choices(letter, word)
                self.assertEqual(len(choices), 3)
                self.assertEqual(len(set(choices)), 3, choices)
                self.assertIn(letter, choices)

    def test_spelling_walks_the_word_left_to_right(self):
        question = word_rocket.make_question("spell")
        for index, letter in enumerate(question["word"]):
            self.assertEqual(word_rocket._next_blank(question), index)
            question["filled"][index] = letter
        self.assertIsNone(word_rocket._next_blank(question))


class TestPatternQuestions(unittest.TestCase):
    def test_answer_is_offered_and_choices_are_distinct(self):
        for mode in ("picture", "color", "number"):
            for _ in range(REPEATS):
                question = pattern_power.make_question(mode)
                self.assertIn(question["answer"], question["choices"])
                self.assertEqual(len(question["choices"]), 3)
                self.assertEqual(len(set(map(str, question["choices"]))), 3, question)

    def test_sequence_length_is_stable(self):
        for mode in ("picture", "color", "number"):
            for _ in range(REPEATS):
                question = pattern_power.make_question(mode)
                self.assertEqual(len(question["items"]), pattern_power.SHOWN)

    def test_repeating_patterns_really_repeat(self):
        """The answer must continue the pattern the child can actually see."""
        for mode in ("picture", "color"):
            for _ in range(REPEATS):
                question = pattern_power.make_question(mode)
                full = list(question["items"]) + [question["answer"]]
                # Some unit length must tile the whole visible sequence.
                periods = [
                    size
                    for size in (2, 3)
                    if all(full[i] == full[i % size] for i in range(len(full)))
                ]
                self.assertTrue(periods, full)

    def test_number_sequences_step_evenly_and_stay_positive(self):
        for _ in range(REPEATS):
            question = pattern_power.make_question("number")
            items = list(question["items"]) + [question["answer"]]
            step = items[1] - items[0]
            self.assertNotEqual(step, 0)
            for earlier, later in zip(items, items[1:]):
                self.assertEqual(later - earlier, step, items)
            for value in items:
                self.assertGreaterEqual(value, 0, items)
            for value in question["choices"]:
                self.assertGreaterEqual(value, 0, question["choices"])

    def test_picture_patterns_use_real_sprites(self):
        for _ in range(REPEATS):
            question = pattern_power.make_question("picture")
            for name in list(question["items"]) + list(question["choices"]):
                self.assertIn(name, sprites.SPRITES)


class TestTypingLessons(unittest.TestCase):
    """The whole point of the element ladder is that keys arrive in order."""

    def test_lessons_only_use_keys_the_element_has_taught(self):
        for key, label, _, _, allowed in crystal_keys.ELEMENTS:
            for prompt in crystal_keys.LESSONS[key]:
                for letter in prompt:
                    self.assertIn(
                        letter,
                        allowed,
                        f"{label} lesson '{prompt}' needs '{letter}', which that "
                        "element has not introduced yet",
                    )

    def test_earth_is_strictly_home_row(self):
        for prompt in crystal_keys.LESSONS["earth"]:
            for letter in prompt:
                self.assertIn(letter, crystal_keys.HOME_ROW, prompt)

    def test_prompts_are_lowercase_letters_only(self):
        for lesson in crystal_keys.LESSONS.values():
            for prompt in lesson:
                self.assertTrue(prompt.isalpha(), prompt)
                self.assertEqual(prompt, prompt.lower(), prompt)

    def test_every_lesson_can_fill_a_round(self):
        for key, lesson in crystal_keys.LESSONS.items():
            self.assertGreaterEqual(len(lesson), crystal_keys.ROUND_LENGTH, key)
            self.assertEqual(len(lesson), len(set(lesson)), f"{key} has duplicates")

    def test_keyboard_shows_every_letter(self):
        on_screen = set("".join(crystal_keys.KEYBOARD_ROWS))
        self.assertEqual(on_screen, set(string.ascii_lowercase))

    def test_element_key_sets_only_widen(self):
        previous = set()
        for _, label, icon, _, allowed in crystal_keys.ELEMENTS:
            self.assertIn(icon, sprites.SPRITES, label)
            # Each realm must keep everything the previous one taught.
            self.assertTrue(previous <= set(allowed), label)
            previous = set(allowed)


class TestSpriteArt(unittest.TestCase):
    def test_grids_are_16_by_16(self):
        for name, data in sprites.SPRITES.items():
            self.assertEqual(len(data["rows"]), sprites.SIZE, name)
            for index, row in enumerate(data["rows"]):
                self.assertEqual(len(row), sprites.SIZE, f"{name} row {index}")

    def test_every_character_has_a_colour(self):
        for name, data in sprites.SPRITES.items():
            for index, row in enumerate(data["rows"]):
                for char in row:
                    if char != ".":
                        self.assertIn(char, data["key"], f"{name} row {index}: {char!r}")


if __name__ == "__main__":
    unittest.main()
