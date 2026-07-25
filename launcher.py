#!/usr/bin/env python3
"""Retro Learning Arcade -- the front end that ties the games together.

Run this file to play:  python3 launcher.py
"""

import sys

import pygame

from games import crystal_keys, math_blaster, pattern_power, word_rocket
from retro import palette, progress, sfx, sprites, ui
from retro.app import App, Scene

GAMES = [
    ("NUMBER BLASTER", "COUNT AND ADD", "rocket", palette.GREEN, math_blaster.launch),
    ("WORD ROCKET", "LETTERS", "book", palette.CYAN, word_rocket.launch),
    ("PATTERN POWER", "WHAT'S NEXT?", "star", palette.MAGENTA, pattern_power.launch),
    ("CRYSTAL KEYS", "TYPING", "crystal", palette.PURPLE, crystal_keys.launch),
]


class ProfileScene(Scene):
    """Who is playing? Kids pick a picture instead of typing a name."""

    def __init__(self, app):
        super().__init__(app)
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=50, speed=9)
        self.buttons = []
        for index, (name, sprite) in enumerate(progress.PROFILES):
            rect = pygame.Rect(22 + index * 96, 66, 84, 76)
            self.buttons.append(
                ui.Button(
                    rect,
                    name.upper(),
                    palette.ACCENTS[index],
                    sprite=sprite,
                    hotkey=str(index + 1),
                    text_size=16,
                    value=name,
                )
            )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.quit()
                return
            for index, key in enumerate((pygame.K_1, pygame.K_2, pygame.K_3)):
                if event.key == key and index < len(self.buttons):
                    self._choose(self.buttons[index].value)
                    return
        for button in self.buttons:
            if button.handle_event(event):
                self._choose(button.value)
                return

    def _choose(self, name):
        sfx.play("select")
        self.app.push(ArcadeScene(self.app, progress.Player(name)))

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
            surface,
            "LEARNING ARCADE",
            (160, int(14 + wobble)),
            palette.MAGENTA,
            34,
            align="center",
        )
        ui.text(surface, "WHO IS PLAYING?", (160, 46), palette.WHITE, 18, align="center")
        saves = progress.load()
        for index, button in enumerate(self.buttons):
            button.draw(surface)
            stars = saves.get(button.value, {}).get("stars", 0)
            ui.text(
                surface,
                f"{stars} STARS",
                (button.rect.centerx, button.rect.bottom + 4),
                palette.YELLOW,
                13,
                align="center",
            )
        ui.text(
            surface,
            "CLICK A PICTURE, OR PRESS 1 2 3",
            (160, 162),
            palette.GRAY,
            13,
            align="center",
        )


class ArcadeScene(Scene):
    """The game shelf for one player."""

    def __init__(self, app, player):
        super().__init__(app)
        self.player = player
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=50, speed=9)
        self.buttons = []
        # Two by two, so a fifth game later just needs another row.
        for index, (title, _, sprite, color, _) in enumerate(GAMES):
            column, row = index % 2, index // 2
            rect = pygame.Rect(20 + column * 148, 38 + row * 54, 136, 50)
            self.buttons.append(
                ui.Button(
                    rect,
                    title,
                    color,
                    sprite=sprite,
                    hotkey=str(index + 1),
                    text_size=12,
                    value=index,
                    sprite_scale=2,
                )
            )
        self.switch_button = ui.Button(
            (96, 146, 128, 20), "SWITCH PLAYER", palette.PURPLE, text_size=14
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            for index, key in enumerate(
                (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
            ):
                if event.key == key and index < len(GAMES):
                    self._start(index)
                    return
        for button in self.buttons:
            if button.handle_event(event):
                self._start(button.value)
                return
        if self.switch_button.handle_event(event):
            sfx.play("back")
            self.app.pop()

    def _start(self, index):
        sfx.play("select")
        GAMES[index][4](self.app, self.player)

    def on_enter(self):
        # Star total may have grown while we were away in a game.
        self.player = progress.Player(self.player.name)

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        for button in self.buttons + [self.switch_button]:
            button.update(dt)

    def draw(self, surface):
        surface.fill(palette.BG_DEEP)
        self.starfield.draw(surface)
        wobble = ui.title_wobble(self.time)
        ui.text(
            surface,
            f"HI {self.player.name.upper()}!",
            (160, int(8 + wobble)),
            palette.YELLOW,
            30,
            align="center",
        )
        ui.star_counter(surface, self.player.stars, (4, 3))
        crystals = self.player.total_crystals()
        if crystals:
            sprites.draw(surface, "crystal", (272, 2))
            ui.text(surface, f"x{crystals}", (290, 6), palette.MAGENTA, 14)

        hovered = None
        for index, button in enumerate(self.buttons):
            button.draw(surface)
            if button.hover:
                hovered = GAMES[index][1]
        self.switch_button.draw(surface)

        # The shelf is too tight for a caption under every tile, so the
        # hovered game explains itself down here instead.
        ui.text(
            surface,
            hovered or "F = FULL SCREEN   M = MUTE   ESC = BACK",
            (160, 168),
            palette.GRAY if hovered else palette.DARK_GRAY,
            12,
            align="center",
        )


def main():
    app = App("Retro Learning Arcade")
    app.run(ProfileScene(app))
    return 0


if __name__ == "__main__":
    sys.exit(main())
