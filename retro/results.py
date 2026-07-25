"""The end-of-round celebration screen, shared by every game.

There is no "you lose" here. A short round always ends with confetti, a star
count and an invitation to play again -- the worst case is simply fewer stars.
"""

import pygame

from . import palette, sfx, sprites, ui
from .app import Scene


class ResultsScene(Scene):
    """Shown after a round. on_replay(app) starts a fresh round of the game."""

    def __init__(
        self, app, player, game_key, title, correct, total, on_replay, detail=None
    ):
        super().__init__(app)
        self.player = player
        self.game_key = game_key
        self.title = title
        self.correct = correct
        self.total = total
        self.on_replay = on_replay
        # Optional extra line, e.g. typing accuracy and speed.
        self.detail = detail
        self.particles = ui.Particles()
        self.stars_field = ui.Starfield(320, 180, count=40, speed=8)
        self.time = 0.0
        self.revealed = 0          # Stars shown so far, revealed one by one.
        self.reveal_timer = 0.6
        self.is_record = False
        self.buttons = [
            ui.Button((60, 146, 90, 26), "PLAY AGAIN", palette.GREEN, hotkey="1"),
            ui.Button((170, 146, 90, 26), "MENU", palette.CYAN, hotkey="2"),
        ]

    @property
    def earned(self):
        return self.correct

    def on_enter(self):
        self.time = 0.0
        self.revealed = 0
        self.reveal_timer = 0.6
        self.particles.confetti(320, count=50)
        self.is_record = self.player.record_round(self.game_key, self.correct, self.total)
        self.player.add_stars(self.earned)
        sfx.play("fanfare")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_RETURN, pygame.K_SPACE):
                self._replay()
                return
            if event.key in (pygame.K_2, pygame.K_ESCAPE):
                self._menu()
                return
        for index, button in enumerate(self.buttons):
            if button.handle_event(event):
                (self._replay if index == 0 else self._menu)()

    def _replay(self):
        sfx.play("select")
        self.on_replay(self.app)

    def _menu(self):
        sfx.play("back")
        self.app.pop()

    def update(self, dt):
        self.time += dt
        self.stars_field.update(dt)
        self.particles.update(dt)
        for button in self.buttons:
            button.update(dt)
        if self.revealed < self.earned:
            self.reveal_timer -= dt
            if self.reveal_timer <= 0:
                self.revealed += 1
                self.reveal_timer = 0.16
                sfx.play("star")

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.stars_field.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface, "GREAT JOB!", (160, int(14 + wobble)), palette.YELLOW, 34, align="center"
        )
        ui.text(surface, self.title, (160, 42), palette.CYAN, 16, align="center")
        ui.text(
            surface,
            f"{self.correct} OUT OF {self.total} RIGHT",
            (160, 58),
            palette.WHITE,
            18,
            align="center",
        )

        # Earned stars, revealed one at a time with a little chime.
        shown = min(self.earned, 10)
        start_x = 160 - (shown * 18) // 2
        for index in range(shown):
            if index >= self.revealed:
                break
            sprites.draw(surface, "star", (start_x + index * 18, 78), scale=1)
        if self.earned > 10 and self.revealed >= 10:
            ui.text(surface, f"+{self.earned - 10}", (160, 96), palette.YELLOW, 14, align="center")

        if self.is_record and self.revealed >= self.earned:
            ui.text(
                surface, "NEW BEST SCORE!", (160, 110), palette.MAGENTA, 18, align="center"
            )
        if self.detail:
            ui.text(surface, self.detail, (160, 122), palette.CYAN, 14, align="center")
        ui.text(
            surface,
            f"TOTAL STARS: {self.player.stars}",
            (160, 134) if self.detail else (160, 130),
            palette.WHITE,
            14,
            align="center",
        )
        for button in self.buttons:
            button.draw(surface)
        self.particles.draw(surface)
