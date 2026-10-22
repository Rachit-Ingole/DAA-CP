import pygame
import pygame.freetype
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
    def __init__(self, x, y, damage, list, colour):
        Particle.__init__(self, x, y, list)
        self.x += 0.5
        self.v_x = 2 / SPRITE_SIZE
        self.v_y = -5 / SPRITE_SIZE
        self.max_x = self.x + SPRITE_SIZE
        self.max_y = self.y
        self.image, self.rect = myfont.render(str(damage), colour)
        self.rect.topleft = (self.x * SPRITE_SIZE, self.y * SPRITE_SIZE)

    def update(self):
        """
        Moves particle
        """
        # self.x += self.v_x
        self.y += self.v_y
        self.v_y += 0.25 / SPRITE_SIZE
        self.rect.topleft = (self.x * SPRITE_SIZE, self.y * SPRITE_SIZE)
        if self.y >= self.max_y or self.x >= self.max_x:
            self.list.remove(self)
