# Design notes

The brief was to make the game look less generated, play better, tell a better
story and be longer, by studying how the best platformers are built. This is
what was taken from that study and what was deliberately not.

## What was borrowed: craft, not content

Lantern Route has its own hero, cast, story, music and stages. What it takes
from the classics of the genre are methods.

**Movement first.** Before any stage was drawn the jump was tuned: quick
acceleration, a skid when you reverse, a run button, a jump whose height
follows how long the button is held and whose distance follows your speed,
0.1 s of grace after walking off a ledge, and a jump press remembered for
0.12 s before landing. Stomping an enemy bounces you, higher if jump is held.
All numbers are in `lantern/settings.py`.

**Stages are built from the jump.** Every gap and ledge is a multiple of what
the jump can do (see the table in `LEVELS.md`), so distances read correctly at
a glance.

**One idea per stage, in four beats.** Each stage introduces its idea where it
cannot hurt, develops it, twists it, then asks for it under pressure. Example,
Shell Game: one snail on flat ground beside a wall (the shell comes back at
you); a lane of five slimes to bowl over; a shell that must be sent under a
roof to break into a gem alcove; then shells among pits.

**Teach by layout.** Coins trace the arc of a jump. The first enemy walks
toward you on open ground. Signs are used only for button names.

**Protection in layers, generous restarts.** Three hearts, refilled at
checkpoints; fifty coins or a five-stomp chain restores one. Falling in a pit
costs a heart and returns you to safe ground rather than restarting the stage.

**Secrets with a reason.** Three gems per stage: usually one in plain sight
that asks for a good jump, one behind the stage's mechanic, one that needs an
ability or a second look. The reward is narrative: the letter's postscript.

## Story

The earlier build was a chase after a villain. This one is a delivery round.
The keeper's twelve letters gradually admit that she watched the lens being
taken, that she had left the door unlocked for years for the child who took
it, and that nobody above ground ever asked what it is like to live under the
mountain. The last letter is addressed to the thief. The boss fight ends when
you hand it over. The epilogue is a walk up the hill past everyone you
delivered to.

## Look

All sprites and tiles come from one hand-drawn set by one artist, so nothing
clashes. Code-drawn elements use the same flat shapes and palette. Motion adds
the rest: squash and stretch on the hero, dust, a short freeze on a stomp,
screen shake on heavy hits, parallax hills, and real darkness with pools of
torchlight in the Underhollow.

## How it was checked, and what was not

- `tools/levelcheck.py` explores every stage with the real player physics and
  confirms the door is reachable. It treats moving platforms, switch blocks and
  locks optimistically and does not model enemies.
- `tools/bot.py` runs a simple auto-player through the real game loop on every
  stage to catch crashes.
- `tests/test_lantern.py` covers jump height, damage, stomping, switches, the
  boss and the screen flow.

None of that replaces a person playing it. Difficulty, pacing and the boss
have not been tuned by hand.
