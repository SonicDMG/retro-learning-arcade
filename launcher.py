#!/usr/bin/env python3
"""Retro Learning Arcade -- the front end that ties the games together.

Run this file to play:  python3 launcher.py
"""

import sys

import pygame

from games import crystal_keys, logic_lab, math_blaster, pattern_power, word_rocket
from retro import levels, palette, progress, sfx, sprites, ui
from retro.app import App, Scene

GAMES = [
    ("NUMBER BLASTER", "MATHS AND STORY PROBLEMS", "rocket", palette.GREEN, math_blaster.launch),
    ("WORD ROCKET", "LETTERS", "book", palette.CYAN, word_rocket.launch),
    ("PATTERN POWER", "WHAT'S NEXT?", "star", palette.MAGENTA, pattern_power.launch),
    ("CRYSTAL KEYS", "TYPING", "crystal", palette.PURPLE, crystal_keys.launch),
    ("LOGIC LAB", "PUZZLES AND REASONING", "leaf", palette.ORANGE, logic_lab.launch),
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
        player = progress.Player(name)
        # A new player is asked their age once; it sets how hard the games are.
        if player.age is None:
            self.app.push(AgeScene(self.app, player))
        else:
            self.app.push(ArcadeScene(self.app, player))

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


class AgeScene(Scene):
    """How old is the player? This sets the difficulty of every game.

    Asked once per profile, and reachable afterwards from the shelf, because
    a seven-year-old becomes an eight-year-old.
    """

    def __init__(self, app, player, return_to_shelf=False):
        super().__init__(app)
        self.player = player
        self.return_to_shelf = return_to_shelf
        self.time = 0.0
        self.starfield = ui.Starfield(320, 180, count=40, speed=8)
        self.buttons = []
        ages = list(range(levels.MIN_AGE, levels.MAX_AGE + 1))
        for index, age in enumerate(ages):
            column, row = index % 4, index // 4
            rect = pygame.Rect(28 + column * 68, 62 + row * 44, 60, 38)
            self.buttons.append(
                ui.Button(rect, str(age), palette.ACCENTS[index % len(palette.ACCENTS)],
                          text_size=30, value=age)
            )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            if pygame.K_0 <= event.key <= pygame.K_9:
                # Typing 5..9 picks that age directly; 1 and 2 are ambiguous
                # with 10 and 12, so those stay click-only.
                typed = event.key - pygame.K_0
                if levels.MIN_AGE <= typed <= 9:
                    self._choose(typed)
                    return
        for button in self.buttons:
            if button.handle_event(event):
                self._choose(button.value)
                return

    def _choose(self, age):
        sfx.play("select")
        self.player.set_age(age)
        if self.return_to_shelf:
            self.app.pop()
        else:
            self.app.replace(ArcadeScene(self.app, self.player))

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
            f"HI {self.player.name.upper()}!",
            (160, int(8 + wobble)),
            palette.YELLOW,
            28,
            align="center",
        )
        ui.text(surface, "HOW OLD ARE YOU?", (160, 40), palette.WHITE, 18, align="center")
        for button in self.buttons:
            button.draw(surface)
        ui.text(
            surface,
            "THIS PICKS HOW TRICKY THE GAMES ARE",
            (160, 158),
            palette.GRAY,
            12,
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
        # Three by two, with room for a sixth game.
        for index, (title, _, sprite, color, _) in enumerate(GAMES):
            column, row = index % 3, index // 3
            rect = pygame.Rect(10 + column * 100, 36 + row * 52, 96, 48)
            self.buttons.append(
                ui.Button(
                    rect,
                    title,
                    color,
                    sprite=sprite,
                    hotkey=str(index + 1),
                    text_size=11,
                    value=index,
                    sprite_scale=2,
                )
            )
        self.switch_button = ui.Button(
            (24, 144, 120, 20), "SWITCH PLAYER", palette.PURPLE, text_size=13
        )
        # The label carries the current age, so the shelf needs no extra line.
        self.age_button = ui.Button(
            (176, 144, 120, 20), "CHANGE AGE", palette.BLUE, text_size=13
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sfx.play("back")
                self.app.pop()
                return
            keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6)
            for index, key in enumerate(keys):
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
            return
        if self.age_button.handle_event(event):
            sfx.play("click")
            self.app.push(AgeScene(self.app, self.player, return_to_shelf=True))

    def _start(self, index):
        sfx.play("select")
        GAMES[index][4](self.app, self.player)

    def on_enter(self):
        # Star total may have grown while we were away in a game.
        self.player = progress.Player(self.player.name)

    def update(self, dt):
        self.time += dt
        self.starfield.update(dt)
        for button in self.buttons + [self.switch_button, self.age_button]:
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

        age = self.player.age
        self.age_button.label = f"AGE {age} - CHANGE" if age else "SET AGE"

        hovered = None
        for index, button in enumerate(self.buttons):
            button.draw(surface)
            if button.hover:
                hovered = GAMES[index][1]
        self.switch_button.draw(surface)
        self.age_button.draw(surface)

        # The shelf is too tight for a caption under every tile, so the
        # hovered game explains itself down here instead.
        ui.text(
            surface,
            hovered or "CTRL-F FULL SCREEN   CTRL-M MUTE   ESC BACK",
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
