"""Checks on the age system, the harder maths, and the reasoning puzzles.

The one that matters most is ambiguity. A reasoning item with two defensible
answers marks a thinking child wrong, which is worse than no puzzle at all,
so odd-one-out is checked for exactly one unique figure and every item type
is checked for a single correct option.

Run with:  python3 -m unittest discover tests
"""

import os
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from games import logic_lab, math_blaster  # noqa: E402
from retro import levels  # noqa: E402

REPEATS = 200
TIERS = (1, 2, 3, 4)


class TestAgeTiers(unittest.TestCase):
    def test_every_playable_age_maps_to_a_tier(self):
        for age in range(levels.MIN_AGE, levels.MAX_AGE + 1):
            tier = levels.tier_for_age(age)
            self.assertIn(tier, TIERS, age)

    def test_tiers_never_go_backwards_with_age(self):
        previous = 0
        for age in range(levels.MIN_AGE, levels.MAX_AGE + 1):
            tier = levels.tier_for_age(age)
            self.assertGreaterEqual(tier, previous, age)
            previous = tier

    def test_an_eight_year_old_gets_times_tables_and_stories(self):
        """The whole point of asking the age."""
        tier = levels.tier_for_age(8)
        modes = math_blaster.MODES_BY_TIER[tier]
        for expected in ("multiply", "divide", "word"):
            self.assertIn(expected, modes)
        self.assertNotIn("count", modes, "counting ducks is not for an eight-year-old")

    def test_a_five_year_old_is_not_given_division(self):
        modes = math_blaster.MODES_BY_TIER[levels.tier_for_age(5)]
        for too_hard in ("multiply", "divide", "word"):
            self.assertNotIn(too_hard, modes)
        self.assertIn("count", modes)

    def test_unknown_age_falls_back_to_the_middle(self):
        self.assertEqual(levels.tier_for_age(None), levels.DEFAULT_TIER)
        self.assertEqual(levels.tier_for_age("nonsense"), levels.DEFAULT_TIER)

    def test_nudges_stay_inside_the_tier_range(self):
        for age in range(levels.MIN_AGE, levels.MAX_AGE + 1):
            for nudge in (-3, -1, 0, 1, 3):
                tier = levels.tier_for(age, nudge)
                self.assertGreaterEqual(tier, levels.MIN_TIER)
                self.assertLessEqual(tier, levels.MAX_TIER)

    def test_every_tier_offers_at_most_six_modes(self):
        """The menu is a three by two grid."""
        for tier in TIERS:
            self.assertLessEqual(len(math_blaster.MODES_BY_TIER[tier]), 6)
            for mode in math_blaster.MODES_BY_TIER[tier]:
                self.assertIn(mode, math_blaster.MODES)


class TestHarderMaths(unittest.TestCase):
    def _all_questions(self, tier):
        for mode in math_blaster.MODES_BY_TIER[tier]:
            for _ in range(REPEATS // 4):
                yield mode, math_blaster.make_question(mode, tier, "Juni")

    def test_answers_are_offered_and_choices_distinct(self):
        for tier in TIERS:
            for mode, question in self._all_questions(tier):
                self.assertIn(question["answer"], question["choices"], mode)
                self.assertEqual(
                    len(question["choices"]), len(set(question["choices"])), mode
                )

    def test_nothing_is_negative(self):
        for tier in TIERS:
            for mode, question in self._all_questions(tier):
                self.assertGreaterEqual(question["answer"], 0, mode)
                for choice in question["choices"]:
                    self.assertGreaterEqual(choice, 0, mode)

    def test_division_is_always_exact(self):
        for tier in TIERS:
            for _ in range(REPEATS):
                question = math_blaster.make_question("divide", tier)
                left, right = question["prompt"].split(" = ")[0].split(" / ")
                self.assertEqual(int(left) % int(right), 0, question["prompt"])
                self.assertEqual(int(left) // int(right), question["answer"])

    def test_multiplication_matches_its_prompt(self):
        for tier in TIERS:
            for _ in range(REPEATS):
                question = math_blaster.make_question("multiply", tier)
                left, right = question["prompt"].split(" = ")[0].split(" x ")
                self.assertEqual(int(left) * int(right), question["answer"])

    def test_multiplication_gets_harder_with_tier(self):
        def biggest(tier):
            return max(
                math_blaster.make_question("multiply", tier)["answer"]
                for _ in range(REPEATS)
            )

        self.assertLess(biggest(2), biggest(3))
        self.assertLess(biggest(3), biggest(4))

    def test_story_problems_use_the_players_name(self):
        for tier in (2, 3, 4):
            for _ in range(50):
                question = math_blaster.make_question("word", tier, "Juni")
                self.assertIn("JUNI", question["prompt"])
                self.assertTrue(question["prompt"].endswith("?"))

    def test_story_problems_avoid_gendered_pronouns(self):
        """The game does not know a child's pronouns, so it uses none."""
        banned = (" HE ", " SHE ", " HIS ", " HER ", " HIM ")
        for tier in (2, 3, 4):
            for _ in range(80):
                prompt = f" {math_blaster.make_question('word', tier, 'Juni')['prompt']} "
                for word in banned:
                    self.assertNotIn(word, prompt, prompt)

    def test_story_answers_are_whole_and_positive(self):
        for tier in (2, 3, 4):
            for _ in range(REPEATS):
                question = math_blaster.make_question("word", tier, "Juni")
                self.assertIsInstance(question["answer"], int)
                self.assertGreaterEqual(question["answer"], 0, question["prompt"])


class TestReasoningItems(unittest.TestCase):
    def test_answer_index_points_at_a_real_option(self):
        for tier in TIERS:
            for mode in logic_lab.MODES_BY_TIER[tier]:
                for _ in range(REPEATS // 2):
                    item = logic_lab.make_question(mode, tier)
                    self.assertTrue(0 <= item["answer"] < len(item["options"]), mode)

    def test_answer_choices_are_all_different(self):
        """Two identical choices would mean two correct answers.

        Odd-one-out is excluded on purpose: there the four figures are the
        puzzle, not a list of choices, and three identical circles beside one
        square is a perfectly good item. Its own uniqueness rule is checked
        by test_odd_one_out_has_exactly_one_odd_figure.
        """
        for tier in TIERS:
            for mode in logic_lab.MODES_BY_TIER[tier]:
                if mode == "odd":
                    continue
                for _ in range(REPEATS // 2):
                    options = logic_lab.make_question(mode, tier)["options"]
                    self.assertEqual(len(options), len(set(map(str, options))), mode)

    def test_odd_one_out_answer_figure_appears_once(self):
        """Duplicates are allowed, but never of the odd figure itself."""
        for tier in TIERS:
            for _ in range(REPEATS):
                item = logic_lab.make_question("odd", tier)
                answer = item["options"][item["answer"]]
                self.assertEqual(item["options"].count(answer), 1, item["options"])

    def test_odd_one_out_has_exactly_one_odd_figure(self):
        """No second figure may be uniquely different in any property."""
        for tier in TIERS:
            for _ in range(REPEATS):
                item = logic_lab.make_question("odd", tier)
                options = item["options"]
                unique_by = []
                for attribute in range(3):  # shape, colour, size
                    counts = Counter(figure[attribute] for figure in options)
                    singles = [
                        index
                        for index, figure in enumerate(options)
                        if counts[figure[attribute]] == 1
                    ]
                    unique_by.extend(singles)
                self.assertTrue(unique_by, "no figure stands out at all")
                self.assertEqual(
                    set(unique_by),
                    {item["answer"]},
                    f"more than one defensible answer in {options}",
                )

    def test_matrix_answer_follows_row_and_column(self):
        for tier in TIERS:
            for _ in range(REPEATS):
                item = logic_lab.make_question("matrix", tier)
                grid, size = item["grid"], item["size"]
                answer = item["options"][item["answer"]]
                # Shape comes from the last row, colour from the last column.
                self.assertEqual(answer[0], grid[size - 1][0][0])
                self.assertEqual(answer[1], grid[0][size - 1][1])

    def test_matrix_grid_is_consistent(self):
        for _ in range(REPEATS):
            item = logic_lab.make_question("matrix", 3)
            grid = item["grid"]
            for row in grid:
                self.assertEqual(len({figure[0] for figure in row}), 1, "row shape varies")
            for column in range(item["size"]):
                colors = {grid[row][column][1] for row in range(item["size"])}
                self.assertEqual(len(colors), 1, "column colour varies")

    def test_analogy_repeats_the_first_pairs_change(self):
        for tier in (2, 3, 4):
            for _ in range(REPEATS):
                item = logic_lab.make_question("analogy", tier)
                (a, b), (c, d) = item["rows"]
                answer = item["options"][item["answer"]]
                self.assertEqual(answer, d)
                # Whatever changed from a to b must change the same way c to d.
                for attribute in range(3):
                    changed_first = a[attribute] != b[attribute]
                    changed_second = c[attribute] != d[attribute]
                    self.assertEqual(changed_first, changed_second, item)

    def test_sequences_are_consistent_and_positive(self):
        for tier in (2, 3, 4):
            for _ in range(REPEATS):
                item = logic_lab.make_question("sequence", tier)
                series = list(item["items"]) + [item["options"][item["answer"]]]
                for value in series:
                    self.assertGreaterEqual(value, 0, item["rule"])
                self.assertEqual(len(item["items"]), 5)
                self._assert_rule_holds(item["rule"], series)

    def _assert_rule_holds(self, rule, series):
        if rule == "add":
            steps = {b - a for a, b in zip(series, series[1:])}
            self.assertEqual(len(steps), 1, series)
        elif rule in ("double", "multiply"):
            ratios = {b // a for a, b in zip(series, series[1:]) if a}
            self.assertEqual(len(ratios), 1, series)
        elif rule == "fibonacci":
            for i in range(2, len(series)):
                self.assertEqual(series[i], series[i - 1] + series[i - 2], series)
        elif rule == "alternate":
            steps = [b - a for a, b in zip(series, series[1:])]
            self.assertEqual(steps[0::2], steps[0::2][:1] * len(steps[0::2]), series)
            self.assertEqual(steps[1::2], steps[1::2][:1] * len(steps[1::2]), series)

    def test_sequence_options_are_numbers(self):
        for _ in range(REPEATS):
            item = logic_lab.make_question("sequence", 3)
            for option in item["options"]:
                self.assertIsInstance(option, int)


if __name__ == "__main__":
    unittest.main()
