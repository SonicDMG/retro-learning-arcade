"""Logic Lab -- reasoning puzzles in the style of an IQ test.

Four kinds of item, all of them non-verbal except the number sequences:

    ODD ONE OUT  four figures, three share a property and one does not
    ANALOGY      A is to B as C is to ?
    MATRIX       a grid where the row sets the shape and the column the
                 colour, with one cell missing -- the classic matrix item
    SEQUENCE     number series with a rule to spot

Figures are drawn from primitives rather than sprites, so shape, colour and
size can vary independently. That is what lets an item test one property
while deliberately scrambling the others.
"""

import random

import pygame

from retro import levels, palette, sfx, ui
from retro.app import Scene
from retro.results import ResultsScene

GAME_KEY = "logic"
ROUND_LENGTH = 8

SHAPES = ["circle", "square", "triangle", "diamond"]
COLORS = [palette.CYAN, palette.MAGENTA, palette.YELLOW, palette.GREEN, palette.ORANGE]

MODES = {
    "odd": ("ODD ONE OUT", palette.MAGENTA),
    "analogy": ("ANALOGY", palette.CYAN),
    "matrix": ("MATRIX", palette.GREEN),
    "sequence": ("SEQUENCES", palette.ORANGE),
}

MODES_BY_TIER = {
    1: ["odd", "matrix"],
    2: ["odd", "analogy", "matrix", "sequence"],
    3: ["odd", "analogy", "matrix", "sequence"],
    4: ["odd", "analogy", "matrix", "sequence"],
}


def draw_figure(surface, center, figure, scale=1.0):
    """Draw one figure. A figure is (shape, colour, radius)."""
    shape, color, radius = figure
    radius = max(2, int(radius * scale))
    x, y = int(center[0]), int(center[1])
    edge = palette.lighten(color, 0.45)
    if shape == "circle":
        pygame.draw.circle(surface, color, (x, y), radius)
        pygame.draw.circle(surface, edge, (x, y), radius, 1)
    elif shape == "square":
        rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, edge, rect, 1)
    elif shape == "triangle":
        points = [(x, y - radius), (x - radius, y + radius), (x + radius, y + radius)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, edge, points, 1)
    else:  # diamond
        points = [(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, edge, points, 1)


def _figure(shape, color, radius=10):
    return (shape, color, radius)


# -- item generators -------------------------------------------------------


def _paired(values):
    """Four values built from two, each used twice, in random order.

    Noise attributes are laid out this way so none of them singles out an
    item. If sizes were random, a lone big circle would be just as defensibly
    "the odd one" as the intended answer, and the puzzle would have two
    right answers.
    """
    first, second = values
    mixed = [first, first, second, second]
    random.shuffle(mixed)
    return mixed


def _odd_one_out(tier):
    """Three figures share a property; exactly one breaks it."""
    shapes = random.sample(SHAPES, 2)
    colors = random.sample(COLORS, 2)
    sizes = random.sample([8, 10, 12], 2)
    by_shape = random.random() < 0.5

    if by_shape:
        keep, other = shapes
        kinds = [keep, keep, keep, other]
        odd_index = 3
        paints = _paired(colors)
        reason = "shape"
    else:
        keep_color, other_color = colors
        kinds = _paired(shapes)
        paints = [keep_color, keep_color, keep_color, other_color]
        odd_index = 3
        reason = "colour"

    radii = _paired(sizes)
    items = [
        _figure(kinds[i], paints[i], radii[i]) for i in range(4)
    ]
    odd = items[odd_index]
    order = list(range(4))
    random.shuffle(order)
    options = [items[i] for i in order]
    return {
        "mode": "odd",
        "prompt": "WHICH ONE IS DIFFERENT?",
        "options": options,
        "answer": order.index(odd_index),
        "reason": reason,
    }


def _analogy(tier):
    """A is to B as C is to ?, over colour, shape or size."""
    kind = random.choice(["color", "shape", "size"] if tier >= 2 else ["color", "shape"])
    shape_a, shape_b = random.sample(SHAPES, 2)
    color_a, color_b = random.sample(COLORS, 2)

    if kind == "color":
        # Same shape, colour changes: A->B recolours, so C->? recolours too.
        first = (_figure(shape_a, color_a), _figure(shape_a, color_b))
        second = (_figure(shape_b, color_a), _figure(shape_b, color_b))
        wrong = [
            _figure(shape_b, color_a),
            _figure(shape_a, color_b),
            _figure(shape_a, color_a),
        ]
    elif kind == "shape":
        first = (_figure(shape_a, color_a), _figure(shape_b, color_a))
        second = (_figure(shape_a, color_b), _figure(shape_b, color_b))
        wrong = [
            _figure(shape_a, color_b),
            _figure(shape_b, color_a),
            _figure(shape_a, color_a),
        ]
    else:  # size
        first = (_figure(shape_a, color_a, 7), _figure(shape_a, color_a, 13))
        second = (_figure(shape_b, color_b, 7), _figure(shape_b, color_b, 13))
        wrong = [
            _figure(shape_b, color_b, 7),
            _figure(shape_a, color_b, 13),
            _figure(shape_b, color_a, 13),
        ]

    answer = second[1]
    options = [answer]
    for item in wrong:
        if item not in options:
            options.append(item)
    guard = 0
    while len(options) < 4 and guard < 40:
        guard += 1
        candidate = _figure(
            random.choice(SHAPES), random.choice(COLORS), random.choice([7, 10, 13])
        )
        if candidate not in options:
            options.append(candidate)
    random.shuffle(options)
    return {
        "mode": "analogy",
        "prompt": "FINISH THE PAIR",
        "rows": (first, second),
        "options": options,
        "answer": options.index(answer),
    }


def _matrix(tier):
    """Rows fix the shape, columns fix the colour; one cell is missing."""
    size = 2 if tier <= 1 else 3
    shapes = random.sample(SHAPES, size)
    colors = random.sample(COLORS, size)
    grid = [[_figure(shapes[row], colors[column]) for column in range(size)] for row in range(size)]
    answer = grid[size - 1][size - 1]

    wrong_shape = random.choice([s for s in SHAPES if s != shapes[-1]])
    wrong_color = random.choice([c for c in COLORS if c != colors[-1]])
    options = [
        answer,
        _figure(shapes[-1], wrong_color),
        _figure(wrong_shape, colors[-1]),
        _figure(wrong_shape, wrong_color),
    ]
    random.shuffle(options)
    return {
        "mode": "matrix",
        "prompt": "WHICH PIECE IS MISSING?",
        "grid": grid,
        "size": size,
        "options": options,
        "answer": options.index(answer),
    }


def _sequence(tier):
    """A number series with a rule to spot."""
    shown = 5
    if tier <= 2:
        rules = ["add", "double", "alternate"]
    elif tier == 3:
        rules = ["add", "double", "alternate", "multiply", "triangular"]
    else:
        rules = ["multiply", "square", "fibonacci", "triangular", "alternate"]
    rule = random.choice(rules)

    if rule == "add":
        start, step = random.randint(1, 12), random.choice([2, 3, 4, 5, 10])
        items = [start + step * i for i in range(shown + 1)]
    elif rule == "double":
        start = random.randint(1, 6)
        items = [start * (2 ** i) for i in range(shown + 1)]
    elif rule == "multiply":
        start, ratio = random.randint(1, 4), random.choice([3, 4])
        items = [start * (ratio ** i) for i in range(shown + 1)]
    elif rule == "alternate":
        start = random.randint(1, 10)
        first, second = random.sample([2, 3, 5, 7, 10], 2)
        items, value = [start], start
        for i in range(shown):
            value += first if i % 2 == 0 else second
            items.append(value)
    elif rule == "square":
        offset = random.randint(1, 4)
        items = [(i + offset) ** 2 for i in range(shown + 1)]
    elif rule == "triangular":
        offset = random.randint(1, 3)
        items = [(i + offset) * (i + offset + 1) // 2 for i in range(shown + 1)]
    else:  # fibonacci
        first, second = random.randint(1, 4), random.randint(2, 6)
        items = [first, second]
        for _ in range(shown - 1):
            items.append(items[-1] + items[-2])

    answer = items[shown]
    gap = max(1, abs(items[shown] - items[shown - 1]))
    candidates = {answer + gap, answer - gap, answer + 1, answer - 1, items[shown - 1]}
    candidates.discard(answer)
    pool = [value for value in candidates if value >= 0]
    random.shuffle(pool)
    options = [answer] + pool[:2]
    guard = 0
    while len(options) < 3 and guard < 40:
        guard += 1
        candidate = answer + random.randint(2, 9)
        if candidate not in options:
            options.append(candidate)
    random.shuffle(options)
    return {
        "mode": "sequence",
        "prompt": "WHAT COMES NEXT?",
        "items": items[:shown],
        "options": options,
        "answer": options.index(answer),
        "rule": rule,
    }


GENERATORS = {
    "odd": _odd_one_out,
    "analogy": _analogy,
    "matrix": _matrix,
    "sequence": _sequence,
}


def make_question(mode, tier):
    return GENERATORS[mode](levels.clamp_tier(tier))


# -- scenes ----------------------------------------------------------------


def _option_rects(count, top=120, height=40):
    margin, gap = 12, 8
    total = 320 - margin * 2
    width = (total - gap * (count - 1)) // count
    return [
        pygame.Rect(margin + index * (width + gap), top, width, height)
        for index in range(count)
    ]


class LogicRoundScene(Scene):
    """Eight reasoning items of one kind."""

    def __init__(self, app, player, mode, tier):
        super().__init__(app)
        self.player = player
        self.mode = mode
        self.tier = levels.clamp_tier(tier)
        self.label, self.accent = MODES[mode]
        self.index = 0
        self.correct = 0
        self.attempts = 0
        self.question = None
        self.buttons = []
        self.state = "asking"
        self.state_timer = 0.0
        self.time = 0.0
        self.feedback = ""
        self.particles = ui.Particles()
        self.starfield = ui.Starfield(320, 180, count=40, speed=7)
        self.hint = ui.HintTimer(14.0)

    def on_enter(self):
        if self.question is None:
            self._next_question()

    def _next_question(self):
        if self.index >= ROUND_LENGTH:
            self._finish()
            return
        self.index += 1
        self.question = make_question(self.mode, self.tier)
        self.attempts = 0
        self.state = "asking"
        self.feedback = ""
        self.hint.reset()
        self._build_buttons()

    def _build_buttons(self):
        question = self.question
        options = question["options"]
        if question["mode"] == "odd":
            # The figures themselves are the choices, shown large.
            rects = [pygame.Rect(12 + index * 76, 46, 62, 62) for index in range(4)]
        elif question["mode"] == "sequence":
            rects = _option_rects(len(options), top=118, height=40)
        else:
            rects = _option_rects(len(options), top=120, height=38)

        self.buttons = []
        for slot, (rect, option) in enumerate(zip(rects, options)):
            is_number = question["mode"] == "sequence"
            self.buttons.append(
                ui.Button(
                    rect,
                    str(option) if is_number else "",
                    palette.ACCENTS[slot % len(palette.ACCENTS)],
                    hotkey=str(slot + 1),
                    text_size=24 if is_number else 16,
                    value=slot,
                )
            )

    def _finish(self):
        self.app.replace(
            ResultsScene(
                self.app,
                self.player,
                f"{GAME_KEY}_{self.mode}",
                self.label,
                self.correct,
                ROUND_LENGTH,
                lambda app: app.replace(
                    LogicRoundScene(app, self.player, self.mode, self.tier)
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
            self.state = "celebrating"
            self.state_timer = 1.1
            button.set_flash(palette.GREEN, 1.1)
            self.particles.burst(button.rect.center, palette.GREEN, count=18, speed=85)
            self.feedback = random.choice(["YES!", "SHARP!", "GOT IT!", "CLEVER!"])
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
                keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
                for index, key in enumerate(keys):
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

    def _draw_cell(self, surface, rect, figure, border=None):
        pygame.draw.rect(surface, palette.BG_PANEL, rect)
        pygame.draw.rect(surface, border or palette.DARK_GRAY, rect, 1)
        if figure is not None:
            draw_figure(surface, rect.center, figure)

    def _draw_matrix(self, surface):
        question = self.question
        size = question["size"]
        cell, gap = 24, 3
        span = size * cell + (size - 1) * gap
        start_x = 160 - span // 2
        start_y = 34
        for row in range(size):
            for column in range(size):
                rect = pygame.Rect(
                    start_x + column * (cell + gap), start_y + row * (cell + gap), cell, cell
                )
                last = row == size - 1 and column == size - 1
                if last:
                    self._draw_cell(surface, rect, None, palette.YELLOW)
                    ui.text(surface, "?", (rect.centerx, rect.y + 4), palette.YELLOW, 24, align="center")
                else:
                    self._draw_cell(surface, rect, question["grid"][row][column])

    def _draw_analogy(self, surface):
        (a, b), (c, _) = self.question["rows"]
        for row_index, (left, right, unknown) in enumerate(
            ((a, b, False), (c, None, True))
        ):
            y = 42 + row_index * 38
            left_rect = pygame.Rect(100, y, 30, 30)
            right_rect = pygame.Rect(180, y, 30, 30)
            self._draw_cell(surface, left_rect, left)
            ui.text(surface, "->", (145, y + 8), palette.GRAY, 18, align="center")
            if unknown:
                self._draw_cell(surface, right_rect, None, palette.YELLOW)
                ui.text(
                    surface, "?", (right_rect.centerx, right_rect.y + 5), palette.YELLOW, 24, align="center"
                )
            else:
                self._draw_cell(surface, right_rect, right)

    def _draw_sequence(self, surface):
        items = self.question["items"]
        count = len(items) + 1
        cell, gap = 44, 4
        span = count * cell + (count - 1) * gap
        cell = 44 if span <= 300 else 40
        span = count * cell + (count - 1) * gap
        start_x = 160 - span // 2
        y = 52
        for index in range(count):
            rect = pygame.Rect(start_x + index * (cell + gap), y, cell, 34)
            known = index < len(items)
            pygame.draw.rect(surface, palette.BG_PANEL, rect)
            pygame.draw.rect(
                surface, self.accent if known else palette.YELLOW, rect, 1
            )
            value = str(items[index]) if known else "?"
            size = 24 if len(value) <= 3 else 18
            ui.text(
                surface,
                value,
                (rect.centerx, rect.y + (7 if size == 24 else 10)),
                palette.WHITE if known else palette.YELLOW,
                size,
                align="center",
            )

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        ui.text(surface, self.label, (4, 3), self.accent, 14)
        ui.text(
            surface, f"{self.index}/{ROUND_LENGTH}", (316, 3), palette.WHITE, 14, align="right"
        )
        ui.bar(surface, (4, 16, 312, 3), (self.index - 1) / ROUND_LENGTH, self.accent)

        if self.question:
            mode = self.question["mode"]
            ui.text(surface, self.question["prompt"], (160, 22), palette.WHITE, 16, align="center")
            if mode == "matrix":
                self._draw_matrix(surface)
            elif mode == "analogy":
                self._draw_analogy(surface)
            elif mode == "sequence":
                self._draw_sequence(surface)

            for slot, button in enumerate(self.buttons):
                button.draw(surface)
                if mode != "sequence":
                    draw_figure(
                        surface,
                        button.rect.center,
                        self.question["options"][slot],
                        scale=1.4 if mode == "odd" else 1.0,
                    )

        self.particles.draw(surface)
        if self.feedback:
            color = palette.GREEN if self.state == "celebrating" else palette.ORANGE
            ui.text(surface, self.feedback, (160, 110), color, 16, align="center")
        elif self.hint.ready and self.state == "asking":
            ui.text(surface, "LOOK AT EACH ROW...", (160, 110), palette.GRAY, 13, align="center")
        ui.text(surface, "ESC = MENU", (316, 166), palette.DARK_GRAY, 12, align="right")


class LogicMenuScene(Scene):
    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.nudge = player.nudge
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=7)
        self.buttons = []
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
        self._build_modes()

    @property
    def tier(self):
        return self.player.tier(self.nudge)

    def _build_modes(self):
        available = MODES_BY_TIER[levels.tier_for_age(self.player.age)]
        self.buttons = []
        for index, key in enumerate(available):
            label, color = MODES[key]
            column, row = index % 2, index // 2
            rect = pygame.Rect(28 + column * 136, 44 + row * 38, 128, 32)
            self.buttons.append(
                ui.Button(rect, label, color, hotkey=str(index + 1), text_size=14, value=key)
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
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
            for index, key in enumerate(keys):
                if event.key == key and index < len(self.buttons):
                    self._start(self.buttons[index].value)
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
        self.app.push(LogicRoundScene(self.app, self.player, mode, self.tier))

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
            surface, "LOGIC LAB", (160, int(8 + wobble)), palette.GREEN, 30, align="center"
        )
        ui.text(surface, "ESC = BACK", (316, 4), palette.DARK_GRAY, 12, align="right")
        for button in self.buttons:
            button.draw(surface)
        ui.text(surface, "LEVEL", (6, 136), palette.WHITE, 12)
        for button in self.nudge_buttons:
            button.color = palette.YELLOW if button.value == self.nudge else palette.PURPLE
            button.draw(surface)
        age = self.player.age
        ui.text(
            surface,
            f"{'AGE ' + str(age) if age else 'AGE NOT SET'}   -   {levels.tier_name(self.tier)}",
            (160, 158),
            palette.GRAY,
            13,
            align="center",
        )


def launch(app, player):
    app.push(LogicMenuScene(app, player))
