"""Tiny retro game framework: a low-resolution virtual screen, scaled up.

Everything is drawn onto a 320x180 surface and then blown up with
nearest-neighbour scaling, which is what gives the whole suite its chunky
pixel look on a modern Mac display. Scenes are pushed and popped on a stack.
"""

import pygame

from . import palette, sfx

VIRTUAL_W = 320
VIRTUAL_H = 180
DEFAULT_SCALE = 4
FPS = 60


class Scene:
    """Base class for a screen. Subclasses override the interesting parts."""

    def __init__(self, app):
        self.app = app

    def on_enter(self):
        """Called each time this scene becomes the active one."""

    def handle_event(self, event):
        """Handle one pygame event. Mouse positions are in virtual pixels."""

    def update(self, dt):
        """Advance the scene by dt seconds."""

    def draw(self, surface):
        """Draw onto the 320x180 virtual surface."""


class App:
    """Owns the window, the scene stack and the main loop."""

    def __init__(self, title="Retro Learning Arcade", scale=DEFAULT_SCALE):
        pygame.init()
        sfx.init()
        self.title = title
        pygame.display.set_caption(title)
        self.window_size = (VIRTUAL_W * scale, VIRTUAL_H * scale)
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        self.virtual = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert()
        self.clock = pygame.time.Clock()
        self.running = False
        self.fullscreen = False
        self.scenes = []
        self._scanlines = _build_scanlines()
        # Where the scaled image sits inside the window, for mouse mapping.
        self._blit_rect = pygame.Rect(0, 0, *self.window_size)

    # -- scene stack ------------------------------------------------------

    @property
    def scene(self):
        return self.scenes[-1] if self.scenes else None

    def push(self, scene):
        self.scenes.append(scene)
        scene.on_enter()

    def pop(self):
        if len(self.scenes) > 1:
            self.scenes.pop()
            self.scene.on_enter()
        else:
            self.quit()

    def replace(self, scene):
        if self.scenes:
            self.scenes.pop()
        self.push(scene)

    def quit(self):
        self.running = False

    # -- window helpers ---------------------------------------------------

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)

    def _compute_blit_rect(self):
        """Largest integer-scaled centred rect that fits the window."""
        win_w, win_h = self.screen.get_size()
        scale = min(win_w // VIRTUAL_W, win_h // VIRTUAL_H)
        if scale < 1:
            # Window smaller than one virtual pixel per pixel: fall back to fit.
            scale_f = min(win_w / VIRTUAL_W, win_h / VIRTUAL_H)
            w, h = int(VIRTUAL_W * scale_f), int(VIRTUAL_H * scale_f)
        else:
            w, h = VIRTUAL_W * scale, VIRTUAL_H * scale
        return pygame.Rect((win_w - w) // 2, (win_h - h) // 2, w, h)

    def to_virtual(self, pos):
        """Map a window mouse position into virtual-screen coordinates."""
        rect = self._blit_rect
        if rect.width == 0 or rect.height == 0:
            return (0, 0)
        x = (pos[0] - rect.x) * VIRTUAL_W / rect.width
        y = (pos[1] - rect.y) * VIRTUAL_H / rect.height
        return (int(x), int(y))

    # -- main loop --------------------------------------------------------

    def run(self, start_scene):
        self.push(start_scene)
        self.running = True
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Never let a hitch teleport the animations.
            self._pump_events()
            if not self.running:
                break
            scene = self.scene
            if scene:
                scene.update(dt)
                self.virtual.fill(palette.BG_DEEP)
                scene.draw(self.virtual)
            self._present()
        pygame.quit()

    def _pump_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                return
            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.window_size = (event.w, event.h)
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if event.key == pygame.K_q and mods & pygame.KMOD_META:
                    self.quit()
                    return
                if event.key == pygame.K_f and not mods & pygame.KMOD_META:
                    self.toggle_fullscreen()
                    continue
                if event.key == pygame.K_m:
                    sfx.set_muted(not sfx.is_muted())
                    sfx.play("click")
                    continue
            if event.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                # Hand scenes virtual coordinates so they never think in pixels
                # of the real window.
                event = pygame.event.Event(
                    event.type,
                    {**event.dict, "pos": self.to_virtual(event.pos)},
                )
            if self.scene:
                self.scene.handle_event(event)

    def _present(self):
        self._blit_rect = self._compute_blit_rect()
        self.screen.fill(palette.INK)
        scaled = pygame.transform.scale(
            self.virtual, (self._blit_rect.width, self._blit_rect.height)
        )
        scaled.blit(
            pygame.transform.scale(
                self._scanlines, (self._blit_rect.width, self._blit_rect.height)
            ),
            (0, 0),
        )
        self.screen.blit(scaled, self._blit_rect)
        pygame.display.flip()


def _build_scanlines():
    """A faint every-other-line darkening, for a CRT feel."""
    surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
    for y in range(0, VIRTUAL_H, 2):
        pygame.draw.line(surface, (0, 0, 0, 38), (0, y), (VIRTUAL_W, y))
    return surface
