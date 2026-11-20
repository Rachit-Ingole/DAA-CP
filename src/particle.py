import pygame
import pygame.freetype
import math
from constant import *

pygame.init()
dirname = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource')
font_path_name = os.path.join(dirname, 'fonts/FFF_Tusj.ttf')
myfont = pygame.freetype.Font(font_path_name, 20)


class Particle(pygame.sprite.Sprite):
    """
    Class that represents a particle

    Attributes:
        x (arg, int): x position of particle
        y (arg, int): y position of particle
        list (arg, Group): group particle belongs to
    """

    # TODO: add check for when actual map is smaller than RESOLUTION,
    #       so x and y aren't in sync just like the mouse cursor
    def __init__(self, x, y, list):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.list = list
        self.list.append(self)


class MagicParticle(Particle):
    def __init__(self, list, image, line):
        """
        Class that represents a magic spell that moves

        Attributes:
            list (arg, Group): group particle belongs to
            image (arg, Sprite): image of particle
            line (arg, List): list of points particle will travel to
            x (int): x position of particle
            y (int): y position of particle
        """
        x, y = line[0]
        Particle.__init__(self, x, y, list)
        self.index = 0
        self.max_index = len(line)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x * SPRITE_SIZE, self.y * SPRITE_SIZE)
        self.line = line

    def update(self):
        """
        Moves particle
        """
        self.index += 1
        if self.index >= self.max_index:
            self.list.remove(self)
        else:
            x, y = self.line[self.index]
            self.x = x
            self.y = y
            self.rect.topleft = (self.x * SPRITE_SIZE, self.y * SPRITE_SIZE)


class NumberParticle(Particle):
    """
    Class that represents damage number above creature

    Attributes:
        x (arg, int): x position of particle
        y (arg, int): y position of particle
        v_x (int): x velocity of particle
        v_y (int): y velocity of particle
        max_x (int): max x position of particle (after which it disappears)
        max_y (int): max y position of particle (after which it disappears)
        list (arg, Group): group particle belongs to
        color (arg, RGB): color of particle
    """
    # Pixels per second the number is launched upward with, and gravity pulling it back
    LAUNCH_SPEED = 300.0
    GRAVITY = 900.0

    def __init__(self, x, y, damage, list, colour):
        Particle.__init__(self, x, y, list)
        self.x += 0.5
        self.start_y = self.y
        self.t0 = pygame.time.get_ticks()
        self.lifetime = 2 * self.LAUNCH_SPEED / self.GRAVITY
        # Render with a dark outline so numbers stay readable on any tile
        text, _ = myfont.render(str(damage), colour)
        outline, _ = myfont.render(str(damage), (0, 0, 0))
        w, h = text.get_size()
        self.base_image = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
        for ox, oy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            self.base_image.blit(outline, (ox, oy))
        self.base_image.blit(text, (1, 1))
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (int(self.x * SPRITE_SIZE), int(self.y * SPRITE_SIZE))

    def update(self):
        """
        Moves particle along a small arc (time based, so it looks the same
        regardless of frame rate) and fades it out at the end
        """
        t = (pygame.time.get_ticks() - self.t0) / 1000.0
        if t >= self.lifetime:
            if self in self.list:
                self.list.remove(self)
            return
        offset_px = -self.LAUNCH_SPEED * t + 0.5 * self.GRAVITY * t * t
        self.y = self.start_y + offset_px / SPRITE_SIZE
        self.rect.topleft = (int(self.x * SPRITE_SIZE), int(self.y * SPRITE_SIZE))
        remaining = 1 - t / self.lifetime
        if remaining < 0.35:
            self.image = self.base_image.copy()
            self.image.set_alpha(int(255 * remaining / 0.35))


class FadeParticle(Particle):
    """
    A sprite that rises slightly and fades out. Used for creatures that die so
    they don't just vanish.

    Attributes:
        image (arg, Surface): image to fade out
        pos (arg, (float, float)): tile position to show it at
        list (arg, list): particle list it belongs to
    """
    def __init__(self, image, pos, list):
        Particle.__init__(self, pos[0], pos[1], list)
        self.base_image = image.copy()
        self.image = self.base_image
        self.t0 = pygame.time.get_ticks()
        self.rect = self.image.get_rect()
        self.rect.topleft = (int(self.x * SPRITE_SIZE), int(self.y * SPRITE_SIZE))

    def update(self):
        t = (pygame.time.get_ticks() - self.t0) / DEATH_FADE_MS
        if t >= 1.0:
            if self in self.list:
                self.list.remove(self)
            return
        self.image = self.base_image.copy()
        self.image.set_alpha(int(255 * (1 - t)))
        self.rect.topleft = (int(self.x * SPRITE_SIZE), int((self.y - 0.25 * t) * SPRITE_SIZE))


def _outlined_text(text, colour):
    """Renders text with a 1px dark outline so it reads on any tile."""
    fg, _ = myfont.render(str(text), colour)
    outline, _ = myfont.render(str(text), (0, 0, 0))
    w, h = fg.get_size()
    surf = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    for ox, oy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        surf.blit(outline, (ox, oy))
    surf.blit(fg, (1, 1))
    return surf


class FloatingTextParticle(Particle):
    """
    A short label (eg "+ Red Potion", "+10 HP") that drifts upward from a tile
    and fades out.

    Attributes:
        x, y (arg, float): tile position it starts at
        text (arg, str): text to show
        colour (arg, RGB): text colour
        delay_ms (arg, int): wait this long before appearing (to stack labels)
    """
    LIFETIME_MS = 950
    RISE_TILES = 0.75

    def __init__(self, x, y, text, list, colour, delay_ms=0):
        Particle.__init__(self, x, y, list)
        self.base_image = _outlined_text(text, colour)
        self.image = self.base_image.copy()
        self.image.set_alpha(0)
        self.t0 = pygame.time.get_ticks() + delay_ms
        self.rect = self.image.get_rect()
        self._place(0.0)

    def _place(self, t):
        cx = (self.x + 0.5) * SPRITE_SIZE
        cy = (self.y - 0.05 - self.RISE_TILES * (1 - (1 - t) ** 2)) * SPRITE_SIZE
        self.rect.center = (int(cx), int(cy))

    def update(self):
        t = (pygame.time.get_ticks() - self.t0) / self.LIFETIME_MS
        if t < 0:
            return
        if t >= 1.0:
            if self in self.list:
                self.list.remove(self)
            return
        self._place(t)
        alpha = 255 if t < 0.6 else int(255 * (1 - (t - 0.6) / 0.4))
        self.image = self.base_image.copy()
        self.image.set_alpha(alpha)


class PickupParticle(Particle):
    """
    The picked-up item's own sprite hops up, shrinks and flies into the
    collector (so picking things up has visible feedback).

    Attributes:
        image (arg, Surface): item sprite
        start (arg, (float, float)): tile the item was lying on
        target_entity (arg, Entity): entity it flies into (uses its visual position)
    """
    LIFETIME_MS = 320

    def __init__(self, image, start, target_entity, list):
        Particle.__init__(self, start[0], start[1], list)
        self.base_image = image
        self.start = start
        self.target = target_entity
        self.t0 = pygame.time.get_ticks()
        self.image = image
        self.rect = image.get_rect()
        self.rect.topleft = (int(start[0] * SPRITE_SIZE), int(start[1] * SPRITE_SIZE))

    def update(self):
        t = (pygame.time.get_ticks() - self.t0) / self.LIFETIME_MS
        if t >= 1.0:
            if self in self.list:
                self.list.remove(self)
            return
        tx, ty = self.target.visual_pos() if hasattr(self.target, "visual_pos") else (self.target.x, self.target.y)
        ease = t * t
        x = self.start[0] + (tx - self.start[0]) * ease
        hop = 0.45 * math.sin(math.pi * min(1.0, t * 1.4))
        y = self.start[1] + (ty - self.start[1]) * ease - hop
        scale = 1.0 - 0.6 * t
        size = max(1, int(SPRITE_SIZE * scale))
        img = pygame.transform.smoothscale(self.base_image, (size, size))
        img.set_alpha(int(255 * (1 - t * t)))
        self.image = img
        cx = (x + 0.5) * SPRITE_SIZE
        cy = (y + 0.5) * SPRITE_SIZE
        self.rect = img.get_rect(center=(int(cx), int(cy)))
