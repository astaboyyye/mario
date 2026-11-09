"""Sunstone Trail: quest mechanics, layered scenery, and interface."""
import math
from functools import lru_cache
import pygame as pg
from . import setup, constants as c

INK = (24, 41, 63)
CREAM = (255, 249, 225)
GOLD = (255, 204, 77)
STONES = ((620, 475), (3515, 140), (7105, 405))


@lru_cache(maxsize=128)
def art(name, size):
    image = pg.image.load(str(setup.PROJECT_ROOT / 'resources' / 'quest_pack' / name)).convert_alpha()
    if name.startswith('Items/'):
        image = image.subsurface(image.get_bounding_rect())
    return pg.transform.smoothscale(image, size)


@lru_cache(maxsize=24)
def font(size):
    return pg.font.Font(None, size)


def text(surface, value, pos, size=24, color=CREAM):
    surface.blit(font(size).render(str(value), True, color), pos)


def panel(surface, rect, color=INK):
    pg.draw.rect(surface, color, rect, border_radius=16)


@lru_cache(maxsize=1)
def sky():
    image = pg.Surface((800, 600))
    for y in range(600):
        t = y / 600
        pg.draw.line(image, (int(83+137*t), int(173+65*t), int(218+17*t)), (0,y), (800,y))
    return image


def scenery(surface, camera=0, time=0):
    surface.blit(sky(), (0,0))
    pg.draw.circle(surface, (255,238,171), (668,130), 44)
    for i in range(6):
        x = int((i*210-camera*.16-time*.004) % 1150)-180
        surface.blit(art('Items/cloud1.png',(150,80)), (x,95+(i%3)*37))
    for factor, color, baseline, height in ((.19,(126,192,189),490,190),(.35,(76,163,145),525,155)):
        for i in range(-1,6):
            x=int(i*260-(camera*factor)%260)
            pg.draw.ellipse(surface,color,(x,baseline-height,350,height*2))


def title(surface, time):
    scenery(surface, time=time)
    for x in range(0,800,43):
        surface.blit(art('Tiles/grassMid.png',(43,43)),(x,538))
        surface.blit(art('Tiles/grassCenter.png',(43,43)),(x,581))
    panel(surface,(42,46,716,456))
    text(surface,'MARIO  /  A NEW ADVENTURE',(76,75),22,GOLD)
    text(surface,'The Sunstone Trail',(72,111),62)
    text(surface,'The castle beacon has gone dark.',(76,182),29)
    text(surface,'Three Sunstones were scattered across the meadow.',(76,220),24)
    text(surface,'Find them, master the star burst, and bring the light home.',(76,249),24)
    for i, label in enumerate(('01  Find the stones','02  Cross the valley','03  Relight the beacon')):
        text(surface,label,(78+i*223,308),20,GOLD)
    panel(surface,(76,358,276,55),GOLD)
    text(surface,'ENTER  Begin the quest',(96,373),28,INK)
    text(surface,'SPACE  Jump    Z  Star burst    SHIFT  Run',(76,442),23)
    text(surface,'ARROWS  Move     P  Pause     F11  Fullscreen',(76,470),20,(160,191,206))
    surface.blit(art('Items/gemYellow.png',(55,55)),(671,360))


def story_screen(surface, game, state):
    scenery(surface)
    panel(surface,(75,130,650,340))
    won = game.get('quest_complete',False)
    if state == c.GAME_OVER:
        heading = 'The meadow shines again!' if won else 'Every hero gets another try.'
        lines = ('All three Sunstones are home. The beacon is restored.',
                 'Thank you, Mario. A new dawn begins.') if won else (
                 'The Sunstone Trail is waiting for you.', 'Return to the title screen and begin a new adventure.')
    elif state == c.TIME_OUT:
        heading = 'The light is fading...'
        lines = ('Take a breath. Your recovered Sunstones are safe.', 'A fresh attempt begins in a moment.')
    else:
        heading = 'Chapter 1: The Sunstone Trail'
        lines = ('Recover the three glowing stones and reach the castle.',
                 'Z unleashes a star burst. It recharges in four seconds.')
    text(surface,heading,(105,174),37,GOLD)
    for i,line in enumerate(lines): text(surface,line,(105,243+i*36),24)
    text(surface,f"SUNSTONES  {len(game.get('sunstones',[]))}/3     LIVES  {game[c.LIVES]}",(105,365),27)
    text(surface,'SPACE jumps. Hold SHIFT to run. Follow the golden trail.',(105,408),21)


class Quest:
    def __init__(self, level):
        self.level = level
        self.collected = level.game_info.setdefault('sunstones', [])
        self.ready_at = 0
        self.key_down = False
        self.burst_until = 0
        self.message = 'Recover the three Sunstones. Z unleashes your star burst.'
        self.message_until = level.game_info[c.CURRENT_TIME] + 4500

    def update(self, keys):
        level, hero = self.level, self.level.mario
        now = level.current_time
        if hero.dead or hero.in_castle or hero.in_transition_state:
            return
        for i, (x,y) in enumerate(STONES):
            if i not in self.collected and hero.rect.colliderect(pg.Rect(x-6,y-6,44,44)):
                self.collected.append(i)
                level.game_info[c.SCORE] += 1000
                setup.SFX['powerup'].play()
                self.message = ('All Sunstones recovered! Return to the castle beacon.' if len(self.collected)==3
                                else f'Sunstone {len(self.collected)}/3 recovered. Keep following the trail!')
                self.message_until = now + 3500
        pressed = keys[pg.K_z]
        if pressed and not self.key_down and now >= self.ready_at:
            self.ready_at, self.burst_until = now+4000, now+450
            setup.SFX['fireball'].play()
            for enemy in list(level.enemy_group) + list(level.shell_group):
                if pg.Vector2(enemy.rect.center).distance_to(hero.rect.center) < 170:
                    enemy.kill()
                    enemy.start_death_jump(c.RIGHT if enemy.rect.centerx > hero.rect.centerx else c.LEFT)
                    level.sprites_about_to_die_group.add(enemy)
                    level.game_info[c.SCORE] += 100
        self.key_down = pressed

    def world(self, world):
        level = self.level
        view = level.viewport
        surface = world.subsurface(view)
        scenery(surface,view.x,level.current_time)
        for ground in level.ground_group:
            r=ground.rect
            start=max(r.x, r.x + ((view.x-r.x)//43)*43)
            for x in range(start,min(r.right,view.right+43),43):
                width=min(43,r.right-x)
                surface.blit(art('Tiles/grassMid.png',(43,43)),(x-view.x,r.y),(0,0,width,43))
                surface.blit(art('Tiles/grassCenter.png',(43,43)),(x-view.x,r.y+43),(0,0,width,43))
        for step in level.step_group:
            if step.rect.colliderect(view):
                r=step.rect.move(-view.x,0)
                pg.draw.rect(surface,(132,116,99),r,border_radius=4)
                pg.draw.rect(surface,(214,191,145),r,3,border_radius=4)
        for x in (380, 1490, 2260, 3180, 4160, 5070, 6870, 7420):
            if -120 < x-view.x < 800:
                surface.blit(art('Items/bush.png',(100,45)),(x-view.x,493))
        for pipe in level.pipe_group:
            r=pipe.rect.move(-view.x,0)
            if r.right>0 and r.left<800:
                pg.draw.rect(surface,(24,125,109),r,border_radius=10)
                pg.draw.rect(surface,(91,210,145),(r.x+9,r.y,15,r.h),border_radius=7)
                pg.draw.rect(surface,(42,160,120),(r.x-4,r.y,r.w+8,22),border_radius=6)
                pg.draw.line(surface,(159,239,158),(r.x+4,r.y+4),(r.right-4,r.y+4),3)
        castle_x=8670-view.x
        if castle_x<800:
            pg.draw.rect(surface,(240,212,162),(castle_x,345,210,193),border_radius=9)
            for x in (castle_x-16,castle_x+160):
                pg.draw.rect(surface,(255,232,188),(x,315,65,223),border_radius=7)
                pg.draw.polygon(surface,(209,86,73),[(x-8,315),(x+32,265),(x+73,315)])
            pg.draw.rect(surface,INK,(castle_x+82,455,50,83),border_radius=25)
            surface.blit(art('Items/gemYellow.png',(36,36)),(castle_x+89,370))
        for i,(x,y) in enumerate(STONES):
            if i not in self.collected:
                bob=int(math.sin(level.current_time/230+i)*6)
                surface.blit(art('Items/gemYellow.png',(32,32)),(x-view.x,y+bob))
        for group, name in ((level.brick_group,'Tiles/box.png'),(level.coin_box_group,'Tiles/boxCoin.png')):
            for sprite in group:
                sprite.image=art('Tiles/boxEmpty.png' if sprite.state == c.OPENED else name,sprite.rect.size)

    def hud(self, surface):
        level=self.level
        game=level.game_info
        panel(surface,(18,16,764,64))
        text(surface,'SUNSTONE TRAIL',(34,27),22,GOLD)
        text(surface,'MEADOW  /  CHAPTER 01',(34,53),16,(160,191,206))
        text(surface,f"{len(self.collected)}/3 STONES",(265,36),27)
        text(surface,f"{game[c.LIVES]} LIVES",(430,36),24)
        text(surface,f"{game[c.COIN_TOTAL]} COINS",(545,36),24)
        text(surface,f"{max(0,level.overhead_info_display.time)}",(706,33),32,GOLD)
        remaining=max(0,self.ready_at-level.current_time)
        panel(surface,(18,92,190,37))
        text(surface,'Z  STAR BURST' if not remaining else f'Z  RECHARGING {remaining/1000:.1f}s',(31,102),20,GOLD)
        missing = [i for i in range(3) if i not in self.collected]
        if missing:
            nearest = min(missing, key=lambda i: abs(STONES[i][0]-level.mario.rect.x))
            direction = 'LEFT' if STONES[nearest][0] < level.mario.rect.x else 'RIGHT'
            objective = f"SUNSTONE {nearest+1}  /  HEAD {direction}"
        else:
            objective = 'ALL STONES FOUND  /  REACH THE CASTLE'
        panel(surface,(228,92,365,37))
        text(surface,objective,(242,102),20)
        if level.current_time < self.message_until:
            panel(surface,(65,553,670,33))
            text(surface,self.message,(81,562),20)
        if level.current_time < self.burst_until:
            radius=int(170*(1-(self.burst_until-level.current_time)/450))
            pg.draw.circle(surface,GOLD,(level.mario.rect.centerx-level.viewport.x,level.mario.rect.centery),max(5,radius),4)
