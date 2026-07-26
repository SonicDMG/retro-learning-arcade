"""The scoreboard: what a player has done, per game and per mode.

Not a game, but it lives here because it has to know about all of them. The
save file has been recording best scores and rounds played since the start;
this is the screen that finally shows a child their own progress.

One registry describes every game and every mode it can save under, and a
test checks it against what the games actually write -- otherwise a new mode
would quietly never appear here.
"""

import pygame

from retro import levels, palette, sfx, sprites, ui
from retro.app import Scene

from . import crystal_keys, logic_lab, math_blaster, pattern_power, word_rocket


def _math_modes():
    return [(key, MODE[0]) for key, MODE in math_blaster.MODES.items()]


def _word_modes():
    return [(key, label) for key, label, _, _ in word_rocket.MODES]


def _pattern_modes():
    return [(key, label) for key, label, _, _ in pattern_power.MODES]


def _typing_modes():
    return [(key, label) for key, label, _, _, _ in crystal_keys.ELEMENTS]


def _logic_modes():
    return [(key, label) for key, (label, _) in logic_lab.MODES.items()]


# title, icon, colour, save prefix, questions per round, modes
GAME_RECORDS = [
    ("NUMBER BLASTER", "rocket", palette.GREEN, math_blaster.GAME_KEY,
     math_blaster.ROUND_LENGTH, _math_modes()),
    ("WORD ROCKET", "book", palette.CYAN, word_rocket.GAME_KEY,
     word_rocket.ROUND_LENGTH, _word_modes()),
    ("PATTERN POWER", "star", palette.MAGENTA, pattern_power.GAME_KEY,
     pattern_power.ROUND_LENGTH, _pattern_modes()),
    ("CRYSTAL KEYS", "crystal", palette.PURPLE, crystal_keys.GAME_KEY,
     crystal_keys.ROUND_LENGTH, _typing_modes()),
    ("LOGIC LAB", "leaf", palette.ORANGE, logic_lab.GAME_KEY,
     logic_lab.ROUND_LENGTH, _logic_modes()),
]


def game_totals(player, record):
    """Rounds played and best score for one game, across all its modes."""
    _, _, _, prefix, per_round, modes = record
    best = player.entry.get("best", {})
    played = player.entry.get("played", {})
    rounds = sum(played.get(f"{prefix}_{mode}", 0) for mode, _ in modes)
    top = max([best.get(f"{prefix}_{mode}", 0) for mode, _ in modes] or [0])
    return rounds, top, per_round


def total_rounds(player):
    return sum(game_totals(player, record)[0] for record in GAME_RECORDS)


def _row_bar(surface, x, y, fraction, color, width=42, height=5):
    ui.bar(surface, (x, y, width, height), fraction, color)


class ScoreboardScene(Scene):
    """One row per game: rounds played, best score, and a progress bar."""

    ROW_TOP = 56
    ROW_HEIGHT = 16

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=7)
        self.rows = []
        for index, record in enumerate(GAME_RECORDS):
            rect = pygame.Rect(4, self.ROW_TOP + index * self.ROW_HEIGHT, 312, self.ROW_HEIGHT - 2)
            self.rows.append((rect, record))
        self.hover_index = None

    def on_enter(self):
        from retro import progress

        self.player = progress.Player(self.player.name)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5)
            for index, key in enumerate(keys):
                if event.key == key and index < len(self.rows):
                    self._open(index)
                    return
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = None
            for index, (rect, _) in enumerate(self.rows):
                if rect.collidepoint(event.pos):
                    self.hover_index = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, (rect, _) in enumerate(self.rows):
                if rect.collidepoint(event.pos):
                    self._open(index)
                    return

    def _open(self, index):
        sfx.play("select")
        self.app.push(GameDetailScene(self.app, self.player, GAME_RECORDS[index]))

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        wobble = ui.title_wobble(self.time, 1.5)
        ui.text(
            surface,
            f"{self.player.name.upper()}'S SCOREBOARD",
            (160, int(4 + wobble)),
            palette.YELLOW,
            24,
            align="center",
        )

        # Totals strip.
        sprites.draw(surface, "star", (8, 24))
        ui.text(surface, f"{self.player.stars}", (26, 28), palette.YELLOW, 14)
        sprites.draw(surface, "crystal", (74, 24))
        ui.text(surface, f"{self.player.total_crystals()}", (92, 28), palette.MAGENTA, 14)
        rounds = total_rounds(self.player)
        ui.text(surface, f"{rounds} ROUNDS", (150, 28), palette.WHITE, 14)
        age = self.player.age
        if age:
            ui.text(
                surface,
                f"AGE {age} - {levels.tier_name(self.player.tier())}",
                (316, 28),
                palette.GRAY,
                12,
                align="right",
            )

        if rounds == 0:
            # No column headings over an empty table.
            ui.text(
                surface,
                "NO ROUNDS YET - GO AND PLAY!",
                (160, 90),
                palette.WHITE,
                16,
                align="center",
            )
            ui.text(
                surface,
                "EVERY ROUND YOU FINISH SHOWS UP HERE",
                (160, 110),
                palette.GRAY,
                12,
                align="center",
            )
        else:
            ui.text(surface, "GAME", (8, 46), palette.GRAY, 11)
            ui.text(surface, "PLAYED", (218, 46), palette.GRAY, 11, align="right")
            ui.text(surface, "BEST", (262, 46), palette.GRAY, 11, align="right")
            for index, (rect, record) in enumerate(self.rows):
                title, icon, color, _, _, _ = record
                played, best, per_round = game_totals(self.player, record)
                if index == self.hover_index:
                    pygame.draw.rect(surface, palette.dim(color, 0.3), rect)
                sprites.draw(surface, icon, (rect.x + 2, rect.y))
                ui.text(surface, title, (rect.x + 22, rect.y + 2), color, 12)
                ui.text(
                    surface, str(played), (218, rect.y + 2), palette.WHITE, 12, align="right"
                )
                ui.text(
                    surface,
                    f"{best}/{per_round}" if played else "-",
                    (262, rect.y + 2),
                    palette.WHITE if played else palette.DARK_GRAY,
                    12,
                    align="right",
                )
                _row_bar(
                    surface, 270, rect.y + 4, best / per_round if played else 0.0, color
                )

        ui.text(
            surface,
            "CLICK A GAME FOR DETAILS       ESC = BACK",
            (160, 168),
            palette.DARK_GRAY,
            12,
            align="center",
        )


class GameDetailScene(Scene):
    """Every mode of one game, so progress shows up mode by mode."""

    def __init__(self, app, player, record):
        super().__init__(app)
        self.player = player
        self.record = record
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=30, speed=6)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            sfx.play("back")
            self.app.pop()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sfx.play("back")
            self.app.pop()

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)

    def draw(self, surface):
        title, icon, color, prefix, per_round, modes = self.record
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        sprites.draw(surface, icon, (8, 6), scale=1)
        ui.text(surface, title, (160, 6), color, 22, align="center")

        best = self.player.entry.get("best", {})
        played = self.player.entry.get("played", {})
        ui.text(surface, "MODE", (8, 32), palette.GRAY, 11)
        ui.text(surface, "PLAYED", (218, 32), palette.GRAY, 11, align="right")
        ui.text(surface, "BEST", (262, 32), palette.GRAY, 11, align="right")

        top = 44
        height = min(16, (150 - top) // max(1, len(modes)))
        for index, (mode, label) in enumerate(modes):
            key = f"{prefix}_{mode}"
            rounds = played.get(key, 0)
            score = best.get(key, 0)
            y = top + index * height
            ui.text(surface, label, (8, y), palette.WHITE if rounds else palette.GRAY, 12)
            ui.text(
                surface, str(rounds), (218, y), palette.WHITE if rounds else palette.DARK_GRAY, 12, align="right"
            )
            ui.text(
                surface,
                f"{score}/{per_round}" if rounds else "-",
                (262, y),
                palette.WHITE if rounds else palette.DARK_GRAY,
                12,
                align="right",
            )
            _row_bar(surface, 270, y + 2, score / per_round if rounds else 0.0, color)

        if self.record[3] == crystal_keys.GAME_KEY:
            crystals = self.player.crystals
            summary = "  ".join(
                f"{label[:1]}{crystals.get(key, 0)}"
                for key, label in modes
            )
            ui.text(surface, f"CRYSTALS  {summary}", (160, 152), palette.MAGENTA, 12, align="center")

        ui.text(
            surface, "ESC = BACK", (160, 168), palette.DARK_GRAY, 12, align="center"
        )


def launch(app, player):
    app.push(ScoreboardScene(app, player))
