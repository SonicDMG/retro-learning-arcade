"""Shared retro colour palette.

Deliberately small and punchy, in the spirit of 8-bit home computers:
saturated neons on a deep purple-black background.
"""

BG_DEEP = (13, 6, 32)
BG_PANEL = (28, 16, 58)
INK = (8, 4, 18)

WHITE = (245, 245, 255)
GRAY = (120, 110, 150)
DARK_GRAY = (60, 52, 88)

CYAN = (60, 230, 240)
MAGENTA = (255, 70, 170)
YELLOW = (255, 210, 60)
GREEN = (80, 230, 120)
ORANGE = (255, 140, 60)
PURPLE = (150, 100, 240)
BLUE = (70, 130, 255)
RED = (240, 70, 70)
PINK = (255, 150, 200)
BROWN = (150, 90, 50)

# Rotating accent colours, used for menu tiles and answer buttons.
ACCENTS = [CYAN, MAGENTA, YELLOW, GREEN, ORANGE, PURPLE]


def dim(color, factor=0.5):
    """Darken a colour toward black."""
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def lighten(color, factor=0.4):
    """Blend a colour toward white."""
    return (
        int(color[0] + (255 - color[0]) * factor),
        int(color[1] + (255 - color[1]) * factor),
        int(color[2] + (255 - color[2]) * factor),
    )
