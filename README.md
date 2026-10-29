# Wandbound: Ravenmoor Academy — playable alpha

An editable Roblox RPG prototype built from your October 21, 2026 design plan.
This is version **0.1.0**, with a complete first-play loop and the 19 level 1–20
spell handlers. It is a development build, not the completed 18-week launch roadmap.

## Open and play

1. Extract this ZIP to a folder on your computer.
2. In **Roblox Studio**, open `Wandbound-Ravenmoor-Academy.rbxlx` using **File → Open from File**.
3. Press **Play (F5)**. Use Play, rather than Run, so Studio creates a player.
4. Close the welcome panel. Walk to **Oakhart's Wandery**, the shop on the left of the village square. Use its interaction prompt to receive a wand.
5. NPC prompts open conversations: select their service, ask for advice, or ask what to do next.
6. Follow the gold quest marker: Mirror of Choosing → Professor Quill → Training Yard → Tobb → Whisperwood.

No toolbox models, external scripts, paid assets, packages, plugins, asset IDs,
or Rojo installation are required to open this place. The map is already embedded
in Workspace and remains editable in Studio. Code lives in Explorer under
ReplicatedStorage/Shared, ServerScriptService/Services, and StarterPlayerScripts/Controllers.

**Studio practice sessions deliberately do not save.** Published servers use the
DataStore automatically. See `docs/SAVING.md` before testing persistence.

## What you can play

| System | Included behavior |
|---|---|
| World | Storybook Hollowmere (four half-timbered shops, six cottages, paved plaza, lanes, iron lamp posts), curbed academy road and forest path, sky-ferry, terraced academy campus with Main Gate, Grand Stair, Great Hall, five free-standing classroom halls, library, towers and four separate house quarters, training yard, Mirrorlake scenery, Whisperwood clearings, grotto, duel platform |
| Tutorial | First wand, three starter spells, five-question sorting quiz with free house choice, first lesson, five dummy hits, first hunt |
| Combat | Server mana/cooldowns, traveling spherecast projectiles, shield, mirror reflect, self/ally healing, AoE, chain lightning, dodge, light, silence, chill, root, sleep, burn, crowd-control diminishing returns |
| Spells | All 19 spells up to level 20 have handlers; all 29 planned spells appear as catalogue entries, with the remaining 10 clearly locked as future content |
| Learning | On-demand professor lessons; server-scored gesture tracing; five moving targets; server-confirmed hits; two-minute repeat reward cooldown per subject |
| Progression | Level cap 20, two attribute points per level, XP formulas from your plan, five mastery power tiers, daily free attribute reset at the Library |
| Skill tree | One skill point per level; 20 skills across the five schools in three tiers (damage, cooldowns, mana, wards, healing, durations, health); daily free reset at the Library |
| Wands | 6 woods × 5 cores × 3 rarities, each built as a 3D wand from parts. Wood and core each grant a small bonus. Hold one, carry up to 10, buy more from Oakhart, rare boss drops. Three named wands with their own bodies and signatures: Stormfork (The Rotbark Seal reward), Hearthroot (Oakhart commission from Heartwood) and Widow's Bite (Epic, Mother Vexweave drop or 5 trophies) |
| Quests | 11 sequential tutorial/story objectives through Vexweave, plus one daily 15-enemy task |
| Enemies | Five Whisperwood species and Mother Vexweave; aggro, threat from damage, chase, obstacle steering, return, telegraphed attacks, respawning, personal contribution loot |
| Boss | Web roots in phase 1; broodlings in phase 2; faster attacks and lingering pools in phase 3 |
| Houses | Sorting, perks, colored avatar sash, saved personal contribution, standings for the current server |
| Economy | Gilders, ingredients, spell tomes, bank, Health Draught purchase/brewing/use, three Resero chests, discovered Waystones with 25-Gilder travel |
| Duels | Two-sided invitation, 3-second countdown, 1-HP loss, timeout/forfeit, no item loss, one active match at a time, reward cap of 10 per hour |
| Presentation | Parchment menus, brass accents, resource bars, cooldowns, boss bar, quest marker, local spell effects, zone color transition and 20-minute day |
| Data | Native UpdateAsync profile store, expiring session lock, periodic save, leave/shutdown save, no blank live fallback on load failure |

The first quest chain unlocks Flamara's level requirement after the Thornimp hunt.
Classes, monsters and the daily task provide repeatable XP for later spell levels.
Professor Quill can teach a starter practice lesson before you qualify for Resero.

## Controls

| Action | Keyboard / mouse | Gamepad | Touch |
|---|---|---|---|
| Spark Bolt | Left mouse; hold to repeat | RT | Scintara button |
| Ward | Right mouse | LT | Ward button |
| Spell slots | 1, 2, 3, 4 | X, Y, B, RB | Four spell buttons |
| Dodge | Left Shift, or double-tap W/A/S/D | LB | Dodge button |
| Broom: take off and land | F | D-pad Down | Broom button |
| Broom: climb and dive | Space and Q, or look up or down while flying forward | A and L3 | Look up or down |
| Jump | Space | A | Roblox jump button |
| Spellbook | K | D-pad Up | Spellbook button |
| Bag (wands and items) | B | D-pad Left | Bag tab in spellbook |
| Map | M | D-pad Right | Waystone prompt |
| Free cursor / aim lock | Left Ctrl | Default camera | Default camera |
| Interact | Prompt, usually E | Prompt, usually X | Tap prompt |
| Gesture lesson | Drag one stroke | Hold RT + left stick, X to submit | Drag one stroke |

In the spellbook, click **1–4** beneath a learned spell to equip it. Ward spells
also offer **Ward** for the right-mouse / LT ward slot. Basic Spark Bolt stays bound.
Spell controls pause while a menu or text box has focus.

Spoken casting recognizes an exact learned incantation in general chat, such as
`Flamara`, or `/cast Flamara`. It uses the same server checks, adds 10% power and
0.3 seconds of cast time, and can be disabled in Settings. It requires access to
Roblox chat. There is no voice input or microphone feature.

## Important differences from the full plan

- The map is a compact, stylized prototype with part-based scenery, not the final 2048-stud sculpted world. Mirrorlake is decorative geometry in this build.
- Lessons run on demand so the first session is immediately playable. The HUD rotates a suggested subject every five minutes; this is not a scheduled shared lecture or Potions class.
- House standings are local to this server. No global Sunday Cup, weekly winner buff, House War or cross-server leaderboard is implemented.
- Friendly duels retain each player's actual stats. Ranked Crucible, normalized builds, Elo matchmaking and reserved-server teleports are not implemented. The Elo formula is present and tested only as shared math.
- Wands are the only gear. Layered robes, mastery upgrade choices, familiars, wandcrafting and other equipment slots are future work. The house sash is a simple welded cosmetic.
- Brewing is one click and supports Health Draught only. No cauldron timing game, full shop catalogue, premium currency, passes, Robux purchases, receipt processing or trading is enabled.
- The quest chain is a condensed prototype story. Full Chapters 1–2 dialogue, additional daily/weekly quests, the Leviathan, Frostspire, Catacombs, Shadowfen and later chapters remain on the roadmap.
- No imported music, cast audio, voice recordings, cutscenes or custom rig animations are bundled. Dodge is a validated short displacement with invulnerability; the final rolling animation is not included.
- Touch/gamepad bindings and aim assistance are implemented but need device testing. Gesture validation checks submitted paths and server-observed targets; it cannot prove a human physically traced a submitted path.
- Saving uses a small native session-locked service, rather than bundling ProfileStore. Review and stress-test it before a public launch or a future purchase system.

## Editing and rebuilding

The `.rbxlx` file is ready to edit directly in Studio. The ZIP also provides source
for VS Code workflows:

```text
src/shared/          Spell, wand, skill tree, monster, quest, formula, gesture and config modules
src/server/Services/ Server-owned gameplay and persistence
src/serverstorage/   Private loot tables
src/client/          HUD, input, camera and local effects
world/               Editable map, markers and spawn models for Rojo
tools/build.py       Rebuild the XML place and models with Python 3 (houses, roads, lamps)
tools/sync_scripts.py Copy src/ scripts (and with --map, the map) into the place
tools/validate.py    Static, parser and headless logic checks
tests/headless.lua   Mock-based gameplay assertions
docs/               Playtest, saving, architecture and original plan
blender/             Blender scripts for meshes, rigs and animations (see blender/README.md)
tools/blender.py     Run those scripts in Blender and export FBX files for Studio's 3D Importer
```

From this folder:

```bash
python tools/sync_scripts.py
python tools/validate.py
```

After editing code in `src/`, close the place in Studio (save any map edits first) and
run `sync_scripts.py`. It updates only script text and adds new scripts, so map edits
saved from Studio are kept, and it writes a `.bak` copy first. It refuses to run while
Studio has the place open, because saving from that Studio session would overwrite the
synced scripts. `build.py` regenerates the entire place instead (see below).

The map's houses, roads and lamps are generated from data in `tools/build.py` (`SHOPS`,
`HOMES`, `LANES`, `GARDEN_PATHS`, and the `timber_house`/`road_trim`/`lamp` builders), as is the
Castle Grounds training yard (`training_yard`, `YARD_WALLS`, `YARD_PIERS`). To change
them without losing anything else in your Studio-saved place, close the place in Studio and run:

```bash
python tools/build.py --world-only
```

```bash
python tools/sync_scripts.py --map
```

`--world-only` regenerates only the `world/` models. `--map` swaps just `Workspace/Map` into the
place: scripts, Markers, Spawns, Terrain and lighting stay byte for byte, and a `.bak` copy
is written first. Map edits you made in Studio are replaced, so make lasting changes in
`build.py` instead. `validate.py` notes when the place map differs from `world/Map.rbxmx`.
It fails if a shop door no longer lines up with its NPC prompt, for example after the map
was moved or rotated.

`build.py` needs only Python's standard library. The validator's Lua checks need a
Lua 5.4 shared library; the source intentionally uses the Lua subset supported by
Luau. The validator is not a replacement for Studio's engine or script analysis.
On Windows, set `WANDBOUND_LUA_LIBRARY` to the full path of your Lua 5.4 DLL if it
is not on PATH (for example, `$env:WANDBOUND_LUA_LIBRARY = 'C:\xampp\apache\bin\lua54.dll'`
in PowerShell when XAMPP is installed).

If you already use Rojo, `default.project.json` maps the scripts and generated
models into Studio. Start from the supplied place to retain the lighting setup.
**Rebuilding overwrites the generated place and world models.** Keep a separate
saved copy if you have edited the map in Studio. Move source markers in `tools/build.py`
and rebuild to keep generated quest waypoints synchronized.

Tune numerical values in `src/shared/Config.lua`, `SpellData.lua`, `MonsterData.lua`,
`WandData.lua`, `SkillData.lua` and `Formulas.lua`. Live save data is stored under `Wandbound_Alpha_v1`; do not change
that name on a live experience unless you intend to start a separate save namespace.

## Verification status

Completed here: XML integrity and source parity checks; all 27 source files parsed;
334 mocked logic assertions, including delayed client startup, every NPC service,
inventory actions and gamepad prompt routing; all 25 classroom target positions checked against
solid map geometry; shop doors checked against their prompts; houses checked clear of
roads, lanes and each other; walking routes up every academy stair to each hall, house quarter and quest anchor; map kept within 3,300 parts. No imported executable assets or numeric asset requires exist.

**Not run here:** Roblox Studio opening/play mode, actual Roblox physics/replication,
live DataStore calls, chat behavior, real multiplayer, phone/controller playtests,
or performance profiling. Follow `docs/PLAYTEST.md` before sharing the experience.

## API references used during implementation

- [Roblox raycasting and Spherecast](https://create.roblox.com/docs/reference/engine/classes/WorldRoot)
- [TextChannel delivery callbacks](https://create.roblox.com/docs/reference/engine/classes/TextChannel)
- [Custom text chat commands](https://create.roblox.com/docs/chat/examples/custom-text-chat-commands)
- [Player data and session locking](https://create.roblox.com/docs/cloud-services/data-stores/player-data-purchasing)

Original design: `docs/Original-design-plan.txt`. Code and generated geometry are
provided as editable project material for your game.

## Academy campus

The academy is a terraced campus built from the exterior concept canvas: an arrival plaza and Grand Stair, two classroom wings, an upper terrace with the Great Hall, and four separate house quarters to the north. Interiors are not furnished yet. See [the academy design and site plan](docs/ACADEMY-DESIGN.md). The campus on its own is in `world/RavenmoorAcademy.rbxmx`.
