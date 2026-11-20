import os
import pstats, io
import cProfile
import pygame
import config
import menu

def profile(fnc):
    """
    A decorator that uses cProfile to profile a function.

    Profiling slows the whole game down noticeably, so it is only enabled
    when the DAA_PROFILE environment variable is set, eg:
        DAA_PROFILE=1 python src/main.py
    """
    if not os.environ.get("DAA_PROFILE"):
        return fnc

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
