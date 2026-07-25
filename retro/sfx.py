"""Chiptune-style sound effects, synthesised at runtime.

No audio files ship with the project: every beep is a square/triangle wave
built with the standard library and handed straight to pygame.mixer. If the
machine has no working audio device, every call here quietly does nothing.
"""

import math
from array import array

import pygame

SAMPLE_RATE = 22050
_enabled = False
_cache = {}
_muted = False


def init():
    """Prepare the mixer. Safe to call more than once."""
    global _enabled
    if _enabled:
        return
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        _enabled = True
    except pygame.error:
        _enabled = False


def set_muted(value):
    global _muted
    _muted = bool(value)


def is_muted():
    return _muted


def _wave_sample(shape, phase):
    """One sample of the given wave shape at phase (0..1), in -1..1."""
    if shape == "square":
        return 1.0 if phase % 1.0 < 0.5 else -1.0
    if shape == "triangle":
        p = phase % 1.0
        return 4.0 * abs(p - 0.5) - 1.0
    if shape == "saw":
        return 2.0 * (phase % 1.0) - 1.0
    if shape == "noise":
        # Cheap deterministic noise: no random import, no seeding surprises.
        n = int(phase * 100000.0)
        n = (n * 1103515245 + 12345) & 0x7FFFFFFF
        return (n / 0x3FFFFFFF) - 1.0
    return math.sin(phase * math.tau)


def _render_notes(notes, shape="square", volume=0.35):
    """Render a list of (frequency_hz, duration_ms) into a Sound.

    A frequency of 0 is a rest. Each note gets a short attack and a decay so
    the result sounds plucky rather than clicky.
    """
    samples = array("h")
    for freq, ms in notes:
        count = max(1, int(SAMPLE_RATE * ms / 1000.0))
        attack = max(1, int(count * 0.06))
        release = max(1, int(count * 0.35))
        phase = 0.0
        step = freq / SAMPLE_RATE if freq > 0 else 0.0
        for i in range(count):
            if freq <= 0:
                samples.append(0)
                continue
            if i < attack:
                env = i / attack
            elif i > count - release:
                env = max(0.0, (count - i) / release)
            else:
                env = 1.0
            value = _wave_sample(shape, phase) * env * volume
            samples.append(int(max(-1.0, min(1.0, value)) * 32767))
            phase += step
    return pygame.mixer.Sound(buffer=samples.tobytes())


# Each effect is a recipe, rendered on first use and cached after that.
_RECIPES = {
    "click": ([(660, 45)], "square", 0.25),
    "select": ([(520, 45), (780, 70)], "square", 0.28),
    "back": ([(500, 50), (330, 70)], "triangle", 0.28),
    "correct": ([(660, 70), (880, 70), (1320, 130)], "square", 0.30),
    "wrong": ([(240, 90), (180, 140)], "triangle", 0.26),
    "star": ([(1046, 60), (1318, 60), (1568, 60), (2093, 150)], "square", 0.26),
    "launch": ([(200, 60), (400, 60), (700, 60), (1100, 90)], "saw", 0.22),
    "pop": ([(880, 40), (0, 20), (1200, 40)], "square", 0.22),
    "boom": ([(120, 220)], "noise", 0.30),
    "fanfare": (
        [(523, 110), (659, 110), (784, 110), (1046, 240), (784, 90), (1046, 320)],
        "square",
        0.30,
    ),
}


def play(name):
    """Play a named effect. Unknown names and dead audio devices are ignored."""
    if not _enabled or _muted:
        return
    sound = _cache.get(name)
    if sound is None:
        recipe = _RECIPES.get(name)
        if recipe is None:
            return
        notes, shape, volume = recipe
        try:
            sound = _render_notes(notes, shape, volume)
        except pygame.error:
            return
        _cache[name] = sound
    sound.play()
