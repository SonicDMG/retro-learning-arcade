"""Pattern Power -- what comes next?

Sequencing is one of the big early-primary skills, and it sits underneath
both counting and reading. Three modes: repeating picture patterns, repeating
colour patterns, and number sequences that step up or down.
"""

import random

import pygame

from retro import palette, sfx, sprites, ui
from retro.app import Scene
from retro.results import ResultsScene

GAME_KEY = "patterns"
ROUND_LENGTH = 8
SHOWN = 5  # Visible items before the "?" tile.

MODES = [
    ("picture", "PICTURES", "duck", palette.GREEN),
    ("color", "COLOURS", "ball", palette.MAGENTA),
    ("number", "NUMBERS", "star", palette.CYAN),
]

PATTERN_SPRITES = ["star", "apple", "fish", "duck", "cake", "ball", "moon", "frog"]
# Deliberately no purple here: next to magenta it is a coin flip for a
# five-year-old, and the pattern should be the puzzle, not the colour naming.
PATTERN_COLORS = [
    palette.CYAN,
    palette.MAGENTA,
    palette.YELLOW,
    palette.GREEN,
    palette.ORANGE,
]

# Repeating units, written as indexes into a small set of picked items.
UNITS = [
    (0, 1),           # AB
    (0, 1),           # AB again, so the easiest shape stays common
    (0, 0, 1),        # AAB
    (0, 1, 1),        # ABB
    (0, 1, 2),        # ABC
]


def _repeating_question(pool, kind):
    """Build a repeating pattern out of items drawn from pool."""
    unit = random.choice(UNITS)
    needed = max(unit) + 1
    items = random.sample(pool, needed)
    sequence = [items[unit[i % len(unit)]] for i in range(SHOWN + 1)]
    answer = sequence[SHOWN]

    # Distractors: other items from the pattern, then unused ones.
    others = [item for item in items if item != answer]
    spare = [item for item in pool if item not in items]
    random.shuffle(spare)
    choices = [answer] + (others + spare)[:2]
    return {
        "kind": kind,
        "items": sequence[:SHOWN],
        "answer": answer,
        "choices": choices,
    }


def make_question(mode):
    if mode == "picture":
        question = _repeating_question(PATTERN_SPRITES, "picture")
    elif mode == "color":
        question = _repeating_question(PATTERN_COLORS, "color")
    else:
        step = random.choice([1, 1, 2, 2, 5, 10])
        going_up = random.random() < 0.7
        if going_up:
            start = random.randint(0, 10)
        else:
            # Only count down from high enough that we never go negative.
            start = random.randint(SHOWN * step, SHOWN * step + 10)
            step = -step
        sequence = [start + step * i for i in range(SHOWN + 1)]
        answer = sequence[SHOWN]
        distractors = {answer + abs(step), answer - abs(step), answer + 1}
        distractors.discard(answer)
        pool = [value for value in distractors if value >= 0]
        random.shuffle(pool)
        while len(pool) < 2:
            candidate = answer + random.randint(1, 4)
            if candidate not in pool and candidate != answer:
                pool.append(candidate)
        question = {
            "kind": "number",
            "items": sequence[:SHOWN],
            "answer": answer,
            "choices": [answer] + pool[:2],
        }

    random.shuffle(question["choices"])
    return question


def _layout(count):
    margin, gap, top, height = 28, 10, 126, 38
    total = 320 - margin * 2
    width = (total - gap * (count - 1)) // count
    return [
        pygame.Rect(margin + index * (width + gap), top, width, height)
        for index in range(count)
    ]


class PatternRoundScene(Scene):
    """One round of "what comes next?"."""

    def __init__(self, app, player, mode):
        super().__init__(app)
        self.player = player
        self.mode = mode
        self.mode_label = next(label for key, label, _, _ in MODES if key == mode)
        self.accent = next(color for key, _, _, color in MODES if key == mode)
        self.index = 0
        self.correct = 0
        self.attempts = 0
        self.question = None
        self.buttons = []
        self.state = "asking"
        self.state_timer = 0.0
        self.time = 0.0
        self.feedback = ""
        self.reveal = False  # Show the answer in the "?" slot once solved.
        self.particles = ui.Particles()
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)
        self.hint = ui.HintTimer(10.0)

    def on_enter(self):
        if self.question is None:
            self._next_question()

    def _next_question(self):
        if self.index >= ROUND_LENGTH:
            self._finish()
            return
        self.index += 1
        self.question = make_question(self.mode)
        self.attempts = 0
        self.state = "asking"
        self.feedback = ""
        self.reveal = False
        self.hint.reset()
        self.buttons = []
        for slot, (rect, value) in enumerate(
            zip(_layout(len(self.question["choices"])), self.question["choices"])
        ):
            kind = self.question["kind"]
            self.buttons.append(
                ui.Button(
                    rect,
                    "" if kind != "number" else str(value),
                    value if kind == "color" else palette.ACCENTS[slot % len(palette.ACCENTS)],
                    sprite=value if kind == "picture" else None,
                    sprite_scale=2,
                    hotkey=str(slot + 1),
                    text_size=30,
                    value=value,
                    solid=kind == "color",
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
                lambda app: app.replace(PatternRoundScene(app, self.player, self.mode)),
            )
        )

    def _answer(self, button):
        if self.state != "asking" or button.locked:
            return
        if button.value == self.question["answer"]:
            if self.attempts == 0:
                self.correct += 1
            self.state = "celebrating"
            self.state_timer = 1.2
            self.reveal = True
            button.set_flash(palette.GREEN, 1.2)
            self.particles.burst(button.rect.center, palette.GREEN, count=16, speed=80)
            self.feedback = random.choice(["YES!", "THAT'S IT!", "CLEVER!"])
            sfx.play("correct")
        else:
            self.attempts += 1
            button.locked = True
            button.enabled = False
            button.set_flash(palette.RED, 0.4)
            self.feedback = "TRY AGAIN!"
            sfx.play("wrong")
            if self.attempts >= 2:
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
        if self.state == "celebrating":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._next_question()

    # -- drawing ----------------------------------------------------------

    def _draw_cell(self, surface, rect, value, kind, active=False):
        border = palette.YELLOW if active else self.accent
        fill = palette.dim(palette.YELLOW, 0.2) if active else palette.BG_PANEL
        pygame.draw.rect(surface, fill, rect)
        pygame.draw.rect(surface, border, rect, 1)
        if value is None:
            ui.text(surface, "?", (rect.centerx, rect.y + 4), palette.YELLOW, 34, align="center")
        elif kind == "picture":
            image = sprites.get(value, 2)
            surface.blit(image, image.get_rect(center=rect.center))
        elif kind == "color":
            pygame.draw.rect(surface, value, rect.inflate(-8, -8))
        else:
            ui.text(surface, str(value), (rect.centerx, rect.y + 8), palette.WHITE, 24, align="center")

    def _draw_pattern(self, surface):
        question = self.question
        count = SHOWN + 1
        cell = 44 if question["kind"] == "number" else 40
        width = cell - 4
        start_x = 160 - (count * cell) // 2
        y = 52
        for i in range(count):
            rect = pygame.Rect(start_x + i * cell, y, width, 40)
            if i < SHOWN:
                self._draw_cell(surface, rect, question["items"][i], question["kind"])
            else:
                value = question["answer"] if self.reveal else None
                self._draw_cell(surface, rect, value, question["kind"], active=not self.reveal)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        ui.text(surface, self.mode_label, (4, 3), self.accent, 14)
        ui.text(
            surface, f"{self.index}/{ROUND_LENGTH}", (316, 3), palette.WHITE, 14, align="right"
        )
        ui.bar(surface, (4, 16, 312, 3), (self.index - 1) / ROUND_LENGTH, self.accent)
        ui.text(surface, "WHAT COMES NEXT?", (160, 26), palette.WHITE, 20, align="center")

        if self.question:
            self._draw_pattern(surface)
        for button in self.buttons:
            button.draw(surface)
        self.particles.draw(surface)

        if self.feedback:
            color = palette.GREEN if self.state == "celebrating" else palette.ORANGE
            ui.text(surface, self.feedback, (160, 112), color, 16, align="center")
        elif self.hint.ready and self.state == "asking":
            ui.text(surface, "LOOK FOR THE REPEAT...", (160, 112), palette.GRAY, 14, align="center")
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


class PatternMenuScene(Scene):
    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)
        self.buttons = [
            ui.Button(
                (28 + index * 92, 60, 84, 60),
                label,
                color,
                sprite=sprite,
                hotkey=str(index + 1),
                text_size=13,
                value=key,
            )
            for index, (key, label, sprite, color) in enumerate(MODES)
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            for index, key in enumerate((pygame.K_1, pygame.K_2, pygame.K_3)):
                if event.key == key:
                    self._start(MODES[index][0])
                    return
        for button in self.buttons:
            if button.handle_event(event):
                self._start(button.value)
                return

    def _start(self, mode):
        sfx.play("select")
        self.app.push(PatternRoundScene(self.app, self.player, mode))

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        for button in self.buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface, "PATTERN POWER", (160, int(10 + wobble)), palette.GREEN, 30, align="center"
        )
        ui.text(surface, "PICK A GAME", (160, 42), palette.WHITE, 16, align="center")
        ui.star_counter(surface, self.player.stars, (4, 2))
        for button in self.buttons:
            button.draw(surface)
        ui.text(surface, "ESC = BACK", (316, 168), palette.DARK_GRAY, 12, align="right")


def launch(app, player):
    app.push(PatternMenuScene(app, player))
