"""Hand-drawn 16x16 pixel art, stored as character grids.

Each sprite is a list of rows plus a colour key. Rows are padded to the
sprite width on load, so a short row is a harmless mistake rather than a
crash. '.' means transparent.
"""

import pygame

from .palette import (
    BLUE,
    BROWN,
    CYAN,
    GRAY,
    GREEN,
    INK,
    MAGENTA,
    ORANGE,
    PINK,
    PURPLE,
    RED,
    WHITE,
    YELLOW,
)

SIZE = 16

K = INK  # outline / pupils

CAT = {
    "key": {"f": ORANGE, "k": K, "p": PINK, "w": WHITE},
    "rows": [
        "................",
        "..ff........ff..",
        "..fff......fff..",
        "..ffff....ffff..",
        ".ffffffffffffff.",
        ".ffffffffffffff.",
        ".fffkffffffkfff.",
        ".ffffffffffffff.",
        ".ffffffppffffff.",
        ".fffffkffkfffff.",
        ".ffffffffffffff.",
        "..ffffffffffff..",
        "..ffffffffffff..",
        "..ff.ffffff.ff..",
        "..ff.ffffff.ff..",
        ".....ffffff.....",
    ],
}

DOG = {
    "key": {"f": BROWN, "k": K, "p": PINK, "w": WHITE},
    "rows": [
        "................",
        ".ff..........ff.",
        ".fff........fff.",
        ".ffff......ffff.",
        ".ffffffffffffff.",
        ".ffffffffffffff.",
        ".fffkffffffkfff.",
        ".ffffffffffffff.",
        "..ffffffffffff..",
        "..ffffkkkkffff..",
        "..fffkppppkfff..",
        "...ffkppppkff...",
        "...fffkkkkfff...",
        "....ffffffff....",
        "....ff....ff....",
        "....ff....ff....",
    ],
}

SUN = {
    "key": {"y": YELLOW, "o": ORANGE, "k": K},
    "rows": [
        ".......yy.......",
        "...y...yy...y...",
        "....y..yy..y....",
        ".....yooooy.....",
        "....oooooooo....",
        "...oooyyyyooo...",
        "yy.ooyyyyyyoo.yy",
        "yy.ooyykyykyoo.y",
        "yy.ooyyyyyyoo.yy",
        "...ooyykkkyoo...",
        "....oooooooo....",
        ".....yooooy.....",
        "....y..yy..y....",
        "...y...yy...y...",
        ".......yy.......",
        "................",
    ],
}

BUS = {
    "key": {"y": YELLOW, "k": K, "c": CYAN, "w": WHITE, "r": RED, "g": GRAY},
    "rows": [
        "................",
        "................",
        "..kkkkkkkkkkkk..",
        ".kyyyyyyyyyyyyk.",
        ".kyccykyccykyyk.",
        ".kyccykyccykyrk.",
        ".kyyyyyyyyyyyyk.",
        ".kyyyyyyyyyyyyk.",
        ".kkkkkkkkkkkkkk.",
        ".kyyyyyyyyyyyyk.",
        ".kkkkkkkkkkkkkk.",
        "..ggg......ggg..",
        ".ggwgg....ggwgg.",
        ".ggwgg....ggwgg.",
        "..ggg......ggg..",
        "................",
    ],
}

STAR = {
    "key": {"y": YELLOW, "o": ORANGE, "w": WHITE},
    "rows": [
        ".......ww.......",
        ".......yy.......",
        "......yyyy......",
        "......yyyy......",
        ".....yyyyyy.....",
        "yyyyyyyyyyyyyyyy",
        ".yyyyyyyyyyyyyy.",
        "..yyyyyyyyyyyy..",
        "...yyyyyyyyyy...",
        "...yyyyyyyyyy...",
        "..yyyyyyyyyyyy..",
        "..yyyyy..yyyyy..",
        ".yyyyo....oyyyy.",
        ".yyyo......oyyy.",
        "yyo..........oyy",
        "................",
    ],
}

FISH = {
    "key": {"c": CYAN, "b": BLUE, "k": K, "w": WHITE},
    "rows": [
        "................",
        "......bbbb....b.",
        "....bbccccbb.bb.",
        "..bbccccccccbbbb",
        ".bccwwccccccccbb",
        "bbccwkccccccccbb",
        "bbccwwccccccccbb",
        ".bccccccccccccbb",
        "..bbccccccccbbbb",
        "....bbccccbb.bb.",
        "......bbbb....b.",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
}

TREE = {
    "key": {"g": GREEN, "d": (40, 150, 80), "b": BROWN, "k": K},
    "rows": [
        ".......gg.......",
        "......gggg......",
        ".....gggddg.....",
        "....gggggddg....",
        "...ggggggdddg...",
        "..gggggggddddg..",
        ".ggggggggdddddg.",
        "ggggggggggddddgg",
        "..ggggggggdddg..",
        "...gggggggddg...",
        "......bbbb......",
        "......bbbb......",
        "......bbbb......",
        "......bbbb......",
        ".....bbbbbb.....",
        "................",
    ],
}

MOON = {
    "key": {"w": WHITE, "g": GRAY, "y": YELLOW},
    "rows": [
        "................",
        "......wwww......",
        "....wwwwwwww....",
        "...wwwwwwgwww...",
        "..wwwgwwwwwww...",
        "..wwwwwwwwww....",
        ".wwwwwwwww......",
        ".wwwwwwww.......",
        ".wwwwwwww.......",
        ".wwwwwwwww......",
        "..wwwwwwwwww....",
        "..wwwwwgwwwww...",
        "...wwwwwwwwww...",
        "....wwwwwwww....",
        "......wwww......",
        "................",
    ],
}

CAKE = {
    "key": {"p": PINK, "w": WHITE, "r": RED, "y": YELLOW, "k": K, "m": MAGENTA},
    "rows": [
        ".......y........",
        ".......y........",
        "......rrr.......",
        "......rrr.......",
        "....wwwwwwww....",
        "...wwwwwwwwww...",
        "..wwppwwppwwpp..",
        "..pppppppppppp..",
        "..pppppppppppp..",
        "..mmmmmmmmmmmm..",
        "..pppppppppppp..",
        "..pppppppppppp..",
        "..mmmmmmmmmmmm..",
        "..kkkkkkkkkkkk..",
        "................",
        "................",
    ],
}

FROG = {
    "key": {"g": GREEN, "d": (40, 150, 80), "w": WHITE, "k": K, "p": PINK},
    "rows": [
        "................",
        "...gg......gg...",
        "..gwwg....gwwg..",
        "..gwkg....gwkg..",
        "..gggg....gggg..",
        "..gggggggggggg..",
        ".gggggggggggggg.",
        ".gggggggggggggg.",
        ".ggkkkkkkkkkkgg.",
        ".gggggggggggggg.",
        "..dggggggggggd..",
        "..dddggggggdddd.",
        ".dd..dddddd...dd",
        "dd....dddd.....d",
        "................",
        "................",
    ],
}

DUCK = {
    "key": {"y": YELLOW, "o": ORANGE, "k": K, "w": WHITE},
    "rows": [
        "................",
        "......yyyy......",
        ".....yyyyyy.....",
        ".....yykyyy.....",
        "..oooyyyyyy.....",
        "..oooyyyyyy.....",
        ".....yyyyyy.....",
        "......yyyyy.....",
        "....yyyyyyyyy...",
        "...yyyyyyyyyyy..",
        "..yyyyyyyyyyyyy.",
        "..yyyyyyyyyyyyy.",
        "..yyyyyyyyyyyy..",
        "...yyyyyyyyyy...",
        "....oo....oo....",
        "...ooo....ooo...",
    ],
}

BALL = {
    "key": {"r": RED, "w": WHITE, "b": BLUE, "k": K},
    "rows": [
        "................",
        "....wwwwwwww....",
        "..wwrrrrrrrrww..",
        "..wrrrrrrrrrrw..",
        ".wrrrrwwwwrrrrw.",
        ".wrrrwwwwwwrrrw.",
        ".wrrwwbbbbwwrrw.",
        ".wrrwbbbbbbwrrw.",
        ".wrrwbbbbbbwrrw.",
        ".wrrwwbbbbwwrrw.",
        ".wrrrwwwwwwrrrw.",
        ".wrrrrwwwwrrrrw.",
        "..wrrrrrrrrrrw..",
        "..wwrrrrrrrrww..",
        "....wwwwwwww....",
        "................",
    ],
}

ROCKET = {
    "key": {"w": WHITE, "r": RED, "c": CYAN, "y": YELLOW, "o": ORANGE, "k": K},
    "rows": [
        ".......ww.......",
        "......wwww......",
        "......wccw......",
        ".....wwccww.....",
        ".....wwwwww.....",
        "....wwwwwwww....",
        "...rwwwwwwwwr...",
        "..rrwwwwwwwwrr..",
        ".rrrwwwwwwwwrrr.",
        "rrr.wwwwwwww.rrr",
        "....wwwwwwww....",
        ".....wrrrrw.....",
        "......yooy......",
        ".....yyooyy.....",
        "......yooy......",
        ".......yy.......",
    ],
}

APPLE = {
    "key": {"r": RED, "g": GREEN, "b": BROWN, "w": WHITE},
    "rows": [
        "................",
        ".......bb.......",
        "......bb.gg.....",
        ".....bb.gggg....",
        "..rrrrrr.ggg....",
        ".rrrrrrrrr......",
        "rrwrrrrrrrrr....",
        "rrwrrrrrrrrrr...",
        "rrwrrrrrrrrrr...",
        "rrrrrrrrrrrrr...",
        "rrrrrrrrrrrrr...",
        ".rrrrrrrrrrr....",
        ".rrrrrrrrrrr....",
        "..rrrr.rrrr.....",
        "...rr...rr......",
        "................",
    ],
}

BOOK = {
    "key": {"p": PURPLE, "m": MAGENTA, "w": WHITE, "y": YELLOW, "k": K},
    "rows": [
        "................",
        "..pppppkppppppp.",
        ".pmmmmmkmmmmmmmp",
        ".pmwwwmkmwwwwwmp",
        ".pmwwwmkmwwwwwmp",
        ".pmmmmmkmmmmmmmp",
        ".pmwwwwkwwwwwwmp",
        ".pmwwwwkwwwwwwmp",
        ".pmwwwwkwwwwwwmp",
        ".pmwwwwkwwwwwwmp",
        ".pmwwwwkwwwwwwmp",
        ".pmmmmmkmmmmmmmp",
        ".ppppppkpppppppp",
        "...yyyyyyyyy....",
        "................",
        "................",
    ],
}

SPRITES = {
    "cat": CAT,
    "dog": DOG,
    "sun": SUN,
    "bus": BUS,
    "star": STAR,
    "fish": FISH,
    "tree": TREE,
    "moon": MOON,
    "cake": CAKE,
    "frog": FROG,
    "duck": DUCK,
    "ball": BALL,
    "rocket": ROCKET,
    "apple": APPLE,
    "book": BOOK,
}

_cache = {}


def get(name, scale=1):
    """Return a Surface for a named sprite, cached per scale."""
    key = (name, scale)
    if key in _cache:
        return _cache[key]
    data = SPRITES.get(name)
    if data is None:
        surface = pygame.Surface((SIZE * scale, SIZE * scale), pygame.SRCALPHA)
        _cache[key] = surface
        return surface
    surface = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    colours = data["key"]
    for y, row in enumerate(data["rows"][:SIZE]):
        row = row.ljust(SIZE, ".")
        for x, char in enumerate(row[:SIZE]):
            colour = colours.get(char)
            if colour is not None:
                surface.set_at((x, y), colour)
    if scale != 1:
        surface = pygame.transform.scale(surface, (SIZE * scale, SIZE * scale))
    _cache[key] = surface
    return surface


def draw(target, name, pos, scale=1, center=False):
    """Blit a sprite, optionally centred on pos."""
    image = get(name, scale)
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    target.blit(image, rect)
    return rect
