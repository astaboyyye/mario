"""Level preview renderer and reachability checker.

    python tools/levelcheck.py [level ids...] [--no-sim] [--out DIR]

For every level this draws a strip preview and then explores the level with
the real player physics: from each place the player can stand it tries a set
of walks and jumps and records where they land. The door must be reachable
with no ability; gems are reported per ability.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame as pg                                    # noqa: E402
from lantern import actors as A, story                 # noqa: E402
from lantern.game import App                           # noqa: E402
from lantern.play import Play                          # noqa: E402
from lantern.settings import TILE, DT, RUN_SPEED       # noqa: E402

STRIP = 64          # tiles per preview row
PX = 20             # preview pixels per tile


def preview(app, play, path):
    level = play.level
    full = pg.Surface((level.w * TILE, level.h * TILE))
    full.fill((150, 200, 230) if not level.theme_name in ('stone', 'castle', 'night') else (60, 56, 80))
    old_w = None
    import lantern.world as world
    old_w, old_h = world.W, world.H
    world.W, world.H = level.w * TILE, level.h * TILE
    level.draw_tiles(full, 0, 0)
    level.draw_tiles(full, 0, 0, liquid=True)
    world.W, world.H = old_w, old_h
    for group in (play.items, play.movers, play.crumbles, play.enemies):
        for thing in group:
            if isinstance(thing, A.Poker):
                thing.rise, thing.h = 1, thing.HEIGHT
            thing.draw(full, (0, 0))
    for x, y, mark in level.tracks:
        pg.draw.circle(full, (255, 255, 255), (x * TILE + 24, y * TILE + 24), 5)
    play.player.draw(full, (0, 0))
    strips = (level.w + STRIP - 1) // STRIP
    sheet = pg.Surface((STRIP * PX, strips * (level.h * PX + 18)))
    sheet.fill((30, 30, 40))
    font = pg.font.SysFont('consolas', 12)
    for i in range(strips):
        piece = full.subsurface((i * STRIP * TILE, 0, min(STRIP, level.w - i * STRIP) * TILE, level.h * TILE))
        piece = pg.transform.smoothscale(piece, (piece.get_width() * PX // TILE, level.h * PX))
        y = i * (level.h * PX + 18)
        sheet.blit(piece, (0, y + 18))
        for c in range(0, STRIP, 8):
            sheet.blit(font.render(str(i * STRIP + c), True, (255, 255, 255)), (c * PX + 2, y + 3))
            pg.draw.line(sheet, (255, 255, 255), (c * PX, y + 12), (c * PX, y + 18))
    pg.image.save(sheet, path)


def make_static(play):
    """Freeze the moving parts into an optimistic static version for exploring."""
    level = play.level
    proxies = []
    for m in play.movers:
        if m.vertical:
            for y in range(int(m.lo), int(m.hi) + 1, TILE):
                box = A.Box(m.x, y, m.w, m.h)
                proxies.append(box)
        else:
            proxies.append(A.Box(m.lo, m.y, m.hi - m.lo + m.w, m.h))
    for e in play.enemies:
        if isinstance(e, A.Blocker):
            y = e.y
            while not level.solid(int(e.cx // TILE), int((y + e.h) // TILE)) and y < level.h * TILE:
                proxies.append(A.Box(e.x, y, e.w, 18))
                y += TILE
    for box in proxies:
        box.carries = False
    play.platforms = proxies + list(play.crumbles)
    play.solids = []
    for ty in range(level.h):
        for tx in range(level.w):
            ch = level.grid[ty][tx]
            if ch == 'L':
                level.grid[ty][tx] = ' '
            elif ch in 'rb':
                level.grid[ty][tx] = '='
    play.shake = play.dust = play.burst = play.particle = lambda *a, **k: None


def cell(p):
    return int(p.cx // TILE), int((p.y + p.h - 1) // TILE)


def explore(play, ability):
    level = play.level
    p = play.player
    p.ability = ability
    springs = [i for i in play.items if isinstance(i, A.Spring)]
    targets = [i for i in play.items if isinstance(i, (A.Gem, A.Door, A.Checkpoint))]
    found = set()

    def place(node, vx=0):
        p.x = node[0] * TILE + (TILE - p.w) / 2
        p.y = (node[1] + 1) * TILE - p.h
        p.vx, p.vy = vx, 0
        p.ground, p.ride, p.coyote = True, None, 0.1
        p.hearts, p.invuln, p.dead = 3, 0, False
        p.climb = p.spring = False
        p.drop = p.buffer = 0
        p.air_jumps, p.glide = 1, 1.7

    def touch():
        for t in targets:
            if p.touches(t):
                found.add(t)

    def run(node, direction, speed, hold, steer, jump=True, double=False, down=False):
        place(node, direction * RUN_SPEED if speed else 0)
        inp = A.Input()
        landed = []
        left_ground = False
        for frame in range(190):
            t = frame * DT
            inp.x = direction if t < steer else 0
            inp.run = bool(speed)
            inp.y = 1 if down and frame < 3 else 0
            inp.jump_pressed = jump and frame == 0
            inp.jump = jump and t < hold
            if double and left_ground and p.vy > -60 and p.air_jumps and not p.ground:
                inp.jump_pressed = inp.jump = True
            if ability == 'cloud' and p.vy > 0:
                inp.jump = True
            p.update(inp, DT, play)
            for s in springs:
                s.update(DT, play)
            if p.hearts < 3 or p.dead:
                return landed
            touch()
            if not p.ground:
                left_ground = True
            elif left_ground or not jump:
                landed.append(cell(p))
                if left_ground:
                    break
        return landed

    place(cell(p))
    for _ in range(120):
        p.update(A.Input(), DT, play)
    start = cell(p)
    seen, queue = {start}, [start]
    while queue:
        node = queue.pop()
        results = []
        for direction in (-1, 1):
            results += run(node, direction, 0, 0, 1.3, jump=False)
            results += run(node, direction, 1, 0, 1.3, jump=False)
            for hold in (0.04, 0.16, 0.7):
                results += run(node, direction, 0, hold, 9)
                results += run(node, direction, 1, hold, 9)
            results += run(node, direction, 0, 0.7, 0.22)
            results += run(node, direction, 1, 0.7, 0.3)
            if ability == 'heels':
                results += run(node, direction, 1, 0.7, 9, double=True)
                results += run(node, direction, 0, 0.7, 0.3, double=True)
        results += run(node, 0, 0, 0.7, 0)
        if ability == 'heels':
            results += run(node, 0, 0, 0.7, 0, double=True)
        if level.oneway(node[0], node[1] + 1) and not level.solid(node[0], node[1] + 1):
            results += run(node, 0, 0, 0.05, 0, down=True)
        # ladders: standing on or beside one links its two ends
        for tx in (node[0],):
            if level.at(tx, node[1]) == 'H' or level.at(tx, node[1] + 1) == 'H':
                ty = node[1] if level.at(tx, node[1]) == 'H' else node[1] + 1
                top = bottom = ty
                while level.at(tx, top - 1) == 'H':
                    top -= 1
                while level.at(tx, bottom + 1) == 'H':
                    bottom += 1
                results += [(tx, top - 1), (tx, bottom)]
        for landing in results:
            if landing not in seen and 0 <= landing[1] < level.h:
                seen.add(landing)
                queue.append(landing)
    return seen, found


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = 'previews/levels'
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
        args.remove(out)
    os.makedirs(out, exist_ok=True)
    app = App(headless=True)
    ids = args or [r[0] for r in story.ROUTE]
    failed = False
    for level_id in ids:
        index = story.index_of(level_id)
        play = Play(app, index)
        level = play.level
        preview(app, play, os.path.join(out, level_id + '.png'))
        line = '%s  %-20s %3dx%-2d coins %3d' % (level_id, story.ROUTE[index][2], level.w, level.h, play.total_coins)
        gems = sum(isinstance(i, A.Gem) for i in play.items)
        doors = sum(isinstance(i, A.Door) for i in play.items)
        if gems != 3 and level_id != 'w5_1':
            line += '  !! %d gems' % gems
            failed = True
        bottom = ''.join(level.grid[-1])
        if re.search(r'[#~] [#~]', bottom):
            line += '  !! one-tile hole in floor at x=%d' % (re.search(r'[#~] [#~]', bottom).start() + 1)
            failed = True
        if '--no-sim' in sys.argv:
            print(line)
            continue
        began = time.time()
        report = []
        for ability in (None, 'cloud', 'heels'):
            play = Play(app, index)
            make_static(play)
            seen, found = explore(play, ability)
            names = []
            for t in found:
                names.append('gem%d' % (t.index + 1) if isinstance(t, A.Gem) else type(t).__name__.lower())
            report.append('%s: %s' % (ability or 'plain', ' '.join(sorted(names))))
            need = level.header.get('needs')
            if need == 'star':
                need = None
            if ability == need and doors and 'door' not in names and not play.boss:
                failed = True
                report.append('!! DOOR NOT REACHABLE, furthest x=%d' % max(c[0] for c in seen))
        print(line + '  [%.0fs]\n    ' % (time.time() - began) + '\n    '.join(report))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
