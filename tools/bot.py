"""A crude auto-player used as a smoke test: runs right, jumps at walls, pits and enemies.

    python tools/bot.py [level ids...]

It is not clever enough to finish puzzle levels; it exists to exercise the
real game loop (deaths, respawns, checkpoints, the finish) without a human.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SDL_VIDEODRIVER'] = 'dummy'; os.environ['SDL_AUDIODRIVER'] = 'dummy'
from lantern import story, actors as A
from lantern.game import App, Controls
from lantern.play import Play
from lantern.settings import DT, TILE

app = App(headless=True)
for level_id in sys.argv[1:] or [r[0] for r in story.ROUTE]:
    app.scene = Play(app, story.index_of(level_id))
    hold = 0
    furthest = 0
    frames = 0
    while isinstance(app.scene, Play) and frames < 60 * 120:
        play = app.scene
        p, level = play.player, play.level
        inp = Controls()
        inp.x, inp.run = 1, True
        tx, ty = int((p.cx + 30) // TILE), int((p.y + p.h - 1) // TILE)
        wall = any(level.solid(tx + d, ty) for d in (0, 1))
        pit = not any(level.standable(tx, ty + d) for d in (1, 2, 3)) and not any(
            m.x - 20 < p.cx + 40 < m.x + m.w for m in play.platforms)
        foe = any(e.harmful and 0 < e.cx - p.cx < 110 and abs(e.cy - p.cy) < 70 for e in play.enemies)
        if p.ground and (wall or pit or foe):
            inp.jump_pressed = True
            hold = 26 if (wall or pit) else 12
        if hold > 0:
            hold -= 1
            inp.jump = True
        if not p.ground and p.vy > 0 and p.ability:
            inp.jump = True
            inp.jump_pressed = p.ability == 'heels' and p.air_jumps > 0 and p.vy > 200
        play.update(DT, inp)
        frames += 1
        furthest = max(furthest, p.x / TILE)
    last = app.scene.deaths if isinstance(app.scene, Play) else '-'
    print('%s  %-10s furthest %3d  frames %5d  deaths %s' % (
        level_id, 'FINISHED' if not isinstance(app.scene, Play) else 'stopped', furthest, frames, last))
