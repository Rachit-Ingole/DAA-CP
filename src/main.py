import pstats, io
import cProfile
import pygame
import config
import menu

def profile(fnc):
    """A decorator that uses cProfile to profile a function"""

    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return inner


@profile
def start():
    # Pygame screen
    pygame.init()
    pygame.display.set_caption("Treasure Quest")
    pygame.display.set_icon(config.SPRITE.entity_dict["sword"])

    # Repeat keys when held down
    pygame.key.set_repeat(350, 75)

    menu.main_menu()

start()
