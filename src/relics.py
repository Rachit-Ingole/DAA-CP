"""
relics.py
Treasure relics found in each floor's vault room.

Relics are what the 0/1 Knapsack planner [K] is really about: every relic has
a weight and a gold value (randomised per vault, so the best haul is never
obvious), the player can only carry so much, and relics are banked as gold
when the player descends the stairs.

The relic sprites are drawn procedurally at start-up (nothing is added to or
changed in the resource folder).
"""
import random
from constant import *

# name -> (shape, base colour, typical weight range, value-per-weight range)
RELIC_TYPES = {
    "ruby": ("gem", (215, 40, 65), (1, 3), (3.0, 4.5)),
    "sapphire": ("gem", (45, 95, 230), (2, 5), (2.5, 4.0)),
    "emerald": ("gem", (35, 185, 95), (3, 6), (2.2, 3.6)),
    "topaz": ("gem", (240, 170, 40), (2, 5), (2.0, 3.5)),
    "amethyst": ("gem", (160, 80, 220), (4, 7), (1.8, 3.2)),
    "gold bar": ("bar", (235, 190, 60), (6, 10), (1.6, 2.8)),
}

RELIC_NAMES = list(RELIC_TYPES)


def is_relic(name):
    return name in RELIC_TYPES


def roll_relic(rng=random, floor=1):
    """
    Returns:
        (name, weight, value) for a random relic. Value per weight varies, so
        greedily taking the 'best ratio' first is not always optimal. Deeper
        vaults hold richer treasure.
    """
    name = rng.choice(RELIC_NAMES)
    _, _, (w_lo, w_hi), (r_lo, r_hi) = RELIC_TYPES[name]
    weight = rng.randint(w_lo, w_hi)
    value = max(1, int(round(weight * rng.uniform(r_lo, r_hi) + rng.randint(0, 3))))
    value = int(value * (1 + 0.15 * (max(1, floor) - 1)))
    return name, weight, value


def _shade(colour, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in colour)


def _draw_gem(size, colour):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    s = size / 64.0
    P = lambda x, y: (int(x * s), int(y * s))
    crown = [P(14, 26), P(23, 15), P(41, 15), P(50, 26)]
    pavilion = [P(14, 26), P(50, 26), P(32, 52)]
    pygame.draw.polygon(surf, _shade(colour, 0.75), pavilion)
    pygame.draw.polygon(surf, _shade(colour, 1.0), [P(14, 26), P(32, 26), P(32, 52)])
    pygame.draw.polygon(surf, _shade(colour, 1.3), crown)
    pygame.draw.polygon(surf, _shade(colour, 1.55), [P(23, 15), P(32, 26), P(41, 15)])
    pygame.draw.line(surf, _shade(colour, 0.5), P(14, 26), P(50, 26), max(1, int(2 * s)))
    pygame.draw.polygon(surf, _shade(colour, 0.35), crown[:3] + [P(50, 26), P(32, 52), P(14, 26)], max(1, int(2 * s)))
    pygame.draw.line(surf, (255, 255, 255), P(25, 19), P(30, 19), max(1, int(2 * s)))
    return surf


def _draw_bar(size, colour):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    s = size / 64.0
    P = lambda x, y: (int(x * s), int(y * s))
    top = [P(18, 24), P(46, 24), P(54, 34), P(10, 34)]
    front = [P(10, 34), P(54, 34), P(54, 44), P(10, 44)]
    pygame.draw.polygon(surf, _shade(colour, 1.25), top)
    pygame.draw.polygon(surf, _shade(colour, 0.85), front)
    pygame.draw.polygon(surf, _shade(colour, 0.4), [P(18, 24), P(46, 24), P(54, 34), P(54, 44), P(10, 44), P(10, 34)],
                        max(1, int(2 * s)))
    pygame.draw.line(surf, (255, 250, 220), P(20, 27), P(36, 27), max(1, int(2 * s)))
    return surf


def make_relic_sprites(size=SPRITE_SIZE):
    """
    Returns:
        {relic name: Surface} drawn procedurally
    """
    sprites = {}
    for name, (shape, colour, _, _) in RELIC_TYPES.items():
        sprites[name] = _draw_gem(size, colour) if shape == "gem" else _draw_bar(size, colour)
    return sprites
