"""Chunky UI widgets: text, buttons, panels, starfields and particles.

Everything here draws in virtual-screen pixels (320x180) and turns
anti-aliasing off, so text stays crisp and blocky once the frame is scaled up.
"""

import math
import random

import pygame

from . import palette, sfx, sprites

_fonts = {}


def font(size):
    key = int(size)
    if key not in _fonts:
        _fonts[key] = pygame.font.Font(None, key)
    return _fonts[key]


def text_size(message, size=14):
    return font(size).size(str(message))


def text(surface, message, pos, color=palette.WHITE, size=14, align="left", shadow=True):
    """Draw a line of text. align is left, center or right."""
    glyphs = font(size).render(str(message), False, color)
    rect = glyphs.get_rect()
    if align == "center":
        rect.midtop = pos
    elif align == "right":
        rect.topright = pos
    else:
        rect.topleft = pos
    if shadow:
        dark = font(size).render(str(message), False, palette.INK)
        surface.blit(dark, (rect.x + 1, rect.y + 1))
    surface.blit(glyphs, rect)
    return rect


def panel(surface, rect, fill=palette.BG_PANEL, border=palette.PURPLE, width=1):
    """A filled box with a hard 1px border and a dark drop shadow."""
    rect = pygame.Rect(rect)
    shadow = rect.move(2, 2)
    pygame.draw.rect(surface, palette.INK, shadow)
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, width)
    return rect


def bar(surface, rect, fraction, color=palette.GREEN, back=palette.DARK_GRAY):
    """A simple progress bar, clamped to 0..1."""
    rect = pygame.Rect(rect)
    fraction = max(0.0, min(1.0, fraction))
    pygame.draw.rect(surface, back, rect)
    inner = pygame.Rect(rect.x, rect.y, int(rect.width * fraction), rect.height)
    if inner.width > 0:
        pygame.draw.rect(surface, color, inner)
    pygame.draw.rect(surface, palette.INK, rect, 1)


class Button:
    """A big, friendly, clickable box. Optionally shows a sprite and a hotkey."""

    def __init__(
        self,
        rect,
        label,
        color=palette.CYAN,
        sprite=None,
        hotkey=None,
        text_size=16,
        value=None,
        solid=False,
        sprite_scale=None,
    ):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.sprite = sprite
        self.hotkey = hotkey
        self.text_size = text_size
        # Solid buttons are filled with their colour, for use as swatches.
        self.solid = solid
        # None means "pick a scale from the button height".
        self.sprite_scale = sprite_scale
        self.value = value if value is not None else label
        self.hover = False
        self.enabled = True
        self.locked = False  # Locked buttons stop reacting but keep their look.
        self.flash = 0.0     # Seconds of highlight remaining.
        self.flash_color = None
        self.bounce = 0.0
        self._t = random.uniform(0, math.tau)

    def set_flash(self, color, duration=0.6):
        self.flash = duration
        self.flash_color = color

    def update(self, dt):
        self._t += dt
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)
        if self.bounce > 0:
            self.bounce = max(0.0, self.bounce - dt * 3)

    def handle_event(self, event):
        """Return True on a click. Hover tracking happens here too."""
        if not self.enabled or self.locked:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.bounce = 1.0
                return True
        return False

    def draw(self, surface):
        rect = self.rect.copy()
        if self.bounce > 0:
            rect.inflate_ip(-int(self.bounce * 3), -int(self.bounce * 3))
        color = self.color
        if self.flash > 0 and self.flash_color:
            # Blink between the flash colour and the base colour.
            if int(self.flash * 12) % 2 == 0:
                color = self.flash_color
        elif not self.enabled:
            color = palette.DARK_GRAY

        face = palette.dim(color, 0.35)
        if self.hover and self.enabled and not self.locked:
            face = palette.dim(color, 0.55)
            rect = rect.inflate(2, 2)
        if self.solid and self.enabled:
            face = palette.lighten(color, 0.25) if self.hover else color

        pygame.draw.rect(surface, palette.INK, rect.move(2, 2))
        pygame.draw.rect(surface, face, rect)
        pygame.draw.rect(surface, palette.lighten(color, 0.5) if self.solid else color, rect, 1)

        label_y = rect.centery - 6
        if self.sprite:
            # A 2x icon plus a label only fits in a reasonably tall button.
            scale = self.sprite_scale or (2 if rect.height >= 48 else 1)
            image = sprites.get(self.sprite, scale)
            if self.label:
                image_rect = image.get_rect(midtop=(rect.centerx, rect.top + 4))
                label_y = image_rect.bottom + 1
            else:
                # No caption, so the icon gets the whole button.
                image_rect = image.get_rect(center=rect.center)
            surface.blit(image, image_rect)

        if self.label:
            text(
                surface,
                self.label,
                (rect.centerx, label_y),
                palette.WHITE if self.enabled else palette.GRAY,
                self.text_size,
                align="center",
            )
        if self.hotkey:
            text(surface, self.hotkey, (rect.x + 3, rect.y + 2), palette.YELLOW, 12)


class Starfield:
    """Parallax star background. Cheap, and instantly says 'space'."""

    def __init__(self, width, height, count=60, speed=12.0):
        self.width = width
        self.height = height
        self.speed = speed
        self.stars = []
        for _ in range(count):
            depth = random.choice([1, 2, 3])
            self.stars.append(
                [random.uniform(0, width), random.uniform(0, height), depth]
            )

    def update(self, dt):
        for star in self.stars:
            star[1] += self.speed * dt * star[2]
            if star[1] > self.height:
                star[1] = -1
                star[0] = random.uniform(0, self.width)

    def draw(self, surface):
        shades = {1: palette.DARK_GRAY, 2: palette.GRAY, 3: palette.WHITE}
        for x, y, depth in self.stars:
            surface.set_at((int(x) % self.width, int(y) % self.height), shades[depth])


class Particles:
    """Confetti and explosion sparks."""

    def __init__(self):
        self.items = []

    def burst(self, pos, color=palette.YELLOW, count=14, speed=60.0, life=0.7, gravity=90.0):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = random.uniform(speed * 0.3, speed)
            self.items.append(
                {
                    "x": float(pos[0]),
                    "y": float(pos[1]),
                    "vx": math.cos(angle) * velocity,
                    "vy": math.sin(angle) * velocity,
                    "life": life,
                    "max": life,
                    "color": color,
                    "gravity": gravity,
                }
            )

    def confetti(self, width, count=40):
        for _ in range(count):
            self.items.append(
                {
                    "x": random.uniform(0, width),
                    "y": random.uniform(-40, 0),
                    "vx": random.uniform(-12, 12),
                    "vy": random.uniform(20, 60),
                    "life": 3.0,
                    "max": 3.0,
                    "color": random.choice(palette.ACCENTS),
                    "gravity": 8.0,
                }
            )

    def update(self, dt):
        for item in self.items:
            item["vy"] += item["gravity"] * dt
            item["x"] += item["vx"] * dt
            item["y"] += item["vy"] * dt
            item["life"] -= dt
        self.items = [item for item in self.items if item["life"] > 0]

    def draw(self, surface):
        for item in self.items:
            fade = item["life"] / item["max"]
            color = item["color"] if fade > 0.35 else palette.dim(item["color"], 0.6)
            size = 2 if fade > 0.5 else 1
            pygame.draw.rect(surface, color, (int(item["x"]), int(item["y"]), size, size))

    def clear(self):
        self.items.clear()


def star_counter(surface, count, pos=(4, 4)):
    """Little star icon plus a number, drawn top-left by default."""
    sprites.draw(surface, "star", pos, scale=1)
    text(surface, f"x{count}", (pos[0] + 18, pos[1] + 3), palette.YELLOW, 14)


def title_wobble(offset_seconds, amount=2.0, speed=2.2):
    """Vertical bob used by titles and celebration screens."""
    return math.sin(offset_seconds * speed) * amount


class HintTimer:
    """After a while with no answer, games use this to nudge the child."""

    def __init__(self, delay=9.0):
        self.delay = delay
        self.elapsed = 0.0

    def reset(self):
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def ready(self):
        return self.elapsed >= self.delay


def play_click():
    sfx.play("click")
