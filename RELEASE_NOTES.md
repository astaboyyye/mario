# v2.0.0 — Lantern Route

An original, hand-drawn side-scrolling platformer about delivering twelve
letters after the lighthouse goes dark.

- Thirteen stages across Greenway, Saltpan, Frostline, Underhollow, and the
  Lanternhead epilogue.
- A new hero, Juno, and a story told through one letter after each stage.
- Three hidden gems per stage, which reveal each letter's postscript.
- Three abilities, checkpoints, a route map, and a five-hit boss.
- Original synthesised music and sound effects, plus local progress saving.

Run the Windows build from `LanternRoute-v2.0.0-win64.zip`, or run
`python lantern_route.py` after installing `requirements.txt`.

See the [visual comparison](previews/COMPARISON.md) with the original World 1-1
recreation and the v1.0.0 Starfall pilot.

Validation: 13 automated tests passed. A full human playthrough is still
needed for difficulty and pacing.

# v1.0.0 — The Last Train to Starfall

The first playable 3D campaign release.

- Five connected story stages: Applewater Orchard, Switchback Quarry, Copperpipe Foundry, The Sky Express, and Starfall Engine.
- Real 3D geometry, lighting, shadows, modeled Mario and enemies, and a following side camera.
- Each stop has a distinct task. The last stage has a shielded Bowser Jr. fight.
- Optional medals, checkpoints, route selection, and local stage unlock saving.
- Space jumps, Z triggers a rechargeable burst, E interacts, and Shift runs.
- The previous Sunstone Trail remains available with `--legacy`.

Windows executable: `mario_level_1.exe`. Run it from any folder. Progress is stored beside the executable in `starfall-save.json`.

See [the visual comparison](previews/COMPARISON.md) for the original recreation and the new campaign.

Validation: 18 automated tests passed; the packaged executable rendered all five stages and ran 600 simulation frames in its smoke check. A complete human playthrough is still needed.
