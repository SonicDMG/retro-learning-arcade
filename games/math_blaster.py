"""Number Blaster -- a space-themed maths game for early primary kids.

Four modes (count, add, subtract, compare) across three difficulty levels.
Rounds are ten questions long, wrong answers cost nothing but a retry, and a
star is earned for every question answered correctly on the first try.
"""

import random

import pygame

from retro import palette, sfx, sprites, ui
from retro.app import Scene
from retro.results import ResultsScene

GAME_KEY = "math"
ROUND_LENGTH = 10

MODES = [
    ("count", "COUNT", "duck", palette.YELLOW),
    ("add", "ADD +", "rocket", palette.GREEN),
    ("sub", "TAKE AWAY -", "star", palette.MAGENTA),
    ("compare", "MORE OR LESS", "fish", palette.CYAN),
]

COUNTABLE = ["duck", "star", "apple", "fish", "cat", "frog", "ball", "cake"]

# Per-difficulty numeric ranges, keyed by mode.
LIMITS = {
    "count": {1: (1, 5), 2: (1, 10), 3: (5, 15)},
    "add": {1: (1, 5), 2: (1, 10), 3: (2, 12)},
    "sub": {1: (1, 5), 2: (1, 10), 3: (1, 20)},
    "compare": {1: (1, 10), 2: (1, 20), 3: (10, 50)},
}
ADD_CAP = {1: 10, 2: 15, 3: 20}


def _distractors(answer, low, high, count=2):
    """Plausible wrong answers: near misses first, then anything in range."""
    options = set()
    near = [answer + delta for delta in (-2, -1, 1, 2, 3, -3)]
    for value in near:
        if value >= 0 and value != answer:
            options.add(value)
    pool = [value for value in options if low - 2 <= value <= high + 3]
    random.shuffle(pool)
    chosen = pool[:count]
    guard = 0
    while len(chosen) < count and guard < 50:
        guard += 1
        value = random.randint(max(0, low - 1), high + 2)
        if value != answer and value not in chosen:
            chosen.append(value)
    return chosen


def make_question(mode, difficulty):
    """Build one question dictionary for the given mode and difficulty."""
    low, high = LIMITS[mode][difficulty]

    if mode == "count":
        total = random.randint(low, high)
        question = {
            "kind": "count",
            "prompt": "HOW MANY?",
            "sprite": random.choice(COUNTABLE),
            "count": total,
            "answer": total,
        }
        question["choices"] = [total] + _distractors(total, low, high)

    elif mode == "add":
        cap = ADD_CAP[difficulty]
        first = random.randint(low, high)
        second = random.randint(low, max(low, min(high, cap - first)))
        total = first + second
        question = {
            "kind": "expr",
            "prompt": f"{first} + {second} = ?",
            "answer": total,
        }
        question["choices"] = [total] + _distractors(total, low, cap)

    elif mode == "sub":
        first = random.randint(max(2, low), high)
        second = random.randint(0, first)
        result = first - second
        question = {
            "kind": "expr",
            "prompt": f"{first} - {second} = ?",
            "answer": result,
        }
        question["choices"] = [result] + _distractors(result, 0, high)

    else:  # compare
        first = random.randint(low, high)
        second = random.randint(low, high)
        while second == first:
            second = random.randint(low, high)
        want_more = random.random() < 0.5
        answer = max(first, second) if want_more else min(first, second)
        question = {
            "kind": "compare",
            "prompt": "WHICH IS MORE?" if want_more else "WHICH IS LESS?",
            "answer": answer,
            "choices": [first, second],
        }

    random.shuffle(question["choices"])
    return question


def _layout(count):
    """Evenly spaced answer buttons along the bottom of the screen."""
    margin, gap, top, height = 14, 8, 126, 38
    total = 320 - margin * 2
    width = (total - gap * (count - 1)) // count
    return [
        pygame.Rect(margin + index * (width + gap), top, width, height)
        for index in range(count)
    ]


class MathRoundScene(Scene):
    """Ten questions of one mode at one difficulty."""

    def __init__(self, app, player, mode, difficulty):
        super().__init__(app)
        self.player = player
        self.mode = mode
        self.difficulty = difficulty
        self.mode_label = next(label for key, label, _, _ in MODES if key == mode)
        self.accent = next(color for key, _, _, color in MODES if key == mode)
        self.index = 0
        self.correct = 0
        self.streak = 0
        self.question = None
        self.buttons = []
        self.attempts = 0
        self.state = "asking"     # asking -> celebrating -> next question
        self.state_timer = 0.0
        self.time = 0.0
        self.particles = ui.Particles()
        self.starfield = ui.Starfield(320, 180, count=50, speed=10)
        self.hint = ui.HintTimer(9.0)
        self.rocket = None
        self.feedback = ""

    def on_enter(self):
        if self.question is None:
            self._next_question()

    # -- question flow ----------------------------------------------------

    def _next_question(self):
        if self.index >= ROUND_LENGTH:
            self._finish()
            return
        self.index += 1
        self.question = make_question(self.mode, self.difficulty)
        self.attempts = 0
        self.state = "asking"
        self.feedback = ""
        self.hint.reset()
        rects = _layout(len(self.question["choices"]))
        self.buttons = []
        for slot, (rect, value) in enumerate(zip(rects, self.question["choices"])):
            self.buttons.append(
                ui.Button(
                    rect,
                    str(value),
                    palette.ACCENTS[slot % len(palette.ACCENTS)],
                    hotkey=str(slot + 1),
                    text_size=30,
                    value=value,
                )
            )

    def _finish(self):
        self.app.replace(
            ResultsScene(
                self.app,
                self.player,
                f"{GAME_KEY}_{self.mode}",
                self.mode_label,
                self.correct,
                ROUND_LENGTH,
                lambda app: app.replace(
                    MathRoundScene(app, self.player, self.mode, self.difficulty)
                ),
            )
        )

    def _answer(self, button):
        if self.state != "asking" or button.locked:
            return
        if button.value == self.question["answer"]:
            if self.attempts == 0:
                self.correct += 1
                self.streak += 1
            self.state = "celebrating"
            self.state_timer = 1.1
            button.set_flash(palette.GREEN, 1.1)
            self.particles.burst(button.rect.center, palette.GREEN, count=18, speed=90)
            self.rocket = [button.rect.centerx, button.rect.top, -150.0]
            self.feedback = random.choice(["YES!", "NICE!", "WOW!", "GOT IT!"])
            sfx.play("correct")
            # Every third in a row gets a flourish instead of the usual rocket,
            # so a streak is something you hear and not just a label.
            sfx.play("star" if self.streak and self.streak % 3 == 0 else "launch")
        else:
            self.attempts += 1
            self.streak = 0
            button.locked = True
            button.enabled = False
            button.set_flash(palette.RED, 0.4)
            self.feedback = "TRY AGAIN!"
            sfx.play("wrong")
            self.hint.reset()
            if self.attempts >= 2:
                # Two misses is enough struggle: point at the right answer.
                for candidate in self.buttons:
                    if candidate.value == self.question["answer"]:
                        candidate.set_flash(palette.YELLOW, 9.0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            if self.state == "asking":
                for index, key in enumerate((pygame.K_1, pygame.K_2, pygame.K_3)):
                    if event.key == key and index < len(self.buttons):
                        self._answer(self.buttons[index])
                        return
        if self.state == "asking":
            for button in self.buttons:
                if button.handle_event(event):
                    self._answer(button)
                    return

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        self.particles.update(dt)
        for button in self.buttons:
            button.update(dt)
        if self.state == "asking":
            self.hint.update(dt)
        if self.rocket:
            self.rocket[1] += self.rocket[2] * dt
            self.particles.burst(
                (self.rocket[0], self.rocket[1] + 14),
                palette.ORANGE,
                count=2,
                speed=25,
                life=0.35,
                gravity=10,
            )
            if self.rocket[1] < -20:
                self.rocket = None
        if self.state == "celebrating":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._next_question()

    # -- drawing ----------------------------------------------------------

    def _draw_question(self, surface):
        area = pygame.Rect(14, 26, 292, 84)
        ui.panel(surface, area, palette.BG_PANEL, self.accent)
        question = self.question
        if question["kind"] == "count":
            ui.text(surface, question["prompt"], (160, area.y + 5), palette.WHITE, 18, align="center")
            total = question["count"]
            columns = 5
            rows = (total + columns - 1) // columns
            start_y = area.y + 22 + max(0, (62 - rows * 19) // 2)
            for i in range(total):
                row, column = divmod(i, columns)
                in_row = min(columns, total - row * columns)
                x = 160 - in_row * 18 // 2 + column * 18
                bob = ui.title_wobble(self.time + i * 0.4, 1.0, 3.0)
                sprites.draw(surface, question["sprite"], (x, int(start_y + row * 19 + bob)))
        elif question["kind"] == "compare":
            ui.text(surface, question["prompt"], (160, area.y + 8), palette.WHITE, 22, align="center")
            ui.text(
                surface,
                "PICK THE NUMBER BELOW",
                (160, area.y + 60),
                palette.GRAY,
                14,
                align="center",
            )
        else:
            bob = ui.title_wobble(self.time, 1.5, 2.0)
            ui.text(
                surface,
                question["prompt"],
                (160, int(area.y + 26 + bob)),
                palette.WHITE,
                46,
                align="center",
            )

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)

        ui.text(surface, f"{self.mode_label}", (4, 3), self.accent, 14)
        ui.text(
            surface,
            f"{self.index}/{ROUND_LENGTH}",
            (316, 3),
            palette.WHITE,
            14,
            align="right",
        )
        ui.bar(surface, (4, 16, 312, 3), (self.index - 1) / ROUND_LENGTH, self.accent)

        if self.question:
            self._draw_question(surface)
        for button in self.buttons:
            button.draw(surface)

        if self.rocket:
            sprites.draw(
                surface, "rocket", (int(self.rocket[0]), int(self.rocket[1])), center=True
            )
        self.particles.draw(surface)

        if self.feedback:
            color = palette.GREEN if self.state == "celebrating" else palette.ORANGE
            ui.text(surface, self.feedback, (160, 112), color, 16, align="center")
        elif self.hint.ready and self.state == "asking":
            ui.text(
                surface,
                "TAKE YOUR TIME...",
                (160, 112),
                palette.GRAY,
                14,
                align="center",
            )
        if self.streak >= 3 and self.state == "asking":
            ui.text(surface, f"STREAK {self.streak}!", (4, 166), palette.YELLOW, 14)
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


class MathMenuScene(Scene):
    """Pick a mode and a difficulty, then play."""

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.difficulty = 1
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)
        self.mode_buttons = []
        for index, (key, label, sprite, color) in enumerate(MODES):
            column, row = index % 2, index // 2
            rect = pygame.Rect(24 + column * 144, 34 + row * 54, 128, 50)
            self.mode_buttons.append(
                ui.Button(
                    rect, label, color, sprite=sprite, hotkey=str(index + 1), text_size=14, value=key
                )
            )
        # The difficulty row shares a line with its label to save vertical space.
        self.difficulty_buttons = [
            ui.Button((104 + index * 56, 146, 50, 22), label, palette.PURPLE, text_size=14, value=index + 1)
            for index, label in enumerate(("EASY", "OK", "HARD"))
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            for index, key in enumerate(
                (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
            ):
                if event.key == key:
                    self._start(MODES[index][0])
                    return
        for button in self.mode_buttons:
            if button.handle_event(event):
                self._start(button.value)
                return
        for button in self.difficulty_buttons:
            if button.handle_event(event):
                self.difficulty = button.value
                sfx.play("click")
                return

    def _start(self, mode):
        sfx.play("select")
        self.app.push(MathRoundScene(self.app, self.player, mode, self.difficulty))

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        for button in self.mode_buttons + self.difficulty_buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface,
            "NUMBER BLASTER",
            (160, int(8 + wobble)),
            palette.YELLOW,
            30,
            align="center",
        )
        ui.star_counter(surface, self.player.stars, (4, 2))
        ui.text(surface, "ESC = BACK", (316, 4), palette.DARK_GRAY, 12, align="right")
        for button in self.mode_buttons:
            button.draw(surface)
        ui.text(surface, "HOW HARD?", (10, 152), palette.WHITE, 14)
        for button in self.difficulty_buttons:
            button.color = palette.YELLOW if button.value == self.difficulty else palette.PURPLE
            button.draw(surface)


def launch(app, player):
    app.push(MathMenuScene(app, player))
