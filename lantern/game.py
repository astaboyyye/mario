"""Application shell: window, input, saving, title, route map and story screens."""
import json
import math
import os
import random
import sys
import pygame as pg
from . import story
from .actors import Input
from .assets import img, text, wrap, font, init_audio, play as sfx, music, toggle_mute
from .play import Play
from .settings import W, H, FPS, DT, TILE, SAVE_FILE, INK, PAPER, GOLD
from .world import THEMES, make_background

LETTERS = 12


def load_save():
    data = {'done': {}, 'ability': None, 'intro': False, 'cursor': 0}
    try:
        with open(SAVE_FILE, encoding='utf-8') as handle:
            data.update(json.load(handle))
    except (OSError, ValueError):
        pass
    return data


def envelope(surface, x, y, w=120, angle=0):
    h = int(w * 0.66)
    s = pg.Surface((w, h), pg.SRCALPHA)
    pg.draw.rect(s, PAPER, (0, 0, w, h), border_radius=6)
    pg.draw.rect(s, INK, (0, 0, w, h), 3, border_radius=6)
    pg.draw.lines(s, INK, False, [(2, 3), (w / 2, h * 0.55), (w - 3, 3)], 3)
    pg.draw.circle(s, (214, 72, 72), (w // 2, int(h * 0.55)), max(5, w // 12))
    if angle:
        s = pg.transform.rotate(s, angle)
    surface.blit(s, (x - s.get_width() / 2, y - s.get_height() / 2))


def tower(surface, x, base, lit, t):
    """The lighthouse, drawn from flat shapes to sit beside the tile art."""
    if lit:
        beam = pg.Surface((W, H), pg.SRCALPHA)
        sweep = math.sin(t * 0.7) * 0.5
        for side in (-1, 1):
            a = sweep + (0 if side > 0 else math.pi)
            far = [(x + math.cos(a + d) * 1500, base - 300 + math.sin(a + d) * 1500) for d in (-0.09, 0.09)]
            pg.draw.polygon(beam, (255, 244, 180, 70), [(x, base - 300)] + far)
        surface.blit(beam, (0, 0))
    pg.draw.polygon(surface, (238, 232, 220), [(x - 46, base), (x + 46, base), (x + 30, base - 270), (x - 30, base - 270)])
    for k in (0.18, 0.52):
        y0, y1 = base - 270 * k, base - 270 * (k + 0.16)
        w0, w1 = 46 - 16 * k, 46 - 16 * (k + 0.16)
        pg.draw.polygon(surface, (214, 72, 72), [(x - w0, y0), (x + w0, y0), (x + w1, y1), (x - w1, y1)])
    pg.draw.rect(surface, INK, (x - 40, base - 282, 80, 12), border_radius=4)
    pg.draw.rect(surface, (255, 236, 150) if lit else (70, 76, 100), (x - 24, base - 326, 48, 44))
    pg.draw.rect(surface, INK, (x - 24, base - 326, 48, 44), 4)
    pg.draw.polygon(surface, (214, 72, 72), [(x - 34, base - 326), (x + 34, base - 326), (x, base - 368)])
    pg.draw.rect(surface, (120, 84, 60), (x - 12, base - 40, 24, 40), border_radius=10)
    if lit:
        glow = pg.Surface((240, 240), pg.SRCALPHA)
        for r in range(120, 0, -6):
            pg.draw.circle(glow, (255, 240, 170, 5), (120, 120), r)
        surface.blit(glow, (x - 120, base - 424))


_vignette_bg = {}


def vignette(surface, kind, t):
    theme = {'tower_lit': 'night', 'tower_dark': 'night', 'night_lamps': 'night', 'desert': 'sand',
             'rook_face': 'snow', 'rook_letter': 'stone'}.get(kind, 'grass')
    if theme not in _vignette_bg:
        _vignette_bg[theme] = make_background(THEMES[theme], theme)
    sky, layers, _ = _vignette_bg[theme]
    surface.blit(sky, (0, 0))
    for depth, layer in layers:
        surface.blit(layer, (-(t * 14 * depth) % layer.get_width() - layer.get_width(), -60))
        surface.blit(layer, (-(t * 14 * depth) % layer.get_width(), -60))
    tiles = THEMES[theme]['tiles']
    ground = 430
    for x in range(0, W, TILE):
        surface.blit(img('Tiles/%sMid' % tiles), (x, ground))
        for y in range(ground + TILE, H, TILE):
            surface.blit(img('Tiles/%sCenter' % tiles), (x, y))
    bob = math.sin(t * 3) * 4
    if kind in ('tower_lit', 'tower_dark', 'night_lamps'):
        rng = random.Random(4)
        for _ in range(60):
            pg.draw.circle(surface, (255, 255, 240), (rng.randint(0, W), rng.randint(0, 330)), rng.choice((1, 1, 2)))
        tower(surface, 880, ground, kind != 'tower_dark', t)
        if kind == 'night_lamps':
            for i in range(11):
                x = 120 + i * 62
                tint = ((255, 255, 255), (255, 214, 170), (190, 255, 200), (255, 190, 220))[i % 4]
                figure = img('Player/p2_front' if i != 9 else 'Player/p3_front', 0.6, tint=None if i == 9 else tint)
                surface.blit(figure, (x, ground - figure.get_height() + 4 + math.sin(t * 2 + i) * 2))
                glow = pg.Surface((90, 90), pg.SRCALPHA)
                for r in range(45, 0, -5):
                    pg.draw.circle(glow, (255, 230, 150, 12), (45, 45), r)
                surface.blit(glow, (x - 8, ground - 100))
                pg.draw.circle(surface, (255, 236, 160), (x + 37, ground - 54), 6)
    elif kind == 'letters':
        for i in range(12):
            envelope(surface, 420 + i * 40, ground - 60 - (i % 3) * 34 + math.sin(t * 2 + i) * 4, 110, (i * 37) % 30 - 15)
        juno = img('Player/p1_front', 1.6)
        surface.blit(juno, (190, ground - juno.get_height() + 8 + bob))
    elif kind == 'juno':
        juno = img('Player/p1_stand', 2.0)
        surface.blit(juno, (W / 2 - 220, ground - juno.get_height() + 10 + bob))
        envelope(surface, W / 2 + 60, ground - 150 + bob, 170, -8)
    elif kind == 'rook_run':
        frame = img('Player/p3_walk/PNG/p2_walk%02d' % (int(t * 14) % 11 + 1), 1.3)
        x = 700 + math.sin(t * 0.8) * 60
        lens(surface, x - 10, ground - 70, t)
        surface.blit(frame, (x, ground - frame.get_height() + 6))
        juno = img('Player/p1_stand', 1.1)
        surface.blit(juno, (150, ground - juno.get_height() + 6))
    elif kind == 'rook_face':
        rook = img('Player/p3_front', 2.0)
        lens(surface, W / 2 + 90, ground - 110, t)
        surface.blit(rook, (W / 2 - 66, ground - rook.get_height() + 10 + bob))
    elif kind == 'rook_letter':
        rook, juno = img('Player/p3_duck', 1.6), img('Player/p1_stand', 1.6)
        surface.blit(juno, (W / 2 - 300, ground - juno.get_height() + 8))
        surface.blit(rook, (W / 2 + 120, ground - rook.get_height() + 8))
        envelope(surface, W / 2, ground - 110 + bob, 130, 6)
        lens(surface, W / 2 + 330, ground - 60, t)
    elif kind == 'desert':
        for i in range(9):
            pg.draw.ellipse(surface, (196, 150, 100), (240 + i * 100, ground + 10 + (i % 2) * 10, 22, 9))
        surface.blit(img('Items/cactus', 1.4), (120, ground - 96))
        surface.blit(img('Items/rock', 1.2), (1040, ground - 80))


def lens(surface, x, y, t):
    glow = pg.Surface((200, 200), pg.SRCALPHA)
    for r in range(100, 0, -6):
        pg.draw.circle(glow, (255, 240, 170, 7), (100, 100), r)
    surface.blit(glow, (x - 100, y - 100))
    pg.draw.circle(surface, (255, 246, 200), (int(x), int(y)), 30)
    pg.draw.circle(surface, (255, 214, 110), (int(x), int(y)), 30, 5)
    pg.draw.circle(surface, (255, 255, 255), (int(x - 9), int(y - 9)), 8)


class Controls(Input):
    confirm = back = pause = restart = quit_level = read = False
    left = right = up = down = False


# ---------------------------------------------------------------- scenes
class Title:
    def __init__(self, app):
        self.app, self.t, self.choice = app, 0.0, 0
        self.fresh = not app.save['done'] and not app.save['intro']
        self.options = ['Start the route'] if self.fresh else ['Continue', 'New game']
        self.options.append('Quit')
        music('title')

    def update(self, dt, inp):
        self.t += dt
        if inp.up or inp.down:
            self.choice = (self.choice + (1 if inp.down else -1)) % len(self.options)
            sfx('select', 0.4)
        if inp.confirm:
            pick = self.options[self.choice]
            sfx('confirm')
            if pick == 'Quit':
                self.app.running = False
            elif pick == 'Continue':
                self.app.to_map()
            else:
                self.app.save.update({'done': {}, 'ability': None, 'intro': True, 'cursor': 0})
                self.app.write_save()
                self.app.scene = Panels(self.app, story.INTRO, lambda: Play(self.app, 0))

    def draw(self, surface):
        vignette(surface, 'tower_lit', self.t)
        juno = img('Player/p1_walk/PNG/p1_walk%02d' % (int(self.t * 12) % 11 + 1), 1.2)
        x = 160 + (self.t * 60) % 520
        surface.blit(juno, (x, 430 - juno.get_height() + 6))
        envelope(surface, x + 30, 330 + math.sin(self.t * 4) * 5, 44, 10)
        text(surface, 'LANTERN ROUTE', 110, (90, 70), PAPER, bold=True, shadow=INK)
        text(surface, 'Twelve letters. One lamp gone dark.', 30, (96, 200), GOLD, bold=True, shadow=INK)
        for i, option in enumerate(self.options):
            chosen = i == self.choice
            text(surface, ('>  ' if chosen else '    ') + option, 34, (96, 540 + i * 46),
                 GOLD if chosen else PAPER, bold=True, shadow=INK)


class Panels:
    """Storybook pages: a small scene above, a few lines of text below."""
    def __init__(self, app, pages, after, tune='story'):
        self.app, self.pages, self.after = app, pages, after
        self.page, self.t = 0, 0.0
        music(tune)

    def update(self, dt, inp):
        self.t += dt
        full = len(self.pages[self.page][1]) / 48
        if inp.confirm or inp.jump_pressed:
            if self.t < full:
                self.t = full + 1
            else:
                self.page += 1
                self.t = 0
                sfx('select', 0.4)
                if self.page >= len(self.pages):
                    self.page -= 1
                    self.app.scene = self.after()

    def draw(self, surface):
        kind, words = self.pages[self.page]
        vignette(surface, kind, self.t + self.page * 5)
        pg.draw.rect(surface, PAPER, (90, 510, W - 180, 180), border_radius=18)
        pg.draw.rect(surface, INK, (90, 510, W - 180, 180), 4, border_radius=18)
        shown = words[:int(self.t * 48)]
        for i, line in enumerate(wrap(shown, 27, W - 250)):
            text(surface, line, 27, (124, 532 + i * 36), INK)
        if self.t * 48 > len(words) and int(self.t * 2) % 2:
            text(surface, 'Enter', 20, (W - 120, 656), (150, 130, 120), 'topright', True)


class RouteMap:
    def __init__(self, app, cursor=None):
        self.app, self.t = app, 0.0
        self.unlocked = app.unlocked()
        self.cursor = min(self.unlocked, app.save.get('cursor', 0) if cursor is None else cursor)
        self.reading = False
        self.bands = None
        music('title')

    def node(self, i):
        return 78 + i * 93.5, 390 + math.sin(i * 1.05) * 62

    def update(self, dt, inp):
        self.t += dt
        if self.reading:
            if inp.confirm or inp.back or inp.read:
                self.reading = False
            return
        step = (1 if inp.right else 0) - (1 if inp.left else 0)
        if step and 0 <= self.cursor + step <= min(self.unlocked, len(story.ROUTE) - 1):
            self.cursor += step
            sfx('select', 0.4)
        self.app.save['cursor'] = self.cursor
        level_id = story.ROUTE[self.cursor][0]
        if inp.read and level_id in self.app.save['done'] and self.cursor < LETTERS:
            self.reading = True
        elif inp.confirm:
            sfx('confirm')
            self.app.scene = Play(self.app, self.cursor)
        elif inp.back:
            self.app.scene = Title(self.app)

    def draw(self, surface):
        if self.bands is None:
            self.bands = pg.Surface((W, H))
            order = ('grass', 'sand', 'snow', 'stone', 'night')
            edges = [0, 312, 592, 872, 1152, W]
            for i, name in enumerate(order):
                sky, layers, _ = make_background(THEMES[name], name)
                piece = sky.copy()
                for _, layer in layers:
                    piece.blit(layer, (-i * 300, 0))
                self.bands.blit(piece, (edges[i], 0), (edges[i], 0, edges[i + 1] - edges[i], H))
                if i:
                    pg.draw.line(self.bands, PAPER, (edges[i], 0), (edges[i], H), 3)
        surface.blit(self.bands, (0, 0))
        text(surface, 'THE ROUTE', 46, (40, 24), PAPER, bold=True, shadow=INK)
        done = self.app.save['done']
        gems = sum(sum(d.get('gems', [])) for d in done.values())
        surface.blit(img('HUD/hud_gem_red', 0.8), (W - 190, 30))
        text(surface, '%d / %d' % (gems, LETTERS * 3), 28, (W - 144, 30), PAPER, bold=True, shadow=INK)
        for i, name in enumerate(story.WORLDS):
            x = (78 + 93.5 * (i * 3 + 1)) if i < 4 else W - 66
            text(surface, name.upper(), 18, (x, 250), PAPER, 'midtop', True, INK)
        points = [self.node(i) for i in range(len(story.ROUTE))]
        for a, b in zip(points, points[1:]):
            for k in range(1, 6):
                pg.draw.circle(surface, PAPER, (int(a[0] + (b[0] - a[0]) * k / 6), int(a[1] + (b[1] - a[1]) * k / 6)), 4)
        for i, (x, y) in enumerate(points):
            level_id = story.ROUTE[i][0]
            if level_id in done:
                pg.draw.circle(surface, GOLD, (int(x), int(y)), 22)
                pg.draw.circle(surface, INK, (int(x), int(y)), 22, 4)
                envelope(surface, x, y, 24)
            elif i <= self.unlocked:
                r = 20 + math.sin(self.t * 5) * 3
                pg.draw.circle(surface, PAPER, (int(x), int(y)), int(r))
                pg.draw.circle(surface, INK, (int(x), int(y)), int(r), 4)
            else:
                pg.draw.circle(surface, (120, 116, 130), (int(x), int(y)), 16)
                pg.draw.circle(surface, INK, (int(x), int(y)), 16, 4)
            if i == 12:
                pass
        x, y = self.node(self.cursor)
        juno = img('Player/p1_front', 0.62)
        surface.blit(juno, (x - juno.get_width() / 2, y - 34 - juno.get_height() - abs(math.sin(self.t * 4)) * 10))

        entry = story.ROUTE[self.cursor]
        pg.draw.rect(surface, PAPER, (140, 540, W - 280, 150), border_radius=18)
        pg.draw.rect(surface, INK, (140, 540, W - 280, 150), 4, border_radius=18)
        head = 'Letter %d of %d' % (self.cursor + 1, LETTERS) if self.cursor < LETTERS else 'Epilogue'
        text(surface, head, 20, (172, 556), (150, 110, 90), bold=True)
        text(surface, entry[2], 40, (172, 578), INK, bold=True)
        if entry[3]:
            text(surface, 'To ' + entry[3] + (', ' + entry[4] if entry[4] else ''), 23, (172, 634), INK)
        record = done.get(entry[0])
        if record and self.cursor < LETTERS:
            for i, color in enumerate(('red', 'green', 'blue')):
                surface.blit(img('HUD/hud_gem_' + color, 0.8, alpha=None if record['gems'][i] else 60),
                             (W - 320 + i * 44, 558))
            m, s = divmod(int(record.get('time', 0)), 60)
            text(surface, 'Best %d:%02d' % (m, s), 22, (W - 172, 606), INK, 'topright', True)
        hint = 'Enter: set out' + ('     L: read the letter' if record and self.cursor < LETTERS else '')
        text(surface, hint, 20, (W - 172, 648), (150, 110, 90), 'topright', True)
        if self.reading:
            draw_letter(surface, self.cursor, 99, record['gems'])


def draw_letter(surface, index, t, gems):
    """The delivered letter on a sheet of paper; `t` drives the handwriting reveal."""
    entry = story.ROUTE[index]
    veil = pg.Surface((W, H), pg.SRCALPHA)
    veil.fill((20, 16, 30, 180))
    surface.blit(veil, (0, 0))
    sheet = pg.Rect(250, 40, 780, 560)
    pg.draw.rect(surface, (226, 214, 190), sheet.move(8, 10), border_radius=10)
    pg.draw.rect(surface, PAPER, sheet, border_radius=10)
    text(surface, 'Letter %d of %d' % (index + 1, LETTERS), 20, (sheet.x + 44, sheet.y + 28), (170, 130, 110), bold=True)
    pg.draw.circle(surface, (214, 72, 72), (sheet.right - 64, sheet.y + 56), 26)
    text(surface, 'M', 26, (sheet.right - 64, sheet.y + 56), PAPER, 'center', True)
    body = entry[5]
    shown = body[:int(t * 70)]
    y = sheet.y + 76
    for line in wrap(shown, 25, sheet.w - 100):
        text(surface, line, 25, (sheet.x + 48, y), INK)
        y += 35
    if t * 70 > len(body):
        y += 14
        pg.draw.line(surface, (220, 200, 170), (sheet.x + 48, y), (sheet.right - 48, y), 2)
        y += 16
        if all(gems):
            for line in wrap('P.S.  ' + entry[6], 23, sheet.w - 100):
                text(surface, line, 23, (sheet.x + 48, y), (150, 84, 70), bold=True)
                y += 32
        else:
            text(surface, 'P.S.  (smudged. Find all three gems on this round to read it.)', 21,
                 (sheet.x + 48, y), (180, 160, 150))


class Delivered:
    """After a level: the letter, then the tally."""
    def __init__(self, app, play, first_time):
        self.app, self.play, self.t = app, play, 0.0
        self.index = play.index
        self.first = first_time
        self.record = app.save['done'][play.id]
        music('story')

    def update(self, dt, inp):
        self.t += dt
        body = story.ROUTE[self.index][5]
        if inp.confirm or inp.jump_pressed:
            if self.t * 70 < len(body):
                self.t = len(body) / 70 + 0.1
            else:
                sfx('confirm')
                pages = story.AFTER.get(self.play.id) if self.first else None
                if self.play.id == 'w4_3' and self.first:
                    target = lambda: Play(self.app, 12)
                else:
                    target = lambda: RouteMap(self.app, min(self.index + 1, self.app.unlocked()))
                self.app.scene = Panels(self.app, pages, target) if pages else target()

    def draw(self, surface):
        vignette(surface, 'juno', self.t)
        draw_letter(surface, self.index, self.t, self.record['gems'])
        p = self.play
        pg.draw.rect(surface, INK, (250, 618, 780, 78), border_radius=14)
        text(surface, 'DELIVERED', 26, (280, 642), GOLD, bold=True)
        for i, color in enumerate(('red', 'green', 'blue')):
            surface.blit(img('HUD/hud_gem_' + color, 0.74, alpha=None if p.gems[i] else 60), (452 + i * 40, 638))
        surface.blit(img('HUD/hud_coins', 0.7), (600, 640))
        text(surface, '%d/%d' % (p.coins, p.total_coins), 24, (640, 641), PAPER, bold=True)
        m, s = divmod(int(p.time), 60)
        text(surface, '%d:%02d' % (m, s), 24, (790, 641), PAPER, bold=True)
        text(surface, 'Retries %d' % p.deaths, 24, (1000, 641), PAPER, 'topright', True)


class Credits:
    LINES = ['LANTERN ROUTE', '', 'Thank you for delivering every letter.', '',
             'Art: Kenney Vleugels, Platformer Art Deluxe (CC0)', 'Font: Nunito (SIL Open Font License)',
             'Music and sound: synthesised for this game', 'Built with Python and pygame', '',
             'Gems found: %d of 36', '', 'Press Enter']

    def __init__(self, app):
        self.app, self.t = app, 0.0
        music('title')

    def update(self, dt, inp):
        self.t += dt
        if inp.confirm and self.t > 1:
            self.app.to_map(12)

    def draw(self, surface):
        vignette(surface, 'night_lamps', self.t)
        veil = pg.Surface((W, H), pg.SRCALPHA)
        veil.fill((14, 12, 30, 150))
        surface.blit(veil, (0, 0))
        gems = sum(sum(d.get('gems', [])) for d in self.app.save['done'].values())
        for i, line in enumerate(self.LINES):
            line = line % gems if '%d' in line else line
            text(surface, line, 60 if i == 0 else 26, (W / 2, 70 + i * 44 + (0 if i == 0 else 40)),
                 GOLD if i == 0 else PAPER, 'midtop', True, INK)


# ---------------------------------------------------------------- app
class App:
    def __init__(self, headless=False):
        if headless:
            os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
            os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        pg.init()
        flags = 0 if headless else pg.SCALED | pg.RESIZABLE
        self.screen = pg.display.set_mode((W, H), flags)
        pg.display.set_caption('Lantern Route')
        init_audio()
        pg.joystick.init()
        self.pads = [pg.joystick.Joystick(i) for i in range(pg.joystick.get_count())]
        self.clock = pg.time.Clock()
        self.save = load_save()
        self.running = True
        self.headless = headless
        self.scene = Title(self)

    def unlocked(self):
        done = self.save['done']
        for i, entry in enumerate(story.ROUTE):
            if entry[0] not in done:
                return i
        return len(story.ROUTE) - 1

    def write_save(self):
        if self.headless:
            return
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as handle:
                json.dump(self.save, handle, indent=1)
        except OSError:
            pass

    def to_map(self, cursor=None):
        self.scene = RouteMap(self, cursor)

    def finish_level(self, play):
        first = play.id not in self.save['done']
        old = self.save['done'].get(play.id, {})
        best = old.get('time')
        self.save['done'][play.id] = {
            'gems': [a or b for a, b in zip(play.gems, old.get('gems', [False] * 3))],
            'time': play.time if best is None else min(best, play.time),
            'coins': max(play.coins, old.get('coins', 0)),
        }
        self.save['ability'] = play.player.ability
        self.write_save()
        if play.id == 'w5_1':
            self.scene = Panels(self, story.ENDING, lambda: Credits(self), 'ending')
        else:
            self.scene = Delivered(self, play, first)

    def read_input(self):
        inp = Controls()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                k = event.key
                if k in (pg.K_SPACE, pg.K_z, pg.K_k):
                    inp.jump_pressed = True
                if k in (pg.K_x, pg.K_j, pg.K_LSHIFT, pg.K_RSHIFT):
                    inp.action_pressed = True
                if k in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
                    inp.confirm = True
                if k == pg.K_ESCAPE:
                    inp.pause = inp.back = True
                if k == pg.K_p:
                    inp.pause = True
                if k == pg.K_r:
                    inp.restart = True
                if k == pg.K_q:
                    inp.quit_level = True
                if k == pg.K_l:
                    inp.read = True
                if k in (pg.K_LEFT, pg.K_a):
                    inp.left = True
                if k in (pg.K_RIGHT, pg.K_d):
                    inp.right = True
                if k in (pg.K_UP, pg.K_w):
                    inp.up = True
                if k in (pg.K_DOWN, pg.K_s):
                    inp.down = True
                if k == pg.K_m:
                    toggle_mute()
                if k == pg.K_F11:
                    pg.display.toggle_fullscreen()
            elif event.type == pg.JOYBUTTONDOWN:
                if event.button == 0:
                    inp.jump_pressed = inp.confirm = True
                elif event.button in (1, 2):
                    inp.action_pressed = True
                elif event.button == 7:
                    inp.pause = True
            elif event.type == pg.JOYHATMOTION:
                inp.left, inp.right = event.value[0] < 0, event.value[0] > 0
                inp.up, inp.down = event.value[1] > 0, event.value[1] < 0
        keys = pg.key.get_pressed()
        inp.x = (keys[pg.K_RIGHT] or keys[pg.K_d]) - (keys[pg.K_LEFT] or keys[pg.K_a])
        inp.y = (keys[pg.K_DOWN] or keys[pg.K_s]) - (keys[pg.K_UP] or keys[pg.K_w])
        inp.jump = keys[pg.K_SPACE] or keys[pg.K_z] or keys[pg.K_k]
        inp.run = keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT] or keys[pg.K_x] or keys[pg.K_j]
        for pad in self.pads:
            axis_x = pad.get_axis(0) if pad.get_numaxes() > 1 else 0
            axis_y = pad.get_axis(1) if pad.get_numaxes() > 1 else 0
            hat = pad.get_hat(0) if pad.get_numhats() else (0, 0)
            inp.x = inp.x or (axis_x > 0.4) - (axis_x < -0.4) or hat[0]
            inp.y = inp.y or (axis_y > 0.5) - (axis_y < -0.5) or -hat[1]
            inp.jump = inp.jump or pad.get_button(0)
            inp.run = inp.run or pad.get_button(1) or pad.get_button(2)
        return inp

    def run(self):
        while self.running:
            inp = self.read_input()
            self.scene.update(DT, inp)
            self.scene.draw(self.screen)
            pg.display.flip()
            self.clock.tick(FPS)
        self.write_save()
        pg.quit()


def main():
    app = App()
    for arg in sys.argv[1:]:
        if arg.startswith('--level='):
            app.scene = Play(app, story.index_of(arg.split('=')[1]))
    app.run()
