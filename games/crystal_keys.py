"""Crystal Keys -- an elemental typing tutor for older kids (7-9).

Four realms, each of which is really a keyboard lesson in disguise:

    Earth  home row only          a s d f g h j k l
    Water  adds the top row       q w e r t y u i o p
    Air    adds the bottom row    z x c v b n m
    Fire   everything, longer words, for speed

Typing the right key charges an elemental crystal. A wrong key never ends
anything -- the letter simply refuses to advance, the way a real typing tutor
works, so fingers learn the correct key rather than racing past it. An
on-screen keyboard highlights the next key, which is what makes this a tutor
and not just a spelling test.
"""

import math
import random
import time

import pygame

from retro import palette, sfx, sprites, ui
from retro.app import Scene
from retro.results import ResultsScene

GAME_KEY = "typing"
ROUND_LENGTH = 8

HOME_ROW = "asdfghjkl"
TOP_ROW = "qwertyuiop"
BOTTOM_ROW = "zxcvbnm"

# element key, label, icon, colour, the keys it is allowed to use
ELEMENTS = [
    ("earth", "EARTH", "leaf", palette.GREEN, HOME_ROW),
    ("water", "WATER", "droplet", palette.CYAN, HOME_ROW + TOP_ROW),
    ("air", "AIR", "cloud", palette.WHITE, HOME_ROW + TOP_ROW + BOTTOM_ROW),
    ("fire", "FIRE", "flame", palette.ORANGE, HOME_ROW + TOP_ROW + BOTTOM_ROW),
]

# Drills first, then real words. Every entry is checked by the tests against
# the element's allowed keys, so a word can never ask for a key the child has
# not been shown yet.
LESSONS = {
    "earth": [
        "asdf", "jkl", "fjfj", "dkdk", "slsl", "adad",
        "dad", "sad", "ask", "all", "fall", "hall",
        "glass", "salad", "flash", "dash", "flag", "half",
    ],
    "water": [
        "wet", "tide", "pour", "drip", "flow", "pool",
        "tree", "quiet", "water", "spray", "frost", "lake",
        "rapid", "wide", "splash", "waterfall", "ripple", "puddle",
    ],
    "air": [
        "sky", "mist", "gust", "blow", "calm", "vane",
        "wind", "cloud", "brave", "climb", "above", "swirl",
        "breeze", "zephyr", "nimbus", "breath", "cyclone", "balloon",
    ],
    "fire": [
        "ash", "glow", "ember", "spark", "blaze", "torch",
        "smoke", "flame", "candle", "cinder", "scorch", "magma",
        "bonfire", "phoenix", "crackle", "furnace", "volcano", "kindle",
    ],
}

KEYBOARD_ROWS = [TOP_ROW, HOME_ROW, BOTTOM_ROW]
KEY_W, KEY_H, KEY_GAP = 24, 18, 2
KEYBOARD_TOP = 88


def element(key):
    return next(item for item in ELEMENTS if item[0] == key)


class Ambient:
    """Elemental background weather. Cheap particles, one look per realm."""

    def __init__(self, element_key, count=44):
        self.element = element_key
        self.items = []
        for _ in range(count):
            self.items.append(self._spawn(initial=True))

    def _spawn(self, initial=False):
        item = {
            "x": random.uniform(0, 320),
            "y": random.uniform(0, 180) if initial else -4,
            "phase": random.uniform(0, math.tau),
            "size": random.choice([1, 1, 2]),
        }
        if self.element == "earth":
            item.update(
                vx=0.0, vy=random.uniform(6, 18),
                color=random.choice([palette.GREEN, (40, 150, 80), palette.BROWN]),
            )
        elif self.element == "water":
            item.update(
                vx=0.0, vy=random.uniform(70, 130),
                color=random.choice([palette.CYAN, palette.BLUE]),
                size=1,
            )
        elif self.element == "air":
            item.update(
                vx=random.uniform(18, 55), vy=0.0,
                color=random.choice([palette.WHITE, palette.GRAY]),
                x=-4 if not initial else random.uniform(0, 320),
            )
        else:  # fire embers drift upward
            item.update(
                vx=0.0, vy=-random.uniform(20, 60),
                color=random.choice([palette.ORANGE, palette.RED, palette.YELLOW]),
                y=184 if not initial else random.uniform(0, 180),
            )
        return item

    def update(self, dt):
        for index, item in enumerate(self.items):
            item["phase"] += dt * 2.0
            sway = math.sin(item["phase"]) * (14 if self.element in ("earth", "air") else 4)
            item["x"] += (item["vx"] + (sway if self.element == "earth" else 0)) * dt
            item["y"] += item["vy"] * dt
            if self.element == "air":
                item["y"] += math.sin(item["phase"]) * 12 * dt
            off = (
                item["y"] > 184
                or item["y"] < -8
                or item["x"] > 324
                or item["x"] < -8
            )
            if off:
                self.items[index] = self._spawn()

    def draw(self, surface):
        for item in self.items:
            x, y = int(item["x"]), int(item["y"])
            if self.element == "water":
                pygame.draw.line(surface, item["color"], (x, y), (x, y + 3))
            else:
                pygame.draw.rect(surface, item["color"], (x, y, item["size"], item["size"]))


def draw_crystal(surface, center, width, height, color, charge, seconds):
    """A six-sided crystal that fills up from the bottom as the round goes on."""
    cx, cy = center
    half = width // 2
    top = cy - height // 2
    bottom = cy + height // 2
    shoulder = int(height * 0.26)
    points = [
        (cx, top),
        (cx + half, top + shoulder),
        (cx + half, bottom - shoulder),
        (cx, bottom),
        (cx - half, bottom - shoulder),
        (cx - half, top + shoulder),
    ]
    pygame.draw.polygon(surface, palette.dim(color, 0.22), points)

    charge = max(0.0, min(1.0, charge))
    filled = int(height * charge)
    if filled > 0:
        previous = surface.get_clip()
        surface.set_clip(pygame.Rect(cx - half - 1, bottom - filled, width + 2, filled))
        pygame.draw.polygon(surface, color, points)
        surface.set_clip(previous)

    pygame.draw.polygon(surface, palette.lighten(color, 0.55), points, 1)
    pygame.draw.line(
        surface, palette.lighten(color, 0.35), (cx, top + 3), (cx, bottom - 3)
    )
    if charge >= 1.0 and int(seconds * 6) % 2 == 0:
        pygame.draw.rect(surface, palette.WHITE, (cx - 1, top - 4, 2, 2))


def draw_keyboard(surface, next_key, color, wrong_flash=0.0):
    """The on-screen keyboard, with the next key to press lit up."""
    for row_index, row in enumerate(KEYBOARD_ROWS):
        y = KEYBOARD_TOP + row_index * (KEY_H + KEY_GAP)
        start_x = 30 + row_index * 13
        for column, letter in enumerate(row):
            rect = pygame.Rect(start_x + column * (KEY_W + KEY_GAP), y, KEY_W, KEY_H)
            is_next = next_key == letter
            if is_next:
                face = palette.dim(color, 0.75) if wrong_flash <= 0 else palette.dim(palette.RED, 0.7)
                border = palette.WHITE
            else:
                face = palette.BG_PANEL
                border = palette.DARK_GRAY
            pygame.draw.rect(surface, face, rect)
            pygame.draw.rect(surface, border, rect, 1)
            ui.text(
                surface,
                letter.upper(),
                (rect.centerx, rect.y + 4),
                palette.WHITE if is_next else palette.GRAY,
                14,
                align="center",
                shadow=False,
            )


class TypingRoundScene(Scene):
    """One realm's round: eight prompts, typed key by key."""

    def __init__(self, app, player, element_key):
        super().__init__(app)
        self.player = player
        self.element = element_key
        _, self.label, self.icon, self.color, self.allowed = element(element_key)
        self.prompts = random.sample(LESSONS[element_key], ROUND_LENGTH)
        self.index = 0
        self.typed = 0
        self.clean = 0                 # Prompts finished with no wrong keys.
        self.mistakes_here = 0
        self.keystrokes = 0
        self.hits = 0
        self.started_at = None         # Clock starts on the first real keypress.
        self.elapsed = 0.0
        self.state = "typing"
        self.state_timer = 0.0
        self.time = 0.0
        self.shake = 0.0
        self.wrong_flash = 0.0
        self.feedback = ""
        self.particles = ui.Particles()
        self.ambient = Ambient(element_key)

    @property
    def prompt(self):
        return self.prompts[self.index] if self.index < len(self.prompts) else ""

    @property
    def next_key(self):
        prompt = self.prompt
        return prompt[self.typed] if self.typed < len(prompt) else None

    @property
    def accuracy(self):
        if self.keystrokes == 0:
            return 100
        return int(round(self.hits * 100 / self.keystrokes))

    @property
    def wpm(self):
        # Under a second of typing says nothing about speed, and a tiny
        # denominator would report a nonsense number.
        if self.elapsed < 1.0:
            return 0
        words_per_minute = (self.hits / 5.0) / (self.elapsed / 60.0)
        return min(int(words_per_minute), 250)

    # -- input ------------------------------------------------------------

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            sfx.play("back")
            self.app.pop()
            return
        if self.state != "typing":
            return
        char = event.unicode.lower()
        if not char or not char.isalpha():
            return
        self._press(char)

    def _press(self, char):
        expected = self.next_key
        if expected is None:
            return
        if self.started_at is None:
            self.started_at = time.monotonic()
        self.keystrokes += 1
        if char == expected:
            self.hits += 1
            self.typed += 1
            # Each letter is a step up the scale, so a word resolves musically.
            sfx.play_step(self.typed - 1)
            self._spark()
            if self.typed >= len(self.prompt):
                self._finish_prompt()
        else:
            self.mistakes_here += 1
            self.shake = 0.3
            self.wrong_flash = 0.3
            sfx.play("wrong")

    def _prompt_layout(self):
        """Fixed-width letter cells: start x, cell width and font size.

        Laying letters out in even cells keeps the cursor underline aligned
        and avoids the glyph-overlap you get from advancing by each letter's
        own rendered width.
        """
        prompt = self.prompt
        size = 38 if len(prompt) <= 8 else 30
        # The prompt is empty once the last one is done. Nothing to lay out,
        # and max() of no letters would raise.
        widths = [ui.text_size(letter, size)[0] for letter in prompt]
        cell = (max(widths) if widths else 0) + 3
        return 160 - (cell * len(prompt)) // 2, cell, size

    def _spark(self):
        """A puff of element-coloured sparks at the letter just typed."""
        start_x, cell, _ = self._prompt_layout()
        x = start_x + (self.typed - 1) * cell + cell // 2
        self.particles.burst(
            (x, 52), self.color, count=5, speed=45, life=0.4, gravity=30
        )

    def _finish_prompt(self):
        if self.mistakes_here == 0:
            self.clean += 1
            self.feedback = random.choice(["PERFECT!", "CLEAN!", "NICE!"])
        else:
            self.feedback = "GOT IT!"
        sfx.play("correct")
        self.particles.burst((160, 46), self.color, count=18, speed=90)
        self.state = "celebrating"
        self.state_timer = 0.7

    def _next_prompt(self):
        self.index += 1
        self.typed = 0
        self.mistakes_here = 0
        self.feedback = ""
        if self.index >= len(self.prompts):
            self._finish_round()
        else:
            self.state = "typing"

    def _finish_round(self):
        # Crystals are rarer than stars: one for finishing, one for accuracy,
        # one for a flawless round.
        crystals = 1
        if self.accuracy >= 90:
            crystals += 1
        if self.clean == ROUND_LENGTH:
            crystals += 1
        self.player.add_crystals(self.element, crystals)
        sfx.play("charge")  # The crystal finishing charging.
        detail = f"{self.accuracy}% ACCURATE   {self.wpm} WPM   +{crystals} CRYSTAL"
        if crystals != 1:
            detail += "S"
        self.app.replace(
            ResultsScene(
                self.app,
                self.player,
                f"{GAME_KEY}_{self.element}",
                self.label,
                self.clean,
                ROUND_LENGTH,
                lambda app: app.replace(
                    TypingRoundScene(app, self.player, self.element)
                ),
                detail=detail,
            )
        )

    # -- loop -------------------------------------------------------------

    def update(self, dt):
        self.time += dt
        self.ambient.update(dt)
        self.particles.update(dt)
        self.shake = max(0.0, self.shake - dt)
        self.wrong_flash = max(0.0, self.wrong_flash - dt)
        if self.started_at is not None and self.state == "typing":
            self.elapsed = time.monotonic() - self.started_at
        if self.state == "celebrating":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._next_prompt()

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.ambient.draw(surface)

        ui.text(surface, self.label, (4, 3), self.color, 14)
        ui.text(
            surface,
            f"{min(self.index + 1, ROUND_LENGTH)}/{ROUND_LENGTH}",
            (316, 3),
            palette.WHITE,
            14,
            align="right",
        )
        ui.bar(surface, (4, 16, 312, 3), self.index / ROUND_LENGTH, self.color)

        charge = (self.index + self.typed / max(1, len(self.prompt))) / ROUND_LENGTH
        draw_crystal(surface, (24, 46), 28, 46, self.color, charge, self.time)

        self._draw_prompt(surface)

        ui.text(surface, f"{self.accuracy}%", (312, 28), palette.GRAY, 14, align="right")
        if self.clean:
            ui.text(
                surface, f"CLEAN {self.clean}", (312, 42), palette.YELLOW, 12, align="right"
            )

        draw_keyboard(surface, self.next_key, self.color, self.wrong_flash)
        self.particles.draw(surface)

        if self.feedback:
            ui.text(surface, self.feedback, (160, 68), palette.GREEN, 16, align="center")
        elif self.started_at is None:
            ui.text(
                surface,
                "TYPE THE LETTERS!",
                (160, 68),
                palette.GRAY,
                14,
                align="center",
            )
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")

    def _draw_prompt(self, surface):
        """The word, with typed letters lit and the current one underlined."""
        prompt = self.prompt
        if not prompt:
            return
        start_x, cell, size = self._prompt_layout()
        if self.shake > 0:
            start_x += int(math.sin(self.time * 60) * 3)
        y = 28
        for position, letter in enumerate(prompt):
            if position < self.typed:
                color = self.color
            elif position == self.typed:
                color = palette.WHITE
            else:
                color = palette.GRAY
            left = start_x + position * cell
            ui.text(surface, letter.upper(), (left + cell // 2, y), color, size, align="center")
            if position == self.typed and self.state == "typing":
                pygame.draw.rect(
                    surface, palette.YELLOW, (left + 2, y + size - 10, cell - 4, 2)
                )


class ElementMenuScene(Scene):
    """Pick a realm. Each shows how many crystals have been earned there."""

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.time = 0.0
        self.ambient = Ambient("air", count=30)
        self.buttons = [
            ui.Button(
                (12 + index * 76, 54, 68, 62),
                label,
                color,
                sprite=icon,
                hotkey=str(index + 1),
                text_size=13,
                value=key,
            )
            for index, (key, label, icon, color, _) in enumerate(ELEMENTS)
        ]

    def on_enter(self):
        from retro import progress

        self.player = progress.Player(self.player.name)

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
                    self._start(ELEMENTS[index][0])
                    return
        for button in self.buttons:
            if button.handle_event(event):
                self._start(button.value)
                return

    def _start(self, element_key):
        sfx.play("select")
        self.app.push(TypingRoundScene(self.app, self.player, element_key))

    def update(self, dt):
        self.time += dt
        self.ambient.update(dt)
        for button in self.buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.ambient.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface, "CRYSTAL KEYS", (160, int(8 + wobble)), palette.MAGENTA, 30, align="center"
        )
        ui.text(surface, "CHOOSE YOUR ELEMENT", (160, 38), palette.WHITE, 14, align="center")

        crystals = self.player.crystals
        for index, button in enumerate(self.buttons):
            button.draw(surface)
            key = ELEMENTS[index][0]
            sprites.draw(surface, "crystal", (button.rect.x + 16, button.rect.bottom + 2))
            ui.text(
                surface,
                f"x{crystals.get(key, 0)}",
                (button.rect.x + 34, button.rect.bottom + 7),
                palette.MAGENTA,
                13,
            )
        ui.text(
            surface,
            "HOME ROW FIRST -- EARTH IS EASIEST",
            (160, 144),
            palette.GRAY,
            13,
            align="center",
        )
        ui.text(surface, "ESC = BACK", (316, 168), palette.DARK_GRAY, 12, align="right")


def launch(app, player):
    app.push(ElementMenuScene(app, player))
