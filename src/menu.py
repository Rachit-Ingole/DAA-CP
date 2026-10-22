from functools import partial
import sys

import entity_generator
from constant import *
import config
import draw
import game
import game_text
import magic
import buttonmanager


class TextButton:
    def __init__(self, button_text, size, center, colour, clickable=True):
        """
        Class representing button with text

        Args:
            button_text (String): String to display on button
            size ((int, int)): Size of button
            center ((int, int)): Coord of center of button
            colour (Colour): Colour of button
            clickable (Boolean): If button is clickable/mouse-overable

        Attributes:
            normal_colour (Colour): Normal colour of button
            mouse_over_colour (Colour): Mouse over colour of button
        """
        self.button_text = button_text
        self.size = size
        self.center = center
        self.colour = colour
        self.clickable = clickable

        self.normal_colour = self.colour
        # Darkens color
        self.mouse_over_colour = (max(self.colour[0] - 50, 0),
                                  max(self.colour[1] - 50, 0),
                                  max(self.colour[2] - 50, 0))

        self.rect = pygame.Rect((0, 0), size)
        self.rect.center = center

    def draw(self):
        """
        Draws button with text on it
        """
        pygame.draw.rect(config.SURFACE_MAIN, self.colour, self.rect)
        game_text.draw_text(config.SURFACE_MAIN, self.center, BLACK, self.button_text, center=True)

    def mouse_over(self):
        """
        Checks if button is moused over and if so, darken it

        If button is clickable and moused over, darken the button,
        else return button to normal colour
        """
        if self.clickable:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            mouse_over = (self.rect.left <= mouse_x <= self.rect.right and
                          self.rect.top <= mouse_y <= self.rect.bottom)

            if mouse_over:
                self.colour = self.mouse_over_colour
            else:
                self.colour = self.normal_colour


class ModernMenuButton:
    """Clean, modern button with rounded corners, border highlight, and state styling."""
    def __init__(self, text, rect, base_color=(36, 46, 68), hover_color=(54, 76, 116),
                 border_color=(85, 115, 165), text_color=(245, 245, 250), clickable=True):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.base_color = base_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.text_color = text_color
        self.clickable = clickable
        self.is_hovered = False

    def update(self, mouse_pos):
        if self.clickable:
            self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def draw(self, surface):
        bg = self.hover_color if self.is_hovered else (self.base_color if self.clickable else (24, 28, 38))
        border = (130, 185, 255) if self.is_hovered else (self.border_color if self.clickable else (50, 56, 70))
        txt_col = (255, 255, 255) if self.is_hovered else (self.text_color if self.clickable else (110, 115, 130))

        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=6)
        game_text.draw_text(surface, self.rect.center, txt_col, self.text, center=True)


def main_menu():
    """
    Main menu before starting game.
    Clean, modern, simple interface with direct Knight start.
    """
    save_available = os.path.isfile(SAVE_PATH) and os.stat(SAVE_PATH).st_size > 0

    center_x = config.CAMERA.camera_width // 2

    # Button layout dimensions
    btn_w, btn_h = 280, 48
    btn_x = center_x - btn_w // 2

    btn_new = ModernMenuButton("Start Game (Knight)", (btn_x, 240, btn_w, btn_h),
                               base_color=(35, 48, 72), hover_color=(58, 82, 126),
                               border_color=(95, 138, 205), text_color=(250, 250, 255))

    btn_continue = ModernMenuButton("Continue Journey", (btn_x, 305, btn_w, btn_h),
                                    base_color=(32, 54, 44), hover_color=(48, 86, 68),
                                    border_color=(75, 145, 105), text_color=(230, 255, 235),
                                    clickable=save_available)

    btn_controls = ModernMenuButton("Controls & DAA Keys", (btn_x, 370, btn_w, btn_h),
                                    base_color=(36, 42, 58), hover_color=(52, 64, 90),
                                    border_color=(80, 100, 135), text_color=(220, 225, 240))

    btn_exit = ModernMenuButton("Exit Game", (btn_x, 435, btn_w, btn_h),
                                base_color=(46, 36, 40), hover_color=(78, 48, 54),
                                border_color=(135, 75, 82), text_color=(240, 210, 215))

    buttons = [btn_new, btn_continue, btn_controls, btn_exit]
    bg_color = (18, 22, 32)
    accent_bar_color = (65, 115, 195)

    while True:
        config.SURFACE_MAIN.fill(bg_color)

        # Subtle decorative accent lines
        pygame.draw.line(config.SURFACE_MAIN, accent_bar_color, (40, 30),
                         (config.CAMERA.camera_width - 40, 30), 2)
        pygame.draw.line(config.SURFACE_MAIN, accent_bar_color, (40, config.CAMERA.camera_height - 30),
                         (config.CAMERA.camera_width - 40, config.CAMERA.camera_height - 30), 2)

        # Title & Subtitle Typography
        title_y = 75
        game_text.draw_text(config.SURFACE_MAIN, (center_x, title_y), (245, 215, 115),
                            "ALGORITHM LABYRINTH", center=True)
        game_text.draw_text(config.SURFACE_MAIN, (center_x, title_y + 36), (110, 175, 245),
                            "CS3101: Design & Analysis of Algorithms", center=True)
        game_text.draw_text(config.SURFACE_MAIN, (center_x, title_y + 70), (130, 210, 160),
                            "— Active Hero: Knight —", center=True)

        mouse_pos = pygame.mouse.get_pos()

        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw(config.SURFACE_MAIN)

        # Footer hint
        game_text.draw_text(config.SURFACE_MAIN, (center_x, 525), (140, 150, 175),
                            "Press ENTER or Space to start instantly | Key 'C' for Controls", center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    config.PLAYER = entity_generator.generate_player(config.MAP_INFO.map_tree, 'knight')
                    g = game.Game()
                    game.populate_map()
                    g.run()
                    btn_continue.clickable = False
                elif event.key == pygame.K_c:
                    keys_menu()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_new.rect.collidepoint(mouse_pos):
                    config.PLAYER = entity_generator.generate_player(config.MAP_INFO.map_tree, 'knight')
                    g = game.Game()
                    game.populate_map()
                    g.run()
                    btn_continue.clickable = False
                elif btn_continue.rect.collidepoint(mouse_pos) and btn_continue.clickable:
                    g = game.Game()
                    game.load_game()
                    g.run()
                    btn_continue.clickable = False
                elif btn_controls.rect.collidepoint(mouse_pos):
                    keys_menu()
                elif btn_exit.rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        config.CLOCK.tick(FPS)
        pygame.display.update()


def pause():
    """
    Pause menu with continue button, save and exit button and exit button
    """
    # Make buttons
    resume_button = TextButton("Resume", (BUTTON_WIDTH, BUTTON_HEIGHT),
                               (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 4 + 100), GREEN)

    save_and_quit_button = TextButton("Save and quit", (BUTTON_WIDTH, BUTTON_HEIGHT),
                                      (CAMERA_WIDTH // 2, resume_button.rect.midbottom[1] + 100), RED)

    exit_button = TextButton("Exit", (BUTTON_WIDTH, BUTTON_HEIGHT),
                             (CAMERA_WIDTH // 2, save_and_quit_button.rect.midbottom[1] + 100), GREY)

    pause_menu = True
    while pause_menu:
        config.SURFACE_MAIN.blit(config.SPRITE.unfocused_window, (0, 0))

        game_text.draw_text(config.SURFACE_MAIN,
                            (CAMERA_WIDTH // 2, resume_button.rect.midtop[1] - 100), WHITE,
                            "PAUSED", BLACK, center=True)

        mouse_x, mouse_y = pygame.mouse.get_pos()

        resume_button.mouse_over()
        save_and_quit_button.mouse_over()
        exit_button.mouse_over()

        resume_button.draw()

        save_and_quit_button.draw()

        exit_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    pause_menu = False
                    break
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if resume_button.rect.collidepoint((mouse_x, mouse_y)):
                        pause_menu = False
                        break
                    elif save_and_quit_button.rect.collidepoint((mouse_x, mouse_y)) and resume_button.clickable:
                        game.quit_game()
                    elif exit_button.rect.collidepoint((mouse_x, mouse_y)):
                        pygame.quit()
                        sys.exit()

        config.CLOCK.tick(FPS)
        pygame.display.update()


def map_menu():
    """
    Creates full map menu

    Only input available is closing game or clicking any other button to close map
    """
    menu_closed = False
    while not menu_closed:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_closed = True
                    break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button = config.BUTTON_PANEL.check_if_button_pressed(mouse_x, mouse_y)
                    if button:
                        menu_closed = True
                        break

        draw.draw_map(config.MAP_INFO)
        config.BUTTON_PANEL.draw_buttons(config.SURFACE_MAIN)
        config.CLOCK.tick(FPS)
        pygame.display.update()


def magic_select_menu():
    """
    Shows spells that are castable and allows for choosing which spell to cast
    """
    select_menu = _draw_castable_spells()

    select_magic = True
    while select_magic:
        game.update_game()
        draw.draw_mouse()
        select_menu.draw_buttons(config.SURFACE_MAIN)

        mouse_x, mouse_y = pygame.mouse.get_pos()

        hovered_button = select_menu.check_if_button_hovered(mouse_x, mouse_y)
        if hovered_button and hovered_button.mouse_over_fn:
            hovered_button.mouse_over_fn()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    select_magic = False
                    break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    button = config.BUTTON_PANEL.check_if_button_pressed(mouse_x, mouse_y)
                    if button:
                        select_magic = False
                        break

                    magic_button = select_menu.check_if_button_pressed(mouse_x, mouse_y)
                    if magic_button:
                        magic_targetting_menu(magic_button.left_click_fn)

        config.CLOCK.tick(FPS)
        pygame.display.flip()


def _draw_castable_spells():
    """
    Initializes spell selection button manager and return button mananger

    Returns:
        magic_select (ButtonManager): ButtonManager with buttons corresponding to spells
    """
    num_of_spaces = 5
    menu_width = config.CAMERA.camera_width // 2 - (num_of_spaces // 2 * SPRITE_SIZE)
    menu_height = config.CAMERA.camera_height // 2 + (2 * SPRITE_SIZE)

    magic_select = buttonmanager.ButtonManager(menu_width,
                                                   menu_height,
                                                   num_of_spaces, 1, BLACK)

    fireball = buttonmanager.IconButton(0, 0, config.SPRITE.magic["fireball"],
                                        magic.cast_fireball)
    tmp = (lambda: draw.draw_description(0, 0, menu_width,
                                          menu_height, magic.spell_description("fireball")))
    fireball.mouse_over_fn = tmp
    magic_select.add_button(fireball, "fireball")

    lightning = buttonmanager.IconButton(2 * SPRITE_SIZE, 0, config.SPRITE.magic["lightning"],
                                         magic.cast_lightning)
    tmp1 = (lambda: draw.draw_description(lightning.rect.topleft[0], lightning.rect.topleft[1],
                                           menu_width, menu_height, magic.spell_description("lightning")))
    lightning.mouse_over_fn = tmp1
    magic_select.add_button(lightning, "lightning")

    confusion = buttonmanager.IconButton(4 * SPRITE_SIZE, 0, config.SPRITE.magic["confusion"],
                                         magic.cast_confusion)
    tmp2 = (lambda: draw.draw_description(confusion.rect.topleft[0], confusion.rect.topleft[1], menu_width,
                                        menu_height, magic.spell_description("confusion")))
    confusion.mouse_over_fn = tmp2
    magic_select.add_button(confusion, "confusion")

    return magic_select


def magic_targetting_menu(spell_to_cast):
    """
    Selects target for spell and cast spell_to_cast and updates display

    Args:
        spell_to_cast (fn pointer):
    """
    magic_cast = True
    while magic_cast:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    magic_cast = False
                    break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    button = config.BUTTON_PANEL.check_if_button_pressed(mouse_x, mouse_y)
                    if button:
                        button.left_click_fn()
                        break

                    game.cast_magic(spell_to_cast, line)
                    magic_cast = False
                    break

        config.CLOCK.tick(FPS)
        game.update_game()
        draw.draw_mouse()
        m_x, m_y = config.CAMERA.get_mouse_coord()
        line = magic.line(config.PLAYER.position, (m_x, m_y), config.MAP_INFO.tile_array, config.FOV)
        draw.draw_magic_path(line)
        pygame.display.flip()


def stat_menu():
    """
    Draws stat menu
    """
    menu_width, menu_height = config.CAMERA.camera_width / 3, config.CAMERA.camera_height / 3
    stat_surface = pygame.Surface((menu_width, menu_height))

    # Could move this to _draw_stat if you want animated character icon in stat menu
    character_icon = pygame.transform.scale(config.PLAYER.image, (SPRITE_SIZE * 2, SPRITE_SIZE * 2))

    stat_open = True
    while stat_open:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                stat_open = False
                break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                stat_open = False
                break

        config.CLOCK.tick(FPS)
        game.update_game()
        _draw_stat(config.PLAYER, stat_surface, character_icon)
        # Centers stat_menu
        stat_rect = stat_surface.get_rect()
        stat_rect.center = (config.CAMERA.camera_width // 2, config.CAMERA.camera_height // 2)

        config.SURFACE_MAIN.blit(stat_surface, stat_rect)
        draw.draw_mouse()

        pygame.display.flip()


def _draw_stat(player, surface, character_icon):
    """
    Draws player stat to stat_surface

    Args:
        player (Entity): Player's stat to draw
        surface (Surface): Surface to draw stats on
        character_icon (Sprite): Sprite of character
    """
    max_hp = player.creature.stat.max_hp
    max_mp = player.creature.stat.max_mp
    hp = player.creature.stat.hp
    mp = player.creature.stat.mp
    strength = player.creature.stat.strength
    defense = player.creature.stat.defense
    wizardry = player.creature.stat.wizardry
    exp = player.creature.stat.exp
    level = player.creature.stat.level

    stat_list = ["hp: " + str(hp) + "/" + str(max_hp),
                 "mp: " + str(mp) + "/" + str(max_mp),
                 "strength: " + str(strength),
                 "defense: " + str(defense),
                 "wizardry: " + str(wizardry),
                 "exp: " + str(exp) + "/ 100",
                 "level: " + str(level)]

    for i, stat in enumerate(stat_list):
        game_text.draw_text(surface, (character_icon.get_width(), FONT_SIZE * i),
                            WHITE, stat)

    surface.blit(character_icon, (0, 0))


def inventory_menu():
    """
    create screens for inventory + equipment menus
    """
    menu_closed = False
    menu_width, menu_height = config.CAMERA.camera_width / 2, config.CAMERA.camera_height
    menu_surface = pygame.Surface((menu_width, menu_height - SPRITE_SIZE))
    menu_surface.fill(INVENTORY_BEIGE)

    while not menu_closed:
        events_list = pygame.event.get()
        game.update_game()

        config.SURFACE_MAIN.blit(menu_surface, (menu_width, 0))

        equipment = _load_equipment_screen()
        equipment.draw_buttons(config.SURFACE_MAIN)

        inventory = _load_inventory_screen()
        inventory.draw_buttons(config.SURFACE_MAIN)

        draw.draw_mouse()

        mouse_x, mouse_y = pygame.mouse.get_pos()

        hovered_inventory_button = inventory.check_if_button_hovered(mouse_x, mouse_y)
        if hovered_inventory_button and hovered_inventory_button.mouse_over_fn:
            hovered_inventory_button.mouse_over_fn()

        hovered_equipment_button = equipment.check_if_button_pressed(mouse_x, mouse_y)
        if hovered_equipment_button and hovered_equipment_button.mouse_over_fn:
            hovered_equipment_button.mouse_over_fn()

        for event in events_list:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    inventory_button = config.BUTTON_PANEL.check_if_specific_button_pressed(
                        'inventory', mouse_x, mouse_y)
                    if inventory_button:
                        menu_closed = True
                        break

                    map_button = config.BUTTON_PANEL.check_if_specific_button_pressed(
                        'map', mouse_x, mouse_y)
                    if map_button:
                        map_menu()
                        break

                    stat_button = config.BUTTON_PANEL.check_if_specific_button_pressed(
                        'stats', mouse_x, mouse_y)
                    if stat_button:
                        stat_menu()
                        break

                    item_slot = inventory.check_if_button_pressed(mouse_x, mouse_y)
                    if item_slot and item_slot.left_click_fn:
                        item_slot.left_click_fn()

                    equip_slot = equipment.check_if_button_pressed(mouse_x, mouse_y)
                    if equip_slot and equip_slot.left_click_fn:
                        equip_slot.left_click_fn()

                elif event.button == 3:
                    clicked_button = inventory.check_if_button_pressed(mouse_x, mouse_y)
                    if clicked_button and clicked_button.right_click_fn:
                        clicked_button.right_click_fn()
                        game.update_creatures(config.GAME_DATA.creature_data, 0, 0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    game.toggle_minimap()
                if event.key == pygame.K_i or event.key == pygame.K_ESCAPE:
                    menu_closed = True
                    break

        config.CLOCK.tick(FPS)
        pygame.display.update()


def _load_equipment_screen():
    """
    Helper method to create equipment screen with equip slots

    Returns:
        equip_slot (ButtonManager): ButtonManager representing equip slots + equipped items
    """
    menu_width = config.CAMERA.camera_width / 2
    menu_height = 0

    num_of_row = TILE_WIDTH // 2
    num_of_col = TILE_HEIGHT // 2

    equip_slot = buttonmanager.ButtonManager(menu_width, menu_height, num_of_row, num_of_col)

    hand_scale = (SPRITE_SIZE * 2, SPRITE_SIZE * 4)
    armor_scale = (SPRITE_SIZE * 4, SPRITE_SIZE * 6)

    # Make equipment slots
    left_hand_slot = pygame.transform.scale(config.SPRITE.empty_inventory_slot, hand_scale)
    left_hand = buttonmanager.IconButton(0, SPRITE_SIZE * 1, left_hand_slot)
    equip_slot.add_button(left_hand, "Left hand")

    right_hand_slot = pygame.transform.scale(config.SPRITE.empty_inventory_slot, hand_scale)
    right_hand = buttonmanager.IconButton(SPRITE_SIZE * 6, SPRITE_SIZE * 1, right_hand_slot)
    equip_slot.add_button(right_hand, "Right hand")

    armor_slot = pygame.transform.scale(config.SPRITE.empty_inventory_slot, armor_scale)
    armor = buttonmanager.IconButton(SPRITE_SIZE * 2, 0, armor_slot)
    equip_slot.add_button(armor, "Armor")

    # Find all entities equipped by player
    equipped_entities = config.PLAYER.creature.equip_slot.values()
    for equip_entity in equipped_entities:
        if equip_entity and equip_entity.item.equip_stat.equipped:
            slot = equip_entity.item.equip_stat.slot
            if slot == "Left hand":
                scaled_equip = pygame.transform.scale(equip_entity.image, hand_scale)
                left_hand_slot.blit(scaled_equip, (0, 0))
                left_hand.left_click_fn = equip_entity.item.equip_stat.toggle_equip
                left_hand.mouse_over_fn = partial(draw.draw_description, left_hand.rect.bottomleft[0],
                                                                        left_hand.rect.bottomleft[1],
                                                                        menu_width, menu_height,
                                                                        equip_entity.item.item_description())
            elif slot == "Right hand":
                scaled_equip = pygame.transform.scale(equip_entity.image, hand_scale)
                right_hand_slot.blit(scaled_equip, (0, 0))
                right_hand.left_click_fn = equip_entity.item.equip_stat.toggle_equip
                right_hand.mouse_over_fn = partial(draw.draw_description, right_hand.rect.bottomleft[0],
                                                                        right_hand.rect.bottomleft[1],
                                                                        menu_width, menu_height,
                                                                        equip_entity.item.item_description())
            elif slot == "Armor":
                scaled_equip = pygame.transform.scale(equip_entity.image, armor_scale)
                armor_slot.blit(scaled_equip, (0, 0))
                armor.left_click_fn = equip_entity.item.equip_stat.toggle_equip
                armor.mouse_over_fn = partial(draw.draw_description, armor.rect.bottomleft[0],
                                                                    armor.rect.bottomleft[1],
                                                                    menu_width, menu_height,
                                                                    equip_entity.item.item_description())

    return equip_slot


# def _load_equipment_screen():
#     """
#     Helper to create equipment_screen with items
#     :return:  equipment_surface
#     """
#     equipment_rects = []
#
#     menu_width, menu_height = config.CAMERA.camera_width / 2, config.CAMERA.camera_height / 2
#     equipment_surface = pygame.Surface((menu_width, menu_height))
#
#     helmet_tl, helmet_br = (243, 24), (294, 67)
#     armor_tl, armor_br = (218, 70), (319, 185)
#     amulet_tl, amulet_br = (323, 52), (361, 89)
#     main_tl, main_br = (38, 83), (114, 274)
#     off_tl, off_br = (390, 83), (466, 274)
#     ringL_tl, ringL_br = (176, 171), (214, 208)
#     ringR_tl, ringR_br = (323, 171), (361, 208)
#     pants_tl, pants_br = (218, 188), (319, 301)
#     gloves_tl, gloves_br = (134, 230), (209, 299)
#     boots_tl, boots_br = (232, 308), (305, 356)
#
#     helmet_rect = pygame.Rect(helmet_tl, ((helmet_br[0] - helmet_tl[0]), (helmet_br[1] - helmet_tl[1])))
#     armor_rect = pygame.Rect(armor_tl, ((armor_br[0] - armor_tl[0]), (armor_br[1] - armor_tl[1])))
#     amulet_rect = pygame.Rect(amulet_tl, ((amulet_br[0] - amulet_tl[0]), (amulet_br[1] - amulet_tl[1])))
#     main_rect = pygame.Rect(main_tl, ((main_br[0] - main_tl[0]), (main_br[1] - main_tl[1])))
#     off_rect = pygame.Rect(off_tl, ((off_br[0] - off_tl[0]), (off_br[1] - off_tl[1])))
#     ringL_rect = pygame.Rect(ringL_tl, ((ringL_br[0] - ringL_tl[0]), (ringL_br[1] - ringL_tl[1])))
#     ringR_rect = pygame.Rect(ringR_tl, ((ringR_br[0] - ringR_tl[0]), (ringR_br[1] - ringR_tl[1])))
#     pants_rect = pygame.Rect(pants_tl, ((pants_br[0] - pants_tl[0]), (pants_br[1] - pants_tl[1])))
#     gloves_rect = pygame.Rect(gloves_tl, ((gloves_br[0] - gloves_tl[0]), (gloves_br[1] - gloves_tl[1])))
#     boots_rect = pygame.Rect(boots_tl, ((boots_br[0] - boots_tl[0]), (boots_br[1] - boots_tl[1])))
#
#     equipment_rects.append(helmet_rect)
#     equipment_rects.append(armor_rect)
#     equipment_rects.append(amulet_rect)
#     equipment_rects.append(main_rect)
#     equipment_rects.append(off_rect)
#     equipment_rects.append(ringL_rect)
#     equipment_rects.append(ringR_rect)
#     equipment_rects.append(pants_rect)
#     equipment_rects.append(gloves_rect)
#     equipment_rects.append(boots_rect)
#
#     for rect in equipment_rects:
#         pygame.draw.rect(equipment_surface, INVENTORY_BEIGE, rect)
#
#     equipment_surface.blit(config.SPRITE.equip_screen, (0, 0))
#
#     return equipment_surface
#
#     # equip_dictionary = {
#     #     "main": None,
#     #     "off": None,
#     #     "helmet": None,
#     #     "armor": None,
#     #     "amulet": None,
#     #     "ring": None,
#     #     "pants": None,
#     #     "boots": None,
#     #     "gloves": None,
#     # }


def _load_inventory_screen():
    """
    Helper method to create inventory screen with items

    Returns:
        inventory (GridButtonManager): GridButtonManager representing inventory + items
    """
    menu_width, menu_height = config.CAMERA.camera_width / 2, config.CAMERA.camera_height / 2
    counter = 0

    num_item_in_row = TILE_WIDTH // 2
    num_item_in_col = TILE_HEIGHT // 2 - 1

    inventory = buttonmanager.GridButtonManager(menu_width, menu_height, num_item_in_row, num_item_in_col,
                                                (num_item_in_row * num_item_in_col))

    for y in range(num_item_in_col):
        for x in range(num_item_in_row):
            inventory_array = config.PLAYER.container.inventory
            # Separate surface for item
            item_slot = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE))
            item_slot.blit(config.SPRITE.empty_inventory_slot, (0, 0))

            inventory.create_button(item_slot, str(x + (num_item_in_row * y)))
            if len(inventory_array) >= counter + 1:
                button = inventory.get_button(str(x + (num_item_in_row * y)))
                item_entity = inventory_array[counter]
                item_slot.blit(item_entity.image, (0, 0))
                counter = counter + 1

                _create_item_mouse_interaction(button, item_entity, menu_height, menu_width)

    return inventory


def _create_item_mouse_interaction(button, item_entity, menu_height, menu_width):
    """
    Creates all mouse interaction for button

    Args:
        button (IconButton): IconButton to create mouse interaction for
        item_entity (Entity): Entity representing item that IconButton is
            holding/creating actions for
        menu_width (int): Where GridButtonManager is (needed for finding where to
            place hover box)
        menu_height (int): Where GridButtonManager is (needed for finding where to
            place hover box)
    """
    _create_item_mouse_interaction_hover(button, item_entity, menu_height, menu_width)

    _create_item_mouse_interaction_right_click(button, item_entity)

    _create_item_mouse_interaction_left_click(button, item_entity)


def _create_item_mouse_interaction_left_click(button, item_entity):
    """
    Creates IconButton left mouse click action for items

    Args:
        button (IconButton): IconButton to create interaction for
        item_entity (Entity): Entity representing item that IconButton is
            holding/creating actions for
    """
    button.left_click_fn = item_entity.item.use_item


def _create_item_mouse_interaction_right_click(button, item_entity):
    """
    Creates IconButton right mouse click action for items

    Args:
        button (IconButton): IconButton to create interaction for
        item_entity (Entity): Entity representing item that IconButton is
            holding/creating actions for
    """
    button.right_click_fn = partial(item_entity.item.drop_item, item_entity.item.current_container.owner)


def _create_item_mouse_interaction_hover(button, item_entity, menu_height, menu_width):
    """
    Creates IconButton hover mouse action for items

    Args:
        button (IconButton): IconButton to create interaction for
        item_entity (Entity): Entity representing item that IconButton is
            holding/creating actions for
        menu_width (int): Where GridButtonManager is (needed for finding where to
            place hover box)
        menu_height (int): Where GridButtonManager is (needed for finding where to
            place hover box)
    """
    button_x, button_y = button.rect.topleft
    button.mouse_over_fn = partial(draw.draw_description, button_x, button_y, menu_width, menu_height, item_entity.item.item_description())


def win_menu():
    """
    Win menu after using chest

    Deletes save file if there is data
    """
    if os.path.isfile(SAVE_PATH) and os.stat(SAVE_PATH).st_size > 0:
        open(SAVE_PATH, 'w').close()

    str = "Congratulations you found the treasure"

    new_button = TextButton("New Game", (BUTTON_WIDTH, BUTTON_HEIGHT),
                            (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 4 + 250), RED)

    exit_button = TextButton("Exit", (BUTTON_WIDTH, BUTTON_HEIGHT),
                             (CAMERA_WIDTH // 2, new_button.rect.midbottom[1] + 100), GREY)

    while True:
        config.SURFACE_MAIN.blit(config.SPRITE.unfocused_window, (0, 0))

        mouse_x, mouse_y = pygame.mouse.get_pos()

        new_button.mouse_over()
        exit_button.mouse_over()

        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 4 + 100),
                            WHITE, str, center=True)

        new_button.draw()

        exit_button.draw()

        g = game.Game()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if new_button.rect.collidepoint((mouse_x, mouse_y)):
                        game.new_game()
                        game.populate_map()
                        g.run()
                    elif exit_button.rect.collidepoint((mouse_x, mouse_y)):
                        pygame.quit()
                        sys.exit()

        pygame.display.update()


def keys_menu():
    """
    Shows controls
    """
    controls = "Key \n" \
               "w \n" \
               "a \n" \
               "s \n" \
               "d \n" \
               "q \n" \
               "e \n" \
               "z \n" \
               "c \n" \
               "x \n" \
               "Left mouse click \n" \
               "m \n" \
               "t \n" \
               "TAB \n" \
               "TAB + Movement keys \n" \
               "TAB + ENTER \n" \
               "v \n" \
               "p \n" \
               "i \n" \
               "i + Left mouse click \n" \
               "i + Right mouse click \n" \
               "SPACE \n" \
               "SPACE + Left mouse click \n" \
               "SPACE + Left mouse click + Left mouse click \n" \
               "1 (On upstairs) \n" \
               "2 (On downstairs) \n" \
               "ESC \n" \
               "F2 \n" \
               "F3 \n " \
               "F12"

    actions = "Action\n" \
                "Walk up \n" \
                "Walk left \n" \
                "Walk down \n" \
                "Walk right \n" \
                "Walk diagonally up and left \n" \
                "Walk diagonally up and right \n" \
                "Walk diagonally down and left \n" \
                "Walk diagonally down and right \n" \
                "Stay still \n" \
                "Move to mouse cursor \n" \
                "Toggle minimap \n" \
                "Pickup item \n" \
                "Toggle camera \n" \
                "Move camera around \n" \
                "Move to camera location \n" \
                "Auto explore \n" \
                "Pause and open menu \n" \
                "Toggle inventory screen \n" \
                "Use item / Equip / Unequip \n" \
                "Drop item \n" \
                "Toggle magic selection \n" \
                "Choose spell to cast \n" \
                "Cast chosen spell \n" \
                "Transition to previous level \n" \
                "Transition to next level \n" \
                "Close opened menu \n" \
                "Manually save game \n" \
                "Manually load game \n" \
                "Toggle FOV limitations \n"

    back_button = TextButton("Go back", (BUTTON_WIDTH, BUTTON_HEIGHT - 20),
                                 (CAMERA_WIDTH // 2, config.CAMERA.camera_height - (BUTTON_HEIGHT // 2)), RED)

    controls_rect = pygame.Rect(0, 0, config.CAMERA.camera_width, config.CAMERA.camera_height)
    actions_rect = pygame.Rect(config.CAMERA.camera_width // 2, 0, config.CAMERA.camera_width // 2, config.CAMERA.camera_height)

    controls_surface = game_text.multiLineSurface(controls, FONT_CONTROL_TEXT, controls_rect, BLACK, WHITE, 0)
    actions_surface = game_text.multiLineSurface(actions, FONT_CONTROL_TEXT, actions_rect, BLACK, WHITE, 0)

    control_open = True

    while control_open:
        back_button.mouse_over()

        config.SURFACE_MAIN.blit(controls_surface, controls_rect)
        config.SURFACE_MAIN.blit(actions_surface, actions_rect)

        back_button.draw()

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_c, pygame.K_RETURN, pygame.K_SPACE):
                    control_open = False
                    break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button.rect.collidepoint((mouse_x, mouse_y)):
                        control_open = False
                        break

        config.CLOCK.tick(FPS)
        pygame.display.update()


def instruction_menu():
    """
    Instruction menu telling player how to win
    """
    instructions = "Reach the lowest level of the dungeon and find the chest full of treasure! \n \n " \
                   "As you progress further into the dungeon, monsters get harder. \n" \
                   "Find items to aid you in your adventure and fight monster to get experience."
    continue_str = "Press any key to continue"

    instruction_rect = pygame.Rect(0, 0, config.CAMERA.camera_width // 2, SPRITE_SIZE * 6)
    continue_rect = pygame.Rect(0, 0, config.CAMERA.camera_width // 2, SPRITE_SIZE * 3)
    chest_rect = pygame.Rect(0, 0, SPRITE_SIZE, SPRITE_SIZE)

    instruction_surface = game_text.multiLineSurfaceTransparentBG(instructions, FONT_MESSAGE_TEXT, instruction_rect,
                                                                  BLACK, WHITE, None, justification=0)
    continue_surface = game_text.multiLineSurfaceTransparentBG(continue_str, FONT_MESSAGE_TEXT, continue_rect,
                                                               BLACK, WHITE, None, justification=1)

    instruction_rect.midtop = (config.CAMERA.camera_width // 2, (SPRITE_SIZE - FONT_SIZE))
    chest_rect.midtop = (config.CAMERA.camera_width // 2, config.CAMERA.camera_height // 2)
    continue_rect.midtop = (config.CAMERA.camera_width // 2, config.CAMERA.camera_height - SPRITE_SIZE)

    instruction_menu_open = True
    while instruction_menu_open:
        config.SURFACE_MAIN.fill(WHITE)

        config.SURFACE_MAIN.blit(instruction_surface, instruction_rect)
        config.SURFACE_MAIN.blit(config.SPRITE.entity_dict["chest"], chest_rect)
        config.SURFACE_MAIN.blit(continue_surface, continue_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                instruction_menu_open = False
                break

        pygame.display.update()


def class_selection_menu():
    """
    create screens for character selection
    """

    knight_entity = entity_generator.generate_player(config.MAP_INFO.map_tree, 'knight')
    config.PLAYER = knight_entity
    return knight_entity

def lose_menu():
    """
    Lose menu with go to main menu and exit button

    Deletes save file if there is data
    """
    if os.path.isfile(SAVE_PATH) and os.stat(SAVE_PATH).st_size > 0:
        open(SAVE_PATH, 'w').close()

    # Make buttons
    new_button = TextButton("Go to main menu", (BUTTON_WIDTH, BUTTON_HEIGHT),
                               (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 4 + 100), GREEN)

    exit_button = TextButton("Exit", (BUTTON_WIDTH, BUTTON_HEIGHT),
                             (CAMERA_WIDTH // 2, new_button.rect.midbottom[1] + 100), GREY)

    loss_menu = True

    while loss_menu:
        config.SURFACE_MAIN.blit(config.SPRITE.unfocused_window, (0, 0))

        game_text.draw_text(config.SURFACE_MAIN,
                            (CAMERA_WIDTH // 2, new_button.rect.midtop[1] - 100), WHITE,
                            "You lost", BLACK, center=True)

        mouse_x, mouse_y = pygame.mouse.get_pos()

        new_button.mouse_over()
        exit_button.mouse_over()

        new_button.draw()

        exit_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if new_button.rect.collidepoint((mouse_x, mouse_y)):
                        loss_menu = False
                        break
                    elif exit_button.rect.collidepoint((mouse_x, mouse_y)):
                        pygame.quit()
                        sys.exit()

        config.CLOCK.tick(FPS)
        pygame.display.update()


def knapsack_menu():
    """
    Interactive 0/1 Knapsack Problem Optimizer:
    Compares Dynamic Programming vs Greedy heuristic under carry-weight capacity constraint.
    """
    from algorithms.knapsack import KnapsackItem, compare_knapsack

    # Sample loot / relic vault pool
    relic_pool = [
        KnapsackItem("Iron Sword", 4, 12),
        KnapsackItem("Knight Shield", 6, 18),
        KnapsackItem("Dragon Armor", 12, 45),
        KnapsackItem("Shadow Cloak", 3, 14),
        KnapsackItem("Titan Maul", 14, 52),
        KnapsackItem("Health Potion", 1, 5),
        KnapsackItem("Mana Elixir", 1, 6),
        KnapsackItem("Teleport Rune", 2, 10),
        KnapsackItem("Crown of Kings", 5, 30),
        KnapsackItem("Ring of Power", 1, 15)
    ]

    capacity = getattr(config, 'KNAPSACK_CAPACITY', 20)
    running = True

    while running:
        config.SURFACE_MAIN.fill((18, 22, 32))
        comp = compare_knapsack(relic_pool, capacity)

        # Header
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, 35), YELLOW,
                            "=== INVENTORY KNAPSACK OPTIMIZER (0/1 DP vs GREEDY) ===", BLACK, center=True)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, 70), WHITE,
                            f"Carry Weight Capacity: {capacity}  [Left/Right Arrow or -/+ to Adjust]", None, center=True)

        col_w = CAMERA_WIDTH // 2 - 40
        top_y = 110

        # --- Left Column: Dynamic Programming ---
        left_surf = pygame.Surface((col_w, 420), pygame.SRCALPHA)
        left_surf.fill((28, 38, 55, 230))
        pygame.draw.rect(left_surf, (0, 200, 255), (0, 0, col_w, 420), 2)
        config.SURFACE_MAIN.blit(left_surf, (30, top_y))

        game_text.draw_text(config.SURFACE_MAIN, (30 + col_w // 2, top_y + 20), CYAN,
                            "DYNAMIC PROGRAMMING (0/1 OPTIMAL)", None, center=True)
        game_text.draw_text(config.SURFACE_MAIN, (50, top_y + 55), WHITE,
                            f"Total Value: {comp['dp_value']} Gold", None)
        game_text.draw_text(config.SURFACE_MAIN, (50, top_y + 85), WHITE,
                            f"Total Weight: {comp['dp_weight']} / {capacity}", None)
        game_text.draw_text(config.SURFACE_MAIN, (50, top_y + 115), LIGHT_GREY,
                            f"Time: {comp['dp_time_ms']:.4f} ms  | O(N * W)", None)

        game_text.draw_text(config.SURFACE_MAIN, (50, top_y + 155), YELLOW, "Selected Items:", None)
        y_it = top_y + 185
        for item_name in comp['dp_items'][:8]:
            game_text.draw_text(config.SURFACE_MAIN, (65, y_it), GREEN, f"- {item_name}", None)
            y_it += 26

        # --- Right Column: Greedy Heuristic ---
        right_surf = pygame.Surface((col_w, 420), pygame.SRCALPHA)
        right_surf.fill((38, 32, 28, 230))
        pygame.draw.rect(right_surf, (255, 160, 50), (0, 0, col_w, 420), 2)
        config.SURFACE_MAIN.blit(right_surf, (CAMERA_WIDTH // 2 + 10, top_y))

        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2 + 10 + col_w // 2, top_y + 20), (255, 180, 60),
                            "GREEDY (VALUE/WEIGHT RATIO)", None, center=True)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2 + 30, top_y + 55), WHITE,
                            f"Total Value: {comp['greedy_value']} Gold", None)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2 + 30, top_y + 85), WHITE,
                            f"Total Weight: {comp['greedy_weight']} / {capacity}", None)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2 + 30, top_y + 115), LIGHT_GREY,
                            f"Time: {comp['greedy_time_ms']:.4f} ms  | O(N log N)", None)

        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2 + 30, top_y + 155), YELLOW, "Selected Items:", None)
        y_it = top_y + 185
        for item_name in comp['greedy_items'][:8]:
            game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2 + 45, y_it), (255, 200, 100), f"- {item_name}", None)
            y_it += 26

        # Bottom Summary Bar
        ratio_pct = comp['greedy_competitive_ratio'] * 100.0
        optimal_str = "OPTIMAL MATCH" if comp['optimal_reached'] else "GREEDY SUB-OPTIMAL"
        opt_color = GREEN if comp['optimal_reached'] else RED

        summary_text = f"Greedy Competitive Ratio: {ratio_pct:.1f}%  |  Status: {optimal_str}"
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, CAMERA_HEIGHT - 85), opt_color,
                            summary_text, BLACK, center=True)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, CAMERA_HEIGHT - 45), LIGHT_GREY,
                            "Press [ESC] to Close  |  [+/-] to change capacity", None, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_k):
                    running = False
                elif event.key in (pygame.K_RIGHT, pygame.K_EQUALS, pygame.K_PLUS):
                    capacity = min(60, capacity + 2)
                    config.KNAPSACK_CAPACITY = capacity
                elif event.key in (pygame.K_LEFT, pygame.K_MINUS):
                    capacity = max(4, capacity - 2)
                    config.KNAPSACK_CAPACITY = capacity

        config.CLOCK.tick(FPS)
        pygame.display.flip()


def rune_puzzle_menu():
    """
    Ancient Rune Vault Constraint-Satisfaction Backtracking Puzzle:
    Allows manual dialing or running the Backtracking Solver to verify solvability.
    """
    from algorithms.backtracking_puzzle import generate_solvable_puzzle

    puzzle = generate_solvable_puzzle(num_dials=4, max_rune=5, seed=random.randint(1, 99999))
    current_dials = [1, 1, 1, 1]
    solved_message = ""
    running = True

    while running:
        config.SURFACE_MAIN.fill((20, 18, 28))

        # Title
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, 40), YELLOW,
                            "=== ANCIENT RUNIC VAULT (BACKTRACKING PUZZLE) ===", BLACK, center=True)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, 80), WHITE,
                            f"Target Sum: {puzzle.target_sum}  |  Constraint: No adjacent dials identical (c[i] != c[i+1])",
                            None, center=True)

        # Draw Dials
        start_x = CAMERA_WIDTH // 2 - 180
        for i in range(4):
            dx = start_x + i * 100
            dial_rect = pygame.Rect(dx, 160, 70, 90)
            pygame.draw.rect(config.SURFACE_MAIN, (50, 45, 75), dial_rect)
            pygame.draw.rect(config.SURFACE_MAIN, (180, 150, 255), dial_rect, 3)

            game_text.draw_text(config.SURFACE_MAIN, (dx + 35, 175), CYAN, f"#{i+1}", None, center=True)
            game_text.draw_text(config.SURFACE_MAIN, (dx + 35, 215), YELLOW, str(current_dials[i]), None, center=True)

        # Current status
        curr_sum = sum(current_dials)
        has_adj_dup = any(current_dials[i] == current_dials[i+1] for i in range(3))
        is_user_solved = (curr_sum == puzzle.target_sum) and not has_adj_dup

        status_text = f"Current Sum: {curr_sum} / {puzzle.target_sum}"
        if has_adj_dup:
            status_text += " [VIOLATION: Adjacent duplicates!]"
            stat_color = RED
        elif is_user_solved:
            status_text += " [VAULT UNLOCKED! SOLVED!]"
            stat_color = GREEN
        else:
            status_text += " [Sum mismatch]"
            stat_color = WHITE

        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, 290), stat_color, status_text, None, center=True)

        # Solver Output
        if solved_message:
            game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, 340), GREEN, solved_message, None, center=True)

        # Instructions
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, CAMERA_HEIGHT - 120), LIGHT_GREY,
                            "Press [1, 2, 3, 4] to change dials (1 to 5)", None, center=True)
        game_text.draw_text(config.SURFACE_MAIN, (CAMERA_WIDTH // 2, CAMERA_HEIGHT - 80), YELLOW,
                            "Press [S] to run Backtracking Solver  |  [ESC] to Exit", None, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_u):
                    running = False
                elif event.key == pygame.K_1:
                    current_dials[0] = (current_dials[0] % 5) + 1
                elif event.key == pygame.K_2:
                    current_dials[1] = (current_dials[1] % 5) + 1
                elif event.key == pygame.K_3:
                    current_dials[2] = (current_dials[2] % 5) + 1
                elif event.key == pygame.K_4:
                    current_dials[3] = (current_dials[3] % 5) + 1
                elif event.key == pygame.K_s:
                    # Run Backtracking Solver
                    puzzle.solve(find_all=False)
                    if puzzle.solution:
                        current_dials = list(puzzle.solution)
                        solved_message = (f"Backtracking Solver Found Solution in {puzzle.recursive_calls} calls, "
                                          f"{puzzle.backtracks} backtracks ({puzzle.execution_time_ms:.3f} ms)!")
                        game_text.add_game_message_to_print("Vault puzzle solved by Backtracking!", GREEN)

        config.CLOCK.tick(FPS)
        pygame.display.flip()
