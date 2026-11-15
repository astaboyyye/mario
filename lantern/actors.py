"""The player, enemies, pickups and moving scenery."""
import math
import pygame as pg
from . import settings as S
from .settings import TILE
from .assets import img, play as sfx


class Box:
    alive = True
    dx = dy = 0

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def rect(self):
        return pg.Rect(round(self.x), round(self.y), self.w, self.h)

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def touches(self, other):
        return (self.x < other.x + other.w and self.x + self.w > other.x
                and self.y < other.y + other.h and self.y + self.h > other.y)

    def blit(self, surface, cam, image, dy=0):
        """Draw `image` with its feet on the bottom centre of the box."""
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0],
                             self.y + self.h - image.get_height() - cam[1] + dy))


class Input:
    x = y = 0
    jump = jump_pressed = run = action_pressed = False


# ---------------------------------------------------------------- player
class Player(Box):
    def __init__(self, x, y):
        super().__init__(x, y, 30, 56)
        self.vx = self.vy = 0.0
        self.facing = 1
        self.ground = None
        self.ride = None
        self.coyote = self.buffer = self.invuln = self.drop = 0.0
        self.hearts = S.MAX_HEARTS
        self.ability = None
        self.air_jumps = 0
        self.glide = 0.0
        self.spring = False
        self.climb = False
        self.dead = False
        self.dead_time = 0.0
        self.safe = (x, y)
        self.keys = 0
        self.combo = 0
        self.walk = 0.0
        self.squash = 0.0
        self.frozen = False
        self.duck = False

    # -- helpers
    def jump(self, play, speed, sound='jump'):
        self.vy = -speed
        self.ground = self.ride = None
        self.coyote = self.buffer = 0
        self.climb = self.spring = False
        self.squash = -0.25
        sfx(sound, 0.5)

    def hurt(self, play, source_x=None, force=False):
        if (self.invuln > 0 and not force) or self.dead:
            return False
        self.hearts -= 1
        play.shake(8)
        if self.hearts <= 0:
            self.die(play)
            return True
        self.invuln = 1.6
        self.vy = -420
        self.vx = 240 * (1 if source_x is None or self.cx >= source_x else -1)
        self.climb = False
        sfx('hurt')
        return True

    def die(self, play):
        self.dead, self.dead_time = True, 0
        self.hearts = 0
        self.vy, self.vx = -720, 0
        sfx('die')
        play.on_death()

    def fall_out(self, play, liquid):
        if liquid:
            play.burst(self.cx, self.y + self.h, play.liquid_color, 14, 260)
        sfx('splash' if liquid else 'hurt')
        self.hearts -= 1
        play.shake(6)
        if self.hearts <= 0:
            self.die(play)
            return
        self.x, self.y = self.safe
        self.vx = self.vy = 0
        self.invuln = 2.0
        self.ride = None

    # -- frame update
    def update(self, inp, dt, play):
        level = play.level
        if self.dead:
            self.dead_time += dt
            self.vy += S.GRAVITY * dt
            self.y += self.vy * dt
            return
        if self.frozen:
            inp = Input()
        self.invuln = max(0, self.invuln - dt)
        self.drop = max(0, self.drop - dt)
        if self.ride:
            if self.ride.alive and self.ride.carries:
                self.x += self.ride.dx
                self.y = self.ride.y - self.h
            else:
                self.ride = None

        on_ladder = level.ladder(self)
        if self.climb and not on_ladder:
            self.climb = False
        if on_ladder and not self.climb and (inp.y < 0 or (inp.y > 0 and not self.ground)):
            self.climb, self.vx, self.vy = True, 0, 0
        feet = (int(self.cx // TILE), int((self.y + self.h + 2) // TILE))
        if self.ground is True and inp.y > 0 and level.at(*feet) == 'H' and not self.climb:
            self.climb, self.drop, self.ground = True, 0.25, None
            self.x = feet[0] * TILE + (TILE - self.w) / 2
            self.y += 6

        if self.climb:
            self.vx = inp.x * 120
            self.vy = inp.y * S.CLIMB_SPEED
            self.walk += abs(self.vy) * dt / 26
            if inp.jump_pressed:
                self.jump(play, S.JUMP_SPEED * (0.55 if inp.y > 0 else 0.9))
        else:
            self.duck = bool(self.ground) and inp.y > 0 and abs(self.vx) < 40
            top = S.RUN_SPEED if inp.run else S.WALK_SPEED
            want = 0 if self.duck else inp.x
            if want:
                self.facing = 1 if want > 0 else -1
                skidding = self.vx * want < 0
                rate = (S.SKID if skidding and self.ground else S.ACCEL_GROUND if self.ground else S.ACCEL_AIR)
                if skidding and self.ground and abs(self.vx) > 200 and int(self.walk * 4) % 2 == 0:
                    play.dust(self.cx, self.y + self.h)
                if abs(self.vx) > top and not skidding:      # ease down from a run
                    self.vx -= math.copysign(min(S.FRICTION * 0.5 * dt, abs(self.vx) - top), self.vx)
                else:
                    self.vx = max(-top, min(top, self.vx + want * rate * dt))
            elif self.ground:
                self.vx -= math.copysign(min(S.FRICTION * dt, abs(self.vx)), self.vx)
            else:
                self.vx -= math.copysign(min(S.FRICTION * 0.2 * dt, abs(self.vx)), self.vx)

            self.coyote = S.COYOTE if self.ground else max(0, self.coyote - dt)
            self.buffer = S.JUMP_BUFFER if inp.jump_pressed else max(0, self.buffer - dt)
            if self.buffer > 0 and self.coyote > 0:
                if inp.y > 0 and self.ground and self.ground is not True or \
                        (inp.y > 0 and self.ground is True and self.on_oneway(level)):
                    self.drop, self.buffer, self.ground, self.ride = 0.2, 0, None, None
                    self.y += 2
                else:
                    self.jump(play, S.JUMP_SPEED + abs(self.vx) * S.JUMP_RUN_BONUS)
                    play.dust(self.cx, self.y + self.h)
            elif inp.jump_pressed and not self.ground and self.ability == 'heels' and self.air_jumps > 0:
                self.air_jumps -= 1
                self.jump(play, S.DOUBLE_JUMP, 'jump2')
                play.burst(self.cx, self.y + self.h, (255, 150, 60), 8, 160)
            if self.spring:
                gravity = S.SPRING_GRAVITY
                self.spring = self.vy < 0
            elif self.vy < 0:
                gravity = S.GRAVITY_HELD if inp.jump else S.GRAVITY_CUT
            else:
                gravity = S.GRAVITY
            self.vy = min(S.MAX_FALL, self.vy + gravity * dt)
            if self.ability == 'cloud' and inp.jump and self.vy > S.GLIDE_FALL and self.glide > 0 and not self.ground:
                self.vy = S.GLIDE_FALL
                self.glide -= dt
                if int(self.glide * 14) % 2 == 0:
                    play.particle(self.cx, self.y + self.h, 0, 30, 0.5, (255, 255, 255), 7)
            if inp.action_pressed and self.ability == 'star' and not any(isinstance(s, StarShot) for s in play.shots):
                play.shots.append(StarShot(self))
                sfx('throw')

        was_air = not self.ground
        fall_speed = self.vy
        flags, ground, bump = level.move(self, self.vx * dt, self.vy * dt, play.platforms, play.solids)
        if 'l' in flags or 'r' in flags:
            self.vx = 0
        if 'u' in flags:
            self.vy = 60
            if bump:
                play.bump(*bump)
            else:
                sfx('bump', 0.4)
        self.ground = ground if 'd' in flags else None
        self.ride = ground if ground not in (None, True) else None
        if self.ground:
            if was_air and fall_speed > 300:
                self.squash = min(0.3, fall_speed / 2600)
                play.dust(self.cx, self.y + self.h)
            self.vy = 0
            self.combo = 0
            self.air_jumps = 1
            self.glide = S.GLIDE_TIME
            self.spring = False
            if ground is True and self.invuln == 0 and self.safe_spot(level):
                self.safe = (self.x, self.y)
        self.walk += abs(self.vx) * dt / 22 if self.ground else 0
        self.squash *= 0.82

        if self.keys:
            self.try_locks(play)
        danger = level.hazard(self)
        if self.y > level.h * TILE + 80 or danger == 'liquid':
            self.fall_out(play, danger == 'liquid')
        elif danger == 'spike':
            self.hurt(play)

    def on_oneway(self, level):
        ty = int((self.y + self.h + 2) // TILE)
        cells = range(int(self.x // TILE), int((self.x + self.w - 0.01) // TILE) + 1)
        return all(not level.solid(tx, ty) for tx in cells)

    def safe_spot(self, level):
        ty = int((self.y + self.h + 2) // TILE)
        for tx in (int(self.x // TILE), int((self.x + self.w) // TILE)):
            if not level.standable(tx, ty) or level.at(tx, ty) in 'rb':
                return False
            if any(level.at(tx + d, ty - 1) in '^~' or level.at(tx + d, ty) == '~' for d in (-1, 0, 1)):
                return False
        return True

    def try_locks(self, play):
        level = play.level
        for ty in range(int((self.y - 4) // TILE), int((self.y + self.h + 4) // TILE) + 1):
            for tx in range(int((self.x - 6) // TILE), int((self.x + self.w + 6) // TILE) + 1):
                if level.at(tx, ty) == 'L':
                    stack = [(tx, ty)]
                    while stack:
                        cx, cy = stack.pop()
                        if level.at(cx, cy) == 'L' and 0 <= cx < level.w:
                            level.set(cx, cy, ' ')
                            play.burst(cx * TILE + 24, cy * TILE + 24, S.GOLD, 8, 200)
                            stack += [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
                    self.keys -= 1
                    sfx('unlock')
                    return

    def draw(self, surface, cam):
        if self.invuln > 0 and int(self.invuln * 16) % 2 and not self.dead:
            return
        if self.dead or (self.invuln > 1.2):
            name = 'Player/p1_hurt'
        elif self.climb:
            name = 'Player/p1_front'
        elif not self.ground:
            name = 'Player/p1_jump'
        elif self.duck:
            name = 'Player/p1_duck'
        elif abs(self.vx) > 20:
            name = 'Player/p1_walk/PNG/p1_walk%02d' % (int(self.walk) % 11 + 1)
        else:
            name = 'Player/p1_stand'
        image = img(name, flip=self.facing < 0)
        if abs(self.squash) > 0.02:
            w, h = image.get_size()
            image = pg.transform.scale(image, (round(w * (1 + self.squash)), round(h * (1 - self.squash))))
        bob = math.sin(self.walk * 1.2) * 2 if self.climb else 0
        self.blit(surface, cam, image, 3 + bob)


# ---------------------------------------------------------------- shots
class StarShot(Box):
    """Thrown star: flies out, then comes home. Hits enemies, buttons, pickups."""
    def __init__(self, player):
        super().__init__(player.cx - 14, player.cy - 20, 28, 28)
        self.dir = player.facing
        self.t = 0.0

    def update(self, dt, play):
        self.t += dt
        if self.t < 0.42:
            self.x += self.dir * (900 - self.t * 1700) * dt
        else:
            px, py = play.player.cx - 14, play.player.cy - 14
            dist = math.hypot(px - self.x, py - self.y)
            speed = min(dist, (500 + (self.t - 0.42) * 1400) * dt)
            if dist < 22 or self.t > 3:
                self.alive = False
                return
            self.x += (px - self.x) / dist * speed
            self.y += (py - self.y) / dist * speed
        for e in play.enemies:
            if e.alive and e.star_kills and self.touches(e):
                e.knock(play, self.dir)
        for item in play.items:
            if item.alive and item.star_grabs and self.touches(item):
                item.collect(play)

    def draw(self, surface, cam):
        image = pg.transform.rotate(img('Items/star', 0.55), self.t * -720)
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0], self.cy - image.get_height() / 2 - cam[1]))


class Bomb(Box):
    def __init__(self, x, y, vx, vy):
        super().__init__(x, y, 30, 30)
        self.vx, self.vy, self.fuse = vx, vy, 1.5
        self.landed = False

    def update(self, dt, play):
        if not self.landed:
            self.vy += S.GRAVITY * 0.6 * dt
            flags, _, _ = play.level.move(self, self.vx * dt, self.vy * dt)
            if 'd' in flags:
                self.landed = True
                sfx('bump', 0.3)
            elif flags:
                self.vx = 0
        else:
            self.fuse -= dt
        if self.fuse <= 0 or self.y > play.level.h * TILE:
            self.alive = False
            play.burst(self.cx, self.cy, (255, 170, 60), 22, 380)
            play.burst(self.cx, self.cy, (90, 90, 100), 10, 200)
            play.shake(10)
            sfx('boom')
            p = play.player
            if math.hypot(p.cx - self.cx, p.cy - self.cy) < 86:
                p.hurt(play, self.cx)

    def draw(self, surface, cam):
        flash = self.landed and int(self.fuse * (6 if self.fuse > 0.6 else 14)) % 2
        self.blit(surface, cam, img('Items/bombFlash' if flash else 'Items/bomb', 0.62), 6)


# ---------------------------------------------------------------- enemies
class Enemy(Box):
    stompable = True
    star_kills = True
    harmful = True
    gravity = True
    points = 100

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.vx, self.vy = 0.0, 0.0
        self.dir = -1
        self.t = 0.0
        self.knocked = False
        self.squashed = 0.0

    def stomp(self, play):
        self.squashed = 0.35
        self.harmful = False

    def knock(self, play, direction=1):
        """Knocked off the screen by a shell, star or bumped block."""
        if self.knocked:
            return
        self.knocked, self.harmful = True, False
        self.vy, self.vx = -520, 160 * direction
        play.score_at(self.cx, self.y, play.chain())
        sfx('kick')

    def base_update(self, dt, play):
        """Shared death handling. Returns True when the subclass should skip its AI."""
        self.t += dt
        if self.knocked:
            self.vy += S.GRAVITY * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.alive = self.y < play.level.h * TILE + 200
            return True
        if self.squashed > 0:
            self.squashed -= dt
            self.alive = self.squashed > 0
            return True
        if self.y > play.level.h * TILE + 100:
            self.alive = False
        return False

    def walk(self, dt, play, speed, ledges=True):
        level = play.level
        self.vy = min(S.MAX_FALL, self.vy + S.GRAVITY * dt)
        flags, ground, _ = level.move(self, self.dir * speed * dt, self.vy * dt, play.platforms)
        if 'd' in flags:
            self.vy = 0
            if ledges and ground is True:
                ahead = int((self.cx + self.dir * (self.w / 2 + 4)) // TILE)
                below = int((self.y + self.h + 4) // TILE)
                if not level.standable(ahead, below) or level.at(ahead, below - 1) in '^~':
                    self.dir *= -1
        if ('l' in flags and self.dir < 0) or ('r' in flags and self.dir > 0):
            self.dir *= -1
        return flags

    def flipped(self, name, scale=S.TILE / 70):
        return pg.transform.flip(img(name, scale), False, True)


class Slime(Enemy):
    def __init__(self, x, y):
        super().__init__(x + 5, y + TILE - 24, 38, 24)

    def update(self, dt, play):
        if not self.base_update(dt, play):
            self.walk(dt, play, 62)

    def draw(self, surface, cam):
        if self.knocked:
            image = self.flipped('Enemies/slimeWalk1')
        elif self.squashed > 0:
            image = img('Enemies/slimeDead')
        else:
            image = img('Enemies/slimeWalk%d' % (1 + int(self.t * 5) % 2), flip=self.dir > 0)
        self.blit(surface, cam, image, 2)


class Snail(Enemy):
    points = 100

    def __init__(self, x, y):
        super().__init__(x + 5, y + TILE - 26, 38, 26)

    def update(self, dt, play):
        if not self.base_update(dt, play):
            self.walk(dt, play, 44)

    def stomp(self, play):
        self.alive = False
        play.enemies.append(Shell(self.x, self.y))

    def draw(self, surface, cam):
        image = self.flipped('Enemies/snailWalk1') if self.knocked else \
            img('Enemies/snailWalk%d' % (1 + int(self.t * 4) % 2), flip=self.dir > 0)
        self.blit(surface, cam, image, 2)


class Shell(Enemy):
    """A snail shell: sits still until kicked, then clears everything in its lane."""
    points = 0
    star_kills = False

    def __init__(self, x, y):
        super().__init__(x, y, 36, 26)
        self.moving = False
        self.grace = 0.3
        self.harmful = False

    def kick(self, play, direction):
        self.moving, self.dir, self.grace = True, direction, 0.3
        self.harmful = True
        sfx('kick')

    def stomp(self, play):
        if self.moving:
            self.moving, self.harmful, self.grace = False, False, 0.3
        else:
            self.kick(play, 1 if play.player.cx < self.cx else -1)

    def update(self, dt, play):
        if self.base_update(dt, play):
            return
        self.grace = max(0, self.grace - dt)
        level = play.level
        self.vy = min(S.MAX_FALL, self.vy + S.GRAVITY * dt)
        speed = 540 if self.moving else 0
        flags, _, _ = level.move(self, self.dir * speed * dt, self.vy * dt, play.platforms)
        if 'd' in flags:
            self.vy = 0
        if ('l' in flags or 'r' in flags) and self.moving:
            tx = int((self.cx + self.dir * (self.w / 2 + 6)) // TILE)
            ty = int(self.cy // TILE)
            if level.at(tx, ty) == 'B':
                while level.at(tx, ty) == 'B':      # the whole stack comes down
                    play.smash(tx, ty)
                    ty -= 1
            else:
                sfx('bump', 0.3)
            self.dir *= -1
        if self.moving:
            for e in play.enemies:
                if e is not self and e.alive and not e.knocked and e.squashed <= 0 and self.touches(e) \
                        and not isinstance(e, (Poker, Blocker)):
                    e.knock(play, self.dir)
            for item in play.items:
                if isinstance(item, Button) and self.touches(item):
                    item.press(play)
        elif self.grace == 0 and self.touches(play.player) and not play.player.dead:
            self.kick(play, 1 if play.player.cx < self.cx else -1)

    def draw(self, surface, cam):
        image = self.flipped('Enemies/snailShell') if self.knocked else img('Enemies/snailShell')
        wobble = math.sin(self.t * 40) * 2 if self.moving else 0
        self.blit(surface, cam, image, 2 + wobble)


class Fly(Enemy):
    gravity = False

    def __init__(self, x, y):
        super().__init__(x + 3, y + 10, 42, 24)
        self.home_x, self.home_y = self.x, self.y
        self.span = 3 * TILE

    def update(self, dt, play):
        if self.base_update(dt, play):
            return
        self.x = self.home_x + math.sin(self.t * 1.1) * self.span
        self.y = self.home_y + math.sin(self.t * 3.3) * 10
        self.dir = 1 if math.cos(self.t * 1.1) > 0 else -1

    def stomp(self, play):
        self.knocked, self.harmful = True, False
        self.vy, self.vx = 80, 0

    def draw(self, surface, cam):
        image = img('Enemies/flyDead', flip=self.dir > 0) if self.knocked else \
            img('Enemies/flyFly%d' % (1 + int(self.t * 12) % 2), flip=self.dir > 0)
        self.blit(surface, cam, image, 4)


class Fish(Enemy):
    """Leaps out of liquid on a timer. In lava it is a fireball and cannot be stomped."""
    gravity = False

    def __init__(self, x, y, fire):
        super().__init__(x + 6, y + 8, 36, 34)
        self.home = self.y
        self.fire = fire
        self.stompable = self.star_kills = not fire
        self.t = (x // TILE) % 5 * 0.45
        self.vy = 0
        self.airborne = False

    def update(self, dt, play):
        if self.base_update(dt, play):
            return
        if not self.airborne:
            if self.t > 2.3:
                self.airborne, self.vy = True, -1040
                play.burst(self.cx, self.home, play.liquid_color, 6, 160)
        else:
            self.vy += 1800 * dt
            self.y += self.vy * dt
            if self.y >= self.home and self.vy > 0:
                self.y, self.airborne, self.t = self.home, False, 0
        self.harmful = self.airborne

    def stomp(self, play):
        self.knocked, self.harmful = True, False
        self.vy, self.vx = 60, 0

    def draw(self, surface, cam):
        if not self.airborne and not self.knocked:
            return
        if self.fire:
            image = img('Items/fireball', 0.9)
            if self.vy > 0:
                image = pg.transform.flip(image, False, True)
        else:
            base = img('Enemies/fishDead' if self.knocked else 'Enemies/fishSwim%d' % (1 + int(self.t * 8) % 2))
            image = pg.transform.rotate(base, -90 if self.vy < 0 else 90)
        self.blit(surface, cam, image, 6)


class Poker(Enemy):
    """Rises out of the ground on a timer. Cannot be stomped: wait it out."""
    stompable = False
    star_kills = False
    gravity = False
    HEIGHT = 100

    def __init__(self, x, y):
        super().__init__(x + 8, (y + 1) * 1.0, 32, 0)
        self.base = y + TILE
        self.t = (x // TILE) % 4 * 0.8
        self.rise = 0.0

    def update(self, dt, play):
        self.t += dt
        phase = self.t % 3.6
        if phase < 1.5:
            target = 0
        elif phase < 2.1:
            target = 0.14          # the tip shows first as a warning
        else:
            target = 1
        self.rise += (target - self.rise) * min(1, dt * (16 if target == 1 else 9))
        self.h = self.rise * self.HEIGHT
        self.y = self.base - self.h
        self.harmful = self.rise > 0.3

    def knock(self, play, direction=1):
        pass

    def draw(self, surface, cam):
        if self.rise < 0.02:
            return
        image = img('Enemies/pokerMad' if self.rise > 0.5 else 'Enemies/pokerSad', self.HEIGHT / 146)
        shown = int(self.h)
        shake = math.sin(self.t * 50) * 2 if 0.05 < self.rise < 0.3 else 0
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0] + shake, self.base - shown - cam[1]),
                     (0, 0, image.get_width(), shown))


class Blocker(Enemy):
    """A stone face that slams down when you walk under it, then climbs back.

    While it rests or rises it is solid, so it can be ridden upward.
    """
    stompable = False
    star_kills = False
    gravity = False
    carries = True

    def __init__(self, x, y):
        super().__init__(x - 12, y, 72, 72)
        self.home = y
        self.state = 'idle'
        self.t = 0.0
        self.harmful = False

    def knock(self, play, direction=1):
        pass

    def update(self, dt, play):
        self.t += dt
        p, level = play.player, play.level
        old = self.y
        if self.state == 'idle':
            if abs(p.cx - self.cx) < 76 and self.y + self.h <= p.y + 4 < self.y + 10 * TILE and not p.dead:
                self.state, self.t = 'shake', 0
        elif self.state == 'shake':
            if self.t > 0.32:
                self.state, self.vy = 'fall', 200
        elif self.state == 'fall':
            self.vy = min(1300, self.vy + 5200 * dt)
            self.y += self.vy * dt
            ty = int((self.y + self.h) // TILE)
            hit = any(level.solid(tx, ty) for tx in range(int(self.x // TILE), int((self.x + self.w - 1) // TILE) + 1))
            if hit or self.y > level.h * TILE:
                self.y = ty * TILE - self.h
                self.state, self.t = 'rest', 0
                play.shake(9)
                play.dust(self.x, self.y + self.h)
                play.dust(self.x + self.w, self.y + self.h)
                sfx('slam')
            else:
                if self.touches(p) and p.y > self.y + 20:
                    p.hurt(play, self.cx)
                for e in play.enemies:
                    if e is not self and e.alive and e.stompable and self.touches(e):
                        e.knock(play)
        elif self.state == 'rest':
            if self.t > 0.9:
                self.state = 'rise'
        elif self.state == 'rise':
            self.y = max(self.home, self.y - 96 * dt)
            if self.y == self.home:
                self.state = 'idle'
        self.dy = self.y - old

    @property
    def solid_now(self):
        return self.state != 'fall'

    def draw(self, surface, cam):
        name = {'idle': 'blockerSad', 'rise': 'blockerBody', 'rest': 'blockerBody'}.get(self.state, 'blockerMad')
        shake = math.sin(self.t * 70) * 3 if self.state == 'shake' else 0
        surface.blit(img('Enemies/' + name, 72 / 51), (self.x - cam[0] + shake, self.y - cam[1]))


# ---------------------------------------------------------------- platforms
class Mover(Box):
    carries = True

    def __init__(self, x, y, lo, hi, vertical):
        super().__init__(x * TILE, y * TILE, 3 * TILE, 18)
        self.vertical = vertical
        self.lo, self.hi = lo * TILE, (hi * TILE if vertical else (hi - 2) * TILE)
        self.dir = 1
        self.wait = 0.0

    def update(self, dt, play):
        self.dx = self.dy = 0
        if self.wait > 0:
            self.wait -= dt
            return
        step = self.dir * 110 * dt
        pos = (self.y if self.vertical else self.x) + step
        if pos >= self.hi or pos <= self.lo:
            pos = max(self.lo, min(self.hi, pos))
            self.dir *= -1
            self.wait = 0.45
        if self.vertical:
            self.dy, self.y = pos - self.y, pos
        else:
            self.dx, self.x = pos - self.x, pos

    def draw(self, surface, cam):
        for i in range(3):
            surface.blit(img('Tiles/bridge'), (self.x + i * TILE - cam[0], self.y - 21 - cam[1]))


class Crumble(Box):
    """A log bridge section that drops shortly after being stepped on."""
    carries = True

    def __init__(self, x, y):
        super().__init__(x * TILE, y * TILE + 14, TILE, 16)
        self.home = self.y
        self.t = 0.0
        self.state = 'idle'
        self.vy = 0.0

    def update(self, dt, play):
        self.dy = 0
        if self.state == 'idle':
            if play.player.ride is self:
                self.state, self.t = 'shake', 0
        elif self.state == 'shake':
            self.t += dt
            if self.t > 0.45:
                self.state = 'fall'
                sfx('crumble', 0.4)
        elif self.state == 'fall':
            self.vy += S.GRAVITY * dt
            self.dy = self.vy * dt
            self.y += self.dy
            if self.y > self.home + 700:
                self.state, self.t, self.vy = 'gone', 0, 0
        elif self.state == 'gone':
            self.t += dt
            if self.t > 2.5 and not self.touches(play.player):
                self.state, self.y = 'idle', self.home

    @property
    def active(self):
        return self.state in ('idle', 'shake')

    def draw(self, surface, cam):
        if self.state == 'gone':
            return
        shake = math.sin(self.t * 60) * 2 if self.state == 'shake' else 0
        surface.blit(img('Tiles/bridgeLogs'), (self.x - cam[0] + shake, self.y - 14 - 20 - cam[1]))


# ---------------------------------------------------------------- pickups
class Item(Box):
    star_grabs = False

    def update(self, dt, play):
        pass

    def collect(self, play):
        self.alive = False


class Coin(Item):
    star_grabs = True

    def __init__(self, x, y, popped=False):
        super().__init__(x * TILE + 10, y * TILE + 10, 28, 28)
        self.popped = popped
        self.t = 0.0 if popped else (x * 0.35) % 6.28
        self.vy = -560 if popped else 0

    def update(self, dt, play):
        self.t += dt
        if self.popped:
            self.vy += 1900 * dt
            self.y += self.vy * dt
            if self.t > 0.45:
                self.alive = False
        elif self.touches(play.player):
            self.collect(play)

    def collect(self, play):
        self.alive = False
        play.add_coin(self.cx, self.cy)

    def draw(self, surface, cam):
        image = img('Items/coinGold', 0.6)
        width = max(4, abs(math.cos(self.t * (9 if self.popped else 2.4))) * image.get_width())
        image = pg.transform.scale(image, (round(width), image.get_height()))
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0], self.cy - image.get_height() / 2 - cam[1]))


class Gem(Item):
    star_grabs = True
    COLORS = ('Red', 'Green', 'Blue')

    def __init__(self, x, y, index, owned):
        super().__init__(x * TILE + 6, y * TILE + 6, 36, 36)
        self.index, self.owned = index, owned
        self.t = 0.0

    def update(self, dt, play):
        self.t += dt
        if self.touches(play.player):
            self.collect(play)

    def collect(self, play):
        self.alive = False
        play.gems[self.index] = True
        play.burst(self.cx, self.cy, (255, 255, 255), 14, 240)
        play.score_at(self.cx, self.y, 0 if self.owned else 1000)
        sfx('gem')

    def draw(self, surface, cam):
        image = img('Items/gem' + self.COLORS[self.index], 0.95, alpha=90 if self.owned else None)
        y = self.cy + math.sin(self.t * 3) * 5
        if not self.owned and int(self.t * 2) % 3 == 0:
            pg.draw.circle(surface, (255, 255, 255), (int(self.cx - cam[0] + 14), int(y - cam[1] - 12)), 3)
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0], y - image.get_height() / 2 - cam[1]))


class Pickup(Item):
    """Heart, key or ability. Abilities and hearts rise out of item boxes."""
    ART = {'heart': ('HUD/hud_heartFull', 0.8), 'key': ('Items/keyYellow', 0.8), 'cloud': ('Items/cloud1', 0.42),
           'heels': ('Items/springboardUp', 0.75), 'star': ('Items/star', 0.9)}
    star_grabs = True

    def __init__(self, x, y, kind, rising=False):
        super().__init__(x * TILE + 6, y * TILE + 6, 36, 36)
        self.kind = kind
        self.rise = TILE if rising else 0
        self.t = 0.0

    def update(self, dt, play):
        self.t += dt
        if self.rise > 0:
            step = min(self.rise, 120 * dt)
            self.rise -= step
            self.y -= step
        elif self.touches(play.player):
            self.collect(play)

    def collect(self, play):
        if self.rise > 0:
            return
        self.alive = False
        p = play.player
        if self.kind == 'heart':
            if p.hearts < S.MAX_HEARTS:
                p.hearts += 1
            else:
                play.score_at(self.cx, self.y, 500)
            sfx('heart')
        elif self.kind == 'key':
            p.keys += 1
            sfx('key')
        else:
            p.ability = self.kind
            play.announce(ABILITY_HELP[self.kind])
            sfx('power')
        play.burst(self.cx, self.cy, (255, 240, 170), 12, 220)

    def draw(self, surface, cam):
        name, scale = self.ART[self.kind]
        image = img(name, scale)
        y = self.cy + (math.sin(self.t * 3) * 4 if self.rise <= 0 else 0)
        if self.kind in ('cloud', 'heels', 'star'):
            glow = 20 + math.sin(self.t * 5) * 3
            pg.draw.circle(surface, (255, 250, 200), (int(self.cx - cam[0]), int(y - cam[1])), int(glow), 3)
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0], y - image.get_height() / 2 - cam[1]))


ABILITY_HELP = {
    'cloud': 'CLOUD COAT   Hold JUMP in the air to float',
    'heels': 'SPRING HEELS   Press JUMP again in mid-air',
    'star': 'POST STAR   Press X to throw. It comes back',
}
ABILITY_ICON = {'cloud': ('Items/cloud1', 0.34), 'heels': ('Items/springboardUp', 0.6), 'star': ('Items/star', 0.7)}


class Spring(Item):
    def __init__(self, x, y):
        super().__init__(x * TILE + 4, y * TILE + 22, 40, 26)
        self.t = 1.0

    def update(self, dt, play):
        self.t += dt
        p = play.player
        if self.touches(p) and p.vy > 0 and not p.dead and p.y + p.h < self.y + 22:
            p.y = self.y - p.h + 6
            p.vy, p.spring, p.ground, p.ride = -S.SPRING_SPEED, True, None, None
            p.air_jumps, p.glide = 1, S.GLIDE_TIME
            p.squash = -0.3
            self.t = 0
            sfx('spring')

    def draw(self, surface, cam):
        image = img('Items/springboardDown' if self.t < 0.12 else 'Items/springboardUp')
        surface.blit(image, (self.x - 4 - cam[0], self.y - 22 - cam[1]))


class Button(Item):
    star_grabs = True

    def __init__(self, x, y):
        super().__init__(x * TILE + 6, y * TILE + 26, 36, 22)
        self.cool = 0.0
        self.inside = False

    def update(self, dt, play):
        self.cool = max(0, self.cool - dt)
        inside = self.touches(play.player)
        if inside and not self.inside:
            self.press(play)
        self.inside = inside

    def press(self, play):
        if self.cool == 0:
            self.cool = 0.7
            play.level.toggle(play.player)
            sfx('button')

    collect = press

    def draw(self, surface, cam):
        color = 'Red' if play_red(self) else 'Blue'
        image = img('Items/button%s%s' % (color, '_pressed' if self.cool > 0.35 else ''))
        surface.blit(image, (self.x - 6 - cam[0], self.y - 26 - cam[1]))


def play_red(button):
    return getattr(button, 'red', True)


class Checkpoint(Item):
    def __init__(self, x, y):
        super().__init__(x * TILE + 8, y * TILE - TILE, 32, TILE * 2)
        self.tile = (x, y)
        self.on = False
        self.t = 0.0

    def update(self, dt, play):
        self.t += dt
        if not self.on and self.touches(play.player) and not play.player.dead:
            self.on = True
            play.reach_checkpoint(self)

    def draw(self, surface, cam):
        name = 'Items/flagGreenHanging' if not self.on else 'Items/flagGreen' + ('2' if int(self.t * 6) % 2 else '')
        surface.blit(img(name), (self.tile[0] * TILE - cam[0], self.tile[1] * TILE - cam[1]))


class Door(Item):
    def __init__(self, x, y):
        super().__init__(x * TILE + 12, y * TILE, 24, TILE)
        self.tile = (x, y)
        self.open = False

    def update(self, dt, play):
        p = play.player
        if not self.open and self.touches(p) and p.ground and not p.dead:
            self.open = True
            play.finish()

    def draw(self, surface, cam):
        x, y = self.tile[0] * TILE - cam[0], self.tile[1] * TILE - cam[1]
        state = 'open' if self.open else 'closed'
        surface.blit(img('Tiles/door_%sMid' % state), (x, y))
        surface.blit(img('Tiles/door_%sTop' % state), (x, y - TILE))


class Sign(Item):
    """A signpost or a character with something to say when you stand close."""
    def __init__(self, x, y, message, art='Tiles/sign'):
        super().__init__(x * TILE - 30, y * TILE - TILE, TILE + 60, TILE * 2)
        self.tile = (x, y)
        self.message = message
        self.art = art
        self.near = 0.0

    def update(self, dt, play):
        self.near += ((1 if self.touches(play.player) else 0) - self.near) * min(1, dt * 10)

    def draw(self, surface, cam):
        image = img(self.art)
        surface.blit(image, (self.tile[0] * TILE + (TILE - image.get_width()) / 2 - cam[0],
                             (self.tile[1] + 1) * TILE - image.get_height() - cam[1]))


# ---------------------------------------------------------------- boss
class Rook(Enemy):
    """The lamp thief. Stomp five times; each hit changes how Rook fights."""
    star_kills = False
    points = 0
    HP = 5

    def __init__(self, x, y):
        super().__init__(x, y - 30, 44, 76)
        self.hp = self.HP
        self.state, self.t = 'wait', 0.0
        self.count = 0
        self.flash = 0.0
        self.left, self.right = x - 19 * TILE, x + 2 * TILE
        self.ground = False
        self.walkt = 0.0

    def stomp(self, play):
        if self.flash > 0:
            return
        self.hp -= 1
        self.flash = 1.4
        play.shake(10)
        play.burst(self.cx, self.y, (255, 120, 180), 18, 300)
        sfx('bosshit')
        if self.hp <= 0:
            self.harmful = False
            self.state, self.t = 'beaten', 0
            self.vx = 0
            play.shots[:] = [s for s in play.shots if not isinstance(s, Bomb)]
            play.boss_beaten()
        else:
            self.state, self.t, self.count = 'flee', 0, 0
            self.vy = -700
            self.vx = 300 * (1 if self.cx > (self.left + self.right) / 2 else -1) * -1
            if self.hp == 2:
                play.lights_out()

    def knock(self, play, direction=1):
        pass

    def update(self, dt, play):
        self.t += dt
        self.flash = max(0, self.flash - dt)
        p, level = play.player, play.level
        rage = (self.HP - self.hp) * 0.12
        toward = 1 if p.cx > self.cx else -1
        if self.state == 'wait':
            self.vx = 0
            if p.x > self.left + TILE:
                self.state, self.t = 'taunt', 0
                play.boss_started()
        elif self.state == 'taunt':
            if self.t > 1.2:
                self.state, self.t, self.count = 'hop', 0, 0
        elif self.state == 'hop':
            if self.ground and self.t > 0.55 - rage:
                if self.count >= 3:
                    self.state, self.t, self.count = ('throw' if self.hp < self.HP else 'tired'), 0, 0
                else:
                    self.count += 1
                    self.vy = -900
                    self.vx = max(-420, min(420, (p.cx - self.cx) * 1.25))
                    self.t = 0
                    sfx('jump2', 0.4)
        elif self.state == 'throw':
            self.vx = 0
            self.dir = toward
            if self.t > 0.5 and self.count < 2 + (self.hp <= 2):
                self.count += 1
                self.t = 0.05
                distance = p.cx - self.cx + (self.count - 2) * 90
                play.shots.append(Bomb(self.cx - 15, self.y, distance * 0.95, -760))
                sfx('throw')
            elif self.t > 1.0:
                self.state, self.t = ('dash' if self.hp <= 3 else 'tired'), 0
        elif self.state == 'dash':
            if self.t < 0.6:
                self.vx = 0                      # wind-up: crouch and shake
                self.dir = toward
            else:
                self.vx = self.dir * (560 + rage * 300)
                if int(self.t * 20) % 3 == 0:
                    play.dust(self.cx, self.y + self.h)
                if self.t > 0.7 and (self.x <= self.left or self.x + self.w >= self.right or self.vx == 0):
                    self.state, self.t = 'tired', 0
                    play.shake(6)
                    sfx('slam', 0.5)
        elif self.state == 'tired':
            self.vx = 0
            if self.t > 1.5 - rage * 2:
                self.state, self.t, self.count = 'hop', 0, 0
        elif self.state == 'flee':
            if self.ground and self.t > 0.3:
                self.vx = 0
                if self.t > 1.0:
                    self.state, self.t, self.count = 'hop', 0, 0
        if self.state == 'beaten':
            self.vx = 0
        self.vy = min(S.MAX_FALL, self.vy + S.GRAVITY * 0.85 * dt)
        flags, _, _ = level.move(self, self.vx * dt, self.vy * dt)
        self.ground = 'd' in flags
        if self.ground:
            self.vy = 0
            if self.state in ('hop', 'flee') and self.t > 0.1:
                self.vx *= 0.5
        if 'l' in flags or 'r' in flags:
            self.vx = 0
        self.x = max(self.left, min(self.right - self.w, self.x))
        if abs(self.vx) > 10:
            self.dir = 1 if self.vx > 0 else -1
            self.walkt += dt * 16
        self.stompable = self.state != 'beaten'

    def draw(self, surface, cam):
        if self.flash > 0 and int(self.flash * 18) % 2:
            return
        if self.state in ('tired', 'beaten') or self.flash > 0:
            name = 'Player/p3_hurt' if self.flash > 0 else 'Player/p3_duck'
        elif not self.ground:
            name = 'Player/p3_jump'
        elif self.state == 'dash' and self.t < 0.6:
            name = 'Player/p3_duck'
        elif abs(self.vx) > 10:
            name = 'Player/p3_walk/PNG/p2_walk%02d' % (int(self.walkt) % 11 + 1)
        else:
            name = 'Player/p3_stand'
        image = img(name, 0.86, flip=self.dir < 0)
        shake = math.sin(self.t * 60) * 3 if self.state == 'dash' and self.t < 0.6 else 0
        surface.blit(image, (self.cx - image.get_width() / 2 - cam[0] + shake,
                             self.y + self.h - image.get_height() - cam[1] + 3))
        if self.state == 'tired':
            for i in range(3):
                a = self.t * 5 + i * 2.1
                surface.blit(img('Items/star', 0.25), (self.cx + math.cos(a) * 26 - 9 - cam[0],
                                                       self.y - 16 + math.sin(a) * 6 - cam[1]))
