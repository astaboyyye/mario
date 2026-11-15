# Level format

Levels are text files in `lantern/levels/`. A file is a short header, then
sections separated by a line starting with `-`. Sections are joined left to
right and aligned at the bottom, so each one only needs the rows it uses.
Rows start with `|`. Lines starting with `.` are column rulers and are ignored.

Header keys: `theme` (grass, sand, snow, stone, castle, night), `music`,
`items` (what each `!` box gives, left to right: heart, cloud, heels, star),
`signs` (texts separated by `|`, left to right), `dark: 1`, `dim` (darkness
0-255), `rows` (minimum height), `cave` (bottom rows drawn as underground),
`needs` (ability the level cannot be finished without; used by the checker).

| Char | Meaning | Char | Meaning |
| --- | --- | --- | --- |
| `#` | ground | `=` | one-way ledge |
| `B` | crate (breaks from below or by shell) | `X` | solid block |
| `?` | coin box | `!` | item box |
| `o` | coin | `G` | gem (three per level) |
| `h` | heart | `K` `L` | key, lock |
| `S` | spring | `H` | ladder |
| `C` | checkpoint | `E` | door (goal) |
| `P` | start | `p` | sign |
| `^` | spikes | `~` | water or lava |
| `s` | slime | `n` | snail |
| `f` | fly | `F` | fish or fireball (place in liquid) |
| `k` | needle | `T` | stone face |
| `M` and `-` | platform and its horizontal rail | `V` and `:` | platform and its vertical rail |
| `D` | plank that falls | `R` | button |
| `r` `b` | red / blue switch block | `Z` | boss |
| `N` `O` | villager, Rook | `, ; j l u a A m` | plant, bush, fence, torch, window, scenery |

Design numbers (48 px tiles): a standing jump rises 4 tiles, a running jump
about 4.7. Keep required rises to 3. A walking jump crosses 5 tiles, a running
jump 8; keep required gaps to 4 (walk) or 6 (run). A spring lifts 6.9 tiles.
Boxes meant to be hit from the ground sit with three empty rows beneath them.

After editing, run `python tools/levelcheck.py <id>`. It writes a picture to
`previews/levels/` and explores the level with the real jump physics to
confirm the door and gems can be reached.
