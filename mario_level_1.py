#!/usr/bin/env python
__author__ = 'justinarmstrong'

"""
This is an attempt to recreate the first level of
Super Mario Bros for the NES.
"""

import sys


if __name__ == '__main__':
    if '--legacy' in sys.argv:
        import pygame as pg
        from data.main import main
        try:
            main()
        finally:
            pg.quit()
    else:
        from adventure.app import main
        main()
