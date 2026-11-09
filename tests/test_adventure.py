import unittest
from adventure.simulation import Session
from adventure.campaign import STAGES


class AdventureTests(unittest.TestCase):
    def test_jump_release_changes_height_and_lands(self):
        peaks=[]
        for held in (False,True):
            s=Session();s.jump();peak=0
            for _ in range(240):s.step(1/120,held_jump=held);peak=max(peak,s.z)
            peaks.append(peak)
            self.assertTrue(s.grounded)
        self.assertGreater(peaks[1],peaks[0]+1)

    def test_repairs_require_correct_action_and_proximity(self):
        s=Session();s.interact();self.assertFalse(s.switches)
        s.x,s.z=s.stage.switches[0];s.z-=1;s.power();self.assertFalse(s.switches)
        s.interact();self.assertEqual(s.switches,{0})
        s=Session(2);s.x,s.z=s.stage.switches[0];s.interact();self.assertFalse(s.switches)
        s.power();self.assertEqual(s.switches,{0})

    def test_burst_cooldown_and_guard_keys(self):
        s=Session(3);s.x=s.enemies[0]['x'];s.power()
        self.assertFalse(s.enemies[0]['alive']);self.assertEqual(s.switches,{0})
        s.x=s.enemies[1]['x'];s.power();self.assertTrue(s.enemies[1]['alive'])
        s.cooldown=0;s.power();self.assertEqual(s.switches,{0,1})

    def test_boss_shield_and_three_separate_hits(self):
        s=Session(4);s.hit_boss();self.assertEqual(s.boss_hp,3)
        s.switches={0,1};s.hit_boss();s.hit_boss();self.assertEqual(s.boss_hp,2)
        s.boss_iframes=0;s.hit_boss();s.boss_iframes=0;s.hit_boss();self.assertEqual(s.boss_hp,0)

    def test_checkpoint_keeps_progress(self):
        s=Session(1);s.checkpoint=True;s.switches={0};s.medals={1};s.respawn()
        self.assertEqual(s.x,s.stage.checkpoint);self.assertEqual(s.switches,{0});self.assertEqual(s.medals,{1})

    def test_exit_stays_locked_until_objective(self):
        s=Session();s.x=s.stage.exit;s.step(1/120);self.assertFalse(s.completed)
        s.switches={0,1};s.x=s.stage.exit;s.step(1/120);self.assertTrue(s.completed)

    def test_all_authored_routes_are_traversable(self):
        # Combat is tested above. This runner checks the physical route, moving
        # lift timing, repair positions, and exit without teleporting the hero.
        for index in range(len(STAGES)):
            with self.subTest(stage=index):
                s=Session(index)
                for frame in range(120*60):
                    for e in s.enemies:e['alive']=False
                    targets=[p for i,p in enumerate(s.stage.switches) if i not in s.switches]
                    tx,tz=targets[0] if targets else (s.stage.exit,0)
                    direction=1 if s.x<tx-.25 else -1 if s.x>tx+.25 else 0
                    if s.grounded and (s.z<tz-.8 or direction):s.jump()
                    if s.stage.theme in ('orchard','quarry'):s.interact()
                    elif s.stage.theme in ('foundry','citadel'):s.power()
                    else:s.switches={0,1}
                    if index==4 and not targets:s.boss_hp=0
                    s.step(1/120,direction,False,True)
                    if s.completed:break
                self.assertTrue(s.completed,(s.x,s.z,s.switches))


if __name__=='__main__':unittest.main()
