#!/usr/bin/env python3
"""Regenerate the screenshots used in README.md.

Run from the project root:

    python3 tools/screenshots.py

Scenes are posed with hand-picked questions rather than random ones, so the
images stay stable between runs and actually show something legible. Frames
are rendered exactly as the game presents them -- upscaled with
nearest-neighbour and given the same CRT scanline overlay -- so what lands in
the README is what a player sees.
"""

import os
import random
import sys
import time

# Headless by default: this only needs a surface to draw on.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import launcher  # noqa: E402
from games import (  # noqa: E402
    crystal_keys,
    logic_lab,
    math_blaster,
    pattern_power,
    word_rocket,
)
from retro import palette, progress  # noqa: E402
from retro.app import VIRTUAL_H, VIRTUAL_W, App  # noqa: E402

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots"
)
SCALE = 3
WARMUP_FRAMES = 24  # Let the wobble and starfield settle into a nice pose.


def render(app, scene, scale=SCALE, frames=WARMUP_FRAMES):
    """Draw a scene the way the running game would, and return the surface."""
    for _ in range(frames):
        scene.update(1 / 60)
    app.virtual.fill(palette.BG_DEEP)
    scene.draw(app.virtual)
    out = pygame.transform.scale(
        app.virtual, (VIRTUAL_W * scale, VIRTUAL_H * scale)
    )
    scanlines = pygame.transform.scale(
        app._scanlines, (VIRTUAL_W * scale, VIRTUAL_H * scale)
    )
    out.blit(scanlines, (0, 0))
    return out


def posed_scene(app, module, scene_factory, question):
    """Build a round scene showing one specific, hand-picked question."""
    original = module.make_question
    module.make_question = lambda *args, **kwargs: question
    try:
        scene = scene_factory()
        scene.on_enter()
    finally:
        module.make_question = original
    return scene


def demo_player(stars=42, age=8):
    player = progress.Player(progress.PROFILES[0][0])
    # In memory only; never written to disk.
    player.entry["stars"] = stars
    player.entry["age"] = age
    return player


def build():
    random.seed(7)
    os.makedirs(OUT_DIR, exist_ok=True)
    app = App()
    player = demo_player()
    shots = {}

    # The game shelf.
    arcade = launcher.ArcadeScene(app, player)
    shots["arcade"] = render(app, arcade)

    # Number Blaster, mid-round, on a times-table question.
    math_scene = posed_scene(
        app,
        math_blaster,
        lambda: math_blaster.MathRoundScene(app, player, "multiply", 2),
        {"kind": "expr", "prompt": "7 x 6 = ?", "answer": 42, "choices": [42, 36, 48]},
    )
    math_scene.index = 4
    shots["number-blaster"] = render(app, math_scene)

    # A story problem, which is where the player's own name turns up.
    story_scene = posed_scene(
        app,
        math_blaster,
        lambda: math_blaster.MathRoundScene(app, player, "word", 2),
        {
            "kind": "story",
            "prompt": "JUNI HAS 18 MARBLES AND GIVES AWAY 7. HOW MANY ARE LEFT?",
            "answer": 11,
            "choices": [9, 11, 13],
        },
    )
    story_scene.index = 6
    shots["story-problem"] = render(app, story_scene)

    # Number Blaster's counting mode, which shows off the pixel art.
    count_scene = posed_scene(
        app,
        math_blaster,
        lambda: math_blaster.MathRoundScene(app, player, "count", 1),
        {
            "kind": "count",
            "prompt": "HOW MANY?",
            "sprite": "duck",
            "count": 6,
            "answer": 6,
            "choices": [5, 6, 8],
        },
    )
    count_scene.index = 2
    shots["counting"] = render(app, count_scene)

    # Word Rocket, missing a middle letter.
    word_scene = posed_scene(
        app,
        word_rocket,
        lambda: word_rocket.WordRoundScene(app, player, "missing"),
        {"word": "CAT", "sprite": "cat", "blanks": [1], "filled": {}},
    )
    word_scene.index = 3
    shots["word-rocket"] = render(app, word_scene)

    # Pattern Power, on a repeating picture pattern.
    pattern_scene = posed_scene(
        app,
        pattern_power,
        lambda: pattern_power.PatternRoundScene(app, player, "picture"),
        {
            "kind": "picture",
            "items": ["star", "apple", "star", "apple", "star"],
            "answer": "apple",
            "choices": ["star", "apple", "fish"],
        },
    )
    pattern_scene.index = 5
    shots["pattern-power"] = render(app, pattern_scene)

    # Crystal Keys, part way through a fire word.
    typing = crystal_keys.TypingRoundScene(app, player, "fire")
    typing.prompts = ["ember", "spark", "torch", "phoenix", "blaze", "glow", "magma", "ash"]
    typing.index = 3
    typing.typed = 3
    typing.clean = 3
    typing.keystrokes, typing.hits = 40, 39
    typing.started_at = time.monotonic() - 30  # Half a minute in, for a real WPM.
    shots["crystal-keys"] = render(app, typing)

    # Logic Lab, on a matrix item -- the classic IQ-test shape.
    matrix_scene = posed_scene(
        app,
        logic_lab,
        lambda: logic_lab.LogicRoundScene(app, player, "matrix", 3),
        logic_lab.make_question("matrix", 3),
    )
    matrix_scene.index = 3
    shots["logic-lab"] = render(app, matrix_scene)

    for name, surface in shots.items():
        path = os.path.join(OUT_DIR, f"{name}.png")
        pygame.image.save(surface, path)
        print(f"wrote {os.path.relpath(path)}  {surface.get_width()}x{surface.get_height()}")

    # A wide banner of the three games, for the top of the README.
    banner_scale = 2
    panels = [
        render(app, math_scene, scale=banner_scale, frames=1),
        render(app, word_scene, scale=banner_scale, frames=1),
        render(app, pattern_scene, scale=banner_scale, frames=1),
        render(app, typing, scale=banner_scale, frames=1),
        render(app, matrix_scene, scale=banner_scale, frames=1),
    ]
    gap = 8
    width = sum(panel.get_width() for panel in panels) + gap * (len(panels) - 1)
    banner = pygame.Surface((width, panels[0].get_height()))
    banner.fill(palette.INK)
    x = 0
    for panel in panels:
        banner.blit(panel, (x, 0))
        x += panel.get_width() + gap
    banner_path = os.path.join(OUT_DIR, "banner.png")
    pygame.image.save(banner, banner_path)
    print(f"wrote {os.path.relpath(banner_path)}  {banner.get_width()}x{banner.get_height()}")

    pygame.quit()


if __name__ == "__main__":
    build()
