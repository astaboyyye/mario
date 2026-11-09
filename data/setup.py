"""Initialize Pygame and load assets when the game starts."""

from pathlib import Path

import pygame as pg

from . import constants as c
from . import tools


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_CAPTION = c.ORIGINAL_CAPTION

SCREEN: pg.Surface | None = None
SCREEN_RECT: pg.Rect | None = None
FONTS: dict = {}
MUSIC: dict = {}
GFX: dict = {}
SFX: dict = {}


def initialize() -> None:
    """Create the window and load resources from the project directory."""
    global SCREEN, SCREEN_RECT

    if SCREEN is not None:
        return

    pg.init()
    pg.event.set_allowed([pg.KEYDOWN, pg.KEYUP, pg.QUIT,
                          pg.VIDEORESIZE, pg.WINDOWFOCUSLOST])
    pg.display.set_caption(ORIGINAL_CAPTION)
    pg.display.set_mode(c.SCREEN_SIZE, pg.RESIZABLE)
    SCREEN = pg.Surface(c.SCREEN_SIZE).convert()
    SCREEN_RECT = SCREEN.get_rect()

    resources = PROJECT_ROOT / "resources"
    FONTS.update(tools.load_all_fonts(resources / "fonts"))
    MUSIC.update(tools.load_all_music(resources / "music"))
    GFX.update(tools.load_all_gfx(resources / "graphics"))
    SFX.update(tools.load_all_sfx(resources / "sound"))


