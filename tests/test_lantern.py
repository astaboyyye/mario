"""Headless checks for Lantern Route: python -m unittest tests.test_lantern -v"""
import os
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from lantern import actors as A, story, settings as S
from lantern.game import App, Controls, Delivered, Panels, Credits, RouteMap, Title
from lantern.play import Play

app = App(headless=True)


def step(scene_owner, frames, **held):
    inp = Controls()
    for key, value in held.items():
        setattr(inp, key, value)
    for _ in range(frames):
        scene_owner.scene.update(S.DT, inp)


class Levels(unittest.TestCase):
    def test_every_level_loads_with_goal_and_gems(self):
        for index, entry in enumerate(story.ROUTE):
            play = Play(app, index)
            gems = sum(isinstance(i, A.Gem) for i in play.items)
            doors = sum(isinstance(i, A.Door) for i in play.items)
            self.assertTrue(doors == 1 or play.boss, entry[0])
            if entry[0] != 'w5_1':
                self.assertEqual(gems, 3, entry[0])
            self.assertTrue(all(len(row) == play.level.w for row in play.level.grid))

    def test_every_level_runs_and_draws(self):
        for index in range(len(story.ROUTE)):
            app.scene = Play(app, index)
            for frame in range(420):
                inp = Controls()
                inp.x, inp.run = 1, frame % 90 > 30
                inp.jump = frame % 45 < 18
                inp.jump_pressed = frame % 45 == 0
                inp.action_pressed = frame % 70 == 0
                app.scene.update(S.DT, inp)
                if frame % 60 == 0:
                    app.scene.draw(app.screen)

    def test_letters_exist_for_all_twelve(self):
        for entry in story.ROUTE[:12]:
            self.assertTrue(entry[3] and entry[5] and entry[6], entry[0])


class Movement(unittest.TestCase):
    def jump(self, hold, run=0):
        play = Play(app, 0)
        p = play.player
        step_inp = A.Input()
        for _ in range(30):
            p.update(step_inp, S.DT, play)
        floor = p.y
        p.vx = run
        best = 0
        for frame in range(120):
            inp = A.Input()
            inp.jump_pressed = frame == 0
            inp.jump = frame < hold
            p.update(inp, S.DT, play)
            best = max(best, floor - p.y)
        return best / S.TILE

    def test_held_jump_clears_four_tiles(self):
        self.assertTrue(3.8 < self.jump(60) < 4.3)

    def test_tap_is_a_short_hop(self):
        self.assertLess(self.jump(2), 2.0)

    def test_pit_costs_a_heart_and_returns_to_safe_ground(self):
        play = Play(app, 0)
        p = play.player
        for _ in range(30):
            p.update(A.Input(), S.DT, play)
        safe = p.safe
        p.y = play.level.h * S.TILE + 200
        p.update(A.Input(), S.DT, play)
        self.assertEqual(p.hearts, S.MAX_HEARTS - 1)
        self.assertEqual((p.x, p.y), safe)


class Rules(unittest.TestCase):
    def test_stomp_kills_slime_and_bounces(self):
        play = Play(app, 0)
        slime = next(e for e in play.enemies if isinstance(e, A.Slime))
        p = play.player
        p.x, p.y, p.vy = slime.x, slime.y - p.h - 2, 300
        play.cam_x = p.x - 600
        play.update(S.DT, Controls())
        play.update(S.DT, Controls())
        self.assertLess(p.vy, 0)
        self.assertFalse(slime.harmful)
        self.assertEqual(p.hearts, S.MAX_HEARTS)

    def test_side_contact_hurts(self):
        play = Play(app, 0)
        slime = next(e for e in play.enemies if isinstance(e, A.Slime))
        p = play.player
        p.x, p.y = slime.x - 10, slime.y + slime.h - p.h
        play.cam_x = p.x - 600
        play.update(S.DT, Controls())
        self.assertEqual(p.hearts, S.MAX_HEARTS - 1)

    def test_button_swaps_blocks(self):
        play = Play(app, story.index_of('w2_3'))
        button = next(i for i in play.items if isinstance(i, A.Button))
        self.assertTrue(play.level.red_on)
        button.press(play)
        self.assertFalse(play.level.red_on)

    def test_boss_takes_five_stomps_then_level_ends(self):
        app.scene = play = Play(app, story.index_of('w4_3'))
        boss = play.boss
        play.player.x = boss.left + 3 * S.TILE
        play.cam_x = play.level.w * S.TILE - S.W
        step(app, 5)
        self.assertNotEqual(boss.state, 'wait')
        for _ in range(boss.HP):
            boss.flash = 0
            boss.stomp(play)
        self.assertEqual(boss.hp, 0)
        step(app, 400)
        self.assertIsInstance(app.scene, Delivered)


class Flow(unittest.TestCase):
    def test_finishing_a_level_shows_the_letter_then_the_map(self):
        app.save['done'] = {}
        app.scene = play = Play(app, 0)
        play.gems = [True, True, True]
        app.finish_level(play)
        self.assertIsInstance(app.scene, Delivered)
        self.assertEqual(app.save['done']['w1_1']['gems'], [True, True, True])
        app.scene.draw(app.screen)
        step(app, 1, confirm=True)
        step(app, 1, confirm=True)
        self.assertIsInstance(app.scene, RouteMap)
        self.assertEqual(app.unlocked(), 1)
        app.scene.draw(app.screen)

    def test_epilogue_leads_to_ending_and_credits(self):
        app.scene = play = Play(app, 12)
        app.finish_level(play)
        self.assertIsInstance(app.scene, Panels)
        for _ in range(len(story.ENDING) * 2 + 1):
            app.scene.draw(app.screen)
            step(app, 1, confirm=True)
        self.assertIsInstance(app.scene, Credits)
        app.scene.draw(app.screen)

    def test_title_and_intro_draw(self):
        app.scene = Title(app)
        app.scene.draw(app.screen)
        app.scene = Panels(app, story.INTRO, lambda: Title(app))
        for _ in range(3):
            app.scene.draw(app.screen)
            step(app, 30)


if __name__ == '__main__':
    unittest.main()
