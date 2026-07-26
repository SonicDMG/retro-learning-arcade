"""Word Rocket -- picture-and-letter phonics practice.

A pixel-art picture appears, the word sits underneath with letters missing,
and the child picks letters from three big buttons. Three modes: the first
letter only, one missing letter anywhere, or spelling the whole word.
"""

import random
import string

import pygame

from retro import levels, palette, sfx, sprites, ui
from retro.app import Scene
from retro.results import ResultsScene

GAME_KEY = "words"
ROUND_LENGTH = 8

# Only words whose picture is unambiguous at 16x16.
WORDS = [
    ("CAT", "cat"),
    ("DOG", "dog"),
    ("SUN", "sun"),
    ("BUS", "bus"),
    ("STAR", "star"),
    ("FISH", "fish"),
    ("TREE", "tree"),
    ("MOON", "moon"),
    ("CAKE", "cake"),
    ("FROG", "frog"),
    ("DUCK", "duck"),
    ("BALL", "ball"),
    ("APPLE", "apple"),
    ("BOOK", "book"),
]

# "rocket" already has art (it's a mode icon below) but was never a playable
# word -- its six letters give the older tiers something longer to spell
# without needing new pixel art.
ROCKET_WORD = ("ROCKET", "rocket")

# The word pool a round is drawn from, and how many letters are blanked out
# in MISSING LETTER, and how many letter choices are offered. Tier 2 keeps
# the original, unfiltered word list and single blank/three choices exactly
# as it always was.
WORD_POOL_BY_TIER = {
    1: [word for word in WORDS if len(word[0]) <= 3],
    2: WORDS,
    3: [word for word in WORDS if len(word[0]) >= 4],
    4: [word for word in WORDS if len(word[0]) >= 4] + [ROCKET_WORD],
}
BLANKS_BY_TIER = {1: 1, 2: 1, 3: 2, 4: 3}
CHOICES_BY_TIER = {1: 3, 2: 3, 3: 4, 4: 4}

MODES = [
    ("first", "FIRST LETTER", "apple", palette.GREEN),
    ("missing", "MISSING LETTER", "book", palette.CYAN),
    ("spell", "SPELL IT!", "rocket", palette.MAGENTA),
]

VOWELS = "AEIOU"


def _letter_choices(answer, word, count=3):
    """The right letter plus lookalike distractors, shuffled."""
    # A vowel is easiest to confuse with another vowel, likewise consonants.
    pool = VOWELS if answer in VOWELS else "".join(
        c for c in string.ascii_uppercase if c not in VOWELS
    )
    candidates = [c for c in pool if c != answer and c not in word]
    if len(candidates) < count - 1:
        candidates = [c for c in string.ascii_uppercase if c != answer]
    letters = [answer] + random.sample(candidates, count - 1)
    random.shuffle(letters)
    return letters


def make_question(mode, tier=levels.DEFAULT_TIER):
    tier = levels.clamp_tier(tier)
    word, sprite = random.choice(WORD_POOL_BY_TIER[tier])
    if mode == "first":
        blanks = [0]
    elif mode == "missing":
        count = min(BLANKS_BY_TIER[tier], len(word))
        blanks = sorted(random.sample(range(len(word)), count))
    else:
        blanks = list(range(len(word)))
    return {
        "word": word,
        "sprite": sprite,
        "blanks": blanks,
        "filled": {},  # index -> letter the child has placed
    }


def _next_blank(question):
    for index in question["blanks"]:
        if index not in question["filled"]:
            return index
    return None


def _layout(count):
    margin, gap, top, height = 28, 10, 126, 38
    total = 320 - margin * 2
    width = (total - gap * (count - 1)) // count
    return [
        pygame.Rect(margin + index * (width + gap), top, width, height)
        for index in range(count)
    ]


class WordRoundScene(Scene):
    """One round of picture-word questions."""

    def __init__(self, app, player, mode, tier=levels.DEFAULT_TIER):
        super().__init__(app)
        self.player = player
        self.mode = mode
        self.tier = levels.clamp_tier(tier)
        self.mode_label = next(label for key, label, _, _ in MODES if key == mode)
        self.accent = next(color for key, _, _, color in MODES if key == mode)
        self.index = 0
        self.correct = 0
        self.perfect_word = True   # No mistakes yet on the current word.
        self.question = None
        self.buttons = []
        self.state = "asking"
        self.state_timer = 0.0
        self.time = 0.0
        self.attempts = 0
        self.feedback = ""
        self.particles = ui.Particles()
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)

    def on_enter(self):
        if self.question is None:
            self._next_question()

    def _next_question(self):
        if self.index >= ROUND_LENGTH:
            self._finish()
            return
        self.index += 1
        self.question = make_question(self.mode, self.tier)
        self.perfect_word = True
        self.state = "asking"
        self.feedback = ""
        self._build_buttons()

    def _build_buttons(self):
        blank = _next_blank(self.question)
        if blank is None:
            self.buttons = []
            return
        answer = self.question["word"][blank]
        letters = _letter_choices(answer, self.question["word"], CHOICES_BY_TIER[self.tier])
        self.attempts = 0
        self.buttons = [
            ui.Button(
                rect,
                letter,
                palette.ACCENTS[slot % len(palette.ACCENTS)],
                hotkey=str(slot + 1),
                text_size=34,
                value=letter,
            )
            for slot, (rect, letter) in enumerate(zip(_layout(len(letters)), letters))
        ]

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
                    WordRoundScene(app, self.player, self.mode, self.tier)
                ),
                detail=f"LEVEL {levels.tier_name(self.tier)}",
            )
        )

    def _answer(self, button):
        if self.state != "asking" or button.locked:
            return
        blank = _next_blank(self.question)
        if blank is None:
            return
        expected = self.question["word"][blank]
        if button.value == expected:
            self.question["filled"][blank] = expected
            sfx.play("pop")
            self.particles.burst(button.rect.center, self.accent, count=12, speed=70)
            if _next_blank(self.question) is None:
                # Word complete.
                if self.perfect_word:
                    self.correct += 1
                self.state = "celebrating"
                self.state_timer = 1.2
                self.feedback = random.choice(["YES!", "SUPER!", "WELL DONE!"])
                sfx.play("correct")
                self.particles.confetti(320, count=18)
            else:
                self._build_buttons()
        else:
            self.perfect_word = False
            self.attempts += 1
            button.locked = True
            button.enabled = False
            button.set_flash(palette.RED, 0.4)
            self.feedback = "TRY AGAIN!"
            sfx.play("wrong")
            if self.attempts >= 2:
                for candidate in self.buttons:
                    if candidate.value == expected:
                        candidate.set_flash(palette.YELLOW, 9.0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            if self.state == "asking":
                keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
                for index, key in enumerate(keys):
                    if event.key == key and index < len(self.buttons):
                        self._answer(self.buttons[index])
                        return
                # Typing the letter itself works too, for kids who know the keys.
                name = pygame.key.name(event.key).upper()
                if len(name) == 1 and name.isalpha():
                    for button in self.buttons:
                        if button.value == name:
                            self._answer(button)
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
        if self.state == "celebrating":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._next_question()

    def _draw_word(self, surface):
        word = self.question["word"]
        cell = 26 if len(word) <= 4 else 20
        total = len(word) * cell
        start_x = 160 - total // 2
        y = 80
        active = _next_blank(self.question)
        for index, letter in enumerate(word):
            rect = pygame.Rect(start_x + index * cell, y, cell - 4, 28)
            is_blank = index in self.question["blanks"]
            shown = self.question["filled"].get(index, None if is_blank else letter)
            if index == active:
                border = palette.YELLOW
                fill = palette.dim(palette.YELLOW, 0.25)
            elif shown is None:
                border = palette.DARK_GRAY
                fill = palette.BG_PANEL
            else:
                border = self.accent
                fill = palette.dim(self.accent, 0.3)
            pygame.draw.rect(surface, fill, rect)
            pygame.draw.rect(surface, border, rect, 1)
            if shown is not None:
                ui.text(
                    surface,
                    shown,
                    (rect.centerx, rect.y + 4),
                    palette.WHITE,
                    30,
                    align="center",
                )

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        ui.text(surface, self.mode_label, (4, 3), self.accent, 14)
        ui.text(
            surface, f"{self.index}/{ROUND_LENGTH}", (316, 3), palette.WHITE, 14, align="right"
        )
        ui.bar(surface, (4, 16, 312, 3), (self.index - 1) / ROUND_LENGTH, self.accent)

        if self.question:
            bob = ui.title_wobble(self.time, 2.0, 2.0)
            sprites.draw(
                surface, self.question["sprite"], (160, int(50 + bob)), scale=3, center=True
            )
            self._draw_word(surface)
        for button in self.buttons:
            button.draw(surface)
        self.particles.draw(surface)

        if self.feedback:
            color = palette.GREEN if self.state == "celebrating" else palette.ORANGE
            ui.text(surface, self.feedback, (160, 112), color, 16, align="center")
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


class WordMenuScene(Scene):
    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.nudge = player.nudge
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)
        self.buttons = [
            ui.Button(
                (28 + index * 92, 46, 84, 56),
                label,
                color,
                sprite=sprite,
                hotkey=str(index + 1),
                text_size=13,
                value=key,
            )
            for index, (key, label, sprite, color) in enumerate(MODES)
        ]
        self.nudge_buttons = [
            ui.Button(
                (56 + index * 72, 130, 68, 20),
                levels.NUDGE_NAMES[value],
                palette.PURPLE,
                text_size=12,
                value=value,
            )
            for index, value in enumerate(levels.NUDGES)
        ]

    @property
    def tier(self):
        return self.player.tier(self.nudge)

    def on_enter(self):
        from retro import progress

        self.player = progress.Player(self.player.name)
        self.nudge = self.player.nudge

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
        for button in self.nudge_buttons:
            if button.handle_event(event):
                self.nudge = button.value
                self.player.set_nudge(button.value)
                sfx.play("click")
                return

    def _start(self, mode):
        sfx.play("select")
        self.app.push(WordRoundScene(self.app, self.player, mode, self.tier))

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        for button in self.buttons + self.nudge_buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface, "WORD ROCKET", (160, int(6 + wobble)), palette.CYAN, 26, align="center"
        )
        ui.star_counter(surface, self.player.stars, (4, 2))
        for button in self.buttons:
            button.draw(surface)
        ui.text(surface, "LEVEL", (6, 136), palette.WHITE, 12)
        for button in self.nudge_buttons:
            button.color = palette.YELLOW if button.value == self.nudge else palette.PURPLE
            button.draw(surface)
        age = self.player.age
        summary = f"AGE {age}" if age else "AGE NOT SET"
        ui.text(
            surface,
            f"{summary}   -   {levels.tier_name(self.tier)}",
            (160, 158),
            palette.GRAY,
            13,
            align="center",
        )
        ui.text(surface, "ESC = BACK", (316, 168), palette.DARK_GRAY, 12, align="right")


def launch(app, player):
    app.push(WordMenuScene(app, player))
