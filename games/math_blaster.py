"""Number Blaster -- a space-themed maths game.

Which modes appear, and how hard they are, follows the player's age: a
five-year-old counts ducks, an eight-year-old gets times tables, division and
word problems, and a twelve-year-old gets two-digit multiplication and
two-step problems. The age sets the starting tier; the menu still lets a
child nudge it easier or harder.

Rounds are ten questions. Wrong answers cost nothing but a retry, and a star
is earned for every question answered correctly first time.
"""

import random

import pygame

from retro import levels, palette, sfx, sprites, ui
from retro.app import Scene
from retro.results import ResultsScene

GAME_KEY = "math"
ROUND_LENGTH = 10

# key, label, icon, colour
MODES = {
    "count": ("COUNT", "duck", palette.YELLOW),
    "add": ("ADD +", "rocket", palette.GREEN),
    "sub": ("TAKE AWAY -", "star", palette.MAGENTA),
    "multiply": ("TIMES x", "flame", palette.ORANGE),
    "divide": ("SHARE /", "crystal", palette.CYAN),
    "word": ("STORY", "book", palette.PURPLE),
    "compare": ("MORE OR LESS", "fish", palette.BLUE),
}

# Six modes at most, so the menu stays a tidy three by two.
MODES_BY_TIER = {
    1: ["count", "add", "sub", "compare"],
    2: ["add", "sub", "multiply", "divide", "word", "compare"],
    3: ["add", "sub", "multiply", "divide", "word", "compare"],
    4: ["multiply", "divide", "word", "add", "sub", "compare"],
}

COUNTABLE = ["duck", "star", "apple", "fish", "cat", "frog", "ball", "cake"]

COUNT_RANGE = {1: (1, 5), 2: (4, 12), 3: (6, 15), 4: (8, 15)}
ADD_RANGE = {1: (1, 5, 10), 2: (2, 20, 30), 3: (10, 99, 150), 4: (50, 499, 999)}
SUB_MAX = {1: 5, 2: 20, 3: 100, 4: 999}
COMPARE_RANGE = {1: (1, 10), 2: (1, 50), 3: (1, 500), 4: (100, 9999)}

STORY_ITEMS = [
    "STICKERS", "MARBLES", "APPLES", "COINS",
    "SHELLS", "CARDS", "BLOCKS", "CONKERS",
]


def _distractors(answer, count=2):
    """Wrong answers that scale with the size of the right one."""
    if answer <= 20:
        offsets = [-3, -2, -1, 1, 2, 3]
    elif answer <= 100:
        offsets = [-10, -5, -2, -1, 1, 2, 5, 10]
    else:
        offsets = [-100, -20, -10, -1, 1, 10, 20, 100]
    options = {answer + offset for offset in offsets}
    options = [value for value in options if value >= 0 and value != answer]
    random.shuffle(options)
    chosen = options[:count]
    guard = 0
    while len(chosen) < count and guard < 50:
        guard += 1
        candidate = max(0, answer + random.randint(-4, 4))
        if candidate != answer and candidate not in chosen:
            chosen.append(candidate)
    return chosen


def _story(tier, name):
    """A word problem, using the player's own name."""
    who = (name or "SAM").upper()
    item = random.choice(STORY_ITEMS)
    if tier <= 2:
        first = random.randint(5, 20)
        second = random.randint(2, min(first, 12))
        if random.random() < 0.5:
            text = f"{who} HAS {first} {item} AND FINDS {second} MORE. HOW MANY NOW?"
            answer = first + second
        else:
            text = f"{who} HAS {first} {item} AND GIVES AWAY {second}. HOW MANY ARE LEFT?"
            answer = first - second
    elif tier == 3:
        if random.random() < 0.5:
            bags = random.randint(3, 8)
            each = random.randint(3, 9)
            text = f"{who} HAS {bags} BAGS WITH {each} {item} IN EACH. HOW MANY {item}?"
            answer = bags * each
        else:
            friends = random.randint(3, 6)
            each = random.randint(3, 9)
            text = (
                f"{who} SHARES {friends * each} {item} BETWEEN {friends} FRIENDS. "
                "HOW MANY EACH?"
            )
            answer = each
    else:
        packs = random.randint(4, 9)
        each = random.randint(4, 9)
        used = random.randint(2, min(9, packs * each - 1))
        text = (
            f"{who} BUYS {packs} PACKS OF {each} {item} AND USES {used}. "
            "HOW MANY ARE LEFT?"
        )
        answer = packs * each - used
    return text, answer


def make_question(mode, tier, name=None):
    """Build one question for the given mode and difficulty tier."""
    tier = levels.clamp_tier(tier)

    if mode == "count":
        low, high = COUNT_RANGE[tier]
        total = random.randint(low, high)
        question = {
            "kind": "count",
            "prompt": "HOW MANY?",
            "sprite": random.choice(COUNTABLE),
            "count": total,
            "answer": total,
        }

    elif mode == "add":
        low, high, cap = ADD_RANGE[tier]
        first = random.randint(low, high)
        second = random.randint(low, max(low, min(high, cap - first)))
        question = {
            "kind": "expr",
            "prompt": f"{first} + {second} = ?",
            "answer": first + second,
        }

    elif mode == "sub":
        high = SUB_MAX[tier]
        first = random.randint(2, high)
        second = random.randint(0, first)
        question = {
            "kind": "expr",
            "prompt": f"{first} - {second} = ?",
            "answer": first - second,
        }

    elif mode == "multiply":
        if tier <= 2:
            first = random.choice([2, 5, 10])
            second = random.randint(1, 10)
        elif tier == 3:
            first = random.randint(2, 12)
            second = random.randint(2, 12)
        else:
            first = random.randint(11, 25)
            second = random.randint(3, 9)
        question = {
            "kind": "expr",
            "prompt": f"{first} x {second} = ?",
            "answer": first * second,
        }

    elif mode == "divide":
        if tier <= 2:
            divisor = random.choice([2, 5, 10])
            result = random.randint(1, 10)
        elif tier == 3:
            divisor = random.randint(2, 12)
            result = random.randint(2, 12)
        else:
            divisor = random.randint(3, 12)
            result = random.randint(11, 30)
        # Built from the answer up, so it always divides exactly.
        question = {
            "kind": "expr",
            "prompt": f"{divisor * result} / {divisor} = ?",
            "answer": result,
        }

    elif mode == "word":
        text, answer = _story(tier, name)
        question = {"kind": "story", "prompt": text, "answer": answer}

    else:  # compare
        low, high = COMPARE_RANGE[tier]
        first = random.randint(low, high)
        second = random.randint(low, high)
        while second == first:
            second = random.randint(low, high)
        want_more = random.random() < 0.5
        question = {
            "kind": "compare",
            "prompt": "WHICH IS MORE?" if want_more else "WHICH IS LESS?",
            "answer": max(first, second) if want_more else min(first, second),
            "choices": [first, second],
        }

    if "choices" not in question:
        question["choices"] = [question["answer"]] + _distractors(question["answer"])
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
    """Ten questions of one mode at one tier."""

    def __init__(self, app, player, mode, tier):
        super().__init__(app)
        self.player = player
        self.mode = mode
        self.tier = levels.clamp_tier(tier)
        self.mode_label, _, self.accent = MODES[mode]
        self.index = 0
        self.correct = 0
        self.streak = 0
        self.question = None
        self.buttons = []
        self.attempts = 0
        self.state = "asking"
        self.state_timer = 0.0
        self.time = 0.0
        self.particles = ui.Particles()
        self.starfield = ui.Starfield(320, 180, count=50, speed=10)
        self.hint = ui.HintTimer(12.0)
        self.rocket = None
        self.feedback = ""

    def on_enter(self):
        if self.question is None:
            self._next_question()

    def _next_question(self):
        if self.index >= ROUND_LENGTH:
            self._finish()
            return
        self.index += 1
        self.question = make_question(self.mode, self.tier, self.player.name)
        self.attempts = 0
        self.state = "asking"
        self.feedback = ""
        self.hint.reset()
        rects = _layout(len(self.question["choices"]))
        # Long numbers need a smaller face than single digits.
        widest = max(len(str(value)) for value in self.question["choices"])
        size = 30 if widest <= 3 else (24 if widest <= 4 else 18)
        self.buttons = []
        for slot, (rect, value) in enumerate(zip(rects, self.question["choices"])):
            self.buttons.append(
                ui.Button(
                    rect,
                    str(value),
                    palette.ACCENTS[slot % len(palette.ACCENTS)],
                    hotkey=str(slot + 1),
                    text_size=size,
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
                    MathRoundScene(app, self.player, self.mode, self.tier)
                ),
                detail=f"LEVEL {levels.tier_name(self.tier)}",
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
        kind = question["kind"]

        if kind == "count":
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

        elif kind == "story":
            ui.text_block(
                surface,
                question["prompt"],
                160,
                area.y + 10,
                palette.WHITE,
                14,
                area.width - 16,
            )

        elif kind == "compare":
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
            size = 46 if len(question["prompt"]) <= 12 else 34
            ui.text(
                surface,
                question["prompt"],
                (160, int(area.y + 26 + bob)),
                palette.WHITE,
                size,
                align="center",
            )

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)

        ui.text(surface, self.mode_label, (4, 3), self.accent, 14)
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
            ui.text(surface, "TAKE YOUR TIME...", (160, 112), palette.GRAY, 14, align="center")
        if self.streak >= 3 and self.state == "asking":
            ui.text(surface, f"STREAK {self.streak}!", (4, 166), palette.YELLOW, 14)
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


class MathMenuScene(Scene):
    """Pick a mode. Which ones are offered depends on the player's age."""

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.nudge = 0
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)
        self.mode_buttons = []
        self.nudge_buttons = [
            ui.Button(
                (56 + index * 72, 132, 68, 20),
                levels.NUDGE_NAMES[value],
                palette.PURPLE,
                text_size=12,
                value=value,
            )
            for index, value in enumerate(levels.NUDGES)
        ]
        self._build_modes()

    @property
    def tier(self):
        return self.player.tier(self.nudge)

    def _build_modes(self):
        """Three by two, showing only what suits this player's age."""
        available = MODES_BY_TIER[levels.tier_for_age(self.player.age)]
        self.mode_buttons = []
        for index, key in enumerate(available[:6]):
            label, icon, color = MODES[key]
            column, row = index % 3, index // 3
            rect = pygame.Rect(10 + column * 100, 38 + row * 46, 96, 42)
            self.mode_buttons.append(
                ui.Button(
                    rect,
                    label,
                    color,
                    sprite=icon,
                    hotkey=str(index + 1),
                    text_size=12,
                    value=key,
                )
            )

    def on_enter(self):
        from retro import progress

        self.player = progress.Player(self.player.name)
        self._build_modes()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6)
            for index, key in enumerate(keys):
                if event.key == key and index < len(self.mode_buttons):
                    self._start(self.mode_buttons[index].value)
                    return
        for button in self.mode_buttons:
            if button.handle_event(event):
                self._start(button.value)
                return
        for button in self.nudge_buttons:
            if button.handle_event(event):
                self.nudge = button.value
                sfx.play("click")
                return

    def _start(self, mode):
        sfx.play("select")
        self.app.push(MathRoundScene(self.app, self.player, mode, self.tier))

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        for button in self.mode_buttons + self.nudge_buttons:
            button.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface,
            "NUMBER BLASTER",
            (160, int(6 + wobble)),
            palette.YELLOW,
            28,
            align="center",
        )
        ui.text(surface, "ESC = BACK", (316, 4), palette.DARK_GRAY, 12, align="right")
        for button in self.mode_buttons:
            button.draw(surface)
        ui.text(surface, "LEVEL", (6, 138), palette.WHITE, 12)
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


def launch(app, player):
    app.push(MathMenuScene(app, player))
