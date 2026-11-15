# Lantern Route

A hand-drawn side-scrolling platformer. Twelve letters, thirteen stages, one
lamp gone dark.

The lighthouse at Lanternhead has lost its lens. You are Juno, in your first
week as the valley's post carrier, and the keeper has given you twelve letters
and one instruction: don't chase the thief, just deliver these, in order.
Every stage ends at a door. Every door gets a letter, and the letters tell
the story.

## Play

Run `dist\LanternRoute.exe`, or from source:

```powershell
.\.venv\Scripts\python.exe lantern_route.py
```

| Control | Action |
| --- | --- |
| Arrows or A / D | Move |
| Space or Z | Jump. Hold for height |
| Shift or X | Run. Throw the Post Star when you have it |
| Up / Down | Climb ladders. Down + Jump drops through a ledge |
| R | Back to the last checkpoint |
| Esc or P | Pause |
| L (on the route map) | Re-read a delivered letter |
| M / F11 | Mute / fullscreen |

A gamepad works too: stick or d-pad, A to jump, B or X to run.

## What is in it

- Four regions and an epilogue: Greenway, Saltpan, Frostline, Underhollow,
  then the walk up to Lanternhead. Thirteen stages.
- Each stage is built around one idea and teaches it before testing it:
  shell kicking, falling planks, needles on a timer, keys and wells, red and
  blue switch blocks, a double jump, stone faces you can ride, a vertical
  climb, stages in the dark, and a five-hit boss.
- Three abilities found in item boxes: the Cloud Coat (float), Spring Heels
  (double jump) and the Post Star (a thrown star that comes back and fetches
  things through walls).
- Three gems hidden in every stage. Finding all three un-smudges the
  postscript on that stage's letter.
- Three hearts. A pit costs one and puts you back on the last safe ground;
  losing all three returns you to the checkpoint. There are no lives.
- Progress, gems and best times save to `lantern-save.json` beside the game.

## Source

| Path | Contents |
| --- | --- |
| `lantern/levels/*.txt` | The stages, as text. See `LEVELS.md` |
| `lantern/story.py` | Every letter, cutscene and sign |
| `lantern/actors.py` | Player, enemies, pickups, boss |
| `lantern/world.py` | Level loading, collision, backgrounds |
| `lantern/play.py` | The in-stage rules, camera, HUD |
| `lantern/game.py` | Window, input, title, route map, story screens |
| `tools/levelcheck.py` | Stage previews and a reachability check using the real jump physics |
| `tools/make_audio.py` | Synthesises all music and sound effects |
| `tools/bot.py` | A crude auto-player used as a crash test |

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_lantern -v
.\.venv\Scripts\python.exe tools\levelcheck.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean lantern_route.spec
```

Only `pygame` is needed to run from source.

## Older builds

`adventure/` and `data/` hold the two earlier versions of this project (the 3D
pilot and the original pixel recreation). The launcher no longer starts them.
They, `resources/graphics`, `resources/music`, `resources/sound`,
`mario_level_1.exe` and `release/` are not used by Lantern Route and can be
deleted.

Credits are in `ASSET_CREDITS.md`; design reasoning is in `DESIGN_NOTES.md`.

See the [release notes](RELEASE_NOTES.md) and [visual comparison](previews/COMPARISON.md)
with the previous builds.
