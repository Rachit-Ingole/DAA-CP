from exceptions import *
from constant import *


class IconButton:
    """
    IconButton class

    Args:
        x (int): x position of button's topleft
        y (int): y position of button's topleft

    Attributes:
        image (arg, image): image of button
        rect (arg, rect): rect of image
        left_click_fn (arg, function): function to call when left button clicked
        right_click_fn (arg, function): function to call when right button clicked
        mouse_over_fn (arg, function): Function to call when button is hovered over
    """
    def __init__(self, x, y, image, left_click_fn=None, right_click_fn=None, mouse_over_fn=None):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = x, y
        self.left_click_fn = left_click_fn
        self.right_click_fn = right_click_fn
        self.mouse_over_fn = mouse_over_fn

    def check_if_button_hovered(self, x, y):
        """
        Return if button is hovered over

        Args:
            x (int): x coord of mouse
            y (int): y coord of mouse

        Returns:
            mouse_over (int): True if button is hovered over else false
        """
        mouse_over = (self.rect.left <= x <= self.rect.right and
                      self.rect.top <= y <= self.rect.bottom)
        return mouse_over

    def check_if_button_clicked(self, x, y):
        """
        Return if button pressed

        Args:
            x (int): x coord of mouse
            y (int): y coord of mouse

        Returns:
            True if button is clicked else false
        """
        if self.rect.collidepoint(x, y):
            return True
        return False


class ButtonManager:
    """
    Manager for the buttons

    Attributes:
        x (arg, int): x coord of button manager
        y (arg, int): y coord of button
        width (arg, int): width of button manager in icons
        height (arg, int): height of button manager in icons
        image (surface): surface that holds the buttons.
            This surface is blitted to game surface
        button_dict (list): list of buttons
        colorkey (arg, Colour): Colour to make transparent
    """
    def __init__(self, x, y, width, height, colorkey=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = pygame.Surface((SPRITE_SIZE * self.width, SPRITE_SIZE * self.height))
        if colorkey:
            self.image.set_colorkey(colorkey)
        self.button_dict = {}

    def add_button(self, icon_button, button_id):
        """
        Adds created IconButton

        Raises IconButtonException when button_id
        is already in button_dict

        Args:
            icon_button (IconButton): IconButton to add
            button_id (String): String of button key
        """
        if button_id not in self.button_dict:
            self.button_dict[button_id] = icon_button
        else:
            raise IconButtonException("IconButton exist")

    def remove_button(self, button_id):
        """
        Removes button from button manager

        Raises IconButtonException if button doesn't exist in button_dict

        Args:
            button_id (String): Key of button to remove
        """
        if button_id in self.button_dict:
            self.button_dict.pop(button_id)
        else:
            raise IconButtonException("IconButton doesn't exist")

    def get_button(self, button_id):
        """
        Args:
            button_id (String): Key of button_id

        Returns:
            Returns button with key of button_id
        """
        return self.button_dict[button_id]

    def draw_buttons(self, surface):
        """
        Draws buttons

        First draws buttons onto image and then draws
        image onto config.SURFACE_MAIN at self.x, self.y

        Args:
            surface (Surface): Surface to draw buttons on
        """
        for key in self.button_dict:
            button = self.button_dict[key]
            self.image.blit(button.image, button.rect)
        surface.blit(self.image,
                     (self.x, self.y))

    def check_if_button_hovered(self, mouse_x, mouse_y):
        """
        Checks if any of the bottoms are hovered over and returns
        button hovered over if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button hovered over
        """
        final_x = mouse_x - self.x
        final_y = mouse_y - self.y
        for button in self.button_dict.values():
            if button.check_if_button_hovered(final_x, final_y):
                return button
        return None

    def check_if_specific_button_hovered(self, button_id, mouse_x, mouse_y):
        """
        Checks if button with button_id is hovered over and returns
        button hovered over if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            button_id (string): button_id of button to check
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button hovered over
        """
        final_x = mouse_x - self.x
        final_y = mouse_y - self.y
        button = self.button_dict[button_id]
        if button.check_if_button_hovered(final_x, final_y):
            return button
        return None

    def check_if_button_pressed(self, mouse_x, mouse_y):
        """
        Checks if any of the bottoms are clicked and returns
        button pressed if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button pressed
        """
        final_x = mouse_x - self.x
        final_y = mouse_y - self.y
        for button in self.button_dict.values():
            if button.check_if_button_clicked(final_x, final_y):
                return button
        return None

    def check_if_specific_button_pressed(self, button_id, mouse_x, mouse_y):
        """
        Checks if button with button_id is clicked and returns
        button pressed if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            button_id (string): button_id of button to check
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button pressed
        """
        final_x = mouse_x - self.x
        final_y = mouse_y - self.y
        button = self.button_dict[button_id]
        if button.check_if_button_clicked(final_x, final_y):
            return button
        return None


class GridButtonManager(ButtonManager):
    """
    Manager for the buttons ordered in a grid format

    Attributes:
        num_button (arg, int): max number of buttons
        x (int): x position of button manager
        y (int): y position of button
        width (int): width of button manager in icons
        height (int): height of button manager in icons
        image (surface): surface that holds the buttons.
            This surface is blitted to game surface
        button_dict (list): list of buttons
        button_count (int): number of buttons currently in button manager
        colorkey (Colour): Colour to make transparent
    """

    def __init__(self, x, y, width, height, num_button, colorkey=None):
        super().__init__(x, y, width, height, colorkey)
        self.num_button = num_button
        self.button_count = 0

    def add_button(self, icon_button, button_id):
        """
        Adds created IconButton

        Raises IconButtonException when button_id
        is already in button_dict

        Args:
            icon_button (IconButton): IconButton to add
            button_id (String): String of button key
        """
        if not self.button_count >= self.num_button and button_id not in self.button_dict:
            self.button_dict[button_id] = icon_button
            self.button_count += 1
        else:
            raise IconButtonException("IconButton exist")

    def create_button(self, img, button_id, left_click_fn=None, right_click_fn=None, mouse_over_fn=None):
        """
        Creates IconButton and adds it to button manager

        Makes button and adds that button to button_list
        and increment button counter by 1

        Raises IconButtonException when button_id
        is already in button_dict

        Args:
            mouse_over_fn (fn pointer): fn IconButton should call when hovered over
            right_click_fn (fn pointer): fn IconButton should call when right clicked
            left_click_fn (fn pointer):fn IconButton should call when left clicked
            img (sprite): image of button
            button_id (string): the type of button it is. String must be
                unique
        """
        if not self.button_count >= self.num_button:
            if button_id not in self.button_dict:
                # The x and y coord of button depends on
                # nums of button currently in GridButtonManager
                x = self.button_count % self.width
                y = self.button_count // self.width
                button = IconButton(SPRITE_SIZE * x, SPRITE_SIZE * y, img, left_click_fn, right_click_fn, mouse_over_fn)
                self.button_dict[button_id] = button
                self.button_count += 1
            else:
                raise IconButtonException("IconButton exist")

    def remove_button(self, button_id):
        """
        Removes button from button manager

        Raises IconButtonException if button doesn't exist in button_dict

        Args:
            button_id (String): Key of button to remove
        """
        if button_id in self.button_dict:
            self.button_dict.pop(button_id)
            self.button_count -= 1
        else:
            raise IconButtonException("IconButton doesn't exist")

    def get_button(self, button_id):
        """
        Args:
            button_id (String): Key of button_id

        Returns:
            Returns button with key of button_id
        """
        return super().get_button(button_id)

    def draw_buttons(self, surface):
        """
        Draws buttons

        First draws buttons onto image and then draws
        image onto config.SURFACE_MAIN at self.x, self.y

        Args:
            surface (Surface): Surface to draw buttons on
        """
        super().draw_buttons(surface)

    def check_if_button_hovered(self, mouse_x, mouse_y):
        """
        Checks if any of the bottoms are hovered over and returns
        button hovered over if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button hovered over
        """
        return super().check_if_button_hovered(mouse_x, mouse_y)

    def check_if_specific_button_hovered(self, button_id, mouse_x, mouse_y):
        """
        Checks if button with button_id is hovered over and returns
        button hovered over if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            button_id (string): button_id of button to check
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button hovered over
        """
        return super().check_if_specific_button_hovered(button_id, mouse_x, mouse_y)

    def check_if_button_pressed(self, mouse_x, mouse_y):
        """
        Checks if any of the bottoms are clicked and returns
        button pressed if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button pressed
        """
        return super().check_if_button_pressed(mouse_x, mouse_y)

    def check_if_specific_button_pressed(self, button_id, mouse_x, mouse_y):
        """
        Checks if button with button_id is clicked and returns
        button pressed if any, else return None

        Since the mouse_x, mouse_y is relative to topleft corner
        of screen but the first button's topleft is (0, 0), need to
        adjust mouse_x and mouse_y so that both are in sync

        Args:
            button_id (string): button_id of button to check
            mouse_x (int): x position of mouse
            mouse_y (int): y position of mouse

        Returns:
            button (IconButton): button pressed
        """
        return super().check_if_specific_button_pressed(button_id, mouse_x, mouse_y)