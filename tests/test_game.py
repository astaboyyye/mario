"""Regression checks for the game loop and the playable level."""

import os
import unittest
from collections import defaultdict

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg

from data import constants as c
from data import level_layout as layout
from data import setup
from data.states.level1 import Level1
from data.states.load_screen import LoadScreen
from data.states.main_menu import Menu
from data.tools import Control


class GameSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup.initialize()

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    def make_level(self):
        level = Level1()
        level.startup(0, Menu().persist)
        return level

    def test_space_jumps_and_z_burst_recharges(self):
        level = self.make_level()
        keys = defaultdict(bool)
        keys[pg.K_SPACE] = True
        level.update(setup.SCREEN, keys, 16)
        self.assertLess(level.mario.y_vel, 0)
        from data.components.enemies import Goomba
        enemy = Goomba(x=level.mario.rect.x + 60)
        level.enemy_group.add(enemy)
        keys[pg.K_z] = True
        level.update(setup.SCREEN, keys, 32)
        self.assertNotIn(enemy, level.enemy_group)
        ready = level.quest.ready_at
        level.update(setup.SCREEN, keys, 48)
        self.assertEqual(level.quest.ready_at, ready)

    def test_stones_persist_and_lock_castle(self):
        level = self.make_level()
        level.mario.rect.topleft = (620,475)
        level.current_time = 16
        level.quest.update(defaultdict(bool))
        self.assertEqual(level.game_info['sunstones'], [0])
        retry = Level1()
        retry.startup(100, level.game_info)
        self.assertEqual(retry.quest.collected, [0])
        retry.current_time = 100
        retry.mario.rect.x = 8504
        retry.check_points_check()
        self.assertNotEqual(retry.mario.state, c.FLAGPOLE)
        retry.game_info['sunstones'][:] = [0,1,2]
        retry.mario.rect.x = 8504
        retry.check_points_check()
        self.assertEqual(retry.mario.state, c.FLAGPOLE)

    def test_menu_to_level_transition(self):
        menu = Menu()
        loading = LoadScreen()
        level = Level1()
        control = Control(c.ORIGINAL_CAPTION, setup.SCREEN)
        control.setup_states({c.MAIN_MENU: menu, c.LOAD_SCREEN: loading,
                              c.LEVEL1: level}, c.MAIN_MENU)
        menu.done = True
        control.update()
        self.assertEqual(control.state_name, c.LOAD_SCREEN)
        control.current_time = 3000
        control.update()
        control.update()
        self.assertEqual(control.state_name, c.LEVEL1)
        self.assertEqual(level.mario.rect.x, 110)
        control.present()

    def test_running_is_faster_than_walking(self):
        positions = []
        for running in (False, True):
            level = self.make_level()
            keys = defaultdict(bool)
            keys[pg.K_RIGHT] = True
            keys[pg.K_LSHIFT] = running
            for frame in range(70):
                level.update(setup.SCREEN, keys, frame * 16)
            positions.append(level.mario.rect.x)
        self.assertGreater(positions[1], positions[0] + 30)
        self.assertLessEqual(level.mario.x_vel, c.MAX_RUN_SPEED)

    def test_pause_keeps_the_frame_stable(self):
        level = self.make_level()
        level.update(setup.SCREEN, defaultdict(bool), 16)
        control = Control(c.ORIGINAL_CAPTION, setup.SCREEN)
        control.setup_states({c.LEVEL1: level}, c.LEVEL1)
        control.set_paused(True)
        control.draw_pause_overlay()
        first = pg.image.tobytes(control.screen, "RGB")
        control.draw_pause_overlay()
        self.assertEqual(pg.image.tobytes(control.screen, "RGB"), first)
        control.set_paused(False)

    def test_simulation_uses_fixed_steps(self):
        control = Control(c.ORIGINAL_CAPTION, setup.SCREEN)
        menu = Menu()
        control.setup_states({c.MAIN_MENU: menu}, c.MAIN_MENU)
        control.accumulator = 0
        control.advance(50.1)
        self.assertAlmostEqual(control.current_time, 50)
        self.assertEqual(menu.game_info[c.CURRENT_TIME], control.current_time)

    def test_mute_controls_music_and_effects(self):
        control = Control(c.ORIGINAL_CAPTION, setup.SCREEN)
        control.toggle_mute()
        self.assertTrue(control.muted)
        self.assertEqual(pg.mixer.music.get_volume(), 0)
        self.assertEqual(next(iter(setup.SFX.values())).get_volume(), 0)
        control.toggle_mute()
        self.assertFalse(control.muted)
        self.assertEqual(pg.mixer.music.get_volume(), 1)

    def test_resized_window_preserves_logical_screen(self):
        control = Control(c.ORIGINAL_CAPTION, setup.SCREEN)
        control.setup_states({c.MAIN_MENU: Menu()}, c.MAIN_MENU)
        pg.event.post(pg.event.Event(pg.VIDEORESIZE, w=1000, h=700))
        control.event_loop()
        control.present()
        self.assertEqual(setup.SCREEN.get_size(), c.SCREEN_SIZE)
        self.assertEqual(pg.display.get_surface().get_size(), (1000, 700))

    def test_castle_checkpoint_ends_player_control(self):
        level = self.make_level()
        level.game_info["sunstones"] = [0, 1, 2]
        level.mario.rect.x = 8775
        level.check_points_check()
        self.assertEqual(level.state, c.IN_CASTLE)
        self.assertEqual(level.mario.state, c.STAND)
        self.assertTrue(level.mario.in_castle)

    def test_level_layout_builds_all_groups(self):
        level = self.make_level()
        self.assertEqual(len(level.ground_group), len(layout.GROUND_RECTS))
        self.assertEqual(len(level.pipe_group), len(layout.PIPE_RECTS))
        self.assertEqual(len(level.step_group), len(layout.STEP_RECTS))
        self.assertEqual(len(level.brick_group), len(layout.BRICKS))
        self.assertEqual(len(level.coin_box_group), len(layout.COIN_BOXES))
        self.assertEqual(len(level.enemy_group_list), len(layout.ENEMY_WAVES))
        self.assertEqual(len(level.check_point_group), len(layout.CHECKPOINTS))
        level.mario.rect.x = 510
        level.check_points_check()
        self.assertEqual(len(level.enemy_group), 1)

    def test_death_and_level_clear_transitions(self):
        level = self.make_level()
        level.mario.dead = True
        level.death_timer = 1
        level.current_time = 4000
        level.play_death_song()
        self.assertEqual(level.game_info[c.LIVES], 2)
        self.assertEqual(level.next, c.LOAD_SCREEN)

        cleared = self.make_level()
        cleared.flag_timer = 1
        cleared.current_time = 4000
        cleared.end_game()
        self.assertTrue(cleared.done)
        self.assertEqual(cleared.next, c.GAME_OVER)


if __name__ == "__main__":
    unittest.main()
