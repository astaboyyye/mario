"""Level files, the tile grid, collision and background drawing."""
import math
import os
import random
import pygame as pg
from .settings import TILE, W, H, LEVELS
from .assets import img

THEMES = {
    'grass': dict(tiles='grass', sky=((98, 190, 232), (218, 242, 248)), liquid='Water', plant='Items/plant',
                  bush='Items/bush', ridges=((168, 222, 196), (124, 200, 150)), clouds=True),
    'sand': dict(tiles='sand', sky=((250, 190, 120), (254, 238, 196)), liquid='Water', plant='Items/cactus',
                 bush='Items/rock', ridges=((244, 208, 150), (226, 178, 118)), clouds=True),
    'snow': dict(tiles='snow', sky=((138, 180, 222), (236, 244, 252)), liquid='Water', plant='Items/snowhill',
                 bush='Items/rock', ridges=((214, 228, 244), (182, 204, 232)), clouds=True),
    'stone': dict(tiles='stone', sky=((30, 24, 46), (66, 52, 88)), liquid='Lava', plant='Items/plantPurple',
                  bush='Items/rock', ridges=((54, 44, 74), (42, 34, 60)), clouds=False),
    'castle': dict(tiles='castle', sky=((22, 22, 36), (52, 50, 72)), liquid='Lava', plant='Items/plantPurple',
                   bush='Items/rock', ridges=((44, 44, 62), (34, 34, 50)), clouds=False),
    'night': dict(tiles='grass', sky=((20, 26, 64), (84, 86, 140)), liquid='Water', plant='Items/plant',
                  bush='Items/bush', ridges=((52, 70, 112), (40, 58, 96)), clouds=False),
}

STATIC = '#=B?!XxyL~^Hrb'
DECOR = {',': 'plant', ';': 'bush', 'j': 'Tiles/fence', 'l': 'Tiles/tochLit', 'u': 'Tiles/window',
         'a': 'Tiles/hill_large', 'A': 'Tiles/hill_small', 'm': 'Items/mushroomRed', 'q': 'Tiles/signRight'}


def read_level(name):
    """Return (header dict, rows). Chunks are top-padded and joined left to right."""
    header, chunks, chunk = {}, [], []
    with open(os.path.join(LEVELS, name + '.txt'), encoding='utf-8') as handle:
        for line in handle.read().splitlines():
            if line.startswith('|'):
                chunk.append(line[1:].rstrip('|'))
            elif line.startswith('-'):
                if chunk:
                    chunks.append(chunk)
                chunk = []
            elif ':' in line and not chunks and not chunk:
                key, value = line.split(':', 1)
                header[key.strip()] = value.strip()
    if chunk:
        chunks.append(chunk)
    height = max(max(len(c) for c in chunks), int(header.get('rows', 15)))
    rows = [''] * height
    for c in chunks:
        width = max(len(r) for r in c)
        padded = [' ' * width] * (height - len(c)) + [r.ljust(width) for r in c]
        rows = [a + b for a, b in zip(rows, padded)]
    return header, rows


class Level:
    def __init__(self, name):
        self.name = name
        self.header, rows = read_level(name)
        self.theme_name = self.header.get('theme', 'grass')
        self.theme = THEMES[self.theme_name]
        self.dark = self.header.get('dark', '0') == '1'
        self.cave = int(self.header.get('cave', 0))
        self.dim = int(self.header.get('dim', 236))
        self.h, self.w = len(rows), len(rows[0])
        self.grid = [list(r) for r in rows]
        self.spawns, self.decor, self.tracks = [], [], set()
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                if ch in STATIC or ch == ' ':
                    continue
                if ch in DECOR:
                    self.decor.append((ch, x, y))
                elif ch in '-:':
                    self.tracks.add((x, y, ch))
                else:
                    self.spawns.append((ch, x, y))
                row[x] = '~' if ch == 'F' else ' '
        self.red_on = True
        self.ghost = set()
        self.bumps = {}
        self.time = 0
        self._cache = {}
        self._bg = None

    # --- queries -----------------------------------------------------
    def at(self, tx, ty):
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.grid[ty][tx]
        return '#' if (tx < 0 or tx >= self.w) and ty < self.h else ' '

    def solid(self, tx, ty):
        ch = self.at(tx, ty)
        if ch in '#B?!XxyL':
            return True
        if ch == 'r' or ch == 'b':
            return (ch == 'r') == self.red_on and (tx, ty) not in self.ghost
        return False

    def oneway(self, tx, ty):
        ch = self.at(tx, ty)
        return ch == '=' or (ch == 'H' and self.at(tx, ty - 1) != 'H' and not self.solid(tx, ty - 1))

    def standable(self, tx, ty):
        return self.solid(tx, ty) or self.oneway(tx, ty)

    def set(self, tx, ty, ch):
        self.grid[ty][tx] = ch
        self._cache.pop((tx, ty), None)

    def track_range(self, x, y, vertical):
        """Extent of the rail a moving platform at (x, y) travels along."""
        mark = ':' if vertical else '-'
        lo = hi = y if vertical else x
        step = (lambda v: (x, v, mark)) if vertical else (lambda v: (v, y, mark))
        while step(lo - 1) in self.tracks:
            lo -= 1
        while step(hi + 1) in self.tracks:
            hi += 1
        return lo, hi

    # --- movement ----------------------------------------------------
    def move(self, a, dx, dy, platforms=(), solids=()):
        """Move box `a` and resolve against tiles, one-way ledges and actors.

        Returns (flags, ground, bump): flags is a set of 'l' 'r' 'u' 'd',
        ground is True for tiles or the actor stood on, bump is the tile hit
        from below.
        """
        flags, ground, bump = set(), None, None
        a.x += dx
        top, bottom = int(a.y // TILE), int((a.y + a.h - 0.01) // TILE)
        if dx > 0:
            tx = int((a.x + a.w - 0.01) // TILE)
            if any(self.solid(tx, ty) for ty in range(top, bottom + 1)):
                a.x = tx * TILE - a.w
                flags.add('r')
        elif dx < 0:
            tx = int(a.x // TILE)
            if any(self.solid(tx, ty) for ty in range(top, bottom + 1)):
                a.x = (tx + 1) * TILE
                flags.add('l')
        for s in solids:
            if s is not a and a.x < s.x + s.w and a.x + a.w > s.x and a.y < s.y + s.h and a.y + a.h > s.y + 6:
                if a.x + a.w / 2 < s.x + s.w / 2:
                    a.x = s.x - a.w
                    flags.add('r')
                else:
                    a.x = s.x + s.w
                    flags.add('l')
        a.y += dy
        left, right = int(a.x // TILE), int((a.x + a.w - 0.01) // TILE)
        if dy >= 0:
            ty = int((a.y + a.h - 0.01) // TILE)
            before = a.y + a.h - dy
            dropping = getattr(a, 'drop', 0) > 0
            for tx in range(left, right + 1):
                if self.solid(tx, ty) or (self.oneway(tx, ty) and before <= ty * TILE + 0.5 and not dropping):
                    a.y = ty * TILE - a.h
                    flags.add('d')
                    ground = True
                    break
            for p in list(platforms) + list(solids):
                if p is a or a.x + a.w <= p.x or a.x >= p.x + p.w:
                    continue
                if p in platforms and dropping:
                    continue
                if before <= p.y + 8 + max(0, -p.dy) and a.y + a.h >= p.y and a.y < p.y:
                    a.y = p.y - a.h
                    flags.add('d')
                    ground = p
        else:
            ty = int(a.y // TILE)
            hit = [tx for tx in range(left, right + 1) if self.solid(tx, ty)]
            if hit:
                a.y = (ty + 1) * TILE
                flags.add('u')
                middle = int((a.x + a.w / 2) // TILE)
                bump = (middle if middle in hit else hit[0], ty)
            for s in solids:
                if s is not a and a.x < s.x + s.w and a.x + a.w > s.x and s.y < a.y < s.y + s.h:
                    a.y = s.y + s.h
                    flags.add('u')
        return flags, ground, bump

    def hazard(self, a):
        """'liquid', 'spike' or None for the box `a`."""
        for ty in range(int(a.y // TILE), int((a.y + a.h - 0.01) // TILE) + 1):
            for tx in range(int(a.x // TILE), int((a.x + a.w - 0.01) // TILE) + 1):
                ch = self.at(tx, ty)
                if ch == '~' and a.y + a.h > ty * TILE + 22:
                    return 'liquid'
                if ch == '^' and a.y + a.h > ty * TILE + 26 and a.x + a.w > tx * TILE + 8 and a.x < tx * TILE + 40:
                    return 'spike'
        return None

    def ladder(self, a):
        tx, ty = int((a.x + a.w / 2) // TILE), int((a.y + a.h / 2) // TILE)
        return self.at(tx, ty) == 'H'

    # --- drawing -----------------------------------------------------
    def tile_image(self, tx, ty):
        key = (tx, ty)
        if key in self._cache:
            return self._cache[key]
        ch, t = self.grid[ty][tx], self.theme['tiles']
        name = None
        if ch == '#':
            if self.at(tx, ty - 1) == '#':
                name = t + 'Center'
            else:
                l, r = self.at(tx - 1, ty) == '#', self.at(tx + 1, ty) == '#'
                name = t + ('Mid' if l and r else 'Left' if r else 'Right' if l else '')
        elif ch == '=':
            l, r = self.at(tx - 1, ty) == '=', self.at(tx + 1, ty) == '='
            name = t + 'Half' + ('Mid' if l and r else 'Left' if r else 'Right' if l else '')
        elif ch == '~':
            liquid = 'liquid' + self.theme['liquid']
            name = liquid if self.at(tx, ty - 1) == '~' else liquid + 'Top_mid'
        elif ch == 'H':
            name = 'ladder_mid' if self.at(tx, ty - 1) == 'H' else 'ladder_top'
        else:
            name = {'B': 'box', '?': 'boxCoin', '!': 'boxItem', 'X': 'boxEmpty', 'x': 'boxCoin_disabled',
                    'y': 'boxItem_disabled', 'L': 'lock_yellow'}.get(ch)
        image = img('Tiles/' + name) if name else None
        if ch == '^':
            image = img('Items/spikes')
        self._cache[key] = image
        return image

    def draw_tiles(self, surface, cam_x, cam_y, liquid=False):
        x0, x1 = max(0, int(cam_x // TILE)), min(self.w, int((cam_x + W) // TILE) + 1)
        y0, y1 = max(0, int(cam_y // TILE)), min(self.h, int((cam_y + H) // TILE) + 1)
        for ty in range(y0, y1):
            row = self.grid[ty]
            for tx in range(x0, x1):
                ch = row[tx]
                px, py = tx * TILE - cam_x, ty * TILE - cam_y
                if not liquid and ch != '#' and ty >= self.h - self.cave:
                    surface.blit(img('Tiles/%sCenter' % self.theme['tiles'], tint=(150, 140, 150)), (px, py))
                if ch == ' ' or (ch == '~') != liquid:
                    continue
                if ch in 'rb':
                    on = (ch == 'r') == self.red_on
                    tint = (255, 120, 110) if ch == 'r' else (120, 170, 255)
                    surface.blit(img('Tiles/boxEmpty', tint=tint, alpha=None if on else 60), (px, py))
                    continue
                if ch == '~':
                    px += math.sin(self.time * 2 + ty) * 3
                elif (tx, ty) in self.bumps:
                    py -= math.sin(self.bumps[(tx, ty)] / 0.18 * math.pi) * 12
                image = self.tile_image(tx, ty)
                if image:
                    surface.blit(image, (px, py))
        if liquid:
            return
        for ch, tx, ty in self.decor:
            if x0 - 2 <= tx <= x1 + 1:
                name = DECOR[ch]
                image = img(self.theme[name] if name in ('plant', 'bush') else name)
                surface.blit(image, (tx * TILE - cam_x + (TILE - image.get_width()) // 2,
                                     (ty + 1) * TILE - cam_y - image.get_height()))

    def update(self, dt, player=None):
        self.time += dt
        for key in list(self.bumps):
            self.bumps[key] -= dt
            if self.bumps[key] <= 0:
                del self.bumps[key]
        if self.ghost and player:
            self.ghost = {(tx, ty) for tx, ty in self.ghost
                          if player.x < (tx + 1) * TILE and player.x + player.w > tx * TILE
                          and player.y < (ty + 1) * TILE and player.y + player.h > ty * TILE}

    def toggle(self, player):
        self.red_on = not self.red_on
        for ty in range(int(player.y // TILE), int((player.y + player.h) // TILE) + 1):
            for tx in range(int(player.x // TILE), int((player.x + player.w) // TILE) + 1):
                if self.at(tx, ty) in 'rb':
                    self.ghost.add((tx, ty))

    def draw_background(self, surface, cam_x, cam_y):
        if self._bg is None:
            self._bg = make_background(self.theme, self.theme_name)
        sky, layers, clouds = self._bg
        surface.blit(sky, (0, 0))
        lift = 0 if self.h * TILE <= H else (cam_y / max(1, self.h * TILE - H) - 1) * 60
        if clouds:
            for i, (cx, cy, kind) in enumerate(clouds):
                x = (cx - cam_x * 0.12 + self.time * (6 + i % 3 * 3)) % (W + 300) - 150
                surface.blit(img('Items/cloud%d' % kind, 1.0 + (i % 3) * 0.25), (x, cy))
        for depth, layer in layers:
            x = -(cam_x * depth) % layer.get_width()
            surface.blit(layer, (x - layer.get_width(), -lift * depth * 2))
            surface.blit(layer, (x, -lift * depth * 2))


def make_background(theme, seed):
    top, bottom = theme['sky']
    sky = pg.Surface((W, H))
    for y in range(H):
        k = y / H
        pg.draw.line(sky, [round(top[i] + (bottom[i] - top[i]) * k) for i in range(3)], (0, y), (W, y))
    rng = random.Random(seed)
    layers = []
    for index, color in enumerate(theme['ridges']):
        width = 1920
        layer = pg.Surface((width, H), pg.SRCALPHA)
        waves = [(rng.randint(1, 3 + index * 2), rng.uniform(0, 6.28), rng.uniform(18, 60)) for _ in range(4)]
        base = 430 + index * 110
        points = [(0, H)]
        for x in range(0, width + 1, 12):
            y = base + sum(math.sin(x / width * 2 * math.pi * f + p) * a for f, p, a in waves) * (0.9 - index * 0.3)
            points.append((x, y))
        points.append((width, H))
        pg.draw.polygon(layer, color, points)
        layers.append((0.18 + index * 0.2, layer.convert_alpha()))
    clouds = [(rng.randint(0, W), rng.randint(30, 300), rng.randint(1, 3)) for _ in range(7)] if theme['clouds'] else []
    return sky.convert(), layers, clouds
