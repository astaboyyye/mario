"""The in-level scene: entities, rules, camera, HUD."""
import math
import random
import pygame as pg
from . import actors as A
from . import story
from .settings import W, H, TILE, MAX_HEARTS, INK, PAPER, GOLD, JUMP_SPEED, STOMP_BOUNCE, GLIDE_TIME
from .assets import img, text, wrap, font, play as sfx, music
from .world import Level

CHAIN = (100, 200, 400, 800, 1000, 2000)
NPC_TINTS = ((255, 255, 255), (255, 214, 170), (190, 255, 200), (255, 190, 220), (220, 200, 255))
_lights = {}


def light(radius):
    if radius not in _lights:
        s = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        for r in range(radius, 0, -3):
            k = 1 - r / radius
            pg.draw.circle(s, (0, 0, 0, min(255, int(255 * k ** 0.6 * 1.25))), (radius, radius), r)
        _lights[radius] = s
    return _lights[radius]


class Play:
    def __init__(self, app, index, checkpoint=None, carried=None):
        self.app, self.index = app, index
        self.id = story.ROUTE[index][0]
        self.title = story.ROUTE[index][2]
        self.level = Level(self.id)
        level = self.level
        self.liquid_color = (255, 130, 40) if level.theme['liquid'] == 'Lava' else (120, 210, 240)
        saved = app.save['done'].get(self.id, {})
        owned = saved.get('gems', [False] * 3)
        self.enemies, self.items, self.shots, self.movers, self.crumbles = [], [], [], [], []
        self.particles, self.floaters = [], []
        self.platforms, self.solids = [], []
        self.gems = [False] * 3
        self.coins = self.score = self.deaths = 0
        self.time = 0.0
        self.total_coins = 0
        self.box_items = {}
        self.boss = None
        self.boss_lock = None
        self.banner, self.banner_time = '', 0.0
        self.freeze = self.shake_amount = 0.0
        self.done_time = None
        self.paused = False
        self.checkpoint = checkpoint
        start = (2, level.h - 3)

        kinds = level.header.get('items', 'heart').split()
        boxes = sorted((x, y) for y in range(level.h) for x in range(level.w) if level.grid[y][x] == '!')
        for i, pos in enumerate(boxes):
            self.box_items[pos] = kinds[min(i, len(kinds) - 1)]
        self.total_coins = sum(row.count('?') for row in level.grid)
        lines = [s.strip() for s in level.header.get('signs', '').split('|')]
        if self.id == 'w5_1':
            lines = story.EPILOGUE_LINES
        talkers = sorted((x, y, ch) for ch, x, y in level.spawns if ch in 'pNO')
        gem_spots = sorted((x, y) for ch, x, y in level.spawns if ch == 'G')
        for ch, x, y in sorted(level.spawns, key=lambda s: (s[1], s[2])):
            px, py = x * TILE, y * TILE
            if ch == 'P':
                start = (x, y)
            elif ch == 'o':
                self.items.append(A.Coin(x, y))
                self.total_coins += 1
            elif ch == 'G':
                i = min(2, gem_spots.index((x, y)))
                self.items.append(A.Gem(x, y, i, owned[i]))
            elif ch == 'h':
                self.items.append(A.Pickup(x, y, 'heart'))
            elif ch == 'K':
                self.items.append(A.Pickup(x, y, 'key'))
            elif ch == 'S':
                self.items.append(A.Spring(x, y))
            elif ch == 'R':
                self.items.append(A.Button(x, y))
            elif ch == 'C':
                flag = A.Checkpoint(x, y)
                flag.on = checkpoint is not None and checkpoint[0] >= x
                self.items.append(flag)
            elif ch == 'E':
                self.items.append(A.Door(x, y))
            elif ch in 'pNO':
                i = talkers.index((x, y, ch))
                message = lines[i] if i < len(lines) else ''
                sign = A.Sign(x, y, message, {'p': 'Tiles/sign', 'N': 'Player/p2_front', 'O': 'Player/p3_front'}[ch])
                sign.tint = NPC_TINTS[i % len(NPC_TINTS)] if ch == 'N' else None
                sign.glow = ch != 'p'
                self.items.append(sign)
            elif ch == 's':
                self.enemies.append(A.Slime(px, py))
            elif ch == 'n':
                self.enemies.append(A.Snail(px, py))
            elif ch == 'f':
                self.enemies.append(A.Fly(px, py))
            elif ch == 'F':
                self.enemies.append(A.Fish(px, py, level.theme['liquid'] == 'Lava'))
            elif ch == 'k':
                self.enemies.append(A.Poker(px, py))
            elif ch == 'T':
                self.enemies.append(A.Blocker(px, py))
            elif ch == 'Z':
                self.boss = A.Rook(px, py)
                self.enemies.append(self.boss)
            elif ch == 'M':
                lo, hi = level.track_range(x, y, False)
                self.movers.append(A.Mover(x, y, lo, hi, False))
            elif ch == 'V':
                lo, hi = level.track_range(x, y, True)
                self.movers.append(A.Mover(x, y, lo, hi, True))
            elif ch == 'D':
                self.crumbles.append(A.Crumble(x, y))
        self.start = start
        if checkpoint:
            start = checkpoint[:2]
            self.coins = checkpoint[2]
        self.player = A.Player(start[0] * TILE + 9, (start[1] + 1) * TILE - 56)
        if carried:
            self.gems, self.deaths, self.time = carried['gems'], carried['deaths'], carried['time']
            for item in self.items:
                if isinstance(item, A.Gem) and self.gems[item.index]:
                    item.alive = False
        else:
            self.player.ability = app.save.get('ability')
        self.cam_x = max(0, min(level.w * TILE - W, self.player.cx - W / 2))
        self.cam_y = self.cam_target_y()
        self.look = 0.0
        music(level.header.get('music', 'greenway'))
        if not checkpoint:
            self.banner, self.banner_time = self.title, 2.6

    # ------------------------------------------------------------ hooks
    def shake(self, amount):
        self.shake_amount = max(self.shake_amount, amount)

    def particle(self, x, y, vx, vy, life, color, size, gravity=0):
        self.particles.append([x, y, vx, vy, life, life, color, size, gravity])

    def burst(self, x, y, color, count, speed):
        for _ in range(count):
            a, s = random.uniform(0, 6.28), random.uniform(0.3, 1) * speed
            self.particle(x, y, math.cos(a) * s, math.sin(a) * s - speed * 0.3, random.uniform(0.3, 0.7), color,
                          random.randint(3, 6), 900)

    def dust(self, x, y):
        for _ in range(4):
            self.particle(x + random.uniform(-10, 10), y - 2, random.uniform(-60, 60), random.uniform(-70, -10),
                          0.35, (240, 236, 224), random.randint(4, 7))

    def announce(self, message, seconds=4.0):
        self.banner, self.banner_time = message, seconds

    def chain(self):
        p = self.player
        p.combo += 1
        if p.combo == 5 and p.hearts < MAX_HEARTS:
            p.hearts += 1
            sfx('heart')
            self.announce('Five in a row!  +1 heart', 2.5)
        return CHAIN[min(p.combo, len(CHAIN)) - 1]

    def score_at(self, x, y, points):
        if points:
            self.score += points
            self.floaters.append([x, y, str(points), 0.8])

    def add_coin(self, x, y):
        self.coins += 1
        self.score += 10
        sfx('coin', 0.45)
        for _ in range(4):
            self.particle(x, y, random.uniform(-90, 90), random.uniform(-160, -40), 0.4, GOLD, 4, 500)
        if self.coins % 50 == 0 and self.player.hearts < MAX_HEARTS:
            self.player.hearts += 1
            sfx('heart')
            self.announce('50 coins!  +1 heart', 2.5)

    def smash(self, tx, ty):
        self.level.set(tx, ty, ' ')
        for name, vx, vy in (('1a', -150, -420), ('1b', 150, -420), ('2a', -90, -260), ('2b', 90, -260)):
            self.particle(tx * TILE + 24, ty * TILE + 24, vx, vy, 0.9, 'Items/particleBrick' + name, 1, 1900)
        self.score += 50
        sfx('break', 0.55)

    def bump(self, tx, ty):
        level, ch = self.level, self.level.at(tx, ty)
        for e in self.enemies:
            if e.alive and e.stompable and not e.knocked and int(e.cx // TILE) == tx \
                    and int((e.y + e.h + 4) // TILE) == ty:
                e.knock(self, 1 if e.cx > self.player.cx else -1)
        if ch == 'B':
            self.smash(tx, ty)
        elif ch == '?':
            level.set(tx, ty, 'x')
            level.bumps[(tx, ty)] = 0.18
            self.items.append(A.Coin(tx, ty - 1, popped=True))
            self.add_coin(tx * TILE + 24, ty * TILE - 10)
        elif ch == '!':
            level.set(tx, ty, 'y')
            level.bumps[(tx, ty)] = 0.18
            self.items.append(A.Pickup(tx, ty, self.box_items.get((tx, ty), 'heart'), rising=True))
            sfx('sprout')
        else:
            sfx('bump', 0.4)

    def reach_checkpoint(self, flag):
        self.checkpoint = (flag.tile[0], flag.tile[1], self.coins)
        self.player.hearts = MAX_HEARTS
        sfx('checkpoint')
        self.burst(flag.cx, flag.y + 20, (120, 220, 120), 14, 240)
        self.announce('Checkpoint.  Hearts refilled', 2.2)

    def on_death(self):
        self.deaths += 1
        self.app.save['ability'] = None
        music(None)

    def respawn(self):
        carried = {'gems': self.gems, 'deaths': self.deaths, 'time': self.time}
        self.app.scene = Play(self.app, self.index, self.checkpoint, carried)

    def finish(self):
        if self.done_time is None:
            self.done_time = 0.0
            self.player.frozen = True
            self.player.vx = 0
            music(None)
            sfx('deliver')

    def boss_started(self):
        self.boss_lock = self.level.w * TILE - W
        self.announce(story.BOSS_OPEN, 4.5)
        music('boss')

    def boss_beaten(self):
        self.announce(story.BOSS_END, 6)
        self.level.dark = False
        music(None)
        sfx('deliver')
        self.done_time = -3.2
        self.player.invuln = 6

    def lights_out(self):
        self.level.dark = True
        self.level.decor = [d for d in self.level.decor if d[0] != 'l']
        self.announce('Rook smashes the lamps!', 2.5)

    # ------------------------------------------------------------ update
    def cam_target_y(self):
        span = self.level.h * TILE - H
        return max(0, min(span, self.player.cy - H * 0.55)) if span > 0 else span

    def update(self, dt, inp):
        if inp.pause and self.done_time is None:
            self.paused = not self.paused
            sfx('select')
        if self.paused:
            if inp.confirm:
                self.paused = False
            elif inp.restart:
                self.respawn_or_restart()
            elif inp.quit_level:
                self.app.to_map(self.index)
            return
        if inp.restart and not self.player.dead and self.done_time is None:
            self.respawn_or_restart()
            return
        if self.freeze > 0:
            self.freeze -= dt
            return
        level, p = self.level, self.player
        self.time += dt if self.done_time is None else 0
        level.update(dt, p)
        for m in self.movers + self.crumbles:
            m.update(dt, self)
        self.platforms = self.movers + [c for c in self.crumbles if c.state != 'gone']
        self.solids = [e for e in self.enemies if isinstance(e, A.Blocker) and e.solid_now]
        was_y = p.y
        p.update(inp, dt, self)
        if self.boss_lock is not None and self.done_time is None:
            p.x = max(p.x, self.boss_lock + 4)
        if p.dead and p.dead_time > 1.5:
            self.respawn()
            return

        centre = self.cam_x + W / 2
        for e in self.enemies:
            if abs(e.cx - centre) > W * 0.85 and not e.knocked:
                if isinstance(e, A.Shell) and e.moving:
                    e.alive = False
                continue
            e.update(dt, self)
            if not e.alive or e.knocked or e.squashed > 0 or p.dead or not e.touches(p) or isinstance(e, A.Blocker):
                continue
            if e.stompable and p.vy > 0 and was_y + p.h - e.y < 30:
                self.stomp(e, inp)
            elif e.harmful:
                p.hurt(self, e.cx)
        for group in (self.items, self.shots):
            for thing in group:
                thing.update(dt, self)
        for item in self.items:
            if isinstance(item, A.Button):
                item.red = level.red_on
        self.enemies = [e for e in self.enemies if e.alive]
        self.items = [i for i in self.items if i.alive]
        self.shots = [s for s in self.shots if s.alive]

        for q in self.particles:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += q[8] * dt
            q[4] -= dt
        self.particles = [q for q in self.particles if q[4] > 0]
        for f in self.floaters:
            f[1] -= 60 * dt
            f[3] -= dt
        self.floaters = [f for f in self.floaters if f[3] > 0]
        self.banner_time = max(0, self.banner_time - dt)
        self.shake_amount = max(0, self.shake_amount - 40 * dt)

        if abs(p.vx) > 60:
            self.look += (p.facing * 110 - self.look) * min(1, dt * 2.5)
        target = max(0, min(level.w * TILE - W, p.cx - W / 2 + self.look))
        if self.boss_lock is not None:
            target = self.boss_lock
        self.cam_x += (target - self.cam_x) * min(1, dt * 9)
        self.cam_y += (self.cam_target_y() - self.cam_y) * min(1, dt * 5)

        if self.done_time is not None:
            self.done_time += dt
            if self.done_time >= 0 and self.boss and not p.frozen:
                p.frozen = True
            if self.done_time > 1.5:
                self.app.finish_level(self)

    def respawn_or_restart(self):
        self.deaths += 1
        self.respawn()

    def stomp(self, e, inp):
        p = self.player
        e.stomp(self)
        p.y = e.y - p.h
        p.vy = -(JUMP_SPEED if inp.jump else STOMP_BOUNCE)
        p.spring = False
        p.air_jumps, p.glide = 1, GLIDE_TIME
        p.squash = -0.2
        self.freeze = 0.045
        self.burst(e.cx, e.y, (255, 255, 255), 6, 160)
        if e.points:
            self.score_at(e.cx, e.y, self.chain())
        sfx('stomp')

    # ------------------------------------------------------------ draw
    def draw(self, surface):
        level, p = self.level, self.player
        ox = random.uniform(-1, 1) * self.shake_amount
        oy = random.uniform(-1, 1) * self.shake_amount
        cam = (round(self.cam_x + ox), round(self.cam_y + oy))
        level.draw_background(surface, cam[0], cam[1])
        if self.id == 'w5_1':
            from .game import tower
            for item in self.items:
                if isinstance(item, A.Door):
                    tower(surface, item.cx - cam[0], item.y + TILE - cam[1], False, 0)
        level.draw_tiles(surface, cam[0], cam[1])
        view = pg.Rect(cam[0] - 120, cam[1] - 160, W + 240, H + 320)
        for group in (self.items, self.movers, self.crumbles, self.enemies):
            for thing in group:
                if view.collidepoint(thing.cx, thing.cy):
                    if isinstance(thing, A.Sign) and thing.tint:
                        image = img(thing.art, tint=thing.tint)
                        surface.blit(image, (thing.tile[0] * TILE + (TILE - image.get_width()) / 2 - cam[0],
                                             (thing.tile[1] + 1) * TILE - image.get_height() - cam[1]))
                    else:
                        thing.draw(surface, cam)
        p.draw(surface, cam)
        for s in self.shots:
            s.draw(surface, cam)
        level.draw_tiles(surface, cam[0], cam[1], liquid=True)
        for x, y, vx, vy, life, full, color, size, g in self.particles:
            if isinstance(color, str):
                surface.blit(img(color, 1.4), (x - cam[0], y - cam[1]))
            else:
                r = max(1, size * life / full)
                pg.draw.circle(surface, color, (int(x - cam[0]), int(y - cam[1])), int(r))
        if level.dark:
            self.draw_darkness(surface, cam)
        for x, y, string, life in self.floaters:
            text(surface, string, 20, (x - cam[0], y - cam[1]), (255, 255, 255), 'midbottom', True, INK)
        for item in self.items:
            if isinstance(item, A.Sign) and item.near > 0.05 and item.message:
                self.draw_bubble(surface, item, cam)
        self.draw_hud(surface)
        if self.paused:
            self.draw_pause(surface)

    def draw_darkness(self, surface, cam):
        dark = pg.Surface((W, H), pg.SRCALPHA)
        dark.fill((6, 5, 14, self.level.dim))
        spots = [(self.player.cx, self.player.cy, 210)]
        for ch, tx, ty in self.level.decor:
            if ch == 'l':
                spots.append((tx * TILE + 24, ty * TILE + 14, 170 + int(math.sin(self.level.time * 9 + tx) * 6)))
        for item in self.items:
            if isinstance(item, A.Sign):
                if getattr(item, 'glow', False):
                    spots.append((item.cx, item.cy, 150))
            elif not isinstance(item, (A.Spring, A.Button)):
                spots.append((item.cx, item.cy, 110 if isinstance(item, (A.Door, A.Checkpoint)) else 54))
        for e in self.enemies:
            if isinstance(e, A.Fish) and e.fire and e.airborne:
                spots.append((e.cx, e.cy, 90))
            elif isinstance(e, A.Rook):
                spots.append((e.cx, e.cy, 150))
        for s in self.shots:
            spots.append((s.cx, s.cy, 80))
        for x, y, r in spots:
            x, y = x - cam[0], y - cam[1]
            if -r < x < W + r and -r < y < H + r:
                dark.blit(light(r), (x - r, y - r), special_flags=pg.BLEND_RGBA_SUB)
        surface.blit(dark, (0, 0))

    def draw_bubble(self, surface, sign, cam):
        lines = wrap(sign.message, 20, 330)
        w = max(font(20).size(l)[0] for l in lines) + 32
        h = len(lines) * 26 + 22
        x = max(12, min(W - w - 12, sign.cx - cam[0] - w / 2))
        y = sign.y - cam[1] - h - 18 + (1 - sign.near) * 12
        box = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.rect(box, PAPER + (int(245 * sign.near),), (0, 0, w, h), border_radius=14)
        pg.draw.rect(box, INK + (int(255 * sign.near),), (0, 0, w, h), 3, border_radius=14)
        surface.blit(box, (x, y))
        if sign.near > 0.6:
            for i, line in enumerate(lines):
                text(surface, line, 20, (x + 16, y + 10 + i * 26), INK)

    def draw_hud(self, surface):
        p = self.player
        for i in range(MAX_HEARTS):
            surface.blit(img('HUD/hud_heart' + ('Full' if i < p.hearts else 'Empty'), 0.72), (22 + i * 42, 18))
        surface.blit(img('HUD/hud_coins', 0.72), (22, 62))
        text(surface, '%d' % self.coins, 26, (64, 60), (255, 255, 255), bold=True, shadow=INK)
        for i, color in enumerate(('red', 'green', 'blue')):
            surface.blit(img('HUD/hud_gem_' + color, 0.78, alpha=None if self.gems[i] else 70), (W - 150 + i * 42, 18))
        for i in range(p.keys):
            surface.blit(img('HUD/hud_keyYellow', 0.7), (160 + i * 36, 22))
        if p.ability:
            name, scale = A.ABILITY_ICON[p.ability]
            pg.draw.circle(surface, PAPER, (W - 190, 38), 24)
            pg.draw.circle(surface, INK, (W - 190, 38), 24, 3)
            icon = img(name, scale)
            surface.blit(icon, (W - 190 - icon.get_width() / 2, 38 - icon.get_height() / 2))
        minutes, seconds = divmod(int(self.time), 60)
        text(surface, '%d:%02d' % (minutes, seconds), 22, (W - 24, 66), (255, 255, 255), 'topright', True, INK)
        if self.boss and self.boss_lock is not None and self.boss.hp > 0:
            for i in range(self.boss.HP):
                color = (255, 110, 170) if i < self.boss.hp else (70, 60, 80)
                pg.draw.rect(surface, color, (W / 2 - 110 + i * 46, 26, 38, 14), border_radius=6)
                pg.draw.rect(surface, INK, (W / 2 - 110 + i * 46, 26, 38, 14), 2, border_radius=6)
        if self.banner_time > 0:
            alpha = min(1, self.banner_time * 3)
            lines = wrap(self.banner, 24, 860, True)
            w = max(font(24, True).size(l)[0] for l in lines) + 48
            h = len(lines) * 32 + 20
            box = pg.Surface((w, h), pg.SRCALPHA)
            pg.draw.rect(box, INK + (int(225 * alpha),), (0, 0, w, h), border_radius=18)
            surface.blit(box, (W / 2 - w / 2, 112))
            if alpha > 0.5:
                for i, line in enumerate(lines):
                    text(surface, line, 24, (W / 2, 122 + i * 32), PAPER, 'midtop', True)

    def draw_pause(self, surface):
        veil = pg.Surface((W, H), pg.SRCALPHA)
        veil.fill((20, 16, 30, 170))
        surface.blit(veil, (0, 0))
        text(surface, 'Paused', 64, (W / 2, 150), PAPER, 'midtop', True)
        for i, (keys, what) in enumerate(story.CONTROLS):
            text(surface, keys, 22, (W / 2 - 20, 260 + i * 34), GOLD, 'topright', True)
            text(surface, what, 22, (W / 2 + 20, 260 + i * 34), PAPER)
        text(surface, 'Enter: resume      R: checkpoint      Q: route map', 24, (W / 2, 580), PAPER, 'midtop', True)
