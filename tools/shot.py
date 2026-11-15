"""Render game screens headless: python tools/shot.py OUT.png level_id frames [x_tile]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame as pg
from lantern import story, actors as A
from lantern.game import App, Title, RouteMap, Panels, Delivered
from lantern.play import Play
from lantern.settings import DT, TILE
app = App(headless=True)
out, what, frames = sys.argv[1], sys.argv[2], int(sys.argv[3])
if what == 'title': app.scene = Title(app)
elif what == 'map':
    app.save['done'] = {r[0]: {'gems': [True, False, True], 'time': 95} for r in story.ROUTE[:5]}
    app.scene = RouteMap(app, 5)
elif what == 'intro': app.scene = Panels(app, story.INTRO, lambda: None)
else:
    app.scene = Play(app, story.index_of(what))
    if len(sys.argv) > 4:
        p = app.scene.player
        p.x = int(sys.argv[4]) * TILE
        p.y = (int(sys.argv[5]) if len(sys.argv) > 5 else 2) * TILE
        if len(sys.argv) > 6: p.ability = sys.argv[6]
        app.scene.cam_x = p.x - 640
inp = A.Input(); inp.confirm = inp.pause = inp.restart = inp.quit_level = inp.up = inp.down = inp.left = inp.right = inp.back = inp.read = False
for f in range(frames):
    if what not in ('title', 'map', 'intro'):
        inp.x = 1; inp.jump = f % 50 < 20; inp.jump_pressed = f % 50 == 0
    app.scene.update(DT, inp)
if what == 'letter':
    pass
app.scene.draw(app.screen)
pg.image.save(app.screen, out)
