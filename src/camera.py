import random
from constant import *


class Camera:
    """
    Camera that smoothly follows a target (usually the player) around the map.

    The camera works in *pixel* space rather than tile space, so it can sit
    between two tiles while an entity is gliding from one tile to the next.
    Everything that gets drawn is shifted by (-offset_x, -offset_y).

    Attributes:
        map_info (arg, MapInfo): map info of map
        camera_width (int): width of camera (screen) in pixels
        camera_height (int): height of camera (screen) in pixels
        offset_x (float): world pixel x shown at the left edge of the screen
        offset_y (float): world pixel y shown at the top edge of the screen
        camera (Rect): legacy rect whose topleft is the (negative) draw offset
    """

    def __init__(self, map_info, camera_width=CAMERA_WIDTH, camera_height=CAMERA_HEIGHT):
        self.map_info = map_info
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._shake_start = 0
        self._shake_dx = 0
        self._shake_dy = 0
        self.camera = pygame.Rect(0, 0, map_info.pixel_width, map_info.pixel_height)

    # ------------------------------------------------------------------ #
    # Following
    # ------------------------------------------------------------------ #
    def update(self, target):
        """
        Centers the camera on target's *visual* position (so the camera glides
        along with a moving entity), clamped to the map edges.

        Args:
            target (Entity): entity to follow
        """
        if hasattr(target, "visual_pos"):
            vx, vy = target.visual_pos()
        else:
            vx, vy = target.x, target.y

        tx = vx * SPRITE_SIZE + SPRITE_SIZE / 2 - self.camera_width / 2
        ty = vy * SPRITE_SIZE + SPRITE_SIZE / 2 - self.camera_height / 2

        self.offset_x = self._clamp_axis(tx, self.map_info.pixel_width, self.camera_width)
        self.offset_y = self._clamp_axis(ty, self.map_info.pixel_height, self.camera_height)

        self._update_shake()

        self.camera = pygame.Rect(-self.ix, -self.iy, self.map_info.pixel_width, self.map_info.pixel_height)

    @staticmethod
    def _clamp_axis(value, map_size, view_size):
        """Clamp camera offset to the map; center the map if it is smaller than the view."""
        if map_size <= view_size:
            return (map_size - view_size) / 2
        return max(0.0, min(value, map_size - view_size))

    # ------------------------------------------------------------------ #
    # Screen shake
    # ------------------------------------------------------------------ #
    def shake(self):
        """Starts a short screen shake (used when the player gets hit)."""
        self._shake_start = pygame.time.get_ticks()

    def _update_shake(self):
        elapsed = pygame.time.get_ticks() - self._shake_start
        if self._shake_start and elapsed < SHAKE_MS:
            strength = SHAKE_PIXELS * (1 - elapsed / SHAKE_MS)
            self._shake_dx = int(random.uniform(-strength, strength))
            self._shake_dy = int(random.uniform(-strength, strength))
        else:
            self._shake_dx = self._shake_dy = 0

    # ------------------------------------------------------------------ #
    # Coordinate helpers
    # ------------------------------------------------------------------ #
    @property
    def ix(self):
        """Integer pixel offset on x (including shake) used for drawing."""
        return int(round(self.offset_x)) + self._shake_dx

    @property
    def iy(self):
        """Integer pixel offset on y (including shake) used for drawing."""
        return int(round(self.offset_y)) + self._shake_dy

    def apply_with_image(self, entity):
        """
        Apply camera offset to entity that has a pixel rect (eg particles)

        Args:
            entity (object): Entity to apply offset to
        """
        return entity.rect.move(self.camera.topleft)

    def apply_without_image(self, entity):
        """
        Apply camera offset to an object positioned in tile coordinates

        Args:
            entity (object): Entity to apply offset to
        """
        return self.world_to_screen(entity.x, entity.y)

    def world_to_screen(self, x, y):
        """
        Converts a (possibly fractional) tile coordinate to a screen pixel coordinate

        Args:
            x (float): tile x
            y (float): tile y

        Returns:
            (int, int): top-left pixel of that tile on screen
        """
        return int(round(x * SPRITE_SIZE)) - self.ix, int(round(y * SPRITE_SIZE)) - self.iy

    @property
    def camera_position(self):
        """
        Returns:
            x, y (int, int): world pixel shown at top-left of the screen
        """
        return self.ix, self.iy

    def visible_tile_range(self):
        """
        Returns the range of tiles currently (partly) on screen so drawing
        can skip everything that is off screen.

        Returns:
            (x0, x1, y0, y1): half-open tile ranges [x0, x1) and [y0, y1)
        """
        x0 = max(0, self.ix // SPRITE_SIZE)
        y0 = max(0, self.iy // SPRITE_SIZE)
        x1 = min(self.map_info.tile_width, (self.ix + self.camera_width) // SPRITE_SIZE + 1)
        y1 = min(self.map_info.tile_height, (self.iy + self.camera_height) // SPRITE_SIZE + 1)
        return x0, x1, y0, y1

    def get_mouse_coord(self):
        """
        Returns the map tile under the mouse cursor (clamped to the map)

        Returns:
            mouse_x, mouse_y ((int, int)): Coordinate of mouse on map
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x = (mouse_x + self.ix) // SPRITE_SIZE
        tile_y = (mouse_y + self.iy) // SPRITE_SIZE
        tile_x = max(0, min(self.map_info.tile_width - 1, tile_x))
        tile_y = max(0, min(self.map_info.tile_height - 1, tile_y))
        return tile_x, tile_y
