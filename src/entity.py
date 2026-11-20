import math
from constant import *
import config
import item as i  # noqa: F401  (kept for import-order side effects)


def _now():
    """Milliseconds since pygame.init(); used as the clock for all visual tweens."""
    return pygame.time.get_ticks()


class Entity:
    """
    Class for Entity which represents entity, which is anything that appears
    and acts in the game

    Attributes:
        x (arg, int): Position on x axis
        y (arg, int): Position on y axis
        object_name (arg, string): name of Entity (ie type of entity).
            Also key of sprite image
        anim_length (arg, int): number of sprites in animation

        left (bool): if Entity is facing left
        right (bool): if Entity is facing right
        moving (bool): if Entity is moving

        flicker_speed (float): how much time we spend on single frame
        flicker_timer (float): how much timer has passed
        anim_frame (int): current frame of animation

        creature (arg, Creature): Creature it is
        ai (arg, ai): Ai Entity has
        item (arg, Item): Item self is
        container (arg, Container): Container self is
    """

    def __init__(self, x, y, object_name, creature=None, ai=None, item=None, container=None):
        self.x = x
        self.y = y
        self.object_name = object_name

        if isinstance(config.SPRITE.entity_dict[self.object_name], dict):
            self.anim_length = len(config.SPRITE.entity_dict[self.object_name]["idle_right"])
        else:
            self.anim_length = 1

        self.left = False
        self.right = True
        self.moving = False

        if self.anim_length > 1:
            self.flicker_speed = ANIMATION_SPEED / self.anim_length / 1.0
            self.flicker_timer = 0.0
            self.anim_frame = 0

        self.creature = creature
        if creature:
            creature.owner = self

        self.ai = ai
        if ai:
            ai.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.container = container
        if self.container:
            self.container.owner = self

    @property
    def position(self):
        """
        Returns object's position

        Returns:
            Object's position
        """
        return self.x, self.y

    @property
    def rect(self):
        """
        Returns entity's rect position, ie where the entity is on the screen,
        which is different then self.x, self.y which is the position of entity
        in game

        Returns:
            Entity's rect position
        """
        return self.x * SPRITE_SIZE, self.y * SPRITE_SIZE

    @property
    def size(self):
        """
        Returns:
            Entity's sprite size, which is usually SPRITE_SIZE
        """
        return SPRITE_SIZE, SPRITE_SIZE

    @property
    def image(self):
        """
        Returns image that entity should show entity

        Returns:
            image (Sprite): Sprite that self should show
        """
        image = None
        if self.anim_length == 1:
            image = config.SPRITE.entity_dict[self.object_name]
        else:
            if self.right:
                if self.moving:
                    image = config.SPRITE.entity_dict[self.object_name]["run_right"][self.anim_frame]
                else:
                    image = config.SPRITE.entity_dict[self.object_name]["idle_right"][self.anim_frame]
            else:
                if self.moving:
                    image = config.SPRITE.entity_dict[self.object_name]["run_left"][self.anim_frame]
                else:
                    image = config.SPRITE.entity_dict[self.object_name]["idle_left"][self.anim_frame]
        return image

    # ------------------------------------------------------------------ #
    # Smooth movement (visual only – game logic still uses integer x, y)
    # ------------------------------------------------------------------ #
    def visual_pos(self):
        """
        Returns the (fractional) tile position the entity should be *drawn* at.

        The logical position (self.x, self.y) changes instantly every turn; this
        lazily notices the change and glides from the previous on-screen position
        to the new tile over MOVE_TWEEN_MS. Jumps of more than one tile
        (teleport, changing floors, loading a save) snap instantly instead.

        Returns:
            (float, float): tile coordinates to draw at
        """
        now = _now()
        target = (self.x, self.y)
        vis_to = getattr(self, "_vis_to", None)

        if vis_to is None:
            self._vis_from = target
            self._vis_to = target
            self._vis_dur = MOVE_TWEEN_MS
            self._vis_t0 = now - MOVE_TWEEN_MS
        elif target != vis_to:
            fx, fy = self._interpolate(now)
            if max(abs(target[0] - fx), abs(target[1] - fy)) <= 1.5:
                self._vis_from = (fx, fy)
            else:
                self._vis_from = target
            self._vis_to = target
            self._vis_t0 = now
            # A slow move (wading through mud, carrying too much) glides slower
            self._vis_dur = MOVE_TWEEN_MS * max(1.0, getattr(self, "move_scale", 1.0))
            self.move_scale = 1.0

        return self._interpolate(now)

    def _tween_ms(self):
        return getattr(self, "_vis_dur", MOVE_TWEEN_MS)

    def _interpolate(self, now):
        t = (now - self._vis_t0) / self._tween_ms()
        if t >= 1.0:
            return self._vis_to
        fx, fy = self._vis_from
        tx, ty = self._vis_to
        return fx + (tx - fx) * t, fy + (ty - fy) * t

    def is_tweening(self):
        """
        Returns:
            True while the entity is still gliding towards its tile
        """
        self.visual_pos()
        return _now() - self._vis_t0 < self._tween_ms()

    def snap_visual(self):
        """Stops any glide and puts the sprite exactly on its tile."""
        self._vis_from = self._vis_to = (self.x, self.y)
        self._vis_dur = MOVE_TWEEN_MS
        self._vis_t0 = _now() - MOVE_TWEEN_MS

    def start_lunge(self, dx, dy):
        """
        Starts a short 'bump' towards (dx, dy), used when attacking

        Args:
            dx (int): x direction of the attack
            dy (int): y direction of the attack
        """
        self._lunge = (dx, dy, _now())

    def start_hit_flash(self):
        """Makes the sprite flash red for a moment (used when taking damage)."""
        self._hit_t0 = _now()

    def is_hit_flashing(self):
        hit_t0 = getattr(self, "_hit_t0", None)
        return hit_t0 is not None and _now() - hit_t0 < HIT_FLASH_MS

    def render_pos(self):
        """
        Returns:
            (float, float): visual position plus attack-lunge offset
        """
        x, y = self.visual_pos()
        lunge = getattr(self, "_lunge", None)
        if lunge:
            dx, dy, t0 = lunge
            t = (_now() - t0) / LUNGE_MS
            if t >= 1.0:
                self._lunge = None
            else:
                reach = LUNGE_DISTANCE * math.sin(math.pi * t)
                x += dx * reach
                y += dy * reach
        return x, y

    def update_anim(self):
        """
        Updates objects sprite depending on time passed
        and if it is moving and direction it is facing
        """
        if self.anim_length > 1:
            now = _now()
            last = getattr(self, "_anim_last", now)
            self._anim_last = now
            # Clamp so a long pause (menus, loading) doesn't skip many frames
            self.flicker_timer += min(now - last, 100) / 1000.0

            if self.flicker_timer >= self.flicker_speed:
                self.flicker_timer -= self.flicker_speed
                self.anim_frame += 1
                self.anim_frame %= self.anim_length

            # Play the run cycle while gliding (plus a short grace period so
            # walking continuously doesn't flicker back to idle between steps)
            self.visual_pos()
            self.moving = now - self._vis_t0 < self._tween_ms() + 90

    def update(self, dx, dy):
        """
        Updates the Entity depending on its ai or player input
        """
        if self.ai:
            # Stuck in mud: entering a mud tile costs MUD_TURN_COST turns
            if getattr(self, "stuck_turns", 0) > 0:
                self.stuck_turns -= 1
            else:
                self.ai.take_turn()
        else:
            self.creature.move(dx, dy)

        if self.creature.stat:
            # Regenerates hp and mp of creatures
            self.creature.regen()
