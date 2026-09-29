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
    "props_learn": ("TIMES RULES", "book", palette.PURPLE),
    "props_quiz":  ("RULES QUIZ",  "flame", palette.ORANGE),
}

# Six modes at most, so the menu stays a tidy three by two.
MODES_BY_TIER = {
    1: ["count", "add", "sub", "compare"],
    2: ["add", "sub", "multiply", "props_learn", "props_quiz", "compare"],
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


# ---------------------------------------------------------------------------
# Multiplication Properties — shared data & question generator
# ---------------------------------------------------------------------------

# Each property defines:
#   name    – id used by the quiz
#   title   – big label (shown in both learn and quiz)
#   color   – accent color for this property
#   slides  – ordered list of draw-callables; each callable(surface, t) draws
#             one animation frame onto the full virtual surface.  't' is seconds
#             elapsed on this slide so elements can animate in.

import math as _math  # local alias — math is already imported at top level


# -- slide helpers -----------------------------------------------------------

def _slide_title(surface, title, color, t):
    """Animated title drop-in: slides down from above."""
    y = int(max(20, 60 - max(0, t - 0.1) * 280))
    ui.text(surface, title, (160, y), color, 24, align="center")


def _dot_grid(surface, rows, cols, origin_x, origin_y, color, t, delay=0.0):
    """Draw a grid of dots, fading in dot-by-dot starting at t=delay."""
    elapsed = max(0.0, t - delay)
    total = rows * cols
    visible = min(total, int(elapsed * 14))   # ~14 dots per second
    for i in range(visible):
        r, c = divmod(i, cols)
        x = origin_x + c * 10
        y = origin_y + r * 10
        pygame.draw.circle(surface, color, (x, y), 3)


def _fade_in_text(surface, msg, pos, color, size, t, delay=0.0, align="center"):
    """Draw text only after delay seconds."""
    if t >= delay:
        ui.text(surface, msg, pos, color, size, align=align)


def _rect_grow(surface, rect, color, t, delay=0.0, fill=True):
    """Grow a rectangle from zero width to full width."""
    elapsed = max(0.0, t - delay)
    frac = min(1.0, elapsed / 0.35)
    r = pygame.Rect(rect.x, rect.y, int(rect.width * frac), rect.height)
    if r.width > 0:
        if fill:
            pygame.draw.rect(surface, palette.dim(color, 0.45), r)
        pygame.draw.rect(surface, color, r, 1)


# -- commutative slides ------------------------------------------------------
# Idea: show 3×4 dot grid labelled "3 ROWS OF 4", then flip to 4×3 labelled
# "4 ROWS OF 3", then show both side-by-side with "= SAME TOTAL!"

def _comm_slide_0(surface, t):
    _slide_title(surface, "SWAP THE ORDER", palette.CYAN, t)
    _fade_in_text(surface, "DOES THE ORDER YOU MULTIPLY MATTER?",
                  (160, 50), palette.GRAY, 12, t, 0.6)
    _dot_grid(surface, 3, 4, 108, 80, palette.CYAN, t, delay=1.2)
    _fade_in_text(surface, "3 ROWS OF 4", (160, 118), palette.WHITE, 13, t, 2.0)
    _fade_in_text(surface, "= 12", (160, 132), palette.YELLOW, 16, t, 2.5)


def _comm_slide_1(surface, t):
    _slide_title(surface, "SWAP THE ORDER", palette.CYAN, t)
    _dot_grid(surface, 4, 3, 118, 78, palette.GREEN, t, delay=0.3)
    _fade_in_text(surface, "4 ROWS OF 3", (160, 120), palette.WHITE, 13, t, 1.0)
    _fade_in_text(surface, "= 12", (160, 134), palette.YELLOW, 16, t, 1.5)


def _comm_slide_2(surface, t):
    _slide_title(surface, "3 x 4  =  4 x 3", palette.CYAN, t)
    _dot_grid(surface, 3, 4, 52, 78, palette.CYAN, t, delay=0.4)
    _fade_in_text(surface, "12", (88, 130), palette.YELLOW, 18, t, 1.2, align="center")
    _fade_in_text(surface, "=", (160, 100), palette.WHITE, 28, t, 1.6, align="center")
    _dot_grid(surface, 4, 3, 178, 74, palette.GREEN, t, delay=2.0)
    _fade_in_text(surface, "12", (208, 130), palette.YELLOW, 18, t, 2.8, align="center")
    _fade_in_text(surface, "ORDER DOESN'T CHANGE THE ANSWER!",
                  (160, 152), palette.GRAY, 11, t, 3.2)


# -- associative slides ------------------------------------------------------
# Idea: show (2×3)×4 grouped one way → result, then 2×(3×4) → same result.

def _assoc_slide_0(surface, t):
    _slide_title(surface, "GROUP THEM YOUR WAY", palette.MAGENTA, t)
    _fade_in_text(surface, "WHAT IF YOU HAVE THREE NUMBERS?",
                  (160, 50), palette.GRAY, 12, t, 0.6)
    _fade_in_text(surface, "2  x  3  x  4", (160, 85), palette.WHITE, 22, t, 1.2, align="center")
    _fade_in_text(surface, "WHICH PAIR DO YOU MULTIPLY FIRST?",
                  (160, 115), palette.GRAY, 12, t, 2.0)


def _assoc_slide_1(surface, t):
    _slide_title(surface, "GROUP THEM YOUR WAY", palette.MAGENTA, t)
    # Left: (2×3) first, then ×4
    _fade_in_text(surface, "(2 x 3)  x  4", (160, 50), palette.CYAN, 18, t, 0.3, align="center")
    _fade_in_text(surface, "= 6  x  4", (160, 75), palette.WHITE, 16, t, 1.0, align="center")
    _fade_in_text(surface, "= 24", (160, 98), palette.YELLOW, 22, t, 1.7, align="center")
    # Right: 2×(3×4) first
    _fade_in_text(surface, "2  x  (3 x 4)", (160, 124), palette.GREEN, 18, t, 2.4, align="center")
    _fade_in_text(surface, "= 2  x  12", (160, 146), palette.WHITE, 16, t, 3.1, align="center")
    _fade_in_text(surface, "= 24", (160, 166), palette.YELLOW, 22, t, 3.8, align="center")


def _assoc_slide_2(surface, t):
    _slide_title(surface, "SAME ANSWER EITHER WAY!", palette.MAGENTA, t)
    _fade_in_text(surface, "(2x3)x4", (100, 70), palette.CYAN, 18, t, 0.4, align="center")
    _fade_in_text(surface, "=", (160, 85), palette.WHITE, 22, t, 1.0, align="center")
    _fade_in_text(surface, "2x(3x4)", (220, 70), palette.GREEN, 18, t, 1.0, align="center")
    _fade_in_text(surface, "= 24", (160, 115), palette.YELLOW, 26, t, 1.6, align="center")
    _fade_in_text(surface, "GROUP HOWEVER YOU LIKE — IT DOESN'T MATTER!",
                  (160, 148), palette.GRAY, 11, t, 2.2)


# -- distributive slides -----------------------------------------------------
# Idea: show a rectangle split into two parts; label the shared side and each part.

def _dist_slide_0(surface, t):
    _slide_title(surface, "SPLIT AND SHARE", palette.ORANGE, t)
    _fade_in_text(surface, "IMAGINE 3 ROWS OF SEATS...",
                  (160, 50), palette.GRAY, 12, t, 0.6)
    # Big rectangle = 3 rows × (2+4) = 3×6
    _rect_grow(surface, pygame.Rect(68, 72, 184, 54), palette.ORANGE, t, delay=1.2)
    _fade_in_text(surface, "3 ROWS", (38, 94), palette.WHITE, 12, t, 1.8)
    _fade_in_text(surface, "2 + 4 = 6 SEATS WIDE", (160, 134), palette.GRAY, 12, t, 2.4)


def _dist_slide_1(surface, t):
    _slide_title(surface, "SPLIT AND SHARE", palette.ORANGE, t)
    _fade_in_text(surface, "NOW SPLIT IT INTO TWO SECTIONS:",
                  (160, 50), palette.GRAY, 12, t, 0.2)
    # Left block: 3×2
    _rect_grow(surface, pygame.Rect(68, 68, 60, 54), palette.CYAN, t, delay=0.7)
    _fade_in_text(surface, "3x2", (98, 90), palette.CYAN, 14, t, 1.3, align="center")
    _fade_in_text(surface, "=6", (98, 107), palette.YELLOW, 14, t, 1.7, align="center")
    # Right block: 3×4
    _rect_grow(surface, pygame.Rect(132, 68, 120, 54), palette.GREEN, t, delay=2.0)
    _fade_in_text(surface, "3x4", (192, 90), palette.GREEN, 14, t, 2.6, align="center")
    _fade_in_text(surface, "=12", (192, 107), palette.YELLOW, 14, t, 3.0, align="center")
    # Dividing line
    if t >= 0.7:
        pygame.draw.line(surface, palette.WHITE, (132, 68), (132, 122), 1)


def _dist_slide_2(surface, t):
    _slide_title(surface, "3 x (2+4)  =  3x2 + 3x4", palette.ORANGE, t)
    _fade_in_text(surface, "3  x  (2 + 4)", (160, 60), palette.CYAN, 18, t, 0.4, align="center")
    _fade_in_text(surface, "= 3x2  +  3x4", (160, 85), palette.WHITE, 16, t, 1.1, align="center")
    _fade_in_text(surface, "= 6  +  12", (160, 110), palette.WHITE, 16, t, 1.8, align="center")
    _fade_in_text(surface, "= 18", (160, 138), palette.YELLOW, 26, t, 2.5, align="center")
    _fade_in_text(surface, "SHARE THE OUTSIDE NUMBER WITH EACH PART!",
                  (160, 166), palette.GRAY, 11, t, 3.2)


# -- identity slides ---------------------------------------------------------

def _ident_slide_0(surface, t):
    _slide_title(surface, "TIMES ONE = ITSELF", palette.GREEN, t)
    _fade_in_text(surface, "WHAT HAPPENS WHEN YOU MULTIPLY BY 1?",
                  (160, 52), palette.GRAY, 12, t, 0.6)
    sprites.draw(surface, "star", (70, 80))
    sprites.draw(surface, "star", (90, 80))
    sprites.draw(surface, "star", (110, 80))
    _fade_in_text(surface, "3 STARS", (90, 100), palette.WHITE, 13, t, 1.4, align="center")
    _fade_in_text(surface, "x  1  GROUP", (90, 116), palette.CYAN, 13, t, 1.9, align="center")
    if t >= 2.5:
        pygame.draw.rect(surface, palette.dim(palette.CYAN, 0.3),
                         pygame.Rect(62, 76, 68, 46))
        pygame.draw.rect(surface, palette.CYAN, pygame.Rect(62, 76, 68, 46), 1)
    _fade_in_text(surface, "STILL 3 STARS!", (160, 148), palette.YELLOW, 16, t, 3.0, align="center")


def _ident_slide_1(surface, t):
    _slide_title(surface, "TIMES ONE = ITSELF", palette.GREEN, t)
    for i, n in enumerate([4, 7, 12]):
        delay = 0.5 + i * 1.4
        y = 60 + i * 36
        _fade_in_text(surface, f"{n}  x  1  =  {n}", (160, y),
                      palette.WHITE, 20, t, delay, align="center")
    _fade_in_text(surface, "1 IS THE IDENTITY — IT CHANGES NOTHING!",
                  (160, 160), palette.GRAY, 11, t, 4.8)


# -- zero slides -------------------------------------------------------------

def _zero_slide_0(surface, t):
    _slide_title(surface, "TIMES ZERO = ZERO", palette.RED, t)
    _fade_in_text(surface, "WHAT IF EACH GROUP HAS 0 THINGS?",
                  (160, 50), palette.GRAY, 12, t, 0.6)
    # Draw 5 empty boxes side by side
    for i in range(5):
        bx = 68 + i * 38
        box = pygame.Rect(bx, 75, 28, 28)
        pygame.draw.rect(surface, palette.DARK_GRAY, box)
        pygame.draw.rect(surface, palette.GRAY, box, 1)
        _fade_in_text(surface, "0", (bx + 14, 82), palette.GRAY, 14, t,
                      1.0 + i * 0.3, align="center")
    _fade_in_text(surface, "5  EMPTY  BOXES  =  0  TOTAL",
                  (160, 120), palette.WHITE, 14, t, 3.0, align="center")
    _fade_in_text(surface, "5  x  0  =  0", (160, 145), palette.YELLOW, 20, t, 3.8, align="center")


def _zero_slide_1(surface, t):
    _slide_title(surface, "TIMES ZERO = ZERO", palette.RED, t)
    for i, n in enumerate([3, 8, 100]):
        delay = 0.5 + i * 1.5
        y = 60 + i * 36
        _fade_in_text(surface, f"{n}  x  0  =  0", (160, y),
                      palette.WHITE, 20, t, delay, align="center")
    _fade_in_text(surface, "ZERO GROUPS OF ANYTHING IS ALWAYS ZERO!",
                  (160, 160), palette.GRAY, 11, t, 5.0)


# -- property definitions ----------------------------------------------------

_PROPERTIES = [
    {
        "name": "commutative",
        "property": "COMMUTATIVE",
        "title": "SWAP THE ORDER",
        "color": palette.CYAN,
        "slides": [_comm_slide_0, _comm_slide_1, _comm_slide_2],
    },
    {
        "name": "associative",
        "property": "ASSOCIATIVE",
        "title": "GROUP THEM YOUR WAY",
        "color": palette.MAGENTA,
        "slides": [_assoc_slide_0, _assoc_slide_1, _assoc_slide_2],
    },
    {
        "name": "distributive",
        "property": "DISTRIBUTIVE",
        "title": "SPLIT AND SHARE",
        "color": palette.ORANGE,
        "slides": [_dist_slide_0, _dist_slide_1, _dist_slide_2],
    },
    {
        "name": "identity",
        "property": "IDENTITY",
        "title": "TIMES ONE = ITSELF",
        "color": palette.GREEN,
        "slides": [_ident_slide_0, _ident_slide_1],
    },
    {
        "name": "zero",
        "property": "ZERO",
        "title": "TIMES ZERO = ZERO",
        "color": palette.RED,
        "slides": [_zero_slide_0, _zero_slide_1],
    },
]


# ---------------------------------------------------------------------------
# PropLearnScene — animated slideshow, no questions
# ---------------------------------------------------------------------------

class PropLearnScene(Scene):
    """Walk through all five multiplication properties as animated slides."""

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        # Flat list of (prop_index, slide_index) pairs in order.
        self._deck = [
            (pi, si)
            for pi, prop in enumerate(_PROPERTIES)
            for si in range(len(prop["slides"]))
        ]
        self._deck.append(None)   # sentinel for the summary card
        self._card = 0            # index into _deck
        self.slide_t = 0.0        # time elapsed on current slide
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=6)
        self.particles = ui.Particles()

    def on_enter(self):
        self.slide_t = 0.0

    def _total_slides(self):
        return len(self._deck) - 1   # -1 for summary sentinel

    def _go_back(self):
        if self._card > 0:
            sfx.play("back")
            self._card -= 1
            self.slide_t = 0.0

    def _advance(self):
        sfx.play("select")
        self._card += 1
        self.slide_t = 0.0
        if self._card >= len(self._deck):
            # Done — pop back to the menu.
            self.app.pop()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            if event.key == pygame.K_LEFT:
                self._go_back()
                return
            self._advance()
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._advance()

    def update(self, dt):
        self.time += dt
        self.slide_t += dt
        self.starfield.update(dt)
        self.particles.update(dt)

    def _draw_progress(self, surface, prop_index):
        """Five colored pips at the bottom — filled for completed properties."""
        for i, prop in enumerate(_PROPERTIES):
            color = prop["color"] if i <= prop_index else palette.DARK_GRAY
            cx = 148 + i * 10
            pygame.draw.circle(surface, color, (cx, 172), 3)
            if i == prop_index:
                pygame.draw.circle(surface, palette.WHITE, (cx, 172), 3, 1)

    def _draw_summary(self, surface, t):
        """Final card: all 5 property names in their colors."""
        bob = ui.title_wobble(t, 1.5, 1.8)
        ui.text(surface, "YOU LEARNED ALL 5 RULES!",
                (160, int(18 + bob)), palette.YELLOW, 20, align="center")
        for i, prop in enumerate(_PROPERTIES):
            # Property name (e.g. COMMUTATIVE) in color, subtitle in gray
            _fade_in_text(surface, prop["property"], (160, 50 + i * 24),
                          prop["color"], 14, t, i * 0.5, align="center")
            _fade_in_text(surface, prop["title"], (160, 60 + i * 24),
                          palette.GRAY, 11, t, i * 0.5 + 0.1, align="center")
        _fade_in_text(surface, "TRY RULES QUIZ WHEN YOU'RE READY!",
                      (160, 162), palette.GRAY, 11, t, 2.8)
        self.particles.confetti(320)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)

        entry = self._deck[self._card]

        if entry is None:
            # Summary card
            self._draw_summary(surface, self.slide_t)
            self.particles.draw(surface)
        else:
            pi, si = entry
            prop = _PROPERTIES[pi]
            # Draw slide content into the virtual surface
            prop["slides"][si](surface, self.slide_t)
            # Property type (e.g. COMMUTATIVE) + friendly title, always visible
            ui.text(surface, prop["property"], (4, 3), prop["color"], 14)
            ui.text(surface, prop["title"], (4, 13), palette.GRAY, 11)
            # Slide counter within this property (e.g. "1/3") — top-right
            slide_label = f"{si + 1}/{len(prop['slides'])}"
            ui.text(surface, slide_label, (316, 3), palette.DARK_GRAY, 12, align="right")
            # Pip progress row
            self._draw_progress(surface, pi)
            self.particles.draw(surface)

        ui.text(surface, "< BACK     TAP / ANY KEY TO CONTINUE",
                (160, 158), palette.DARK_GRAY, 11, align="center")
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


# ---------------------------------------------------------------------------
# PropQuizScene — 5 questions (one per property), no teach screens
# ---------------------------------------------------------------------------

def make_props_question(prop_name, tier):
    """Build one practice question for the given multiplication property."""
    tier = levels.clamp_tier(tier)

    if prop_name == "commutative":
        if tier <= 2:
            a, b = random.choice([2, 5, 10]), random.randint(1, 6)
        else:
            a, b = random.randint(2, 9), random.randint(2, 9)
        prompt, answer = f"{b} x {a} = ?", b * a

    elif prop_name == "associative":
        a, b, c = random.randint(2, 4), random.randint(2, 4), random.randint(2, 4)
        prompt, answer = f"({a}x{b})x{c} = ?", a * b * c

    elif prop_name == "distributive":
        shared = random.choice([2, 3, 4, 5])
        p, q = random.randint(2, 6), random.randint(2, 6)
        prompt, answer = f"{shared}x{p} + {shared}x{q} = ?", shared * (p + q)

    elif prop_name == "identity":
        n = random.randint(2, 12) if tier >= 2 else random.randint(1, 5)
        prompt, answer = f"{n} x 1 = ?", n

    else:  # zero
        n = random.randint(2, 20) if tier >= 2 else random.randint(1, 5)
        prompt, answer = f"{n} x 0 = ?", 0

    choices = [answer] + _distractors(answer)
    random.shuffle(choices)
    return {"kind": "expr", "prop": prop_name, "prompt": prompt,
            "answer": answer, "choices": choices}


_QUIZ_LENGTH = len(_PROPERTIES)   # 5 questions, one per property


class PropQuizScene(Scene):
    """One question per multiplication property — pure quiz, no teach screens."""

    def __init__(self, app, player, tier):
        super().__init__(app)
        self.player = player
        self.tier = levels.clamp_tier(tier)
        self.accent = palette.PURPLE
        self.index = 0        # which property we're on (0-4)
        self.correct = 0
        self.question = None
        self.buttons = []
        self.attempts = 0
        self.state = "asking"  # "asking" | "celebrating"
        self.state_timer = 0.0
        self.time = 0.0
        self.feedback = ""
        self.particles = ui.Particles()
        self.starfield = ui.Starfield(320, 180, count=50, speed=10)

    def on_enter(self):
        if self.question is None:
            self._load_question()

    def _prop(self):
        return _PROPERTIES[self.index]

    def _load_question(self):
        self.question = make_props_question(self._prop()["name"], self.tier)
        self.attempts = 0
        self.state = "asking"
        self.feedback = ""
        rects = _layout(len(self.question["choices"]))
        widest = max(len(str(v)) for v in self.question["choices"])
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

    def _answer(self, button):
        if self.state != "asking" or button.locked:
            return
        if button.value == self.question["answer"]:
            if self.attempts == 0:
                self.correct += 1
            self.state = "celebrating"
            self.state_timer = 1.1
            button.set_flash(palette.GREEN, 1.1)
            self.particles.burst(button.rect.center, palette.GREEN, count=18, speed=90)
            self.feedback = random.choice(["YES!", "NICE!", "WOW!", "GOT IT!"])
            sfx.play("correct")
            sfx.play("launch")
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

    def _next(self):
        self.index += 1
        if self.index >= _QUIZ_LENGTH:
            self._finish()
        else:
            self._load_question()

    def _finish(self):
        self.app.replace(
            ResultsScene(
                self.app,
                self.player,
                f"{GAME_KEY}_props",
                "RULES QUIZ",
                self.correct,
                _QUIZ_LENGTH,
                lambda app: app.replace(
                    PropQuizScene(app, self.player, self.tier)
                ),
                detail=f"LEVEL {levels.tier_name(self.tier)}",
            )
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            if self.state == "asking":
                for i, key in enumerate((pygame.K_1, pygame.K_2, pygame.K_3)):
                    if event.key == key and i < len(self.buttons):
                        self._answer(self.buttons[i])
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
                self._next()

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)

        prop = self._prop()
        ui.text(surface, "RULES QUIZ", (4, 3), self.accent, 14)
        ui.text(surface, f"{self.index + 1}/{_QUIZ_LENGTH}",
                (316, 3), palette.WHITE, 14, align="right")
        ui.bar(surface, (4, 16, 312, 3), self.index / _QUIZ_LENGTH, self.accent)

        if self.question:
            area = pygame.Rect(14, 26, 292, 84)
            ui.panel(surface, area, palette.BG_PANEL, prop["color"])
            # Property type + friendly title as reminder badge
            ui.text(surface, prop["property"], (area.x + 4, area.y + 4),
                    prop["color"], 11)
            ui.text(surface, prop["title"], (area.x + 4, area.y + 13),
                    palette.GRAY, 11)
            bob = ui.title_wobble(self.time, 1.5, 2.0)
            size = 46 if len(self.question["prompt"]) <= 12 else 30
            ui.text(surface, self.question["prompt"],
                    (160, int(area.y + 28 + bob)), palette.WHITE, size, align="center")

        for button in self.buttons:
            button.draw(surface)

        if self.feedback:
            color = palette.GREEN if self.state == "celebrating" else palette.ORANGE
            ui.text(surface, self.feedback, (160, 112), color, 16, align="center")

        self.particles.draw(surface)
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


class MathMenuScene(Scene):
    """Pick a mode. Which ones are offered depends on the player's age."""

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.nudge = player.nudge
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
        self.nudge = self.player.nudge
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
                self.player.set_nudge(button.value)
                sfx.play("click")
                return

    def _start(self, mode):
        sfx.play("select")
        if mode == "props_learn":
            self.app.push(PropLearnScene(self.app, self.player))
        elif mode == "props_quiz":
            self.app.push(PropQuizScene(self.app, self.player, self.tier))
        else:
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
